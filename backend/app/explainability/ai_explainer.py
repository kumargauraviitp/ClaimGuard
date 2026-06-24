"""
AI-powered fraud explanation generator using Groq (Llama 3.3 70B).

Layer 2 of the explanation system:
- Takes the top SHAP factors + rule-based flags + claim summary
- Generates a 2-3 sentence plain-English narrative explaining why the claim
  has its fraud probability
- Falls back to a deterministic, claim-specific summary if Groq is unavailable

Also provides:
- AI validation of customer data (name/email/phone consistency)
- AI verification of uploaded documents
"""
import os
import json
from typing import Any, Dict, List, Optional

from app.explainability.shap_labels import humanize_feature


def _get_llm():
    """Initialize the Groq LLM. Returns None if GROQ_API_KEY is not set."""
    try:
        from langchain_groq import ChatGroq
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    except Exception:
        return None


def _build_humanized_shap_lines(top_shap: Dict[str, float], limit: int = 5) -> List[str]:
    """Turn raw SHAP features into readable, claim-specific bullet lines."""
    lines = []
    for feat, val in list(top_shap.items())[:limit]:
        label, desc = humanize_feature(feat)
        if val > 0:
            lines.append(f"- {label}: RAISED risk — {desc}")
        else:
            lines.append(f"- {label}: LOWERED risk — {desc}")
    return lines


def generate_fraud_explanation(
    claim_summary: Dict[str, Any],
    fraud_probability: float,
    risk_category: str,
    top_shap: Dict[str, float],
    rule_flags: List[Dict[str, Any]],
) -> str:
    """
    Generate a human-readable fraud explanation.

    Uses the Groq LLM if GROQ_API_KEY is available; otherwise builds a
    detailed, claim-specific narrative from the rule flags and SHAP drivers
    (no longer a one-line generic template).
    """
    # Build human-readable context for the LLM (and for the fallback)
    shap_lines = _build_humanized_shap_lines(top_shap)

    flag_lines = []
    for flag in rule_flags:
        flag_lines.append(
            f"- {flag.get('label', flag.get('rule', 'Unknown'))}: {flag.get('reason', '')}"
        )

    customer = claim_summary.get("customer_name", "the customer")
    vehicle = f"{claim_summary.get('vehicle_make', '')} {claim_summary.get('vehicle_model', '')}".strip() or "the vehicle"
    amount = claim_summary.get("claim_amount", 0) or 0
    claim_number = claim_summary.get("claim_number", "N/A")

    prompt = f"""You are a senior fraud analyst at an insurance company. Write a brief, clear explanation for a claim investigator.

CLAIM SUMMARY:
- Claim Number: {claim_number}
- Customer: {customer}
- Vehicle: {vehicle}
- Claim Amount: ₹{amount:,.0f}
- Fraud Probability: {fraud_probability:.1%}
- Risk Level: {risk_category}

KEY FACTORS FROM ML MODEL:
{chr(10).join(shap_lines) if shap_lines else '- None detected'}

RULE-BASED FLAGS:
{chr(10).join(flag_lines) if flag_lines else '- None triggered'}

INSTRUCTIONS:
- Write 2-3 simple sentences explaining WHY this claim has the given fraud risk level.
- Use plain English that anyone can understand — no technical jargon, no math formulas.
- Mention the most important red flags specifically.
- Be factual and objective — do not accuse anyone.
- Keep it under 100 words."""

    llm = _get_llm()
    if llm:
        try:
            response = llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"AI explanation failed, using fallback: {e}")

    # Deterministic, claim-specific fallback
    return _build_specific_narrative(
        claim_summary=claim_summary,
        fraud_probability=fraud_probability,
        risk_category=risk_category,
        top_shap=top_shap,
        rule_flags=rule_flags,
        shap_lines=shap_lines,
    )


def _build_specific_narrative(
    claim_summary: Dict[str, Any],
    fraud_probability: float,
    risk_category: str,
    top_shap: Dict[str, float],
    rule_flags: List[Dict[str, Any]],
    shap_lines: List[str],
) -> str:
    """Build a detailed, claim-specific explanation when the LLM is unavailable.

    Instead of a single generic sentence, this composes a narrative that:
      1. Names the claim, customer and vehicle.
      2. States the risk level and what it means.
      3. Highlights the top SHAP driver in plain English.
      4. Lists the highest-impact rule flags by name.
    Every claim therefore reads differently because it is built from that
    claim's own data.
    """
    customer = claim_summary.get("customer_name", "this customer")
    vehicle = f"{claim_summary.get('vehicle_make', '')} {claim_summary.get('vehicle_model', '')}".strip()
    vehicle_str = f" for the {vehicle}" if vehicle else ""
    amount = claim_summary.get("claim_amount", 0) or 0
    claim_number = claim_summary.get("claim_number", "")

    pct = f"{fraud_probability*100:.0f}%"

    # 1. Opening sentence — anchored to THIS claim
    parts = [f"Claim {claim_number} ({customer}{vehicle_str}, ₹{amount:,.0f}) "
             f"was assessed at {pct} fraud probability — classified as {risk_category.upper()} risk."]

    # 2. Rule flags — name the most severe ones specifically
    # Sort by impact descending and take the top 3
    significant_flags = sorted(
        [f for f in rule_flags if f.get("score_added", 0) > 0 and f.get("rule") not in ("CRITICAL_MISMATCH", "PARTIAL_MISMATCH")],
        key=lambda f: f.get("score_added", 0),
        reverse=True,
    )[:3]

    mismatch_flag = next((f for f in rule_flags if f.get("rule") == "CRITICAL_MISMATCH"), None)

    flag_reasons = []
    if mismatch_flag:
        flag_reasons.append("both the policy number and vehicle registration could not be verified against our records")
    for f in significant_flags:
        # Use the label, strip the leading emoji for prose
        label = (f.get("label") or "").lstrip("⚠🚨⚠️ ").strip().lower()
        if label:
            flag_reasons.append(label)

    if flag_reasons:
        if len(flag_reasons) == 1:
            parts.append(f"The primary concern is that {flag_reasons[0]}.")
        else:
            parts.append("Key red flags: " + "; ".join(flag_reasons) + ".")

    # 3. Top SHAP driver in plain English
    positive_shap = {k: v for k, v in top_shap.items() if v > 0}
    if positive_shap:
        top_feat = max(positive_shap, key=positive_shap.get)
        label, desc = humanize_feature(top_feat)
        parts.append(f"The model was most influenced by {label.lower()} ({desc.lower()})")

    # 4. Recommendation
    if risk_category in ("Critical", "High"):
        parts.append("Manual investigation is strongly recommended before any payout.")
    elif risk_category == "Medium":
        parts.append("A routine review of the supporting documents is advised.")
    else:
        parts.append("This claim appears low-risk and can proceed through standard processing.")

    return " ".join(parts)


def validate_customer_data(
    name: str,
    email: str,
    phone: str,
    age: Optional[int],
    occupation: Optional[str],
    city: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Use AI to validate customer data for suspicious patterns.
    Returns a list of anomaly flags (empty if data looks fine).
    Falls back to rule-based checks if AI is unavailable.
    """
    # First, do basic rule-based checks
    anomalies = []

    if not name or len(name.strip()) < 2:
        anomalies.append({
            "rule": "INVALID_NAME",
            "label": "⚠ Suspicious name",
            "reason": "The customer name appears to be empty or too short.",
            "score_added": 0.10,
        })

    # NOTE: Email/name mismatch is intentionally NOT checked here.
    # Many legitimate customers use emails that don't contain their name
    # (work emails, shared family accounts, old handles, etc.). Treating a
    # mismatch as fraud caused too many false positives.

    if phone:
        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) < 10 or len(digits) > 13:
            anomalies.append({
                "rule": "INVALID_PHONE",
                "label": "⚠ Invalid phone number",
                "reason": "The phone number format doesn't match a valid Indian mobile/landline number.",
                "score_added": 0.10,
            })

    if age and age < 18:
        anomalies.append({
            "rule": "UNDERAGE",
            "label": "⚠ Customer is underage",
            "reason": f"The customer's age ({age}) is below the legal driving age of 18.",
            "score_added": 0.10,
        })

    if age and occupation:
        suspicious_combos = [
            (18, "retired"), (18, "Retired"), (18, "pensioner"),
            (20, "retired"), (20, "Retired"),
            (70, "student"), (70, "Student"),
            (75, "intern"), (75, "Intern"),
        ]
        for age_threshold, occ in suspicious_combos:
            if age <= age_threshold and occ.lower() in occupation.lower():
                anomalies.append({
                    "rule": "SUSPICIOUS_OCCUPATION",
                    "label": "⚠ Suspicious age-occupation combination",
                    "reason": f"A {age}-year-old listing '{occupation}' as their occupation is unusual.",
                    "score_added": 0.10,
                })

    # Now try AI validation for deeper analysis
    if len(anomalies) == 0 and name and email:
        llm = _get_llm()
        if llm:
            try:
                prompt = f"""Analyze this customer data for an insurance claim and flag any suspicious patterns.
Respond ONLY with a JSON array of objects with keys: "suspicious" (boolean), "reason" (string).
If everything looks legitimate, return [{{"suspicious": false, "reason": ""}}].

Name: {name}
Email: {email}
Phone: {phone or "Not provided"}
Age: {age or "Not provided"}
Occupation: {occupation or "Not provided"}
City: {city or "Not provided"}

Check for: fake names (keyboard smashing), invalid phone formats, implausible age-occupation combinations.
Do NOT flag email-name mismatches — many legitimate emails don't contain the customer's name."""
                response = llm.invoke(prompt)
                text = response.content.strip()
                # Try to parse JSON from response
                import re
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    findings = json.loads(json_match.group())
                    for finding in findings:
                        if finding.get("suspicious") and finding.get("reason"):
                            anomalies.append({
                                "rule": "AI_DATA_VALIDATION",
                                "label": "⚠ Suspicious data (AI detected)",
                                "reason": finding["reason"],
                                "score_added": 0.10,
                            })
            except Exception:
                pass  # AI check failed, rule-based results are sufficient

    return anomalies



def validate_customer_data(
    name: str,
    email: str,
    phone: str,
    age: Optional[int],
    occupation: Optional[str],
    city: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Use AI to validate customer data for suspicious patterns.
    Returns a list of anomaly flags (empty if data looks fine).
    Falls back to rule-based checks if AI is unavailable.
    """
    # First, do basic rule-based checks
    anomalies = []

    if not name or len(name.strip()) < 2:
        anomalies.append({
            "rule": "INVALID_NAME",
            "label": "⚠ Suspicious name",
            "reason": "The customer name appears to be empty or too short.",
            "score_added": 0.10,
        })

    # NOTE: Email/name mismatch is intentionally NOT checked here.
    # Many legitimate customers use emails that don't contain their name
    # (work emails, shared family accounts, old handles, etc.). Treating a
    # mismatch as fraud caused too many false positives.

    if phone:
        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) < 10 or len(digits) > 13:
            anomalies.append({
                "rule": "INVALID_PHONE",
                "label": "⚠ Invalid phone number",
                "reason": "The phone number format doesn't match a valid Indian mobile/landline number.",
                "score_added": 0.10,
            })

    if age and age < 18:
        anomalies.append({
            "rule": "UNDERAGE",
            "label": "⚠ Customer is underage",
            "reason": f"The customer's age ({age}) is below the legal driving age of 18.",
            "score_added": 0.10,
        })

    if age and occupation:
        suspicious_combos = [
            (18, "retired"), (18, "Retired"), (18, "pensioner"),
            (20, "retired"), (20, "Retired"),
            (70, "student"), (70, "Student"),
            (75, "intern"), (75, "Intern"),
        ]
        for age_threshold, occ in suspicious_combos:
            if age <= age_threshold and occ.lower() in occupation.lower():
                anomalies.append({
                    "rule": "SUSPICIOUS_OCCUPATION",
                    "label": "⚠ Suspicious age-occupation combination",
                    "reason": f"A {age}-year-old listing '{occupation}' as their occupation is unusual.",
                    "score_added": 0.10,
                })

    # Now try AI validation for deeper analysis
    if len(anomalies) == 0 and name and email:
        llm = _get_llm()
        if llm:
            try:
                prompt = f"""Analyze this customer data for an insurance claim and flag any suspicious patterns. 
Respond ONLY with a JSON array of objects with keys: "suspicious" (boolean), "reason" (string). 
If everything looks legitimate, return [{{"suspicious": false, "reason": ""}}].

Name: {name}
Email: {email}
Phone: {phone or "Not provided"}
Age: {age or "Not provided"}
Occupation: {occupation or "Not provided"}
City: {city or "Not provided"}

Check for: fake names (keyboard smashing), invalid phone formats, implausible age-occupation combinations.
Do NOT flag email-name mismatches — many legitimate emails don't contain the customer's name."""
                response = llm.invoke(prompt)
                text = response.content.strip()
                # Try to parse JSON from response
                import re
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    findings = json.loads(json_match.group())
                    for finding in findings:
                        if finding.get("suspicious") and finding.get("reason"):
                            anomalies.append({
                                "rule": "AI_DATA_VALIDATION",
                                "label": "⚠ Suspicious data (AI detected)",
                                "reason": finding["reason"],
                                "score_added": 0.10,
                            })
            except Exception:
                pass  # AI check failed, rule-based results are sufficient

    return anomalies
