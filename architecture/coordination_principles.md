
---

# `architecture/coordination_principles.md`

```markdown
# Coordination Principles

## No Central Coordinator
Every agent runs an independent loop:
1) refresh local gossip
2) compute local prices
3) propose intents with bids (tokens)
4) execute the top intent if budget allows

The environment **only** enforces API rate limits and latency; it does not schedule work.

---

## Market of Intents (local decision policy)
Each agent uses a shared price function to value actions and bids tokens accordingly. Budget is finite; rejections burn extra tokens; therefore agents **self-regulate** under contention.

**Price function used in code** (`market.compute_price`):
price = (1 + 3 * demand/(1 + demand))* (1 + 4 * reject_rate)* (1 + 2 * (1 / max(ttl, 0.5)))

- `demand` = recent usage for that API (from gossip counters)
- `reject_rate` = recent rejects / total calls
- `ttl` = time to agent’s local deadline

---

## Gossip + CRDT
Each agent shares partial counters (PN-counters) for usage and rejects. Merges are associative/commutative (CRDT), so views are **stale but converge**. This preserves **asymmetric information** while enabling adaptation.

---

## Token Economics
- Initial `token_balance` per agent: **6.0**
- Per rejected API call penalty: **0.5 tokens** (applied by Verification)
- Loop cadence: **~0.15s ± 0.05**
- Soft deadline (interactive): **900s**; scenario ends earlier on lead.

Budget + penalties make collisions expensive; agents back off naturally (emergent anti-coordination).

---

## Failure Semantics (as implemented)
- **DB errors** → log `db_error`, continue (no hard crash).
- **API rate limit/internal error** → structured reject, penalty applied, continue.
- **Agent exceptions** → caught in `base_agent.run()`, logged as `agent_error`, loop continues.

**Where in code**
- `market.py` — price function
- `gossip.py` — CRDT counters + merge
- `base_agent.py` — tokens, penalties, loop & exception boundaries
- `env.py` — rate limits + jitter
