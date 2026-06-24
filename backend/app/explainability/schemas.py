from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class FeatureImpact(BaseModel):
    feature: str
    value: Any
    impact: str
    explanation: str

class VisualizationData(BaseModel):
    summary_plot: Dict[str, Any]
    waterfall_plot: Dict[str, Any]

class LocalExplanationResponse(BaseModel):
    claim_id: str
    prediction: str
    fraud_probability: float
    base_value: float
    top_positive_features: List[FeatureImpact]
    top_negative_features: List[FeatureImpact]
    visualization: Optional[VisualizationData] = None

class GlobalExplanationResponse(BaseModel):
    model_version: str
    feature_importances: List[Dict[str, Any]]
    
class ExportRequest(BaseModel):
    format: str # 'csv' or 'pdf'
