import numpy as np
from typing import List

# Lazy-import sentence_transformers — it pulls in torch and is heavy.
# If it's not available the app still starts; RAG embedding is disabled.
try:
    from sentence_transformers import SentenceTransformer
    _ST_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    _ST_AVAILABLE = False


class EmbeddingService:
    """Generates vector embeddings for chunked text."""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            if _ST_AVAILABLE:
                # all-MiniLM-L6-v2 is an excellent balance of speed and semantic performance
                cls._instance._model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._instance

    def embed_text(self, text: str) -> List[float]:
        """Embed a single string."""
        if not _ST_AVAILABLE:
            raise RuntimeError("sentence_transformers is not installed — RAG embedding unavailable in this environment.")
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed a batch of strings, returning a numpy array for FAISS."""
        if not _ST_AVAILABLE:
            raise RuntimeError("sentence_transformers is not installed — RAG embedding unavailable in this environment.")
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings
