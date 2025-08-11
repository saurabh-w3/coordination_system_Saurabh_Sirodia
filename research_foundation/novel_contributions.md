# Novel Contributions
- **Market of Intents** for loan approval under asymmetric information with LLM agents.
- Implicit consensus via a public price function plus token budgets (no voting, no leader).
- Strict DB table access per role to constrain LLM actions.


## Engineering Notes
- Token penalties create an implicit **anti-coordination** (minority-game-like) effect that reduces collisions without explicit scheduling.  
- Access control ensures **principled myopia**: agents cannot “cheat” by reading everything.
