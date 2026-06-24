import shap
import joblib
import os
import json
import numpy as np
import pandas as pd
from typing import Any, Tuple, Dict
from .base import BaseExplainer
from .config import settings

class TreeExplainer(BaseExplainer):
    def __init__(self, model: Any, background_data: pd.DataFrame = None):
        # Using model_output='probability' is ideal if supported, otherwise 'raw'
        self.model = model
        try:
            self.explainer = shap.TreeExplainer(self.model)
            # verify we can access expected_value
            _ = self.explainer.expected_value
        except Exception as e:
            print(f"Failed to init TreeExplainer: {e}")
            raise
            
    def explain_instance(self, X: pd.DataFrame) -> Tuple[float, list, float]:
        shap_values = self.explainer.shap_values(X)
        
        # Depending on XGBoost version / objective, shap_values might be a list (for multiclass) 
        # or a 2D array. For binary classification it's usually 2D array (n_samples, n_features)
        
        if isinstance(shap_values, list):
            # If it's a list, [0] is class 0, [1] is class 1. We want class 1 (fraud)
            sv = shap_values[1][0]
            base_value = self.explainer.expected_value[1]
        else:
            if len(shap_values.shape) == 3: # (n_samples, n_features, n_classes)
                sv = shap_values[0, :, 1]
                base_value = self.explainer.expected_value[1]
            else:
                sv = shap_values[0]
                base_value = self.explainer.expected_value
                if isinstance(base_value, (list, np.ndarray)):
                    base_value = base_value[0]
                    
        # Calculate proba for reference
        if hasattr(self.model, "predict_proba"):
            prob = float(self.model.predict_proba(X)[0, 1])
        else:
            # Approximation from log-odds if raw output
            margin = base_value + np.sum(sv)
            prob = float(1 / (1 + np.exp(-margin)))
            
        return float(base_value), sv.tolist(), prob

    def global_explanation(self, X_sample: pd.DataFrame) -> Dict[str, float]:
        shap_values = self.explainer.shap_values(X_sample)
        if isinstance(shap_values, list):
            sv = shap_values[1]
        else:
            if len(shap_values.shape) == 3:
                sv = shap_values[:, :, 1]
            else:
                sv = shap_values
                
        vals = np.abs(sv).mean(0)
        return {col: float(val) for col, val in zip(X_sample.columns, vals)}

class SHAPExplainerSingleton:
    _instance = None
    _explainer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SHAPExplainerSingleton, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        try:
            with open(settings.STATUS_PATH, "r") as f:
                status_data = json.load(f)
            
            best_model_meta = status_data["tuned_leaderboard"][0]
            pipeline_path = best_model_meta.get("pipeline_file")

            # Resolve path relative to artifacts_dir (same logic as FraudModelService)
            # The stored path may be an absolute host path that doesn't exist in Docker.
            artifacts_dir = os.path.dirname(settings.STATUS_PATH)
            if pipeline_path and not os.path.exists(pipeline_path):
                pipeline_path = os.path.join(artifacts_dir, os.path.basename(pipeline_path))
            if pipeline_path and not os.path.exists(pipeline_path):
                checkpoint = os.path.join(artifacts_dir, "tuned_checkpoints", os.path.basename(pipeline_path))
                if os.path.exists(checkpoint):
                    pipeline_path = checkpoint

            if not pipeline_path or not os.path.exists(pipeline_path):
                raise FileNotFoundError(f"Pipeline file not found: {pipeline_path}")
                
            wrapper_pipeline = joblib.load(pipeline_path)
            self.model = getattr(wrapper_pipeline, "model", wrapper_pipeline)
            
            # Extract base estimator if CalibratedClassifierCV
            from sklearn.calibration import CalibratedClassifierCV
            if isinstance(self.model, CalibratedClassifierCV):
                if hasattr(self.model, "calibrated_classifiers_"):
                    self.model = self.model.calibrated_classifiers_[0].estimator
                elif hasattr(self.model, "estimator"):
                    self.model = self.model.estimator
            
            if settings.EXPLAINER_TYPE == "tree":
                self._explainer = TreeExplainer(self.model)
            else:
                raise ValueError(f"Explainer type {settings.EXPLAINER_TYPE} not supported yet.")
                
            print("SHAPExplainerSingleton initialized successfully.")
            
        except Exception as e:
            print(f"Warning: SHAPExplainer initialization failed: {e}")
            self._explainer = None
            
    def get_explainer(self) -> BaseExplainer:
        return self._explainer
