import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
from sqlalchemy.orm import Session

from .explainer import SHAPExplainerSingleton
from .config import settings
from .explanation_generator import ExplanationGenerator
from .utils import format_impact
from .schemas import FeatureImpact

class SHAPService:
    def __init__(self, db: Session):
        self.db = db
        self.singleton = SHAPExplainerSingleton()
        self.explainer = self.singleton.get_explainer()
        self.generator = ExplanationGenerator(self.db)
        
    def generate_local_explanation(self, X: pd.DataFrame) -> Tuple[float, float, List[FeatureImpact], List[FeatureImpact], Dict[str, float]]:
        if not self.explainer:
            raise RuntimeError("SHAP Explainer not initialized.")
            
        base_value, shap_values, prob = self.explainer.explain_instance(X)
        
        feature_names = X.columns.tolist()
        feature_values = X.iloc[0].tolist()
        
        # Combine into list of dicts for sorting
        contributions = []
        for i, (name, val, shap_val) in enumerate(zip(feature_names, feature_values, shap_values)):
            contributions.append({
                "feature": name,
                "value": val,
                "shap_val": shap_val,
                "abs_shap": abs(shap_val)
            })
            
        # Sort by absolute impact
        contributions.sort(key=lambda x: x["abs_shap"], reverse=True)
        
        positive_features = []
        negative_features = []
        
        raw_shap_dict = {}
        
        for item in contributions:
            raw_shap_dict[item["feature"]] = float(item["shap_val"])
            
            # Format impact
            impact_str = format_impact(item["shap_val"])
            explanation_str = self.generator.generate_explanation(item["feature"], item["value"], item["shap_val"])
            
            fi = FeatureImpact(
                feature=item["feature"],
                value=item["value"],
                impact=impact_str,
                explanation=explanation_str
            )
            
            if item["shap_val"] > 0:
                if len(positive_features) < settings.TOP_POSITIVE_FEATURES_COUNT:
                    positive_features.append(fi)
            elif item["shap_val"] < 0:
                if len(negative_features) < settings.TOP_NEGATIVE_FEATURES_COUNT:
                    negative_features.append(fi)
                    
        return base_value, prob, positive_features, negative_features, raw_shap_dict

    def generate_global_importance(self, background_data: pd.DataFrame) -> List[Dict[str, Any]]:
        if not self.explainer:
            raise RuntimeError("SHAP Explainer not initialized.")
            
        importances = self.explainer.global_explanation(background_data)
        
        # Sort and format
        sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        return [{"feature": k, "importance": v} for k, v in sorted_imp]
