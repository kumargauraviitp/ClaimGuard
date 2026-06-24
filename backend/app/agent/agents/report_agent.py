from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from app.agent.schemas import AgentState, FinalInvestigationReport
from .llm import get_llm

def report_agent_node(state: AgentState):
    """Agent 10: Investigation Report Agent."""
    llm = get_llm()
    parser = PydanticOutputParser(pydantic_object=FinalInvestigationReport)
    
    # If QA Agent rejected a previous draft, we append its feedback.
    qa_instruction = ""
    if state.get("qa_feedback"):
        qa_instruction = f"\nCRITICAL FIX REQUIRED (From QA): {state['qa_feedback']}\nEnsure the new report addresses this."
        
    prompt = f"""
    Generate the Final Investigation Report based strictly on:
    Reflected Logic: {state.get('reflection')}
    Risk Assessment: {state.get('risk_assessment')}
    Contradictions: {state.get('contradictions')}
    Recommendations: {state.get('recommendations')}
    {qa_instruction}
    
    You must output exactly and ONLY valid JSON matching the schema below.
    Schema: {parser.get_format_instructions()}
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        report = parser.parse(response.content)
        return {"draft_report": report}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"Report Parsing Error: {str(e)}"]}
