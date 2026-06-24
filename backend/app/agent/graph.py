from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import concurrent.futures

from .schemas import AgentState
from .agents.claim_agent import claim_agent_node
from .agents.prediction_agent import prediction_agent_node
from .agents.shap_agent import shap_agent_node
from .agents.knowledge_agent import knowledge_agent_node
from .agents.policy_agent import policy_agent_node
from .agents.history_agent import history_agent_node

from .agents.contradiction_agent import contradiction_agent_node
from .agents.risk_agent import risk_agent_node
from .agents.recommendation_agent import recommendation_agent_node
from .agents.reflection_agent import reflection_agent_node
from .agents.report_agent import report_agent_node
from .agents.qa_agent import qa_agent_node
from .tools.report_tool import store_report
from app.database import SessionLocal

def parallel_data_gathering_node(state: AgentState):
    """
    Orchestrator Fan-Out Node.
    Executes the 6 foundational agents in parallel using ThreadPoolExecutor
    to achieve maximum performance, acting as the LangGraph Parallel Dispatcher.
    """
    # Execute in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        f_claim = executor.submit(claim_agent_node, state)
        f_pred = executor.submit(prediction_agent_node, state)
        f_shap = executor.submit(shap_agent_node, state)
        f_know = executor.submit(knowledge_agent_node, state)
        f_pol = executor.submit(policy_agent_node, state)
        f_hist = executor.submit(history_agent_node, state)
        
        # Wait and gather
        res_claim = f_claim.result()
        res_pred = f_pred.result()
        res_shap = f_shap.result()
        res_know = f_know.result()
        res_pol = f_pol.result()
        res_hist = f_hist.result()
        
    # Merge states
    return {
        "claim_analysis": res_claim.get("claim_analysis"),
        "prediction_analysis": res_pred.get("prediction_analysis"),
        "shap_analysis": res_shap.get("shap_analysis"),
        "knowledge_context": res_know.get("knowledge_context"),
        "policy_compliance": res_pol.get("policy_compliance"),
        "claim_history": res_hist.get("claim_history"),
        "errors": state.get("errors", []) + res_claim.get("errors", []) + res_pred.get("errors", [])
    }

def store_report_node(state: AgentState):
    """Final node after HITL approval."""
    if not state.get("draft_report"):
        return {"errors": ["No draft report to store"]}
        
    db = SessionLocal()
    try:
        if state.get("human_feedback"):
            state["draft_report"].summary += f"\n\nHuman Reviewer Note: {state['human_feedback']}"
            
        report_data = state["draft_report"].dict()
        report_id = store_report(db, state["claim_id"], report_data, status="approved")
        return {"final_report_id": report_id, "status": "completed"}
    finally:
        db.close()

def route_qa(state: AgentState):
    """Conditional routing based on QA Agent feedback."""
    if state.get("qa_feedback") is None:
        return "StoreReport" # Pass! Proceed to HITL
    else:
        return "ReportAgent" # Fail! Loop back to rewrite

def build_multi_agent_graph():
    """Builds the Phase 11 LangGraph Multi-Agent System."""
    workflow = StateGraph(AgentState)
    
    # 1. Parallel Orchestrator Node
    workflow.add_node("ParallelDataGathering", parallel_data_gathering_node)
    
    # 2. Synthesizer Nodes
    workflow.add_node("ContradictionAgent", contradiction_agent_node)
    workflow.add_node("RiskAgent", risk_agent_node)
    workflow.add_node("RecommendationAgent", recommendation_agent_node)
    workflow.add_node("ReflectionAgent", reflection_agent_node)
    
    # 3. Output & Validation
    workflow.add_node("ReportAgent", report_agent_node)
    workflow.add_node("QAAgent", qa_agent_node)
    workflow.add_node("StoreReport", store_report_node)
    
    # Define Graph Edges
    workflow.add_edge(START, "ParallelDataGathering")
    workflow.add_edge("ParallelDataGathering", "ContradictionAgent")
    workflow.add_edge("ContradictionAgent", "RiskAgent")
    workflow.add_edge("RiskAgent", "RecommendationAgent")
    workflow.add_edge("RecommendationAgent", "ReflectionAgent")
    workflow.add_edge("ReflectionAgent", "ReportAgent")
    workflow.add_edge("ReportAgent", "QAAgent")
    
    # QA Loop Conditional Edge
    workflow.add_conditional_edges(
        "QAAgent",
        route_qa,
        {
            "StoreReport": "StoreReport",
            "ReportAgent": "ReportAgent"
        }
    )
    
    workflow.add_edge("StoreReport", END)
    
    # Set up Memory Checkpointer for HITL (Human Approval Node)
    memory = MemorySaver()
    
    # Compile Graph
    # We interrupt BEFORE "StoreReport" so a human can review the Draft Report
    graph = workflow.compile(
        checkpointer=memory,
        interrupt_before=["StoreReport"]
    )
    
    return graph

# Singleton Instance
multi_agent_graph = build_multi_agent_graph()
