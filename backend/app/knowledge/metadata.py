from typing import Dict, Any
from datetime import datetime

class MetadataExtractor:
    @staticmethod
    def extract_document_metadata(filename: str, content: str) -> Dict[str, Any]:
        """Extract basic metadata from filename and raw text."""
        
        # In a real enterprise system, we might use NLP or RegEx to find Effective Dates, Authors, etc.
        # Here we provide a structured default that can be overridden by user input during upload.
        
        ext = filename.split(".")[-1].lower() if "." in filename else "unknown"
        
        return {
            "title": filename.rsplit(".", 1)[0].replace("_", " ").title(),
            "source_type": ext,
            "version": "1.0",
            "language": "en",
            "extracted_at": datetime.utcnow().isoformat()
        }
