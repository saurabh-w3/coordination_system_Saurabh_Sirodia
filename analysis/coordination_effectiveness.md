# Coordination Effectiveness

## What we measure

- **Reject rate** per API over time (OTP, CIBIL, ITR, Vehicle).
- **Time-to-EMI** and **time-to-eligibility**.
- **Lead outcomes** by eligibility status & confidence.
- **Price variance** (optional) across agents over time.

## How to measure (SQLite on `demonstration/state.sqlite`)

```sql
-- Rejects/sec for OTP
SELECT CAST(t) AS INT AS sec, COUNT(*) AS otp_rejects
FROM events
WHERE metric LIKE 'verify_send_otp_reject'
GROUP BY sec ORDER BY sec;

-- Time-to-EMI per app
SELECT app_id,
       MIN(CASE WHEN metric LIKE 'field_name' THEN t END) AS t_start,
       MIN(CASE WHEN metric='emi' THEN t END) AS t_emi,
       (MIN(CASE WHEN metric='emi' THEN t END) - MIN(CASE WHEN metric LIKE 'field_name' THEN t END)) AS t_to_emi
FROM events
GROUP BY app_id;

-- Lead tally
SELECT metric, COUNT(*) FROM events
WHERE metric IN ('lead_submitted','lead_rejected')
GROUP BY metric;
