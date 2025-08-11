# Agent Interaction Model

## Contracts per agent (inputs → outputs → effects)

### GreetingAgent
- **Reads:** —
- **Writes:** `events(greeting)`
- **External:** —
- **Notes:** One-shot; signals session start.

### ApplicationAgent (interactive)
- **Reads:** `applications`
- **Writes:** `applications(field=value)`, `events(field_*)`
- **External:** —
- **Notes:** Prompts the user in terminal (no LLM normalization). Tries to cast `age`, `loan_amount`, `tenure_months` to `int`.

### VerificationAgent
- **Reads:** `applications`, `verifications`
- **Writes:** `verifications(proof=ok/value)`, `events(verify_*_ok/reject)`
- **External:** `otp` (phone), `otp` (aadhaar), `cibil` (pan), `itr` (pan), `vehicle` (model) — **simulated** with rate limits & jitter
- **Notes:** Orders missing proofs: phone → aadhaar → PAN/CIBIL → ITR → vehicle. Rejections burn extra tokens.

### EMICalculatorAgent
- **Reads:** `applications` (`loan_amount`, `tenure_months`, `vehicle_type`)
- **Writes:** `emi`, `events(emi)`
- **External:** —
- **Notes:** Computes EMI **once** when minimally sufficient fields exist (standard EMI formula).

### EligibilityAgent
- **Reads:** `applications`, `verifications`, `emi`
- **Writes:** `eligibility(status, confidence)`, `events(eligibility_conf)`
- **External:** —
- **Notes:** Simple rules (age bounds; DTI proxy via EMI/amount); confidence boosted by ITR/CIBIL proofs.

### LeadGenerationAgent
- **Reads:** `eligibility`
- **Writes:** `leads(bank, status, meta)`, `events(lead_submitted|lead_rejected)`
- **External:** —
- **Notes:** **Baked-in** acceptance policy; **single attempt**; persists a lead row.

---

## How agents discover & coordinate (code hooks)

All agents implement:
- `propose_intents(self) -> list[Intent]` — propose actions with bids (tokens) based on local price & state
- `execute(self, intent)` — perform the action; may write tables; logs events

**File anchors:**
- `base_agent.py` — main loop (`gossip_exchange → propose_intents → execute`), tokens, deadlines
- `interactive_application_agent.py` — prompts via `input()` (thread executor), writes fields
- `verification_agent.py` — picks & calls simulated APIs; logs ok/reject; applies penalties
- `emi_agent.py` — one-shot EMI
- `eligibility_agent.py` — rules + confidence
- `lead_generation_agent.py` — built-in acceptance constants; persists a lead

---

## Access control (asymmetric information)
- Application → can write `applications` only
- Verification → can write `verifications` only
- EMI → can write `emi`
- Eligibility → can write `eligibility`
- LeadGen → can write `leads`

Checked in `access.py`; DB helpers in `BaseAgent` call only if allowed.
