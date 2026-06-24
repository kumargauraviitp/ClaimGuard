from langchain_core.messages import HumanMessage
from app.agent.schemas import AgentState
from .llm import get_llm

def qa_agent_node(state: AgentState):
    """Agent 11: Quality Assurance Agent."""
    draft = state.get("draft_report")
    
    if not draft:
        return {"qa_feedback": "Draft report is completely missing or failed to parse."}
        
    llm = get_llm()
    prompt = f"""
    You are the QA Agent. Verify this draft report for hallucinations, unsupported claims, or missing sections.
    Report Summary: {draft.summary}
    Reflected Truth: {state.get('reflection')}
    
    If it is acceptable, respond with 'PASS'.
    If it contains unsupported statements or hallucinations, respond with a short description of the error so it can be regenerated.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    if "PASS" in response.content.upper():
        return {"qa_feedback": None}
    else:
        return {"qa_feedback": response.content}
