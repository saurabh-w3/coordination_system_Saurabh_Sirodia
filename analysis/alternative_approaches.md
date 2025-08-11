# Alternative Approaches

## Central scheduler (rejected)
- Conflicts with the “no central coordinator” constraint; creates a single point of failure; requires omniscient state.

## Voting consensus (rejected)
- Ignores heterogeneous utilities; can deadlock under scarcity; not adaptive to changing contention.

## Blackboard/shared memory (rejected)
- Converges toward centralization and breaks asymmetric information.

## RL-based scheduling (future)
- Promising for learned bidding policies, but requires safety rails and careful reward shaping. The current **mechanism-design** approach (price + tokens + penalties) is simple, robust, and interpretable.
