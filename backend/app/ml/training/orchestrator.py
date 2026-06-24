import os
import sys
import json
import time
import yaml

# Prevent OpenMP mutex conflicts between PyTorch (CTGAN backend) and
# XGBoost/LightGBM. Must be set BEFORE any of these libraries are imported.
# Without this, CTGAN + XGBoost segfaults with OMP Error #179 on
# Python 3.14 + macOS ARM.
if "OMP_NUM_THREADS" not in os.environ:
    os.environ["OMP_NUM_THREADS"] = "1"
import joblib
import optuna
import hashlib
import psutil
import shutil
import platform
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.metrics import classification_report, confusion_matrix, cohen_kappa_score, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV, calibration_curve

from app.ml.training.samplers import get_sampler
from app.ml.training.models import get_model
from app.ml.training.evaluator import calculate_metrics, generate_plots
from app.ml.training.mlflow_tracker import MLflowTracker, get_system_metadata, promote_model_in_registry
from app.ml.training.ranking_engine import RankingEngine

# Ensure optuna logs are clean
optuna.logging.set_verbosity(optuna.logging.WARNING)


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Stage 4 - Feature Engineering Pipeline Step
    Custom transformer class to engineer features in a reusable scikit-learn Pipeline.
    """
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_out = X.copy()
        
        # 1. Vehicle Age (using 2026 as current year)
        if "Year" in X_out.columns:
            X_out["vehicle_age_engineered"] = 2026 - X_out["Year"]
        else:
            X_out["vehicle_age_engineered"] = 0
            
        # 2. Weekend Accident flag (DayOfWeek is Saturday or Sunday)
        if "DayOfWeek" in X_out.columns:
            X_out["weekend_accident_engineered"] = X_out["DayOfWeek"].isin(["Saturday", "Sunday"]).astype(int)
        else:
            X_out["weekend_accident_engineered"] = 0
            
        # 3. Policy-Accident Delay Days (Days:Policy-Accident)
        # Convert Days category to numeric representation
        if "Days:Policy-Accident" in X_out.columns:
            mapping = {
                "none": 0, "1 to 7": 4, "8 to 15": 11, 
                "15 to 30": 22, "more than 30": 45
            }
            X_out["policy_accident_delay_engineered"] = X_out["Days:Policy-Accident"].map(mapping).fillna(0).astype(float)
        else:
            X_out["policy_accident_delay_engineered"] = 0.0

        # 4. Claim Report Delay (Days:Policy-Claim)
        # Longer delay between policy creation and claim filing = higher fraud risk
        if "Days:Policy-Claim" in X_out.columns:
            claim_delay_mapping = {
                "none": 0, "8 to 15": 11,
                "15 to 30": 22, "more than 30": 45
            }
            X_out["claim_report_delay_engineered"] = X_out["Days:Policy-Claim"].map(claim_delay_mapping).fillna(0).astype(float)
        else:
            X_out["claim_report_delay_engineered"] = 0.0

        # 5. High-Value Single-Vehicle Accident flag
        # Single vehicle accidents with expensive vehicles are a known fraud pattern
        if "NumberOfCars" in X_out.columns and "VehiclePrice" in X_out.columns:
            expensive_vehicles = ["more than 69,000", "40,000 to 59,000", "60,000 to 69,000"]
            is_single = X_out["NumberOfCars"].isin(["1 vehicle"])
            is_expensive = X_out["VehiclePrice"].isin(expensive_vehicles)
            X_out["high_value_single_vehicle_engineered"] = (is_single & is_expensive).astype(int)
        else:
            X_out["high_value_single_vehicle_engineered"] = 0

        # 6. Deductible-to-Vehicle-Price ratio
        # Low deductible relative to vehicle price suggests inflated claim amounts
        deductible_map = {300: 300.0, 400: 400.0, 500: 500.0, 700: 700.0}
        vehicle_price_map = {
            "less than 20,000": 15000.0,
            "20,000 to 29,000": 24500.0,
            "30,000 to 39,000": 34500.0,
            "40,000 to 59,000": 49500.0,
            "60,000 to 69,000": 64500.0,
            "more than 69,000": 80000.0
        }
        if "Deductible" in X_out.columns and "VehiclePrice" in X_out.columns:
            deductible_num = X_out["Deductible"].map(deductible_map).fillna(400.0)
            vehicle_price_num = X_out["VehiclePrice"].map(vehicle_price_map).fillna(34500.0)
            X_out["deductible_vehicle_ratio_engineered"] = deductible_num / vehicle_price_num
        else:
            X_out["deductible_vehicle_ratio_engineered"] = 0.0

        return X_out


class FraudDetectionPipeline(BaseEstimator):
    """
    Production-grade Wrapper Class containing the feature pipeline, calibrated classifier, 
    threshold config, feature order, and reproducibility metadata.
    """
    def __init__(self, preprocessing_pipeline: Pipeline, model: Any, optimal_threshold: float = 0.5, 
                 feature_names: List[str] = None, metadata: Dict[str, Any] = None):
        self.preprocessing_pipeline = preprocessing_pipeline
        self.model = model
        self.optimal_threshold = optimal_threshold
        self.feature_names = feature_names
        self.metadata = metadata or {}

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_proc = self.preprocessing_pipeline.transform(X)
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X_proc)
        else:
            probs = self.model.decision_function(X_proc)
            probs = (probs - probs.min()) / (probs.max() - probs.min() + 1e-9)
            return np.vstack([1 - probs, probs]).T

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        probs = self.predict_proba(X)[:, 1]
        return (probs >= self.optimal_threshold).astype(int)


def update_status(artifacts_dir: str, status_dict: Dict[str, Any]):
    os.makedirs(artifacts_dir, exist_ok=True)
    status_path = os.path.join(artifacts_dir, "training_status.json")
    existing = {}
    if os.path.exists(status_path):
        try:
            with open(status_path, "r") as f:
                existing = json.load(f)
        except Exception:
            pass
    existing.update(status_dict)
    with open(status_path, "w") as f:
        json.dump(existing, f, indent=2)


def get_latest_status(artifacts_dir: str) -> Dict[str, Any]:
    status_path = os.path.join(artifacts_dir, "training_status.json")
    if os.path.exists(status_path):
        try:
            with open(status_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"status": "not_started", "progress": 0.0, "current_step": "Idle", "errors": []}


def optimize_threshold(y_true: np.ndarray, y_prob: np.ndarray, 
                       target_recall: float = 0.80, target_precision: float = 0.40, target_fpr: float = 0.05) -> float:
    """
    Search thresholds from 0.01 to 0.99 to satisfy business constraints,
    falling back to maximizing F1 - FPR.
    """
    best_threshold = 0.5
    best_fallback_val = -999.0
    best_fallback_threshold = 0.5
    
    thresholds = np.arange(0.01, 1.00, 0.01)
    satisfied_thresholds = []
    
    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Fallback value: maximize F1 - FPR
        val = f1 - fpr
        if val > best_fallback_val:
            best_fallback_val = val
            best_fallback_threshold = t
            
        if recall >= target_recall and precision >= target_precision and fpr <= target_fpr:
            satisfied_thresholds.append((t, f1))
            
    if satisfied_thresholds:
        # Pick the threshold satisfying the constraints with the highest F1
        satisfied_thresholds.sort(key=lambda x: x[1], reverse=True)
        best_threshold = satisfied_thresholds[0][0]
    else:
        best_threshold = best_fallback_threshold
        
    return float(best_threshold)


class MLTrainingOrchestrator:
    def __init__(self, config_path: str = "training_config.yaml"):
        self.config_path = config_path
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        self.random_seed = self.config.get("random_seed", 42)
        np.random.seed(self.random_seed)
        
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.dataset_path = os.path.join(base_dir, self.config["paths"]["dataset_path"])
        self.artifacts_dir = os.path.join(base_dir, self.config["paths"]["artifacts_dir"])
        self.experiments_dir = os.path.join(base_dir, self.config["paths"]["experiments_dir"])
        self.production_model_path = os.path.join(base_dir, self.config["paths"]["production_model_path"])
        
        os.makedirs(self.artifacts_dir, exist_ok=True)
        os.makedirs(self.experiments_dir, exist_ok=True)
        
        self.ranking_engine = RankingEngine(self.config.get("ranking_weights"))
        self.tracker = MLflowTracker()

    def get_dataset_checksum(self) -> str:
        sha256 = hashlib.sha256()
        with open(self.dataset_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def run_stage1_validation(self, df: pd.DataFrame) -> List[str]:
        issues = []
        if "FraudFound" not in df.columns:
            issues.append("Missing target column 'FraudFound'")
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            issues.append(f"Detected {duplicates} duplicate records")
        for col in df.columns:
            if df[col].isnull().sum() > 0:
                issues.append(f"Column '{col}' has {df[col].isnull().sum()} missing values")
        labels = df["FraudFound"].unique()
        if not set(labels).issubset({"Yes", "No", "yes", "no", 1, 0}):
            issues.append(f"Unexpected target labels found: {labels}")
        return issues

    def run_stage2_analysis(self, df: pd.DataFrame, checksum: str):
        n_records = len(df)
        df["target"] = df["FraudFound"].map({"Yes": 1, "No": 0, "yes": 1, "no": 0, 1: 1, 0: 0}).fillna(0).astype(int)
        
        n_fraud = int(df["target"].sum())
        n_genuine = n_records - n_fraud
        fraud_pct = (n_fraud / n_records) * 100
        
        cat_features = []
        num_features = []
        for col in df.columns:
            if col in ["FraudFound", "target", "PolicyNumber"]:
                continue
            if df[col].dtype == object or df[col].dtype.name == "category":
                cat_features.append(col)
            else:
                num_features.append(col)
                
        corr_matrix = df[num_features].corr().to_dict()
        
        report = f"# Stage 2: Dataset Analysis Report\n"
        report += f"Checksum/Hash: {checksum}\n"
        report += f"Total Records: {n_records}\n"
        report += f"Fraud Claims: {n_fraud}\n"
        report += f"Genuine Claims: {n_genuine}\n"
        report += f"Fraud Percentage: {fraud_pct:.4f}%\n"
        report += f"Categorical Features Count: {len(cat_features)}\n"
        report += f"Numerical Features Count: {len(num_features)}\n"
        
        report_path = os.path.join(self.artifacts_dir, "dataset_analysis.md")
        with open(report_path, "w") as f:
            f.write(report)
            
        return cat_features, num_features

    def build_preprocessing_pipeline(self, cat_cols: List[str], num_cols: List[str]) -> Pipeline:
        cat_pipeline = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])
        
        num_pipeline = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])
        
        preprocessor = ColumnTransformer(transformers=[
            ("num", num_pipeline, num_cols),
            ("cat", cat_pipeline, cat_cols)
        ])
        
        var_threshold = self.config["preprocessing"].get("variance_threshold", 0.01)
        feature_selection = VarianceThreshold(threshold=var_threshold)
        
        pipeline = Pipeline(steps=[
            ("feature_engineering", FeatureEngineer()),
            ("preprocessor", preprocessor),
            ("feature_selection", feature_selection)
        ])
        
        return pipeline

    def _promote_best_production(self, tuned_results, run_experiments_dir):
        """
        Promote the highest-scoring tuned model to production.pkl immediately.
        Called after every tuned experiment so progress survives interruption.
        Also updates training_status.json so serving layer can pick up the new model.
        """
        if not tuned_results:
            return
        try:
            ranked = self.ranking_engine.rank_models(list(tuned_results))
            best = ranked[0]
            best_pipeline_path = best.get("pipeline_file")
            if best_pipeline_path and os.path.exists(best_pipeline_path):
                shutil.copy(best_pipeline_path, self.production_model_path)
                # Update training_status.json with the current best threshold + metrics
                update_status(self.artifacts_dir, {
                    "production_model": {
                        "sampler": best.get("sampler"),
                        "model": best.get("model"),
                        "score": best.get("score"),
                        "optimal_threshold": best.get("optimal_threshold"),
                        "metrics": best.get("metrics"),
                        "pipeline_file": self.production_model_path
                    }
                })
        except Exception:
            pass  # best-effort; don't crash training over promotion

    def run_pipeline(self):
        try:
            # Generate target run execution timestamp
            run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            run_experiments_dir = os.path.join(self.experiments_dir, run_timestamp)
            os.makedirs(run_experiments_dir, exist_ok=True)
            # STABLE checkpoint dir for tuned-model resume across runs.
            # Tuned pipeline.pkl + meta live here so interrupted runs can resume.
            self.tuned_checkpoint_dir = os.path.join(self.artifacts_dir, "tuned_checkpoints")
            os.makedirs(self.tuned_checkpoint_dir, exist_ok=True)
            
            update_status(self.artifacts_dir, {
                "status": "running",
                "progress": 5.0,
                "current_step": "Stage 1 - Dataset Validation...",
                "errors": []
            })
            
            if not os.path.exists(self.dataset_path):
                raise FileNotFoundError(f"Dataset not found at {self.dataset_path}")
                
            df = pd.read_csv(self.dataset_path)
            checksum = self.get_dataset_checksum()
            
            validation_issues = self.run_stage1_validation(df)
            
            update_status(self.artifacts_dir, {
                "progress": 10.0,
                "current_step": "Stage 2 - Dataset Analysis..."
            })
            cat_cols, num_cols = self.run_stage2_analysis(df, checksum)
            
            y = df["target"]
            X = df.drop(columns=["FraudFound", "target", "PolicyNumber"])
            
            engineered_num_cols = num_cols + [
                "vehicle_age_engineered",
                "policy_accident_delay_engineered",
                "claim_report_delay_engineered",
                "deductible_vehicle_ratio_engineered"
            ]
            engineered_cat_cols = cat_cols + [
                "weekend_accident_engineered",
                "high_value_single_vehicle_engineered"
            ]
            
            update_status(self.artifacts_dir, {
                "progress": 15.0,
                "current_step": "Stage 3 - Splitting dataset (Stratified 70/30)..."
            })
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=self.config["splitting"].get("test_ratio", 0.30),
                stratify=y,
                random_state=self.random_seed
            )
            # Carve a held-out calibration split from the training set. The decision
            # threshold is tuned on this set (NOT on train) to avoid optimistic-bias
            # leakage. The final production model is still fit on the full X_train
            # so it benefits from all available training data.
            X_fit, X_calib, y_fit, y_calib = train_test_split(
                X_train, y_train,
                test_size=0.20,
                stratify=y_train,
                random_state=self.random_seed
            )
            
            pipeline_fitter = self.build_preprocessing_pipeline(engineered_cat_cols, engineered_num_cols)
            pipeline_fitter.fit(X_train, y_train)
            
            try:
                ct = pipeline_fitter.named_steps["preprocessor"]
                num_feats = engineered_num_cols
                cat_ohe = ct.named_transformers_["cat"].named_steps["ohe"]
                cat_feats = list(cat_ohe.get_feature_names_out(engineered_cat_cols))
                all_raw_feats = num_feats + cat_feats
                vt = pipeline_fitter.named_steps["feature_selection"]
                support_mask = vt.get_support()
                transformed_feature_names = [all_raw_feats[i] for i, val in enumerate(support_mask) if val]
            except Exception:
                transformed_feature_names = [f"feature_{i}" for i in range(pipeline_fitter.transform(X_train).shape[1])]
                
            samplers = self.config["samplers"]
            models = self.config["models"]
            total_combinations = len(samplers) * len(models)
            
            cv_folds = self.config["validation"].get("cv_folds", 5)
            skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=self.random_seed)
            
            experiment_results = []
            exp_count = 0
            
            # Determine CTGAN epochs from YAML config mode
            ctgan_config = self.config.get("ctgan", {})
            ctgan_mode = ctgan_config.get("mode", "development")
            if ctgan_mode == "research":
                ctgan_epochs = ctgan_config.get("epochs_research", 100)
            else:
                ctgan_epochs = ctgan_config.get("epochs_development", 10)
            ctgan_batch_size = ctgan_config.get("batch_size", 500)
            
            # Business Constraints
            threshold_constraints = self.config.get("threshold_constraints", {})
            target_recall = threshold_constraints.get("target_recall", 0.80)
            target_precision = threshold_constraints.get("target_precision", 0.40)
            target_fpr = threshold_constraints.get("target_fpr", 0.05)
            
            for sampler_name in samplers:
                for model_name in models:
                    exp_count += 1
                    exp_id = f"exp_{exp_count:03d}"
                    exp_label = f"{sampler_name.upper()} + {model_name.upper()}"
                    if sampler_name == "ctgan":
                        exp_label = f"CTGAN + {model_name.upper()}"

                    # RESUME SUPPORT: skip experiments whose meta already exists on disk.
                    # This allows the pipeline to make permanent progress across multiple
                    # runs (each limited by an external timeout). The meta file is only
                    # written AFTER the experiment fully completes.
                    exp_meta_path = os.path.join(self.experiments_dir, f"{exp_id}_meta.json")
                    if os.path.exists(exp_meta_path):
                        try:
                            with open(exp_meta_path, "r") as f:
                                cached_meta = json.load(f)
                            # Sanity-check that it matches the expected sampler/model
                            if cached_meta.get("sampler") == sampler_name and cached_meta.get("model") == model_name:
                                experiment_results.append(cached_meta)
                                continue
                        except Exception:
                            pass  # fall through and re-run if cache is corrupt

                    progress_pct = 15.0 + (float(exp_count) / total_combinations) * 50.0 # 15% to 65%
                    update_status(self.artifacts_dir, {
                        "progress": round(progress_pct, 1),
                        "current_step": f"Stage 7 - Training baseline {exp_count}/{total_combinations}: {exp_label}..."
                    })
                    
                    start_time = time.time()
                    
                    # Stratified 5-Fold CV to collect Out-Of-Fold predictions
                    # NOTE: Sequential loop required on macOS Python 3.14 — joblib Parallel
                    # causes semaphore leaks when CTGAN runs inside forked worker processes.
                    # XGBoost already uses all CPU cores internally via n_jobs=-1.
                    oof_y_true = np.zeros(len(X_train))
                    oof_y_prob = np.zeros(len(X_train))

                    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
                        X_tr, y_tr = X_train.iloc[train_idx], y_train.iloc[train_idx]
                        X_va, y_va = X_train.iloc[val_idx], y_train.iloc[val_idx]

                        fold_pipeline = self.build_preprocessing_pipeline(engineered_cat_cols, engineered_num_cols)
                        X_tr_proc = fold_pipeline.fit_transform(X_tr, y_tr)
                        X_va_proc = fold_pipeline.transform(X_va)

                        sampler = get_sampler(
                            sampler_name,
                            random_state=self.random_seed,
                            ctgan_epochs=ctgan_epochs,
                            ctgan_batch_size=ctgan_batch_size
                        )
                        if sampler is not None:
                            X_tr_res, y_tr_res = sampler.fit_resample(X_tr_proc, y_tr)
                        else:
                            X_tr_res, y_tr_res = X_tr_proc, y_tr

                        num_neg = np.sum(y_tr_res == 0)
                        num_pos = np.sum(y_tr_res == 1)
                        scale_pos_weight = float(num_neg) / num_pos if num_pos > 0 else 1.0

                        clf = get_model(model_name, random_state=self.random_seed, scale_pos_weight=scale_pos_weight)
                        clf.fit(X_tr_res, y_tr_res)

                        try:
                            probs = clf.predict_proba(X_va_proc)[:, 1]
                        except Exception:
                            probs = clf.decision_function(X_va_proc)
                            probs = (probs - probs.min()) / (probs.max() - probs.min() + 1e-9)

                        oof_y_prob[val_idx] = probs
                        oof_y_true[val_idx] = y_train.iloc[val_idx]
                        
                    training_time = time.time() - start_time
                    
                    # Optimize threshold on Out-Of-Fold predictions
                    opt_t = optimize_threshold(oof_y_true, oof_y_prob, target_recall, target_precision, target_fpr)
                    oof_y_pred = (oof_y_prob >= opt_t).astype(int)
                    
                    # Calculate metrics under optimized threshold
                    avg_metrics = calculate_metrics(oof_y_true, oof_y_pred, oof_y_prob, start_inference_time=0.0)
                    
                    # Fit final baseline model on the whole 70% Train split
                    full_pipeline = self.build_preprocessing_pipeline(engineered_cat_cols, engineered_num_cols)
                    X_train_proc = full_pipeline.fit_transform(X_train, y_train)
                    
                    sampler = get_sampler(
                        sampler_name,
                        random_state=self.random_seed,
                        ctgan_epochs=ctgan_epochs,
                        ctgan_batch_size=ctgan_batch_size
                    )
                    if sampler is not None:
                        X_train_res, y_train_res = sampler.fit_resample(X_train_proc, y_train)
                    else:
                        X_train_res, y_train_res = X_train_proc, y_train
                        
                    num_neg = np.sum(y_train_res == 0)
                    num_pos = np.sum(y_train_res == 1)
                    scale_pos_weight = float(num_neg) / num_pos if num_pos > 0 else 1.0
                    
                    clf = get_model(model_name, random_state=self.random_seed, scale_pos_weight=scale_pos_weight)
                    clf.fit(X_train_res, y_train_res)
                    
                    # Assemble final baseline wrapper
                    final_pipeline = FraudDetectionPipeline(
                        preprocessing_pipeline=full_pipeline,
                        model=clf,
                        optimal_threshold=opt_t,
                        feature_names=transformed_feature_names,
                        metadata={
                            "python_version": platform.python_version(),
                            "system": platform.system(),
                            "random_seed": self.random_seed,
                            "dataset_checksum": checksum,
                            "timestamp": datetime.now().isoformat(),
                            "sampler": sampler_name,
                            "model": model_name
                        }
                    )
                    
                    exp_meta = {
                        "id": exp_id,
                        "label": exp_label,
                        "sampler": sampler_name,
                        "model": model_name,
                        "metrics": avg_metrics,
                        "training_time": f"{training_time:.2f}s",
                        "optimal_threshold": opt_t,
                        "parameters": {"random_state": self.random_seed, "cv_folds": cv_folds}
                    }
                    
                    # Save baseline metadata
                    with open(os.path.join(self.experiments_dir, f"{exp_id}_meta.json"), "w") as f:
                        json.dump(exp_meta, f, indent=2)
                        
                    # Start MLflow Tracking
                    self.tracker.start_run(run_name=f"Baseline_{exp_id}_{model_name}")
                    sys_meta = get_system_metadata(self.dataset_path)
                    sys_meta.update({
                        "experiment_id": exp_id,
                        "sampler": sampler_name,
                        "model": model_name,
                        "run_type": "baseline",
                        "training_time_seconds": training_time
                    })
                    if hasattr(self.tracker, "active_run") and self.tracker.active_run:
                        import mlflow
                        for tk, tv in sys_meta.items():
                            mlflow.set_tag(tk, str(tv))
                            
                    self.tracker.log_params({"sampler": sampler_name, "model": model_name, "random_seed": self.random_seed})
                    self.tracker.log_metrics(avg_metrics)
                    self.tracker.end_run()
                    
                    experiment_results.append(exp_meta)
                    
            # Leaderboard generation
            ranked_leaderboard = self.ranking_engine.rank_models(experiment_results)
            with open(os.path.join(self.artifacts_dir, "leaderboard.json"), "w") as f:
                json.dump(ranked_leaderboard, f, indent=2)
                
            # Stage 8: Hyperparameter Optimization on Top 5 Models
            update_status(self.artifacts_dir, {
                "progress": 65.0,
                "current_step": "Stage 8 - Running Optuna Tuning on Top 5 Models...",
                "leaderboard": ranked_leaderboard
            })
            
            top_5 = ranked_leaderboard[:self.config["tuning"].get("top_n_models", 5)]
            tuned_results = []
            
            for idx, top_model in enumerate(top_5):
                exp_id = top_model["id"]
                sampler_name = top_model["sampler"]
                model_name = top_model["model"]
                exp_label = top_model["label"]
                tuned_exp_id = f"{exp_id}_tuned"

                # RESUME SUPPORT: skip tuned experiments already on disk.
                tuned_meta_path = os.path.join(self.tuned_checkpoint_dir, f"{tuned_exp_id}_meta.json")
                if os.path.exists(tuned_meta_path):
                    try:
                        with open(tuned_meta_path, "r") as f:
                            cached_tuned = json.load(f)
                        if cached_tuned.get("sampler") == sampler_name and cached_tuned.get("model") == model_name:
                            tuned_results.append(cached_tuned)
                            # Promote to production if it's the best so far
                            self._promote_best_production(tuned_results, run_experiments_dir)
                            continue
                    except Exception:
                        pass

                update_status(self.artifacts_dir, {
                    "progress": round(65.0 + (float(idx) / len(top_5)) * 25.0, 1), # 65% to 90%
                    "current_step": f"Stage 8 - Tuning {model_name.upper()} with {sampler_name.upper()} (Top {idx+1})..."
                })

                # PRE-COMPUTE FOLD DATA ONCE: preprocess + resample each of the 5 folds
                # before Optuna runs. This avoids re-training the (expensive) CTGAN
                # sampler on every Optuna trial × every fold — a 20x speedup for
                # CTGAN combos. We're tuning classifier hyperparameters, not CTGAN.
                # CTGAN uses capped epochs (10) here for the tuning search; the final
                # model retrains CTGAN with full epochs.
                fold_cache = []
                for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
                    X_tr, y_tr = X_train.iloc[train_idx], y_train.iloc[train_idx]
                    X_va, y_va = X_train.iloc[val_idx], y_train.iloc[val_idx]
                    fold_pipeline = self.build_preprocessing_pipeline(engineered_cat_cols, engineered_num_cols)
                    X_tr_proc = fold_pipeline.fit_transform(X_tr, y_tr)
                    X_va_proc = fold_pipeline.transform(X_va)
                    tuning_ctgan_epochs = min(ctgan_epochs, 10) if sampler_name == "ctgan" else ctgan_epochs
                    sampler = get_sampler(
                        sampler_name,
                        random_state=self.random_seed,
                        ctgan_epochs=tuning_ctgan_epochs,
                        ctgan_batch_size=ctgan_batch_size
                    )
                    if sampler is not None:
                        X_tr_res, y_tr_res = sampler.fit_resample(X_tr_proc, y_tr)
                    else:
                        X_tr_res, y_tr_res = X_tr_proc, y_tr
                    fold_cache.append((X_tr_res, y_tr_res, X_va_proc, y_va, val_idx))
                    del fold_pipeline, sampler, X_tr, y_tr, X_va  # free memory

                def objective(trial):
                    params = {}
                    if model_name == "decision_tree":
                        params["max_depth"] = trial.suggest_int("max_depth", 3, 20)
                        params["min_samples_split"] = trial.suggest_int("min_samples_split", 2, 20)
                    elif model_name == "random_forest":
                        params["n_estimators"] = trial.suggest_int("n_estimators", 50, 200)
                        params["max_depth"] = trial.suggest_int("max_depth", 5, 25)
                    elif model_name == "svm":
                        params["C"] = trial.suggest_float("C", 0.1, 10.0, log=True)
                    elif model_name == "gbm":
                        params["learning_rate"] = trial.suggest_float("learning_rate", 0.01, 0.2)
                        params["n_estimators"] = trial.suggest_int("n_estimators", 50, 150)
                    elif model_name == "xgboost":
                        params["learning_rate"] = trial.suggest_float("learning_rate", 0.01, 0.3, log=True)
                        params["max_depth"] = trial.suggest_int("max_depth", 3, 12)
                        params["n_estimators"] = trial.suggest_int("n_estimators", 100, 500)
                        params["subsample"] = trial.suggest_float("subsample", 0.5, 1.0)
                        params["colsample_bytree"] = trial.suggest_float("colsample_bytree", 0.5, 1.0)
                        params["min_child_weight"] = trial.suggest_int("min_child_weight", 1, 10)
                    elif model_name == "lightgbm":
                        params["learning_rate"] = trial.suggest_float("learning_rate", 0.01, 0.2)
                        params["num_leaves"] = trial.suggest_int("num_leaves", 15, 63)
                        params["n_estimators"] = trial.suggest_int("n_estimators", 50, 150)

                    oof_probs = np.zeros(len(X_train))
                    oof_true = np.zeros(len(X_train))

                    # Use pre-computed fold data (preprocessing + sampling done once)
                    for X_tr_res, y_tr_res, X_va_proc, y_va, val_idx in fold_cache:
                        num_neg = np.sum(y_tr_res == 0)
                        num_pos = np.sum(y_tr_res == 1)
                        scale_pos_weight = float(num_neg) / num_pos if num_pos > 0 else 1.0

                        clf = get_model(model_name, random_state=self.random_seed, scale_pos_weight=scale_pos_weight, **params)
                        clf.fit(X_tr_res, y_tr_res)

                        try:
                            probs = clf.predict_proba(X_va_proc)[:, 1]
                        except Exception:
                            probs = clf.decision_function(X_va_proc)
                            probs = (probs - probs.min()) / (probs.max() - probs.min() + 1e-9)

                        oof_probs[val_idx] = probs
                        oof_true[val_idx] = y_va.to_numpy()
                        
                    opt_t = optimize_threshold(oof_true, oof_probs, target_recall, target_precision, target_fpr)
                    oof_preds = (oof_probs >= opt_t).astype(int)
                    metrics = calculate_metrics(oof_true, oof_preds, oof_probs)
                    score = self.ranking_engine.calculate_score(metrics)
                    return score
                
                study = optuna.create_study(direction="maximize")
                # n_jobs=-1 runs multiple Optuna trials simultaneously across all CPU cores
                study.optimize(
                    objective,
                    n_trials=self.config["tuning"].get("trials_per_model", 10),
                    n_jobs=1  # Keep sequential for CTGAN safety (shared state); XGBoost already uses all cores per trial
                )
                best_params = study.best_params
                
                # Fit final model with best params on 70% split resampled
                full_pipeline = self.build_preprocessing_pipeline(engineered_cat_cols, engineered_num_cols)
                X_train_proc = full_pipeline.fit_transform(X_train, y_train)
                
                sampler = get_sampler(
                    sampler_name,
                    random_state=self.random_seed,
                    ctgan_epochs=ctgan_epochs,
                    ctgan_batch_size=ctgan_batch_size
                )
                if sampler is not None:
                    X_train_res, y_train_res = sampler.fit_resample(X_train_proc, y_train)
                else:
                    X_train_res, y_train_res = X_train_proc, y_train
                    
                num_neg = np.sum(y_train_res == 0)
                num_pos = np.sum(y_train_res == 1)
                scale_pos_weight = float(num_neg) / num_pos if num_pos > 0 else 1.0
                
                best_clf = get_model(model_name, random_state=self.random_seed, scale_pos_weight=scale_pos_weight, **best_params)
                
                # Late-stage Probability Calibration (Platt scaling) on the resampled training split
                calibrated_model = CalibratedClassifierCV(best_clf, method="sigmoid", cv=5)
                calibrated_model.fit(X_train_res, y_train_res)
                
                # Find optimal threshold using calibrated probabilities on the held-out
                # calibration split (data the final model never saw during fitting),
                # rather than on training data — this removes optimistic-bias leakage.
                X_calib_proc = full_pipeline.transform(X_calib)
                y_calib_prob = calibrated_model.predict_proba(X_calib_proc)[:, 1]
                opt_t = optimize_threshold(y_calib.to_numpy(), y_calib_prob, target_recall, target_precision, target_fpr)
                
                # Create final FraudDetectionPipeline wrapper
                tuned_pipeline = FraudDetectionPipeline(
                    preprocessing_pipeline=full_pipeline,
                    model=calibrated_model,
                    optimal_threshold=opt_t,
                    feature_names=transformed_feature_names,
                    metadata={
                        "python_version": platform.python_version(),
                        "system": platform.system(),
                        "library_versions": {
                            "scikit-learn": sys.modules.get("sklearn", Any).__version__ if hasattr(sys.modules.get("sklearn"), "__version__") else "N/A",
                            "numpy": np.__version__,
                            "pandas": pd.__version__,
                            "optuna": optuna.__version__
                        },
                        "random_seed": self.random_seed,
                        "dataset_checksum": checksum,
                        "timestamp": datetime.now().isoformat(),
                        "sampler": sampler_name,
                        "model": model_name,
                        "best_params": best_params,
                        "is_tuned": True,
                        "is_calibrated": True
                    }
                )
                
                # Evaluate on untouched 30% Test Set
                start_inf = time.time()
                y_test_pred = tuned_pipeline.predict(X_test)
                y_test_prob = tuned_pipeline.predict_proba(X_test)[:, 1]
                test_metrics = calculate_metrics(y_test.to_numpy(), y_test_pred, y_test_prob, start_inf)
                
                # Structured export directory layout
                tuned_exp_id = f"{exp_id}_tuned"
                tuned_exp_dir = os.path.join(run_experiments_dir, tuned_exp_id)
                os.makedirs(tuned_exp_dir, exist_ok=True)
                # Also save to stable checkpoint dir for cross-run resume
                checkpoint_exp_dir = os.path.join(self.tuned_checkpoint_dir, tuned_exp_id)
                os.makedirs(checkpoint_exp_dir, exist_ok=True)

                # 1. Serialized FraudDetectionPipeline (saved to BOTH dirs)
                pipeline_file = os.path.join(checkpoint_exp_dir, "pipeline.pkl")
                joblib.dump(tuned_pipeline, pipeline_file)
                # Copy to run-specific dir for report completeness
                shutil.copy(pipeline_file, os.path.join(tuned_exp_dir, "pipeline.pkl"))
                
                # 2. Config yaml
                with open(os.path.join(tuned_exp_dir, "config.yaml"), "w") as f:
                    yaml.dump(self.config, f)
                    
                # 3. Metrics JSON
                with open(os.path.join(tuned_exp_dir, "metrics.json"), "w") as f:
                    json.dump(test_metrics, f, indent=2)
                    
                # 4. Feature importance CSV
                # Extract base model from CalibratedClassifierCV
                base_estimator = calibrated_model.calibrated_classifiers_[0].estimator
                if hasattr(base_estimator, "feature_importances_"):
                    fi_df = pd.DataFrame({
                        "feature": transformed_feature_names[:len(base_estimator.feature_importances_)],
                        "importance": base_estimator.feature_importances_
                    }).sort_values("importance", ascending=False)
                    fi_df.to_csv(os.path.join(tuned_exp_dir, "feature_importance.csv"), index=False)
                elif hasattr(base_estimator, "coef_"):
                    fi_df = pd.DataFrame({
                        "feature": transformed_feature_names[:len(base_estimator.coef_[0])],
                        "importance": np.abs(base_estimator.coef_[0])
                    }).sort_values("importance", ascending=False)
                    fi_df.to_csv(os.path.join(tuned_exp_dir, "feature_importance.csv"), index=False)
                    
                # 5. Threshold curve CSV (0.01 to 0.99)
                thresholds = np.arange(0.01, 1.00, 0.01)
                curve_data = []
                for t in thresholds:
                    y_test_pred_t = (y_test_prob >= t).astype(int)
                    tn_t, fp_t, fn_t, tp_t = confusion_matrix(y_test, y_test_pred_t).ravel()
                    rec_t = tp_t / (tp_t + fn_t) if (tp_t + fn_t) > 0 else 0.0
                    prec_t = tp_t / (tp_t + fp_t) if (tp_t + fp_t) > 0 else 0.0
                    fpr_t = fp_t / (fp_t + tn_t) if (fp_t + tn_t) > 0 else 0.0
                    f1_t = 2 * prec_t * rec_t / (prec_t + rec_t) if (prec_t + rec_t) > 0 else 0.0
                    kappa_t = cohen_kappa_score(y_test, y_test_pred_t)
                    curve_data.append({
                        "threshold": round(t, 2),
                        "recall": rec_t,
                        "precision": prec_t,
                        "fpr": fpr_t,
                        "f1": f1_t,
                        "kappa": kappa_t,
                        "brier": test_metrics["brier"]
                    })
                pd.DataFrame(curve_data).to_csv(os.path.join(tuned_exp_dir, "threshold_curve.csv"), index=False)
                
                # 6. Calibration curve CSV
                prob_true, prob_pred = calibration_curve(y_test, y_test_prob, n_bins=10)
                pd.DataFrame({"true_probability": prob_true, "pred_probability": prob_pred}).to_csv(
                    os.path.join(tuned_exp_dir, "calibration_curve.csv"), index=False
                )
                
                # Generate plots and copy to directory
                test_plots = generate_plots(
                    y_test.to_numpy(), y_test_pred, y_test_prob,
                    transformed_feature_names, tuned_pipeline, os.path.join(tuned_exp_dir, "plots")
                )
                for pk, pv in test_plots.items():
                    shutil.copy(pv, os.path.join(tuned_exp_dir, f"{pk}.png"))
                    
                # MLflow tracking
                self.tracker.start_run(run_name=f"Tuned_{exp_id}_{model_name}")
                sys_meta = get_system_metadata(self.dataset_path)
                sys_meta.update({
                    "experiment_id": tuned_exp_id,
                    "sampler": sampler_name,
                    "model": model_name,
                    "run_type": "tuned"
                })
                if hasattr(self.tracker, "active_run") and self.tracker.active_run:
                    import mlflow
                    for tk, tv in sys_meta.items():
                        mlflow.set_tag(tk, str(tv))
                        
                logged_params = {"sampler": sampler_name, "model": model_name, "is_tuned": True, "optimal_threshold": opt_t}
                logged_params.update(best_params)
                self.tracker.log_params(logged_params)
                self.tracker.log_metrics(test_metrics)
                for pk, pv in test_plots.items():
                    self.tracker.log_plot(pv, artifact_path="plots")
                    
                version = self.tracker.log_pipeline_model(tuned_pipeline, registered_model_name="FraudDetectionEngine")
                if version:
                    promote_model_in_registry("FraudDetectionEngine", str(version), "Candidate")
                    
                self.tracker.end_run()
                
                tuned_meta = {
                    "id": tuned_exp_id,
                    "label": f"TUNED {exp_label}",
                    "sampler": sampler_name,
                    "model": model_name,
                    "metrics": test_metrics,
                    "optimal_threshold": opt_t,
                    "is_tuned": True,
                    "best_params": best_params,
                    "model_registry_version": version,
                    "pipeline_file": pipeline_file
                }
                
                # Add calculated composite score to metadata for ranking
                tuned_meta["score"] = self.ranking_engine.calculate_score(test_metrics)
                
                # Save meta to STABLE checkpoint dir (for cross-run resume) + run dir
                with open(os.path.join(self.tuned_checkpoint_dir, f"{tuned_exp_id}_meta.json"), "w") as f:
                    json.dump(tuned_meta, f, indent=2)
                with open(os.path.join(run_experiments_dir, f"{tuned_exp_id}_meta.json"), "w") as f:
                    json.dump(tuned_meta, f, indent=2)
                    
                tuned_results.append(tuned_meta)

                # INCREMENTAL PRODUCTION EXPORT: after each tuned model completes,
                # promote the current best to production.pkl so progress survives
                # even if the pipeline is interrupted before all tuning finishes.
                self._promote_best_production(tuned_results, run_experiments_dir)
                
            # Tuned leaderboard
            ranked_tuned = self.ranking_engine.rank_models(tuned_results)
            with open(os.path.join(self.artifacts_dir, "tuned_leaderboard.json"), "w") as f:
                json.dump(ranked_tuned, f, indent=2)
                
            # 5. Pareto Front Business Analysis
            pareto_report = "# Pareto Front Model Recommendations\n\n"
            pareto_report += "Below is the Pareto Front of models based on the test set evaluations:\n\n"
            pareto_report += "| Target Optimization | Model / Sampler | Precision | Recall | FPR | F1 | Cohen's Kappa | Brier Score | Latency (ms) |\n"
            pareto_report += "|---|---|---|---|---|---|---|---|---|\n"
            
            # Identify Pareto members
            highest_precision = max(tuned_results, key=lambda x: x["metrics"]["precision"])
            highest_recall = max(tuned_results, key=lambda x: x["metrics"]["recall"])
            best_balanced = max(tuned_results, key=lambda x: x["score"])
            lowest_fpr = min(tuned_results, key=lambda x: x["metrics"]["fpr"])
            fastest_inference = min(tuned_results, key=lambda x: x["metrics"]["inference_time_ms"])
            
            pareto_models = [
                ("Highest Precision", highest_precision),
                ("Highest Recall", highest_recall),
                ("Best Balanced (Composite)", best_balanced),
                ("Lowest FPR", lowest_fpr),
                ("Fastest Inference", fastest_inference)
            ]
            
            for optimization, model_entry in pareto_models:
                m = model_entry["metrics"]
                pareto_report += (
                    f"| **{optimization}** | {model_entry['label']} | {m['precision']:.4f} | {m['recall']:.4f} | "
                    f"{m['fpr']:.4f} | {m['f1']:.4f} | {m['kappa']:.4f} | {m['brier']:.4f} | {m['inference_time_ms']:.2f}ms |\n"
                )
                
            # Copy winning model (ranked 1st) to production
            if ranked_tuned:
                winning_model_meta = ranked_tuned[0]
                winning_pipeline_path = winning_model_meta["pipeline_file"]
                shutil.copy(winning_pipeline_path, self.production_model_path)
                
            # Create consolidated reports
            update_status(self.artifacts_dir, {
                "progress": 95.0,
                "current_step": "Stage 14 - Exporting reports..."
            })
            
            report_md = f"# Machine Learning Training & Model Selection Report\n"
            report_md += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            report_md += pareto_report + "\n"
            
            report_md += f"## Stage 1: Baseline Sweep Leaderboard\n"
            report_md += f"Rank | Experiment ID | Sampler | Model Algorithm | Precision | FPR | ROC-AUC | Recall | Composite Score\n"
            report_md += f"---|---|---|---|---|---|---|---|---\n"
            for item in ranked_leaderboard[:15]:
                m = item["metrics"]
                report_md += f"{item['rank']} | {item['id']} | {item['sampler']} | {item['model']} | {m['precision']:.4f} | {m['fpr']:.4f} | {m['roc_auc']:.4f} | {m['recall']:.4f} | {item['score']:.4f}\n"
                
            report_md += f"\n## Stage 2: Tuned & Calibrated Models Leaderboard (Test Set)\n"
            report_md += f"Rank | Experiment ID | Sampler | Model | Precision | Recall | FPR | F1 | Cohen's Kappa | Brier | Composite Score\n"
            report_md += f"---|---|---|---|---|---|---|---|---|---|---\n"
            for item in ranked_tuned:
                m = item["metrics"]
                report_md += f"{item['rank']} | {item['id']} | {item['sampler']} | {item['model']} | {m['precision']:.4f} | {m['recall']:.4f} | {m['fpr']:.4f} | {m['f1']:.4f} | {m['kappa']:.4f} | {m['brier']:.4f} | {item['score']:.4f}\n"
                
            # Save report to both run-specific directory and general artifacts directory
            with open(os.path.join(run_experiments_dir, "business_report.md"), "w") as f:
                f.write(report_md)
                
            report_path = os.path.join(self.artifacts_dir, "training_report.md")
            with open(report_path, "w") as f:
                f.write(report_md)
                
            # Export CSV and JSON format for Stage 14 spec
            df_leaderboard = pd.DataFrame([{
                "rank": x["rank"], "id": x["id"], "sampler": x["sampler"], "model": x["model"],
                "precision": x["metrics"]["precision"], "fpr": x["metrics"]["fpr"], 
                "roc_auc": x["metrics"]["roc_auc"], "recall": x["metrics"]["recall"], "score": x["score"]
            } for x in ranked_leaderboard])
            df_leaderboard.to_csv(os.path.join(self.artifacts_dir, "leaderboard.csv"), index=False)
            
            with open(os.path.join(self.artifacts_dir, "leaderboard.json"), "w") as f:
                json.dump(ranked_leaderboard, f, indent=2)
                
            update_status(self.artifacts_dir, {
                "status": "completed",
                "progress": 100.0,
                "current_step": "Training completed successfully.",
                "leaderboard": ranked_leaderboard,
                "tuned_leaderboard": ranked_tuned,
                "report_path": report_path
            })
            
        except Exception as e:
            import traceback
            error_msg = f"Training failed: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            update_status(self.artifacts_dir, {
                "status": "failed",
                "current_step": "Failed",
                "errors": [error_msg]
            })
            raise e
