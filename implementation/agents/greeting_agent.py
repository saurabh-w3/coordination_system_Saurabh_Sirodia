import time, asyncio, json
from implementation.coordination_framework.intent_types import Intent
from .base_agent import BaseAgent
from implementation.coordination_framework.llm_support import create_llm, run_single_decision_graph

class GreetingAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = create_llm()
        self.greeted = False

    def propose_intents(self):
        if self.greeted:
            return []
        price_by_api = self.observe_price_by_api()
        context = {
            'observed_prices': price_by_api,
            'time_to_deadline': self.deadline_timestamp - time.time(),
            'token_balance': self.token_balance
        }
        system_prompt = (
            "You are the Greeting agent. Greet the user once at the start.\n"
            "Output ONLY JSON: {\"intents\":[{\"action\":\"greet\",\"needs_user\":true,\"bid_tokens\":<0-10>,\"metadata\":{}}]}"
        )
        payload = {'allowed_actions': ['greet'], 'context': context}
        plan = run_single_decision_graph(self.llm, system_prompt, payload)
        intents = []
        if isinstance(plan, dict) and 'intents' in plan and plan['intents']:
            for it in plan['intents'][:1]:
                intents.append(Intent(self.application_id, 'greet', True, self.agent_id, float(it.get('bid_tokens', 0.1)), {}))
        else:
            intents.append(Intent(self.application_id, 'greet', True, self.agent_id, 0.1, {}))
        return intents

    async def execute(self, intent: Intent):
        self.run_logger.log(time.time(), self.agent_id, 'greeting', 1, 'Welcome!')
        self.greeted = True
        await asyncio.sleep(0.01)
