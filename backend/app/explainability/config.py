import os
from pydantic_settings import BaseSettings

class ExplainabilityConfig(BaseSettings):
    # SHAP Config
    EXPLAINER_TYPE: str = "tree" # tree, deep, kernel
    BACKGROUND_SAMPLE_SIZE: int = 100
    SHAP_VERSION: str = "0.45.0"
    
    # Cache Config
    CACHE_TTL_HOURS: int = 24
    
    # Feature Ranking Config
    TOP_POSITIVE_FEATURES_COUNT: int = 5
    TOP_NEGATIVE_FEATURES_COUNT: int = 5
    
    # Paths
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ARTIFACTS_DIR: str = os.path.join(BASE_DIR, "artifacts")
    STATUS_PATH: str = os.path.join(ARTIFACTS_DIR, "training_status.json")

settings = ExplainabilityConfig()
