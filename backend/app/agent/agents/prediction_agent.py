from app.database import SessionLocal
from app.agent.tools.prediction_tool import load_prediction
from app.agent.schemas import AgentState

def prediction_agent_node(state: AgentState):
    """Agent 2: Prediction Analysis Agent. Interprets ML prediction."""
    db = SessionLocal()
    try:
        pred_data = load_prediction(db, state["claim_id"])
        
        # Structure the ML output for downstream agents
        analysis = {
            "fraud_probability": pred_data.get("fraud_probability", 0.0),
            "risk_tier": pred_data.get("risk_tier", "Unknown"),
            "is_fraud_predicted": pred_data.get("is_fraud", False),
            "raw_data": pred_data
        }
        
        return {"prediction_analysis": analysis}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"PredictionAgent Error: {str(e)}"]}
    finally:
        db.close()
