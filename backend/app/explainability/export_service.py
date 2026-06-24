import json
import io
import csv
from typing import Any
from sqlalchemy.orm import Session
from app.models import Explanation

class ExportService:
    def __init__(self, db: Session):
        self.db = db
        
    def export_csv(self, explanation: Explanation) -> str:
        """Export explanation to CSV format string."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write metadata
        writer.writerow(["Claim ID", str(explanation.claim_id)])
        writer.writerow(["Prediction ID", str(explanation.prediction_id)])
        writer.writerow(["Model Version", explanation.model_version])
        writer.writerow(["Fraud Probability", f"{explanation.fraud_probability:.4f}"])
        writer.writerow(["Base Value", f"{explanation.base_value:.4f}"])
        writer.writerow([])
        
        # Write positive features
        writer.writerow(["--- TOP POSITIVE CONTRIBUTORS ---"])
        writer.writerow(["Feature", "Value", "Impact", "Explanation"])
        if explanation.top_positive_features:
            for feat in explanation.top_positive_features:
                writer.writerow([feat.get("feature"), feat.get("value"), feat.get("impact"), feat.get("explanation")])
                
        writer.writerow([])
        
        # Write negative features
        writer.writerow(["--- TOP NEGATIVE CONTRIBUTORS ---"])
        writer.writerow(["Feature", "Value", "Impact", "Explanation"])
        if explanation.top_negative_features:
            for feat in explanation.top_negative_features:
                writer.writerow([feat.get("feature"), feat.get("value"), feat.get("impact"), feat.get("explanation")])
                
        return output.getvalue()
