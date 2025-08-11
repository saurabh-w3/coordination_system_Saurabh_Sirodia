
---

# `demonstration/coordination_scenarios.md`

```markdown
# Coordination Scenarios

## happy_path
- One application, light load.
- Expected: minimal rejects, quick EMI/eligibility, a single lead event.

## contention_spike
- Multiple concurrent applications competing for OTP/CIBIL.
- Expected: early reject spikes; penalties increase; agents back off; rejects/sec decline; EMI/eligibility proceed; verification resumes later.

## verifier_dropout
- Verification agent stops mid-run.
- Expected: eligibility with lower confidence; lead still attempted.

## lossy_gossip
- Gossip updates lag/drop.
- Expected: temporary price differences; convergence by end.

## interactive_console
- Terminal prompts for fields (no LLM normalization).
- Fresh `application_id` per run; ends on first lead, or after idle timeout/hard cap.
- Final summary prints Fields/Proofs/EMI/Eligibility/Leads.
