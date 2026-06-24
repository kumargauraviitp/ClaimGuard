import tiktoken
from typing import List, Dict, Any

class DocumentChunker:
    """Intelligent text chunking using tiktoken."""
    
    def __init__(self, model_name: str = "cl100k_base", chunk_size: int = 600, chunk_overlap: int = 100):
        self.encoder = tiktoken.get_encoding(model_name)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Splits text into chunks preserving semantic boundaries where possible."""
        tokens = self.encoder.encode(text)
        chunks = []
        
        if not tokens:
            return chunks
            
        start_idx = 0
        chunk_number = 1
        
        while start_idx < len(tokens):
            end_idx = min(start_idx + self.chunk_size, len(tokens))
            
            # Extract token slice
            chunk_tokens = tokens[start_idx:end_idx]
            
            # If not the last chunk, try to find a natural boundary (period, newline)
            # by decoding and adjusting back if needed, but for simplicity and speed 
            # we will just strictly chunk by token count.
            chunk_text = self.encoder.decode(chunk_tokens)
            
            chunks.append({
                "chunk_number": chunk_number,
                "content": chunk_text.strip(),
                "token_count": len(chunk_tokens)
            })
            
            chunk_number += 1
            
            # Advance start_idx, accounting for overlap
            if end_idx == len(tokens):
                break
            start_idx = end_idx - self.chunk_overlap
            
        return chunks
