from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from typing import Dict, Any

try:
    from xgboost import XGBClassifier
except Exception:
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier
except Exception:
    LGBMClassifier = None


def get_model(model_name: str, random_state: int = 42, **kwargs) -> Any:
    """
    Factory function to retrieve model instances with random state and parameters.
    """
    name = model_name.lower().strip()
    
    # Extract any hyperparameters passed
    params = {"random_state": random_state}
    params.update(kwargs)
    
    if name == "decision_tree":
        params.pop("scale_pos_weight", None)
        if "class_weight" not in params:
            params["class_weight"] = "balanced"
        return DecisionTreeClassifier(**params)
        
    elif name == "random_forest":
        params.pop("scale_pos_weight", None)
        if "class_weight" not in params:
            params["class_weight"] = "balanced"
        return RandomForestClassifier(**params)
        
    elif name == "svm":
        params.pop("scale_pos_weight", None)
        if "probability" not in params:
            params["probability"] = True
        if "class_weight" not in params:
            params["class_weight"] = "balanced"
        return SVC(**params)
        
    elif name == "gbm":
        params.pop("scale_pos_weight", None)
        return GradientBoostingClassifier(**params)
        
    elif name == "xgboost":
        if XGBClassifier is not None:
            if "eval_metric" not in params:
                params["eval_metric"] = "logloss"
            # n_jobs=-1 (multi-core) causes SIGSEGV on Python 3.14 + macOS ARM.
            # Single-threaded is sufficient for this dataset size (~15K rows).
            # Keep tree_method="hist" for fast training.
            params["n_jobs"] = 1
            params["tree_method"] = "hist"
            return XGBClassifier(**params)
        else:
            params.pop("scale_pos_weight", None)
            allowed_params = ["n_estimators", "max_depth", "learning_rate", "random_state", "min_samples_split"]
            gbm_params = {k: v for k, v in params.items() if k in allowed_params}
            return GradientBoostingClassifier(**gbm_params)
            
    elif name == "lightgbm":
        if LGBMClassifier is not None:
            if "verbose" not in params:
                params["verbose"] = -1
            # n_jobs=-1 causes SIGSEGV on Python 3.14 + macOS ARM
            params["n_jobs"] = 1
            return LGBMClassifier(**params)
        else:
            params.pop("scale_pos_weight", None)
            allowed_params = ["n_estimators", "max_depth", "random_state", "min_samples_split"]
            rf_params = {k: v for k, v in params.items() if k in allowed_params}
            return RandomForestClassifier(**rf_params)
            
    else:
        raise ValueError(f"Unknown model type: {model_name}")
