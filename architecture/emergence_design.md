# Emergence Design

## Signals to observe

1) **Rejects/sec decline** under contention  
   As penalties accumulate, agents self-space, lowering collision rates.

2) **Price convergence** across agents  
   Gossip spreads local counters; price variance shrinks over time.

3) **Stable time-to-EMI**  
   Even with verification backoff, EMI completes quickly once minimal fields exist.

4) **Role specialization**  
   Token spend/action mix per agent shifts and stabilizes (division of labor).

## How we compute from logs

- **Rejects/sec (OTP example):**
  ```sql
  SELECT CAST(t) AS INT AS sec, COUNT(*) AS otp_rejects
  FROM events
  WHERE metric LIKE 'verify_send_otp_reject'
  GROUP BY sec ORDER BY sec;

## Time-to-EMI (per app):
# SELECT app_id,
       MIN(CASE WHEN metric LIKE 'field_name' THEN t END) AS t_start,
       MIN(CASE WHEN metric='emi' THEN t END) AS t_emi,
       (MIN(CASE WHEN metric='emi' THEN t END) - MIN(CASE WHEN metric LIKE 'field_name' THEN t END)) AS t_to_emi
# FROM events GROUP BY app_id;
