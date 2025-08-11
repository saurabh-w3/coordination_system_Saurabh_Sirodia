# Table-level access control to constrain each agent's visibility and writes.
AGENT_TABLE_ACCESS = {
    "greet": set(),
    "app": {"applications", "events"},
    "verify": {"verifications", "events"},
    "emi": {"emi", "events", "applications"},
    "elig": {"eligibility", "events", "applications", "verifications", "emi"},
    "lead": {"leads", "events", "eligibility"},
}

def can_access(agent_id: str, table_name: str) -> bool:
    role_prefix = agent_id.split('_')[0]
    return table_name in AGENT_TABLE_ACCESS.get(role_prefix, set())
