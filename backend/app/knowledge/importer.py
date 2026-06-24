from sqlalchemy.orm import Session
from app.models import KnowledgeDocument, KnowledgeChunk
from .parser import DocumentParser
from .chunker import DocumentChunker
from .metadata import MetadataExtractor

class DocumentImporter:
    def __init__(self, db: Session):
        self.db = db
        self.chunker = DocumentChunker()

    def import_document(self, filename: str, file_bytes: bytes, author: str = None) -> KnowledgeDocument:
        # 1. Parse Text
        raw_text = DocumentParser.parse(file_bytes, filename)
        
        # 2. Extract Metadata
        meta = MetadataExtractor.extract_document_metadata(filename, raw_text)
        
        # 3. Save Document Record
        doc = KnowledgeDocument(
            title=meta["title"],
            source_type=meta["source_type"],
            author=author,
            version=meta["version"],
            language=meta["language"]
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        
        # 4. Chunking
        chunks = self.chunker.chunk_text(raw_text)
        
        # 5. Save Chunks
        db_chunks = []
        for chunk_data in chunks:
            chunk = KnowledgeChunk(
                document_id=doc.id,
                chunk_number=chunk_data["chunk_number"],
                content=chunk_data["content"],
                token_count=chunk_data["token_count"]
            )
            db_chunks.append(chunk)
            
        self.db.add_all(db_chunks)
        self.db.commit()
        
        return doc
