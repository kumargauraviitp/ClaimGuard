from sqlalchemy.orm import Session
from app.models import FeatureMetadata

class ExplanationGenerator:
    def __init__(self, db: Session):
        self.db = db
        # Pre-load metadata for fast lookups
        meta = self.db.query(FeatureMetadata).all()
        self.metadata_dict = {m.feature_name: m for m in meta}

    def generate_explanation(self, feature: str, value: any, shap_val: float) -> str:
        """
        Generate deterministic human-readable explanation based on templates.
        No LLMs used.
        """
        meta = self.metadata_dict.get(feature)
        
        if not meta or not meta.explanation_template:
            # Fallback deterministic string
            direction = "increased" if shap_val > 0 else "decreased"
            return f"The value of '{feature}' ({value}) {direction} the fraud probability."
            
        template = meta.explanation_template
        # Simple string replacement if the template expects `{value}` or `{direction}`
        # e.g., "The unusually high claim amount ({value}) significantly increased the fraud probability."
        
        direction = "increased" if shap_val > 0 else "reduced"
        
        return template.replace("{value}", str(value)).replace("{direction}", direction)
