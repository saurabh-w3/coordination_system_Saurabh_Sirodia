import time, asyncio
from implementation.coordination_framework.intent_types import Intent
from .base_agent import BaseAgent
from implementation.coordination_framework.llm_support import create_llm, run_single_decision_graph

class EligibilityAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = create_llm()

    def propose_intents(self):
        status_existing, _ = self.get_eligibility()
        if status_existing is not None:
            return []

        proofs = self.get_proofs()
        emi_value = self.get_emi()
        if {'phone','pan','vehicle'}.issubset(set(proofs.keys())) and emi_value is not None:
            price_by_api = self.observe_price_by_api()
            context = {
                'observed_prices': price_by_api,
                'time_to_deadline': self.deadline_timestamp - time.time(),
                'token_balance': self.token_balance
            }
            system_prompt = "You are the Eligibility agent. Decide to assess eligibility now. Machine action only: assess_eligibility."
            plan = run_single_decision_graph(self.llm, system_prompt, {'allowed_actions':['assess_eligibility'], 'context': context})
            bid = 0.6
            if isinstance(plan, dict) and 'intents' in plan and plan['intents']:
                bid = float(plan['intents'][0].get('bid_tokens', 0.6))
            return [Intent(self.application_id, 'assess_eligibility', False, self.agent_id, bid, {})]
        return []

    async def execute(self, intent: Intent):
        fields = self.get_fields()
        income = 60000.0
        emi_value = self.get_emi() or 0.0
        age = int(fields.get('age', 100))
        dti_ratio = emi_value / max(1.0, income)
        is_eligible = (dti_ratio < 0.4) and (21 <= age <= 60)
        confidence = 0.7
        proofs = self.get_proofs()
        if 'itr' in proofs: confidence += 0.2
        if 'cibil' in proofs: confidence += 0.1
        status = 'Eligible' if is_eligible else 'Borderline'
        self.set_eligibility_if_allowed(status, confidence)
        self.run_logger.log(time.time(), self.agent_id, 'eligibility_conf', confidence, status)
        await asyncio.sleep(0.01)
