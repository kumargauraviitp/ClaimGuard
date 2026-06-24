from abc import ABC, abstractmethod
import pandas as pd
from typing import Any, Dict, Tuple

class BaseExplainer(ABC):
    
    @abstractmethod
    def __init__(self, model: Any, background_data: pd.DataFrame = None):
        """Initialize the explainer with the model and optional background data."""
        pass
        
    @abstractmethod
    def explain_instance(self, X: pd.DataFrame) -> Tuple[float, list, float]:
        """
        Explain a single instance.
        Returns:
            Tuple[float, list, float]: (base_value, shap_values, prediction_probability)
        """
        pass
        
    @abstractmethod
    def global_explanation(self, X_sample: pd.DataFrame) -> Dict[str, float]:
        """
        Compute global feature importance from a sample of data.
        """
        pass
