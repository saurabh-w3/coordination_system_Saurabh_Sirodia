import json
from typing import Any, Dict
from implementation.coordination_framework.llm_support import create_llm, run_single_decision_graph

NORMALIZER_SYSTEM_PROMPT = """
You are an input normalizer for an auto-credit loan application in India (IN, INR).
Return ONLY JSON with keys: normalized_value, confidence, needs_clarification, clarification_question, notes.

Domain rules:
- vehicle_type: map synonyms to "4w" or "2w" (e.g., "4 wheeler", "car" -> "4w"; "2 wheeler", "bike" -> "2w").
- loan_amount: interpret small numbers as lakhs INR unless user explicitly writes rupees.
  Examples: "14" -> 1400000 (14 lakh), "₹2,50,000" -> 250000, "2.5L" -> 250000.
- age: integer, plausible human ages (18-75 typical; do not clamp, but note if outside).
- tenure_months: integer months; accept "3 years" -> 36.
- phone: normalize to 10 digits (India), drop +91 spaces/dashes.
- PAN: uppercase and fit regex [A-Z]{5}[0-9]{4}[A-Z}; if malformed, keep best-effort normalized and ask clarification if low confidence.
- Aadhaar: 12 digits, remove spaces/dashes; if non-12-digit, ask for clarification.
- domicile: keep a short canonical string (e.g., "RJ", "Rajasthan", "Jaipur" -> "Rajasthan/Jaipur" is okay).
- profession: keep as concise canonical noun (e.g., "Salaried", "Self-Employed", "IT", etc.)
- vehicle_model: keep user string cleaned (trim spaces).

Output schema (strict):
{
  "normalized_value": <string or number>,
  "confidence": <number 0..1>,
  "needs_clarification": <true|false>,
  "clarification_question": <string or null>,
  "notes": <short string>
}
"""

def normalize_with_llm(field_name: str, raw_value: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns dict per schema. If no LLM available or invalid JSON, returns {'normalized_value': raw_value, 'confidence': 0.0, ...}
    """
    llm = create_llm()
    payload = {
        "field": field_name,
        "raw_value": str(raw_value),
        "context": context
    }
    plan = run_single_decision_graph(llm, NORMALIZER_SYSTEM_PROMPT, payload)
    if isinstance(plan, dict) and all(k in plan for k in ["normalized_value", "confidence", "needs_clarification", "clarification_question", "notes"]):
        return plan
    # fallback
    return {
        "normalized_value": raw_value,
        "confidence": 0.0,
        "needs_clarification": False,
        "clarification_question": None,
        "notes": "fallback/no-llm"
    }
