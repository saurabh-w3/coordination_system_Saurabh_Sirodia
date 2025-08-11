# Auto Credit Loan Approval — Decentralized Agentic System

This repository implements a **fully decentralized, emergent-coordination** system for auto-credit loan approval.
Each agent can make LLM-backed decisions when an API key is provided; otherwise it uses safe heuristics. The interactive Application agent deliberately uses terminal prompts (no LLM normalization) to highlight coordination without centralized intelligence.

with strictly limited access to relevant DB tables and
simulated external services. There is **no central coordinator** and **no pre-scripted workflow**; action ordering emerges from
local decisions, shared price signals, token budgets, and rate-limit contention.

## Quickstart (macOS)

```bash
cd coordination_system_Saurabh_Sirodia

# 1) Create and activate a venv
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r implementation/requirements.txt

# 3) (Optional) Enable real LLM agents
export OPENAI_API_KEY=sk-...           # if omitted, system uses safe heuristic fallback
export OPENAI_MODEL=gpt-4o-mini        # optional override

# 4) Run scenarios
# End-to-end, low contention
python3 -m implementation.scenarios.happy_path

# Stress: more apps competing for scarce APIs
python3 -m implementation.scenarios.contention_spike

# Fault: verifier stops mid-run
python3 -m implementation.scenarios.verifier_dropout

# Fault: gossip is lossy/stale
python3 -m implementation.scenarios.lossy_gossip


# Interactive console (type your own details)
python3 -u -m implementation.scenarios.interactive_console

# 5) Logs
open demonstration/execution_logs/
```

**Why this fits the assessment**  
- No coordinator; agents self-organize via **gossip + CRDT + shared price function + token budgets**.  
- **Conflicting objectives** drive negotiation (Application minimizes user burden, Verification maximizes certainty, EMI speed, Eligibility confidence, LeadGen bank acceptance/TTFB).  
- **Emergent behaviors**: collisions reduce over time, phase-shifted access, implicit consensus on action ordering, specialization, resilience to churn.  
- **LLM-first**: each agent contains its own LangGraph reasoning; we do not centralize the “brain.”


## Repo map (what code lives where)

- `implementation/coordination_framework/`
  - `env.py` — simulated external APIs (`otp`, `cibil`, `itr`, `vehicle`) with rate limits & jitter
  - `gossip.py` — CRDT counters + peer merges
  - `market.py` — shared price function
  - `db.py` — SQLite schema & helpers (`applications`, `verifications`, `emi`, `eligibility`, `leads`, `events`)
  - `access.py` — role→table allow-lists
  - `logger.py` — CSV + DB event logging
- `implementation/agents/`
  - `base_agent.py` — core loop (gossip → propose_intents → execute), token budgets, deadlines
  - `interactive_application_agent.py` — terminal prompts (no LLM normalization)
  - `verification_agent.py` — OTP/Aadhaar/CIBIL/ITR/Vehicle (simulated)
  - `emi_agent.py` — standard EMI formula (one-shot)
  - `eligibility_agent.py` — rules + confidence
  - `lead_generation_agent.py` — **baked-in** acceptance policy, single attempt, writes `leads`
- `implementation/scenarios/`
  - `happy_path.py`, `contention_spike.py`, `verifier_dropout.py`, `lossy_gossip.py`, `interactive_console.py`


All agents compute **local prices** from gossip/CRDT, maintain a **token_balance**, and propose Intents using their **LLM**. There is **no central controller**.

## Coordination mechanics (in code)
**Shared price function**
price = (1 + 3 * demand/(1 + demand)) * (1 + 4reject_rate) * (1 + 2(1/max(ttl, 0.5)))
- `demand`: API usage from gossiped counters
- `reject_rate`: recent rejects / total
- `ttl`: time-to-deadline

**Token economics**
- Initial tokens per agent: 6.0
- Penalty per rejected API call (Verification): 0.5 tokens
- Loop cadence: ~0.15s ± 0.05

## Interactive mode (what to expect)
- Fresh `application_id` each run (no DB cleanup needed).
- Agents run concurrently while you type.
- Run **stops on first lead**, or after **idle timeout**, or **hard cap**.
- Final summary prints **Fields, Proofs, EMI, Eligibility, Leads**.
- The process **hard-exits** after the summary to avoid lingering `input()` threads.


