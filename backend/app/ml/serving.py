import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas
from app.ml.preprocessing import DataPreprocessor
import warnings

# Suppress sklearn feature name warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

class FraudModelService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FraudModelService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.artifacts_dir = os.path.join(self.base_dir, "artifacts")
        
        # Load training status to find the best pipeline path and threshold
        status_path = os.path.join(self.artifacts_dir, "training_status.json")
        if not os.path.exists(status_path):
            print("WARNING: training_status.json not found. ML Service running in degraded mode.")
            self.is_ready = False
            return
            
        with open(status_path, "r") as f:
            status_data = json.load(f)
            
        if "tuned_leaderboard" not in status_data or not status_data["tuned_leaderboard"]:
            print("WARNING: No tuned models found in training status.")
            self.is_ready = False
            return
            
        # Get best model (Rank 1)
        best_model_meta = status_data["tuned_leaderboard"][0]
        pipeline_path = best_model_meta.get("pipeline_file")
        
        if not pipeline_path:
            print("WARNING: No pipeline_file specified in training status.")
            self.is_ready = False
            return
        
        # The stored path may be an absolute host path (e.g., /Users/.../production.pkl)
        # which won't exist inside Docker. Resolve it relative to artifacts_dir.
        if not os.path.exists(pipeline_path):
            # Try just the filename relative to artifacts_dir
            pipeline_filename = os.path.basename(pipeline_path)
            pipeline_path = os.path.join(self.artifacts_dir, pipeline_filename)
        
        # Also check tuned_checkpoints subdirectory
        if not os.path.exists(pipeline_path):
            checkpoint_path = os.path.join(self.artifacts_dir, "tuned_checkpoints", os.path.basename(pipeline_path))
            if os.path.exists(checkpoint_path):
                pipeline_path = checkpoint_path
        
        if not os.path.exists(pipeline_path):
            print(f"WARNING: Pipeline file not found at {pipeline_path}")
            self.is_ready = False
            return
        
        # Load the trained pipeline directly from the checkpoint path
        wrapper_pipeline = joblib.load(pipeline_path)
        
        # Extract the underlying model because we use Phase 5's DataPreprocessor for encoding/scaling
        self.model = getattr(wrapper_pipeline, "model", wrapper_pipeline)
        
        # Load features schema — prefer pipeline's own feature_names (authoritative), fallback to features.json
        if hasattr(wrapper_pipeline, "feature_names") and wrapper_pipeline.feature_names:
            self.expected_features = list(wrapper_pipeline.feature_names)
        else:
            features_path = os.path.join(self.artifacts_dir, "features.json")
            with open(features_path, "r") as f:
                features_data = json.load(f)
                if isinstance(features_data, list):
                    self.expected_features = features_data
                else:
                    self.expected_features = features_data.get("features", [])
            
        # Metadata
        self.model_version = str(best_model_meta.get("model_registry_version", "unknown"))
        self.threshold = best_model_meta.get("optimal_threshold", 0.05)
        
        if self.threshold is None:
            self.threshold = 0.05
            
        self.last_training_date = datetime.fromtimestamp(os.path.getmtime(status_path))
        self.is_ready = True
        
        print(f"FraudModelService initialized successfully: version {self.model_version}, threshold {self.threshold}")
        print(f"  Pipeline: {pipeline_path}")
        print(f"  Model type: {type(self.model).__name__}")
        print(f"  Features: {len(self.expected_features)}")

    def _assign_tier(self, prob: float) -> str:
        # Hardcoded business-rule risk tiers (prob is a 0-1 fraction,
        # so the cutoffs below are the percentage boundaries / 100):
        #   0–30 %  → Low
        #   30–65 % → Medium   (needs review)
        #   65–80 % → High
        #   80–100% → Critical
        if prob < 0.30:
            return "Low"
        elif prob < 0.65:
            return "Medium"
        elif prob < 0.80:
            return "High"
        else:
            return "Critical"

    def predict(self, claim_id: str, db: Session) -> Optional[schemas.PredictionResponse]:
        if not self.is_ready:
            print("FraudModelService is not ready. Prediction skipped.")
            return None
            
        preprocessor = DataPreprocessor(db)
        feature_vector, metrics = preprocessor.process_claim(claim_id)
        
        if metrics["status"] != "success" or not feature_vector:
            print(f"Failed to preprocess claim {claim_id}: {metrics.get('errors')}")
            return None
            
        # Convert vector to DataFrame matching the expected feature names
        X = pd.DataFrame([feature_vector], columns=self.expected_features)
        
        # Predict probability
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X)
            fraud_prob = float(probs[0, 1])
        elif hasattr(self.model, "decision_function"):
            decision = self.model.decision_function(X)[0]
            fraud_prob = float(1 / (1 + np.exp(-decision)))
        else:
            print("Model does not support probability prediction.")
            return None
            
        risk_tier = self._assign_tier(fraud_prob)
        confidence = float(min(100.0, max(0.0, 50 + abs(fraud_prob - self.threshold) * 100)))
        
        shap_explanations = None
        try:
            import shap
            try:
                base_estimator = self.model
                if hasattr(self.model, "calibrated_classifiers_"):
                    base_estimator = self.model.calibrated_classifiers_[0].estimator
                    
                explainer = shap.TreeExplainer(base_estimator)
                shap_values = explainer.shap_values(X)
            except Exception:
                # If it's a generic model or SVC, we need an explainer that works
                explainer = shap.KernelExplainer(self.model.predict_proba, shap.sample(X, 10))
                shap_values = explainer.shap_values(X)
            
            if isinstance(shap_values, list):
                contributions = shap_values[1][0]
            else:
                if len(shap_values.shape) == 3:
                    contributions = shap_values[0, :, 1]
                else:
                    contributions = shap_values[0]
            
            shap_explanations = {}
            for i, feature in enumerate(self.expected_features):
                shap_explanations[feature] = float(contributions[i])
                
            # Keep top 10 most impactful features
            shap_explanations = dict(sorted(shap_explanations.items(), key=lambda item: abs(item[1]), reverse=True)[:10])
        except Exception as e:
            print(f"Failed to generate SHAP explanations: {e}")

        # ---- Rule engine: apply hard rules on top of ML probability ----
        base_ml_prob = fraud_prob
        rule_flags = []
        try:
            from app.fraud_rules.engine import FraudRuleEngine
            engine = FraudRuleEngine(db, claim_id)
            fraud_prob, rule_flags = engine.evaluate(base_ml_prob)
            risk_tier = self._assign_tier(fraud_prob)
            confidence = float(min(100.0, max(0.0, 50 + abs(fraud_prob - self.threshold) * 100)))
        except Exception as e:
            print(f"Rule engine failed, using base ML probability: {e}")

        # ---- AI explanation: generate human-readable narrative ----
        explanation_text = ""
        try:
            from app.explainability.ai_explainer import generate_fraud_explanation
            claim = db.query(models.Claim).filter(models.Claim.id == claim_id).first()
            claim_summary = {
                "claim_number": claim.claim_number if claim else "N/A",
                "customer_name": f"{claim.customer.first_name} {claim.customer.last_name}".strip() if claim and claim.customer else "N/A",
                "vehicle_make": claim.vehicle.make if claim and claim.vehicle else "",
                "vehicle_model": claim.vehicle.model if claim and claim.vehicle else "",
                "claim_amount": claim.financial_details.claim_amount if claim and claim.financial_details else 0,
            }
            explanation_text = generate_fraud_explanation(
                claim_summary=claim_summary,
                fraud_probability=fraud_prob,
                risk_category=risk_tier,
                top_shap=shap_explanations or {},
                rule_flags=rule_flags,
            )
        except Exception as e:
            print(f"AI explanation generation failed: {e}")

        # Save to DB
        prediction = models.Prediction(
            claim_id=claim_id,
            fraud_probability=fraud_prob,
            risk_category=risk_tier,
            prediction_confidence=confidence,
            shap_explanations=shap_explanations,
            rule_flags=rule_flags,
            explanation=explanation_text,
            base_ml_probability=base_ml_prob,
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        
        return schemas.PredictionResponse.model_validate(prediction)

    def get_health_stats(self, db: Session) -> Dict[str, Any]:
        if not self.is_ready:
            return {"status": "unavailable"}
            
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_total = db.query(func.count(models.Prediction.id)).filter(
            models.Prediction.created_at >= seven_days_ago
        ).scalar() or 0
        
        recent_flagged = db.query(func.count(models.Prediction.id)).filter(
            models.Prediction.created_at >= seven_days_ago,
            models.Prediction.risk_category.in_(["High", "Critical"])
        ).scalar() or 0
        
        current_rate = (recent_flagged / recent_total * 100) if recent_total > 0 else 0.0
        historical_baseline_rate = 15.0 
        
        return {
            "status": "active",
            "model_version": self.model_version,
            "last_training_date": self.last_training_date.isoformat(),
            "active_threshold": self.threshold,
            "drift_signal": {
                "recent_high_critical_rate_pct": round(current_rate, 2),
                "historical_baseline_rate_pct": historical_baseline_rate,
                "drift_detected": abs(current_rate - historical_baseline_rate) > 10.0 if recent_total > 10 else False,
                "recent_predictions_count": recent_total
            }
        }
