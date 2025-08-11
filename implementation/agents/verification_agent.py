import time, asyncio, json
from implementation.coordination_framework.intent_types import Intent
from .base_agent import BaseAgent
from implementation.coordination_framework.llm_support import create_llm, run_single_decision_graph

class VerificationAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = create_llm()
        self.collision_penalty_tokens = 1.2

    def propose_intents(self):
        price_by_api = self.observe_price_by_api()
        current_fields = self.get_fields()
        current_proofs = self.get_proofs()

        missing_proofs = []
        if 'phone' in current_fields and 'phone' not in current_proofs: missing_proofs.append('phone')
        if 'aadhaar' in current_fields and 'aadhaar' not in current_proofs: missing_proofs.append('aadhaar')
        if 'pan' in current_fields and 'pan' not in current_proofs: missing_proofs.append('pan')
        if 'profession' in current_fields and 'itr' not in current_proofs: missing_proofs.append('itr')
        if 'vehicle_model' in current_fields and 'vehicle' not in current_proofs: missing_proofs.append('vehicle')

        context = {
            'observed_prices': price_by_api,
            'verified': list(current_proofs.keys()),
            'missing_proofs': missing_proofs,
            'time_to_deadline': self.deadline_timestamp - time.time(),
            'token_balance': self.token_balance
        }
        system_prompt = (
            "You are the Verification agent. Maximize certainty per token under rate limits.\n"
            "Allowed actions: send_otp, aadhaar_otp, fetch_cibil, fetch_itr, vehicle_lookup. Machine actions only."
        )
        allowed_actions = ['send_otp','aadhaar_otp','fetch_cibil','fetch_itr','vehicle_lookup']
        plan = run_single_decision_graph(self.llm, system_prompt, {'allowed_actions': allowed_actions, 'context': context})

        intents = []
        if isinstance(plan, dict) and 'intents' in plan and plan['intents']:
            for it in plan['intents'][:3]:
                action = it.get('action')
                bid = float(it.get('bid_tokens', 0.4))
                metadata = {}
                if action == 'send_otp' and 'phone' in current_fields: metadata = {'phone': current_fields['phone']}
                elif action == 'aadhaar_otp' and 'aadhaar' in current_fields: metadata = {'aadhaar': current_fields['aadhaar']}
                elif action == 'fetch_cibil' and 'pan' in current_fields: metadata = {'pan': current_fields['pan']}
                elif action == 'fetch_itr' and 'pan' in current_fields: metadata = {'pan': current_fields['pan']}
                elif action == 'vehicle_lookup' and 'vehicle_model' in current_fields: metadata = {'model': current_fields['vehicle_model']}
                if action in allowed_actions:
                    intents.append(Intent(self.application_id, action, False, self.agent_id, bid, metadata))
        else:
            # Heuristic fallback: choose up to 2 missing proofs in a sensible order
            order = ["phone", "aadhaar", "pan", "itr", "vehicle"]
            picked = 0
            for need in order:
                if need in missing_proofs:
                    if need == "phone" and "phone" in current_fields:
                        intents.append(Intent(self.application_id, "send_otp", False, self.agent_id, 0.5, {"phone": current_fields.get("phone", "")}))
                    elif need == "aadhaar" and "aadhaar" in current_fields:
                        intents.append(Intent(self.application_id, "aadhaar_otp", False, self.agent_id, 0.4, {"aadhaar": current_fields.get("aadhaar", "")}))
                    elif need == "pan" and "pan" in current_fields:
                        intents.append(Intent(self.application_id, "fetch_cibil", False, self.agent_id, 0.6, {"pan": current_fields.get("pan", "")}))
                    elif need == "itr" and "pan" in current_fields:
                        intents.append(Intent(self.application_id, "fetch_itr", False, self.agent_id, 0.5, {"pan": current_fields.get("pan", "")}))
                    elif need == "vehicle" and "vehicle_model" in current_fields:
                        intents.append(Intent(self.application_id, "vehicle_lookup", False, self.agent_id, 0.3, {"model": current_fields.get("vehicle_model", "")}))
                    picked += 1
                    if picked >= 2:
                        break
        return intents

    async def execute(self, intent: Intent):
        api_map = {'send_otp':'otp','aadhaar_otp':'otp','fetch_cibil':'cibil','fetch_itr':'itr','vehicle_lookup':'vehicle'}
        api_name = api_map[intent.action]
        ok, resp = await self.environment.apis[api_name].call(self.agent_id, intent.metadata)
        self.api_usage_by_name[api_name].increment(self.agent_id, 1)
        self.network.local_views[self.agent_id][api_name].increment(self.agent_id, 1)
        if ok:
            if intent.action=='send_otp': self.set_proof_if_allowed('phone','ok')
            elif intent.action=='aadhaar_otp': self.set_proof_if_allowed('aadhaar','ok')
            elif intent.action=='fetch_cibil': self.set_proof_if_allowed('pan','ok'); self.set_proof_if_allowed('cibil','750')
            elif intent.action=='fetch_itr': self.set_proof_if_allowed('itr','ok')
            elif intent.action=='vehicle_lookup': self.set_proof_if_allowed('vehicle','ok')
            self.run_logger.log(time.time(), self.agent_id, f'verify_{intent.action}_ok', 1, '')
        else:
            self.token_balance -= self.collision_penalty_tokens
            self.run_logger.log(time.time(), self.agent_id, f'verify_{intent.action}_reject', 1, '')
