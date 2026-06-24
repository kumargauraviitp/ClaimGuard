from langchain_core.messages import HumanMessage
from app.agent.schemas import AgentState
from .llm import get_llm

def risk_agent_node(state: AgentState):
    """Agent 8: Risk Assessment Agent (with Confidence Aggregation)."""
    llm = get_llm()
    prompt = f"""
    Assess the overall risk based on:
    Contradictions: {state.get('contradictions')}
    Prediction: {state.get('prediction_analysis')}
    SHAP Factors: {state.get('shap_analysis')}
    History Risk: {state.get('claim_history')}
    
    Provide a unified Risk Level (Low, Medium, High, Critical), an explanation, and calculate a confidence score (0.0 to 1.0) aggregating the strength of the evidence.
    Format your response as pure JSON like:
    {{"risk_level": "High", "explanation": "...", "confidence_score": 0.85}}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    
    import json
    try:
        # Strip markdown json blocks
        clean_text = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(clean_text)
    except:
        data = {"risk_level": "Unknown", "explanation": response.content, "confidence_score": 0.5}
        
    return {"risk_assessment": data}
