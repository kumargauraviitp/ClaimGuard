from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from .schemas import SearchRequest, SearchResponse
from .retrieval_service import KnowledgeRetrievalService
from .embedding_service import EmbeddingService
from .vector_store import FAISSVectorStore
from app.models import KnowledgeChunk

router = APIRouter(prefix="/rag", tags=["RAG & Knowledge Retrieval"])

@router.post("/search", response_model=SearchResponse)
def search_knowledge(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Semantic Search Endpoint utilizing Hybrid Search + CrossEncoder Reranking.
    Used by Phase 10 AI Agents.
    """
    service = KnowledgeRetrievalService(db)
    
    try:
        result = service.retrieve(request.query, top_k=request.top_k, filters=request.filters)
        return SearchResponse(
            context_text=result["context_text"],
            citations=result["citations"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reindex")
def rebuild_vector_index(db: Session = Depends(get_db)):
    """
    Rebuilds the FAISS vector index from all active KnowledgeChunks in the DB.
    """
    chunks = db.query(KnowledgeChunk).all()
    if not chunks:
        return {"status": "No chunks found in database."}
        
    texts = [c.content for c in chunks]
    chunk_ids = [str(c.id) for c in chunks]
    
    emb_service = EmbeddingService()
    embeddings = emb_service.embed_batch(texts)
    
    # Initialize a fresh Vector Store and add
    vector_store = FAISSVectorStore()
    
    # We clear the existing index by re-instantiating inside add_embeddings ? 
    # For a true rebuild, we should clear the index.
    try:
        import faiss
        vector_store._index = faiss.IndexFlatL2(vector_store.dimension)
        vector_store._chunk_ids = []
    except ImportError:
        raise HTTPException(status_code=503, detail="faiss is not installed — RAG indexing unavailable in this environment.")
    
    vector_store.add_embeddings(embeddings, chunk_ids)
    
    return {"status": f"Successfully re-indexed {len(chunks)} chunks."}
