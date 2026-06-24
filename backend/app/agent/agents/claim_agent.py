from app.database import SessionLocal
from app.agent.tools.claim_tool import load_claim
from app.agent.schemas import AgentState

def claim_agent_node(state: AgentState):
    """Agent 1: Claim Analysis Agent. Parses and validates raw claim data."""
    db = SessionLocal()
    try:
        claim_data = load_claim(db, state["claim_id"])
        
        # In a full system, an LLM call might parse unstructured claim notes here.
        # For speed, we just structure the DB output.
        analysis = {
            "summary": f"Claim {claim_data['claim_number']} filed on {claim_data['filing_date']}",
            "filing_date": claim_data["filing_date"],
            "raw_data": claim_data,
            "missing_fields": [k for k, v in claim_data.items() if v is None]
        }
        
        return {"claim_analysis": analysis}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"ClaimAgent Error: {str(e)}"]}
    finally:
        db.close()
