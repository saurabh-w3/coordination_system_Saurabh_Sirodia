
---

# `analysis/failure_recovery.md`

```markdown
# Failure Recovery

## Verifier dropout
- Expect lower-confidence eligibility; lead still attempted (policy dependent).

## Lossy gossip
- Temporary price divergence; converges with continued merges; system remains productive.

## DB / Logger issues
- Safe fallbacks; events printed to stdout when files cannot be written.
- The run continues; analysis still possible from partial logs.

## Interactive partial form
- If the user stops mid-form, interactive runner ends after idle timeout and prints a **partial summary**; no lead is expected.
