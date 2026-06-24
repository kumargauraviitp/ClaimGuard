from typing import Dict, Any, List

class ShapDriftMonitor:
    def __init__(self, baseline_shap_values: Dict[str, float] = None):
        self.baseline_shap_values = baseline_shap_values or {}
        
    def check_shap_drift(self, recent_shap_values: List[Dict[str, float]]) -> Dict[str, Any]:
        """Check if SHAP feature importances have drifted."""
        if not self.baseline_shap_values or not recent_shap_values:
            return {"status": "insufficient_data"}
            
        # Aggregate recent shap values
        feature_sums = {}
        for sv in recent_shap_values:
            for feature, val in sv.items():
                feature_sums[feature] = feature_sums.get(feature, 0) + abs(val)
                
        recent_avg_shap = {f: v / len(recent_shap_values) for f, v in feature_sums.items()}
        
        drift_metrics = {}
        drift_detected = False
        
        for feature, base_val in self.baseline_shap_values.items():
            recent_val = recent_avg_shap.get(feature, 0)
            
            # 20% change in absolute SHAP importance
            drift_percentage = abs(recent_val - base_val) / (abs(base_val) + 1e-9)
            is_drifting = drift_percentage > 0.2
            
            if is_drifting:
                drift_detected = True
                
            drift_metrics[feature] = {
                "baseline_importance": float(base_val),
                "recent_importance": float(recent_val),
                "drift_percentage": float(drift_percentage),
                "drifting": bool(is_drifting)
            }
            
        return {
            "status": "completed",
            "drift_detected": drift_detected,
            "metrics": drift_metrics
        }
