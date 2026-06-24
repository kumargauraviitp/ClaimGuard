from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
from app.models import KnowledgeChunk, KnowledgeDocument
from .vector_store import FAISSVectorStore
from .embedding_service import EmbeddingService

class HybridRetriever:
    """Combines vector search with keyword/metadata filtering."""
    
    def __init__(self, db: Session):
        self.db = db
        self.vector_store = FAISSVectorStore()
        self.embedding_service = EmbeddingService()

    def retrieve(self, query: str, top_k: int = 15, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        # 1. Generate query embedding
        query_emb = self.embedding_service.embed_batch([query])[0]
        
        # 2. Vector search (get more than needed to allow metadata filtering and reranking)
        vector_results = self.vector_store.search(query_emb, top_k=top_k * 2)
        
        if not vector_results:
            return []
            
        # 3. Retrieve chunks from DB
        chunk_ids = [chunk_id for chunk_id, _ in vector_results]
        
        query_obj = self.db.query(KnowledgeChunk).join(KnowledgeDocument).filter(
            KnowledgeChunk.id.in_(chunk_ids),
            KnowledgeDocument.status == "active"
        )
        
        # Apply metadata filters (if any)
        if filters:
            if "category_id" in filters:
                query_obj = query_obj.filter(KnowledgeDocument.category_id == filters["category_id"])
            # In a real app, extend with tags, dates, authors, etc.
            
        chunks = query_obj.all()
        
        # Re-associate with similarity scores
        chunk_dict = {str(c.id): c for c in chunks}
        
        final_results = []
        for chunk_id, similarity in vector_results:
            if chunk_id in chunk_dict:
                final_results.append({
                    "chunk": chunk_dict[chunk_id],
                    "vector_score": similarity
                })
                
        # Limit before reranking
        return final_results[:top_k]
