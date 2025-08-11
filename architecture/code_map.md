# Code Map (module → purpose)

## coordination_framework
- `env.py` — Rate-limited endpoints: `otp`, `cibil`, `itr`, `vehicle` (accept/reject counters, jitter).
- `gossip.py` — `PNCounter`, `UsageCRDT`, `GossipNetwork` (merge peers).
- `market.py` — `compute_price(demand, reject_rate, ttl_seconds)`.
- `db.py` — SQLite schema & helpers (applications, verifications, emi, eligibility, leads, events).
- `access.py` — Role→table allow-lists (checked by safe helpers in BaseAgent).
- `logger.py` — `RunLogger.log(t, agent, metric, value, extra)` (CSV + DB).

## agents
- `base_agent.py` — main loop, deadlines, tokens, gossip, safe DB helpers.
- `greeting_agent.py` — single greeting event.
- `application_agent.py` — automated intake.
- `interactive_application_agent.py` — terminal prompts; integer casts for a few fields.
- `verification_agent.py` — choose & call simulated APIs; log `verify_*_ok/reject`; penalize rejects.
- `emi_agent.py` — compute EMI once (standard formula).
- `eligibility_agent.py` — rule-based status + confidence; writes `eligibility`.
- `lead_generation_agent.py` — single attempt; baked-in acceptance probabilities; writes `leads`.

## scenarios
- `happy_path.py`, `contention_spike.py`, `verifier_dropout.py`, `lossy_gossip.py`
- `interactive_console.py` — fresh `application_id`, idle-aware wait, early stop on lead, hard exit after summary.
