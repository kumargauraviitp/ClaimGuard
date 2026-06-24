from langchain_core.messages import HumanMessage
from app.agent.schemas import AgentState
from .llm import get_llm

def recommendation_agent_node(state: AgentState):
    """Agent 9: Recommendation Agent."""
    llm = get_llm()
    prompt = f"""
    Based on the risk assessment: {state.get('risk_assessment')}
    And contradictions: {state.get('contradictions')}
    And SHAP factors: {state.get('shap_analysis')}
    
    Draft specific follow-up actions and investigation recommendations.
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"recommendations": {"actions": response.content}}
