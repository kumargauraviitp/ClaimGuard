from langchain_core.messages import HumanMessage
from app.agent.schemas import AgentState
from .llm import get_llm

def reflection_agent_node(state: AgentState):
    """Reflection Agent: Critiques the aggregated findings."""
    llm = get_llm()
    prompt = f"""
    Critique this aggregated investigation reasoning:
    Risk: {state.get('risk_assessment')}
    Contradictions: {state.get('contradictions')}
    Recommendations: {state.get('recommendations')}
    
    Identify any logical leaps, missing context, or unsupported assumptions. Output an improved, strictly logical narrative.
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"reflection": response.content}
