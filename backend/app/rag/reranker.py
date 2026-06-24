from typing import List, Dict, Any

# Lazy-import sentence_transformers — heavy dependency (pulls torch).
# If unavailable the app still starts; RAG reranking is disabled.
try:
    from sentence_transformers import CrossEncoder
    _ST_AVAILABLE = True
except ImportError:
    CrossEncoder = None
    _ST_AVAILABLE = False


class CrossEncoderReRanker:
    """10/10 Architecture Improvement: Re-ranks retrieved chunks for maximum relevance."""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrossEncoderReRanker, cls).__new__(cls)
            if _ST_AVAILABLE:
                # ms-marco is standard for high quality cross-encoding QA reranking
                cls._instance._model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        return cls._instance

    def rerank(self, query: str, retrieved_items: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not retrieved_items:
            return []

        if not _ST_AVAILABLE or self._model is None:
            # Graceful fallback: return items un-reranked, truncated to top_k
            return retrieved_items[:top_k]

        # Create pairs: (query, chunk_content)
        pairs = [[query, item["chunk"].content] for item in retrieved_items]

        # Predict scores
        scores = self._model.predict(pairs)

        # Assign scores and sort
        for item, score in zip(retrieved_items, scores):
            item["rerank_score"] = float(score)

        retrieved_items.sort(key=lambda x: x["rerank_score"], reverse=True)

        return retrieved_items[:top_k]
