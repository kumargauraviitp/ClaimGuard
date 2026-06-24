from app.database import SessionLocal
from app.agent.tools.shap_tool import load_shap
from app.agent.schemas import AgentState

def shap_agent_node(state: AgentState):
    """Agent 3: SHAP Explanation Agent. Interprets XAI output."""
    db = SessionLocal()
    try:
        shap_data = load_shap(db, state["claim_id"])
        
        analysis = {
            "top_positive": shap_data.get("top_positive_features", []),
            "top_negative": shap_data.get("top_negative_features", []),
            "base_value": shap_data.get("base_value"),
            "raw_data": shap_data
        }
        
        return {"shap_analysis": analysis}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"ShapAgent Error: {str(e)}"]}
    finally:
        db.close()
