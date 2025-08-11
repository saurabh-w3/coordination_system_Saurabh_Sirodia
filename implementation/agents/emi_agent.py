import time, asyncio
from implementation.coordination_framework.intent_types import Intent
from .base_agent import BaseAgent
from implementation.coordination_framework.llm_support import create_llm, run_single_decision_graph

class EMICalculatorAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = create_llm()

    def propose_intents(self):
        current_fields = self.get_fields()
        # Propose only once when EMI not yet computed
        if all(k in current_fields for k in ["loan_amount", "tenure_months", "vehicle_type"]) and (self.get_emi() is None):
            price_by_api = self.observe_price_by_api()
            context = {
                "observed_prices": price_by_api,
                "time_to_deadline": self.deadline_timestamp - time.time(),
                "token_balance": self.token_balance,
            }
            system_prompt = "You are the EMI agent. Propose compute_emi when minimally sufficient fields exist. Machine action only."
            plan = run_single_decision_graph(self.llm, system_prompt, {"allowed_actions": ["compute_emi"], "context": context})
            bid = 0.3
            if isinstance(plan, dict) and "intents" in plan and plan["intents"]:
                bid = float(plan["intents"][0].get("bid_tokens", 0.3))
            return [Intent(self.application_id, "compute_emi", False, self.agent_id, bid, {})]
        return []


    async def execute(self, intent: Intent):
        fields = self.get_fields()
        principal = float(fields.get('loan_amount', 0))
        annual_rate = 0.12 if fields.get('vehicle_type')=='4w' else 0.10
        monthly_rate = annual_rate/12
        months = int(fields.get('tenure_months', 12))
        if principal <= 0 or months <= 0:
            emi_value = 0.0
        else:
            emi_value = (principal*monthly_rate*(1+monthly_rate)**months) / (((1+monthly_rate)**months)-1)
        self.set_emi_if_allowed(emi_value)
        self.run_logger.log(time.time(), self.agent_id, 'emi', emi_value, '')
        await asyncio.sleep(0.01)
