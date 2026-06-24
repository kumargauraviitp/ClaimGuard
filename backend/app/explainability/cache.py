import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Explanation, ExplanationCache
from .config import settings

class ExplanationCacheService:
    def __init__(self, db: Session):
        self.db = db
        
    def get_cached_explanation(self, prediction_id: str):
        """Retrieve explanation if it exists in cache and hasn't expired."""
        cache_entry = self.db.query(ExplanationCache).filter(
            ExplanationCache.prediction_id == prediction_id
        ).first()
        
        if cache_entry:
            if cache_entry.expires_at and cache_entry.expires_at < datetime.utcnow():
                # Expired
                self.db.delete(cache_entry)
                self.db.commit()
                return None
                
            explanation = self.db.query(Explanation).filter(Explanation.id == cache_entry.explanation_id).first()
            return explanation
            
        return None
        
    def cache_explanation(self, explanation: Explanation):
        """Save explanation to cache."""
        expires = datetime.utcnow() + timedelta(hours=settings.CACHE_TTL_HOURS)
        
        cache_entry = ExplanationCache(
            prediction_id=explanation.prediction_id,
            explanation_id=explanation.id,
            expires_at=expires
        )
        
        self.db.add(cache_entry)
        self.db.commit()
        
    def clear_cache(self):
        """Clear all entries from the ExplanationCache table."""
        self.db.query(ExplanationCache).delete()
        self.db.commit()
