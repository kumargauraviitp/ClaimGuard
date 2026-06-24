from typing import Dict, Any, List

class SectionGenerator:
    """
    Generates structured enterprise sections for the Investigation Report.
    These are the 16 mandatory sections.
    """
    
    @staticmethod
    def generate_executive_summary(claim_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> str:
        # We would ideally call an LLM here to synthesize the summary.
        # For now, we mock the automatic executive summary generator.
        claim_id = claim_data.get("claim_id")
        amount = claim_data.get("claim_amount", 0)
        risk = ai_analysis.get("risk_level", "Unknown")
        return f"Executive Summary for Claim {claim_id}: The claim was filed for ${amount}. AI analysis indicates a {risk} risk level. Immediate attention is recommended based on aggregated anomaly scores."

    @staticmethod
    def generate_investigation_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Sorts and formats the timeline of events.
        sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""))
        timeline = []
        for e in sorted_events:
            timeline.append({
                "date": e.get("timestamp"),
                "event": e.get("description"),
                "source": e.get("source")
            })
        return timeline

    @staticmethod
    def generate_ai_confidence_explanation(shap_details: Dict[str, Any], model_metrics: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "overall_confidence": model_metrics.get("confidence_score", 0.0),
            "top_factors": shap_details.get("top_positive_features", []),
            "mitigating_factors": shap_details.get("top_negative_features", []),
            "explanation": "The AI model is highly confident due to strong indicators in the top factors matching historical fraud patterns."
        }
