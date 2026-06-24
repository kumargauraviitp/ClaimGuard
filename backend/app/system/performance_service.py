import time
import statistics
from typing import Dict, List
import json
import os

METRICS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "temp", "metrics.json")

class PerformanceService:
    def __init__(self):
        self.metrics = {
            "prediction": [],
            "shap": [],
            "kb": [],
            "rag": [],
            "agent": []
        }
        self.load_metrics()

    def load_metrics(self):
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, "r") as f:
                    self.metrics = json.load(f)
            except:
                pass

    def save_metrics(self):
        os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
        with open(METRICS_FILE, "w") as f:
            json.dump(self.metrics, f)

    def record(self, metric_type: str, duration_ms: float):
        if metric_type in self.metrics:
            self.metrics[metric_type].append(duration_ms)
            # keep last 1000
            self.metrics[metric_type] = self.metrics[metric_type][-1000:]
            self.save_metrics()

    def get_average(self, metric_type: str) -> float:
        if metric_type in self.metrics and self.metrics[metric_type]:
            return round(statistics.mean(self.metrics[metric_type]), 2)
        return 0.0
        
    def get_all_averages(self) -> Dict[str, float]:
        return {k: self.get_average(k) for k in self.metrics.keys()}

performance_service = PerformanceService()
