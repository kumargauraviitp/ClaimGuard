from sqlalchemy.orm import Session
from typing import Dict, Any, List
import time
from .hybrid_search import HybridRetriever
from .reranker import CrossEncoderReRanker
from .context_builder import ContextBuilder
from app.models import RetrievalHistory

class KnowledgeRetrievalService:
    """
    Clean unified facade for Phase 10 AI Agents.
    Abstracts all RAG complexity (Embeddings, FAISS, CrossEncoders, Citations).
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.retriever = HybridRetriever(db)
        self.reranker = CrossEncoderReRanker()
        self.context_builder = ContextBuilder()

    def retrieve(self, query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main interface for the AI Agent to get knowledge.
        Returns a context dictionary containing formatted text and rich citations.
        """
        start_time = time.time()
        
        # 1. Hybrid Retrieval (Vector + Metadata)
        # Fetch 3x the required amount for the reranker to work optimally
        retrieved_items = self.retriever.retrieve(query, top_k=top_k * 3, filters=filters)
        
        # 2. Cross-Encoder Re-ranking
        reranked_items = self.reranker.rerank(query, retrieved_items, top_k=top_k)
        
        # 3. Context & Citation Building
        final_context = self.context_builder.build_context(reranked_items)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 4. Audit / History Logging
        chunk_ids = [cit["chunk_id"] for cit in final_context["citations"]]
        history = RetrievalHistory(
            query=query,
            latency_ms=latency_ms,
            top_k_returned=len(chunk_ids),
            retrieved_chunk_ids=chunk_ids
        )
        self.db.add(history)
        self.db.commit()
        
        return final_context
