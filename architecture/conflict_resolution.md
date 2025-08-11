# Conflict Resolution

## Core conflicts

- **Minimize user burden vs. Maximize certainty**  
  Application asks for minimal fields; Verification wants proofs (OTP/Aadhaar/CIBIL/ITR/Vehicle).

- **Latency vs. Confidence**  
  EMI/Eligibility aim to complete quickly; Verification slows things down when proofs are expensive.

- **Resource contention**  
  OTP/CIBIL are rate-limited; simultaneous calls collide and get rejected.

## Mechanism (why it works)
- Local **price function** inflates under high demand or high reject rates.
- **Token penalties** make repeated rejects expensive.
- Agents **adapt**: Verification backs off when prices spike; EMI/Eligibility proceed with what's available; Verification resumes once contention subsides.
- All without central scheduling or voting.

## Quant example (contention spike)
- t=0..2s: OTP rejects ~6/sec (cap=2/sec). Each reject burns 0.5 tokens.
- Local price rises ~1.0 → ~3.5 (due to `reject_rate≈0.6`, `demand↑`, `ttl↓`).
- Verification bids fall below other actions; Verification pauses; EMI proceeds.
- By t≈5s, reject rates fall; prices normalize; Verification resumes.

## Lead submission policy (disclosed)
- Eligible: accept probability ≈ `0.85 × confidence × SLA_mult`.
- Borderline: accept probability ≈ `0.60 × confidence × SLA_mult`.
- SLA multiplier: Bank A=0.95, Bank B=1.0.
- Single attempt → either `lead_submitted` or `lead_rejected`.

## Why not voting or a central scheduler?
- Voting ignores heterogeneous utilities and can deadlock under scarcity.
- A scheduler violates the **no-coordinator** constraint and becomes a single point of failure.
- The **market-of-intents** adapts online with partial information and local incentives.
