
import random, time
from implementation.agents.base_agent import BaseAgent
from implementation.coordination_framework.intent_types import Intent

# Acceptance policy (baked in — adjust here if needed)
ELIGIBLE_ACCEPT_PROB = 0.85
BORDERLINE_ACCEPT_PROB = 0.60
SERVICE_MULTIPLIER = {'A': 0.95, 'B': 1.00}  # Bank A has a slightly stricter SLA
FORCE_ACCEPT = False                          # Set True here if you want guaranteed accept in demos

class LeadGenerationAgent(BaseAgent):
    def __init__(self, agent_id, environment, network, run_logger, application_id="default"):
        super().__init__(agent_id, environment, network, run_logger, application_id)
        self.submitted = False
        self.attempted = False

    def propose_intents(self):
        if self.submitted or self.attempted:
            return []
        status, confidence = self.get_eligibility()
        if not status:
            return []
        # Simple bank choice — you can make this smarter using observed prices/latency
        bank = 'A' if status == 'Eligible' else 'A'  # keep A by default
        return [Intent(self.application_id, f'submit_bank_{bank.lower()}', False, self.agent_id, 0.5, {})]

    async def execute(self, intent: Intent):
        self.attempted = True
        status, confidence = self.get_eligibility()
        bank = 'A' if intent.action.endswith('_a') else 'B'
        base = ELIGIBLE_ACCEPT_PROB if status == 'Eligible' else BORDERLINE_ACCEPT_PROB
        mult = SERVICE_MULTIPLIER.get(bank, 1.0)
        if FORCE_ACCEPT:
            accepted = True
        else:
            accepted = random.random() < base * (confidence or 0.5) * mult
        if accepted:
            self.submitted = True
            self.add_lead_if_allowed(bank, 'submitted', f'{status}:{(confidence or 0):.2f}')
            self.run_logger.log(time.time(), self.agent_id, 'lead_submitted', 1, f'Bank{bank}:{status}:{(confidence or 0):.2f}')
        else:
            self.add_lead_if_allowed(bank, 'rejected', f'{status}:{(confidence or 0):.2f}')
            self.run_logger.log(time.time(), self.agent_id, 'lead_rejected', 1, f'Bank{bank}:{status}:{(confidence or 0):.2f}')
