
---

# `analysis/scalability_analysis.md`

```markdown
# Scalability Analysis

## Experiment grid

| concurrent apps | otp cap/s | cibil cap/s | total rejects | median time-to-eligibility | leads submitted |
|---:|---:|---:|---:|---:|---:|
| 2  | 2 | 1 | … | … | … |
| 4  | 2 | 1 | … | … | … |
| 6  | 2 | 1 | … | … | … |
| 10 | 2 | 1 | … | … | … |

Run:
```bash
python3 -m implementation.scenarios.contention_spike   # adjust N inside if needed
sqlite3 demonstration/state.sqlite "SELECT metric, COUNT(*) FROM events WHERE metric LIKE 'verify_%_ok' OR metric LIKE 'verify_%_reject' GROUP BY metric;"
