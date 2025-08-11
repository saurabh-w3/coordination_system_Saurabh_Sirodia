import time, asyncio, random, json
from implementation.coordination_framework.intent_types import Intent
from .base_agent import BaseAgent
from implementation.coordination_framework.llm_support import create_llm, run_single_decision_graph

class ApplicationAgent(BaseAgent):
    REQUIRED_FIELDS = ["name","phone","age","domicile","pan","aadhaar","profession","vehicle_type","vehicle_model","loan_amount","tenure_months"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = create_llm()

    def propose_intents(self):
        price_by_api = self.observe_price_by_api()
        current_fields = self.get_fields()
        missing_fields = [f for f in self.REQUIRED_FIELDS if f not in current_fields]
        context = {
            'observed_prices': price_by_api,
            'missing_fields': missing_fields,
            'time_to_deadline': self.deadline_timestamp - time.time(),
            'token_balance': self.token_balance
        }
        system_prompt = (
            "You are the Application agent. Collect REQUIRED fields with minimal user burden.\n"
            "Return ONLY JSON with up to 2 intents from ask_* actions. Set needs_user=true."
        )
        allowed_actions = [f"ask_{f}" for f in self.REQUIRED_FIELDS]
        plan = run_single_decision_graph(self.llm, system_prompt, {'allowed_actions': allowed_actions, 'context': context})
        intents = []
        if isinstance(plan, dict) and 'intents' in plan and plan['intents']:
            for it in plan['intents'][:2]:
                action = it.get('action', 'ask_name')
                bid = float(it.get('bid_tokens', 0.3))
                intents.append(Intent(self.application_id, action, True, self.agent_id, bid, {}))
        else:
            if missing_fields:
                action = f"ask_{missing_fields[0]}"
                intents.append(Intent(self.application_id, action, True, self.agent_id, 0.3, {}))
        return intents

    async def execute(self, intent: Intent):
        if intent.action.startswith('ask_'):
            field = intent.action.split('ask_')[1]
            mock_value = {
                'name': 'Amit', 'phone': '9998887777', 'age': 28, 'domicile': 'RJ', 'pan': 'ABCDE1234F', 'aadhaar': '1234-5678-9012',
                'profession':'Salaried','vehicle_type': random.choice(['2w','4w']),'vehicle_model':'Swift','loan_amount':500000,'tenure_months':36
            }.get(field, 'NA')
            self.set_field_if_allowed(field, mock_value)
            self.run_logger.log(time.time(), self.agent_id, f'field_{field}', 1, '')
            await asyncio.sleep(0.02)
