from sqlalchemy.orm import Session
from app.rag.retrieval_service import KnowledgeRetrievalService

def retrieve_knowledge(db: Session, query: str, top_k: int = 5) -> dict:
    service = KnowledgeRetrievalService(db)
    return service.retrieve(query=query, top_k=top_k)
