from typing import List, Dict, Any

class CitationEngine:
    """Generates structured citations for RAG context to prevent hallucination without sources."""
    
    @staticmethod
    def build_citation(item: Dict[str, Any]) -> Dict[str, Any]:
        chunk = item["chunk"]
        doc = chunk.document
        
        return {
            "chunk_id": str(chunk.id),
            "document_id": str(doc.id),
            "source_title": doc.title,
            "source_type": doc.source_type,
            "version": doc.version,
            "relevance_score": item.get("rerank_score") or item.get("vector_score"),
            "content": chunk.content
        }

class ContextBuilder:
    """Assembles the final retrieved context payload for the AI Agent."""
    
    def build_context(self, retrieved_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not retrieved_items:
            return {
                "context_text": "",
                "citations": []
            }
            
        citations = []
        text_blocks = []
        
        for i, item in enumerate(retrieved_items, 1):
            cit = CitationEngine.build_citation(item)
            citations.append(cit)
            
            # Create a heavily formatted block that an LLM can easily read and cite
            block = f"[Source {i}: {cit['source_title']} (v{cit['version']})]\n{cit['content']}\n"
            text_blocks.append(block)
            
        return {
            "context_text": "\n---\n".join(text_blocks),
            "citations": citations
        }
