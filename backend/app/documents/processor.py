"""
Document processor — extracts text from uploaded PDFs and images,
then uses AI (Groq) to verify the document is legitimate and relevant.

PDF extraction: PyMuPDF (fitz) — already a project dependency
Image extraction: PyMuPDF can render images to text via OCR-like approach
AI verification: Groq Llama 3.3 70B checks if the extracted text looks like a real FIR/medical bill
"""
import os
import re
from typing import Optional, Tuple, Dict, Any


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file using PyMuPDF."""
    try:
        import fitz
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


def extract_text_from_file(file_path: str, filename: str) -> str:
    """
    Extract text from any uploaded file based on its extension.
    Returns extracted text or empty string if extraction fails.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)

    if ext in (".txt", ".csv", ".json", ".md"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    if ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"):
        # Images: try to extract embedded text via fitz if possible,
        # otherwise return metadata-based description
        return _extract_from_image(file_path, ext)

    if ext in (".doc", ".docx"):
        return _extract_from_docx(file_path)

    return ""


def _extract_from_image(file_path: str, ext: str) -> str:
    """Try to extract text from an image. Falls back to metadata."""
    # Try PyMuPDF image rendering first
    try:
        import fitz
        # PyMuPDF can open images and attempt text extraction
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        text = "\n".join(text_parts).strip()
        if text:
            return text
    except Exception:
        pass

    # Try pytesseract if available
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        return pytesseract.image_to_string(img).strip()
    except ImportError:
        pass
    except Exception:
        pass

    return f"[Image file ({ext}) — text could not be extracted automatically]"


def _extract_from_docx(file_path: str) -> str:
    """Extract text from a .docx file."""
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def verify_document_with_ai(
    extracted_text: str,
    expected_type: str,
    claim_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Use AI to verify an uploaded document is legitimate and relevant.
    Returns: {
        "relevant": bool,
        "document_type": str (detected),
        "confidence": float (0-1),
        "reasoning": str,
        "status": "verified" | "suspicious" | "rejected"
    }
    """
    if not extracted_text or len(extracted_text.strip()) < 10:
        return {
            "relevant": False,
            "document_type": "unknown",
            "confidence": 0.0,
            "reasoning": "The document appears to be empty or contains no readable text.",
            "status": "rejected",
        }

    # First do keyword-based checks (fast, no API needed)
    text_lower = extracted_text.lower()
    result = _keyword_check(text_lower, expected_type)
    if result:
        return result

    # Then use AI for deeper verification
    llm = _get_llm()
    if llm:
        try:
            prompt = f"""You are verifying a document uploaded for an insurance claim. 
Analyze the extracted text and determine if it's legitimate.

EXPECTED DOCUMENT TYPE: {expected_type}
CLAIM CONTEXT: Claim for {claim_context.get('vehicle_make', 'a vehicle')} accident, 
claim amount ₹{claim_context.get('claim_amount', 0)}.

DOCUMENT TEXT (first 1000 chars):
{extracted_text[:1000]}

Respond ONLY with a JSON object:
{{"relevant": true/false, "document_type": "fir/medical_bill/repair_estimate/insurance_policy/other", "confidence": 0.0-1.0, "reasoning": "one sentence explanation"}}

Rules:
- "relevant" = true if the document matches the expected type and appears genuine
- "confidence" = how sure you are (0.0 = not sure, 1.0 = very sure)
- Check for: FIR numbers, medical billing details, repair estimates, policy numbers
- Flag as irrelevant if the text looks like random characters, unrelated content, or is too short"""
            response = llm.invoke(prompt)
            text = response.content.strip()
            # Parse JSON from response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                import json
                parsed = json.loads(json_match.group())
                status = "verified" if (parsed.get("relevant") and parsed.get("confidence", 0) >= 0.7) else \
                         "suspicious" if parsed.get("relevant") else "rejected"
                return {
                    "relevant": parsed.get("relevant", False),
                    "document_type": parsed.get("document_type", "unknown"),
                    "confidence": float(parsed.get("confidence", 0)),
                    "reasoning": parsed.get("reasoning", ""),
                    "status": status,
                }
        except Exception as e:
            print(f"AI document verification failed: {e}")

    # Fallback: accept if it has enough text content
    return {
        "relevant": len(extracted_text) > 50,
        "document_type": expected_type,
        "confidence": 0.5,
        "reasoning": "Document contains readable text but could not be fully verified automatically.",
        "status": "suspicious",
    }


def _keyword_check(text_lower: str, expected_type: str) -> Optional[Dict[str, Any]]:
    """Fast keyword-based document type detection."""
    fir_keywords = ["fir", "first information report", "police station", "cognizable", 
                    "section", "offence", "complainant", "accused"]
    medical_keywords = ["hospital", "patient", "diagnosis", "treatment", "doctor", 
                        "medical", "prescription", "bill", "pharmacy"]
    repair_keywords = ["repair", "estimate", "garage", "workshop", "parts", 
                       "labour", "service", "invoice", "motor"]
    policy_keywords = ["policy", "insurance", "premium", "coverage", "deductible",
                       "insured", "endorsement"]

    fir_score = sum(1 for k in fir_keywords if k in text_lower)
    medical_score = sum(1 for k in medical_keywords if k in text_lower)
    repair_score = sum(1 for k in repair_keywords if k in text_lower)
    policy_score = sum(1 for k in policy_keywords if k in text_lower)

    scores = {
        "fir": fir_score, "medical_bill": medical_score,
        "repair_estimate": repair_score, "insurance_policy": policy_score,
    }
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score >= 3:
        # Strong match
        relevant = best_type == expected_type or expected_type == "any"
        confidence = min(1.0, best_score / 5)
        return {
            "relevant": relevant,
            "document_type": best_type,
            "confidence": confidence,
            "reasoning": f"Document appears to be a {best_type.replace('_', ' ')} "
                        f"({best_score} matching keywords found).",
            "status": "verified" if relevant else "suspicious",
        }

    return None


def _get_llm():
    """Initialize the Groq LLM. Returns None if unavailable."""
    try:
        from langchain_groq import ChatGroq
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    except Exception:
        return None
