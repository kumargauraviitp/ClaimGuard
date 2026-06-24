from app.agent.schemas import AgentState

def history_agent_node(state: AgentState):
    """Agent 6: Claim History Agent."""
    # Mocking History Verification for brevity
    analysis = {
        "previous_claims_count": 0,
        "previous_fraud_flags": False,
        "history_risk_score": 0.1
    }
    return {"claim_history": analysis}
