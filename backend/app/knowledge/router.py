from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import KnowledgeDocument, KnowledgeChunk
from .importer import DocumentImporter
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import FAISSVectorStore

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

@router.post("/import")
async def import_document(
    file: UploadFile = File(...), 
    author: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, DOCX, TXT, CSV), parse it, chunk it, extract metadata, and save to DB.
    Also triggers embedding generation and index addition.
    """
    file_bytes = await file.read()
    filename = file.filename
    
    importer = DocumentImporter(db)
    
    try:
        # 1. Parse, Metadata, Chunk, Save to DB
        doc = importer.import_document(filename, file_bytes, author)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import document: {str(e)}")
        
    # 2. Embed the newly created chunks and add to Vector Store
    try:
        chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).all()
        texts = [c.content for c in chunks]
        chunk_ids = [str(c.id) for c in chunks]
        
        emb_service = EmbeddingService()
        embeddings = emb_service.embed_batch(texts)
        
        vector_store = FAISSVectorStore()
        vector_store.add_embeddings(embeddings, chunk_ids)
        
    except Exception as e:
        # We don't rollback the document creation if embedding fails, but we should log it
        print(f"Warning: Failed to embed document chunks: {e}")
        
    return {
        "status": "success",
        "document_id": str(doc.id),
        "chunks_created": len(chunks)
    }

@router.get("/")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.status == "active").all()
    return [{"id": d.id, "title": d.title, "version": d.version, "author": d.author} for d in docs]

@router.delete("/{document_id}")
def archive_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.status = "archived"
    db.commit()
    return {"status": "archived"}
