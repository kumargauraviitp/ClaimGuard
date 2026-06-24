import numpy as np
import os
import pickle
from typing import List, Tuple, Any

# Lazy-import faiss — it's a heavy native dependency that can be slow to
# install in some environments.  If it's not available the app still starts
# (fraud detection, claims, auth all work); only the RAG knowledge-base
# search feature is disabled.
try:
    import faiss
    _FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    _FAISS_AVAILABLE = False


class FAISSVectorStore:
    """FAISS-based vector store abstracting away Pinecone/Milvus-like operations."""

    def __init__(self, dimension: int = 384, index_path: str = "artifacts/faiss_index.bin", meta_path: str = "artifacts/faiss_meta.pkl"):
        self.dimension = dimension
        self.index_path = index_path
        self.meta_path = meta_path

        if not _FAISS_AVAILABLE:
            self._index = None
            self._chunk_ids = []
            return

        # We use an IndexFlatL2 for exact search, or IndexIVFFlat if huge scale.
        # FlatL2 is extremely fast for <1M vectors anyway.
        self._index = faiss.IndexFlatL2(self.dimension)
        self._chunk_ids = [] # Maps FAISS internal integer ID to KnowledgeChunk UUID

        self.load()

    def add_embeddings(self, embeddings: np.ndarray, chunk_ids: List[str]):
        """Add new embeddings to the index."""
        if not _FAISS_AVAILABLE:
            raise RuntimeError("faiss is not installed — RAG indexing is unavailable in this environment.")

        if embeddings.shape[0] != len(chunk_ids):
            raise ValueError("Number of embeddings must match number of chunk IDs.")

        # FAISS expects float32
        faiss.normalize_L2(embeddings) # Optional: Use inner product (Cosine) with IndexFlatIP instead of L2

        self._index.add(embeddings.astype(np.float32))
        self._chunk_ids.extend(chunk_ids)

        self.save()

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """Search the index for the closest chunks."""
        if not _FAISS_AVAILABLE or self._index is None or self._index.ntotal == 0:
            return []

        # Ensure correct shape (1, dimension)
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        faiss.normalize_L2(query_embedding)

        distances, indices = self._index.search(query_embedding.astype(np.float32), top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self._chunk_ids):
                # distance is L2, lower is better. We can convert to similarity score.
                similarity = 1.0 / (1.0 + float(dist))
                results.append((self._chunk_ids[idx], similarity))

        return results

    def save(self):
        if not _FAISS_AVAILABLE:
            return
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self._index, self.index_path)
        with open(self.meta_path, 'wb') as f:
            pickle.dump(self._chunk_ids, f)

    def load(self):
        if not _FAISS_AVAILABLE:
            return
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self._index = faiss.read_index(self.index_path)
            with open(self.meta_path, 'rb') as f:
                self._chunk_ids = pickle.load(f)
