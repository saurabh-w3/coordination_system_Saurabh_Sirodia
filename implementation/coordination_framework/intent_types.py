from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Intent:
    application_id: str
    action: str
    needs_user: bool
    proposed_by_agent: str
    bid_tokens: float
    metadata: Dict[str, Any] = field(default_factory=dict)
