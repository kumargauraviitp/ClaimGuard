from langchain_core.messages import HumanMessage
from app.agent.schemas import AgentState
from .llm import get_llm

def contradiction_agent_node(state: AgentState):
    """Agent 7: Contradiction Detection Agent."""
    llm = get_llm()
    prompt = f"""
    Analyze the following for CONTRADICTIONS only.
    Claim Data: {state.get('claim_analysis')}
    Prediction: {state.get('prediction_analysis')}
    SHAP Factors: {state.get('shap_analysis')}
    Rules Context: {state.get('knowledge_context')}
    Policy Compliance: {state.get('policy_compliance')}
    Claim History: {state.get('claim_history')}
    
    List any explicit contradictions or evidence mismatches found. If none, say 'No contradictions found.'
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    
    return {"contradictions": {"findings": response.content}}
