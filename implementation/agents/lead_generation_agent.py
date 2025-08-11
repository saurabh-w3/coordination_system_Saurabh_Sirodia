# import time, asyncio, random
# from implementation.coordination_framework.intent_types import Intent
# from .base_agent import BaseAgent
# from implementation.coordination_framework.llm_support import create_llm, run_single_decision_graph

# class LeadGenerationAgent(BaseAgent):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.llm = create_llm()
#         self.submitted = False
#         self.attempted = False 

#     def propose_intents(self):
#         status, confidence = self.get_eligibility()
#         if status and not self.submitted:
#             price_by_api = self.observe_price_by_api()
#             context = {
#                 'observed_prices': price_by_api,
#                 'time_to_deadline': self.deadline_timestamp - time.time(),
#                 'token_balance': self.token_balance,
#                 'eligibility': {'status': status, 'confidence': confidence}
#             }
#             system_prompt = "You are the LeadGeneration agent. Choose submit_bank_a or submit_bank_b to maximize acceptance x SLA."
#             plan = run_single_decision_graph(self.llm, system_prompt, {'allowed_actions':['submit_bank_a','submit_bank_b'], 'context': context})
#             intents = []
#             if isinstance(plan, dict) and 'intents' in plan and plan['intents']:
#                 for it in plan['intents'][:1]:
#                     action = it.get('action','submit_bank_a')
#                     bid = float(it.get('bid_tokens', 0.5))
#                     intents.append(Intent(self.application_id, action, False, self.agent_id, bid, {}))
#             else:
#                 intents.append(Intent(self.application_id, 'submit_bank_a', False, self.agent_id, 0.5, {}))
#             return intents
#         return []

#     async def execute(self, intent: Intent):
#         self.attempted = True
#         status, confidence = self.get_eligibility()
#         bank = 'A' if intent.action.endswith('_a') else 'B'
#         base_accept_probability = 0.8 if status == 'Eligible' else 0.4
#         service_level_adjustment = 0.9 if bank == 'A' else 1.0
#         accepted = random.random() < base_accept_probability * (confidence or 0.5) * service_level_adjustment
#         if accepted:
#             self.submitted = True
#             self.add_lead_if_allowed(bank, 'submitted', f'{status}:{(confidence or 0):.2f}')
#             self.run_logger.log(time.time(), self.agent_id, 'lead_submitted', 1, f'Bank{bank}:{status}:{(confidence or 0):.2f}')
#         else:
#             self.add_lead_if_allowed(bank, 'rejected', f'{status}:{(confidence or 0):.2f}')
#             self.run_logger.log(time.time(), self.agent_id, 'lead_rejected', 1, f'Bank{bank}:{status}:{(confidence or 0):.2f}')

#         await asyncio.sleep(0.01)


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
