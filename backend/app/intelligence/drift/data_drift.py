import numpy as np
import pandas as pd
from typing import Dict, Any

class DataDriftMonitor:
    def __init__(self, baseline_data: pd.DataFrame = None):
        self.baseline_data = baseline_data
        
    def check_drift(self, recent_data: pd.DataFrame) -> Dict[str, Any]:
        """Check for statistical drift between baseline and recent data."""
        if self.baseline_data is None or len(recent_data) == 0:
            return {"status": "insufficient_data", "metrics": {}}
            
        drift_metrics = {}
        drift_detected = False
        
        for col in recent_data.columns:
            if col in self.baseline_data.columns and pd.api.types.is_numeric_dtype(recent_data[col]):
                base_mean = self.baseline_data[col].mean()
                recent_mean = recent_data[col].mean()
                
                # Simple drift detection: 10% change in mean
                drift_percentage = abs(recent_mean - base_mean) / (abs(base_mean) + 1e-9)
                is_drifting = drift_percentage > 0.1
                
                if is_drifting:
                    drift_detected = True
                    
                drift_metrics[col] = {
                    "baseline_mean": float(base_mean),
                    "recent_mean": float(recent_mean),
                    "drift_percentage": float(drift_percentage),
                    "drifting": bool(is_drifting)
                }
                
        return {
            "status": "completed",
            "drift_detected": drift_detected,
            "metrics": drift_metrics
        }
