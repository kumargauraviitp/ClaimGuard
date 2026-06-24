from app.database import SessionLocal
from app.agent.tools.knowledge_tool import retrieve_knowledge
from app.agent.schemas import AgentState

def knowledge_agent_node(state: AgentState):
    """Agent 4: Knowledge Retrieval Agent. Orchestrates RAG."""
    db = SessionLocal()
    try:
        # In a real system, we'd use the ClaimAgent's output to build the query.
        # But since this runs in parallel with ClaimAgent, we just fetch generic rules
        # or we wait for ClaimAgent to finish. 
        # For simplicity in this architecture, we will run Knowledge Agent AFTER Claim Agent
        # or we use the base claim ID. Let's assume we use basic claim_id info.
        
        claim_data = state.get("claim_analysis", {}).get("raw_data", {})
        incident_type = claim_data.get("incident_type", "Vehicle Accident")
        
        query = f"Fraud investigation guidelines and verification steps for {incident_type}"
        context = retrieve_knowledge(db, query, top_k=5)
        
        return {"knowledge_context": context}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"KnowledgeAgent Error: {str(e)}"]}
    finally:
        db.close()
