import json
import yaml
import os
from sqlalchemy.orm import Session
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser

from .schemas import AgentState, FinalInvestigationReport
from .tools.claim_tool import load_claim
from .tools.prediction_tool import load_prediction
from .tools.shap_tool import load_shap
from .tools.knowledge_tool import retrieve_knowledge
from .tools.report_tool import store_report
from app.database import SessionLocal

def get_llm(model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.0):
    """
    Utility function to initialize the LLM.
    We inject the GROQ_API_KEY from environment internally.
    """
    try:
        return ChatGroq(model=model_name, temperature=temperature)
    except Exception as e:
        raise ValueError(f"Failed to initialize ChatGroq: {e}")

def load_inputs_node(state: AgentState):
    """Node 1: Loads Claim, ML Prediction, and SHAP data."""
    claim_id = state["claim_id"]
    db = SessionLocal()
    try:
        claim_data = load_claim(db, claim_id)
        pred_data = load_prediction(db, claim_id)
        shap_data = load_shap(db, claim_id)
        
        return {
            "claim_data": claim_data,
            "prediction_data": pred_data,
            "shap_data": shap_data,
            "errors": state.get("errors", [])
        }
    except Exception as e:
        return {"status": "error", "errors": state.get("errors", []) + [str(e)]}
    finally:
        db.close()

def retrieve_knowledge_node(state: AgentState):
    """Node 2: Retrieve relevant rules using RAG."""
    claim_data = state["claim_data"]
    incident_type = claim_data.get("incident_type", "Unknown")
    
    # Construct a query from the claim context
    query = f"Insurance rules and fraud investigation guidelines for {incident_type} claim"
    
    db = SessionLocal()
    try:
        context = retrieve_knowledge(db, query, top_k=5)
        return {"retrieved_context": context}
    finally:
        db.close()

def contradiction_detection_node(state: AgentState):
    """Node 3: Use LLM to detect contradictions between Claim, Prediction, SHAP, and Rules."""
    llm = get_llm()
    prompt = f"""
    Analyze the following for CONTRADICTIONS only.
    Claim Data: {state['claim_data']}
    Prediction: {state['prediction_data']}
    SHAP: {state['shap_data']}
    Rules: {state['retrieved_context']}
    
    Return a bulleted list of contradictions. If none, return 'None'.
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    contradictions = [c.strip() for c in response.content.split('\n') if c.strip() and c.strip().lower() != 'none']
    
    return {"contradictions_found": contradictions}

def reasoning_engine_node(state: AgentState):
    """Node 4: Initial drafting of the investigation reasoning."""
    llm = get_llm()
    prompt = f"""
    Draft an investigation analysis for this insurance claim.
    Claim: {state['claim_data']}
    ML Prob: {state['prediction_data']}
    SHAP: {state['shap_data']}
    Rules: {state['retrieved_context']}
    Contradictions Detected: {state['contradictions_found']}
    
    Explain the risk, missing evidence, and policy violations.
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"initial_reasoning": response.content}

def reflection_node(state: AgentState):
    """Node 5: Self-critique the reasoning."""
    llm = get_llm()
    prompt = f"""
    Critique and improve this investigation reasoning.
    Initial Reasoning: {state['initial_reasoning']}
    Ensure it strictly relies on the provided Rules: {state['retrieved_context']}
    Identify any logical leaps or assumptions and fix them. Output the improved reasoning.
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"reflected_reasoning": response.content}

def hallucination_verification_node(state: AgentState):
    """Node 6: Strict check to ensure no facts were hallucinated."""
    # In a real heavy enterprise app, we'd do self-ask or strict entailment checking here.
    # For now, we do a basic prompt check.
    llm = get_llm()
    prompt = f"""
    Does this reasoning contain facts NOT present in the Rules or Claim Data?
    Reasoning: {state['reflected_reasoning']}
    Rules: {state['retrieved_context']}
    Claim: {state['claim_data']}
    Reply YES or NO.
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    has_hallucinations = "YES" in response.content.upper()
    return {"hallucinations_detected": has_hallucinations}

def report_generator_node(state: AgentState):
    """Node 7: Generate Final JSON Report using Pydantic Output Parser."""
    llm = get_llm()
    parser = PydanticOutputParser(pydantic_object=FinalInvestigationReport)
    
    prompt = f"""
    Generate the final Investigation Report. 
    You must output exactly and ONLY valid JSON matching the schema below.
    Schema: {parser.get_format_instructions()}
    
    Reasoning to base report on: {state['reflected_reasoning']}
    Contradictions: {state['contradictions_found']}
    Retrieved Citations: {state['retrieved_context']}
    """
    
    # We can retry logic here or rely on LangChain's retry
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        report = parser.parse(response.content)
        return {"draft_report": report, "status": "draft_complete"}
    except Exception as e:
        return {"status": "error", "errors": state.get("errors", []) + [f"Parsing error: {e}"]}

def store_report_node(state: AgentState):
    """Node 8: HITL has approved, store the final report version."""
    if not state.get("draft_report"):
        return {"status": "error", "errors": ["No draft report to store"]}
        
    db = SessionLocal()
    try:
        # Incorporate HITL feedback if any
        if state.get("human_feedback"):
            state["draft_report"].summary += f"\n\nHuman Reviewer Note: {state['human_feedback']}"
            
        report_data = state["draft_report"].dict()
        report_id = store_report(db, state["claim_id"], report_data, status="approved")
        return {"final_report_id": report_id, "status": "completed"}
    finally:
        db.close()
