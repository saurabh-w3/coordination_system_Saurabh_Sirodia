# Failure Modes

## API rate limit or internal error
- Simulated endpoints return structured rejects.
- Verification logs `verify_*_reject`, applies token penalty, and continues.

## Database write error
- Safe DB helpers catch, log `db_error`, and proceed.
- Logger falls back to printing the last rows to stdout if CSV write fails.

## Agent exception
- Caught in `base_agent.run()` and logged as `agent_error`.
- Other agents continue (no cascade failure).

## Verifier dropout
- Eligibility confidence decreases.
- Lead may still be attempted; outcome depends on policy.

## Lossy gossip
- Local prices diverge briefly; converge as merges continue.
