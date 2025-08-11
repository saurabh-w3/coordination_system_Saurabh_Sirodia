def compute_price(observed_demand: float, rejection_rate: float, time_to_deadline_seconds: float) -> float:
    base = 1.0 + 3.0 * (observed_demand / (1.0 + observed_demand))
    penalty = 1.0 + 4.0 * rejection_rate
    urgency = 1.0 + 2.0 * (1.0 / max(time_to_deadline_seconds, 0.5))
    return base * penalty * urgency
