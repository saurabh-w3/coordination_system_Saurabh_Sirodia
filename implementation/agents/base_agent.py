import time, random, asyncio
from typing import Dict
from implementation.coordination_framework.market import compute_price
from implementation.coordination_framework.gossip import UsageCRDT
from implementation.coordination_framework import db, access
from implementation.coordination_framework.intent_types import Intent

class BaseAgent:
    def __init__(self, agent_id: str, environment, network, run_logger, application_id: str='app1'):
        self.agent_id = agent_id
        self.environment = environment
        self.network = network
        self.run_logger = run_logger
        self.token_balance = 6.0
        self.loop_tick_seconds = 0.15 + random.random() * 0.05
        self.deadline_timestamp = time.time() + 15.0
        self.api_usage_by_name: Dict[str, UsageCRDT] = {api: UsageCRDT() for api in ['otp','cibil','itr','vehicle']}
        self.application_id = application_id
        self.random = random.Random(hash(agent_id) & 0xffffffff)
        self.conn = db.initialize_database()

    def gossip_exchange(self, peer_ids):
        if not peer_ids: return
        peer = self.random.choice(peer_ids)
        self.network.gossip_pair(self.agent_id, peer)
        for api in self.api_usage_by_name.keys():
            self.api_usage_by_name[api].merge(self.network.local_views[self.agent_id][api])

    def observe_price_by_api(self) -> Dict[str, float]:
        price_by_api = {}
        for api_name, endpoint in self.environment.apis.items():
            observed_demand = self.api_usage_by_name[api_name].total()
            total = max(1, endpoint.accept_count + endpoint.reject_count)
            rejection_rate = endpoint.reject_count / total
            time_to_deadline_seconds = self.deadline_timestamp - time.time()
            price_by_api[api_name] = compute_price(observed_demand, rejection_rate, time_to_deadline_seconds)
        return price_by_api

    def spend_tokens(self, amount: float) -> bool:
        if self.token_balance >= amount:
            self.token_balance -= amount
            return True
        return False
    
    def add_lead_if_allowed(self, bank: str, status: str, meta: str):
        from implementation.coordination_framework import db, access
        if access.can_access(self.agent_id, 'leads'):
            try:
                db.add_lead(self.conn, self.application_id, bank, status, meta)
            except Exception as e:
                self.run_logger.log(time.time(), self.agent_id, 'db_error', 'add_lead', str(e)[:200])


    async def run(self, peer_ids):

        while time.time() < self.deadline_timestamp:
            try:
                self.gossip_exchange(peer_ids)
            except Exception as e:
                self.run_logger.log(time.time(), self.agent_id, 'gossip_error', 'exchange', str(e)[:200])

            try:
                intents = self.propose_intents()
            except Exception as e:
                self.run_logger.log(time.time(), self.agent_id, 'agent_error', 'propose_intents', str(e)[:200])
                intents = []

            if intents:
                selected_intent = max(intents, key=lambda i: i.bid_tokens)
                if self.spend_tokens(selected_intent.bid_tokens):
                    try:
                        await self.execute(selected_intent)
                    except Exception as e:
                        self.run_logger.log(time.time(), self.agent_id, 'agent_error', 'execute', str(e)[:200])

            await asyncio.sleep(self.loop_tick_seconds)



    # restricted DB helpers
    def set_field_if_allowed(self, field: str, value):
        if access.can_access(self.agent_id, 'applications'):
            db.set_field(self.conn, self.application_id, field, value)
    def set_proof_if_allowed(self, proof: str, value):
        if access.can_access(self.agent_id, 'verifications'):
            db.set_proof(self.conn, self.application_id, proof, value)
    def set_emi_if_allowed(self, amount: float):
        if access.can_access(self.agent_id, 'emi'):
            db.set_emi(self.conn, self.application_id, amount)
    def set_eligibility_if_allowed(self, status: str, confidence: float):
        if access.can_access(self.agent_id, 'eligibility'):
            db.set_eligibility(self.conn, self.application_id, status, confidence)
    def get_fields(self): return db.get_fields(self.conn, self.application_id)
    def get_proofs(self): return db.get_proofs(self.conn, self.application_id)
    def get_emi(self): return db.get_emi(self.conn, self.application_id)
    def get_eligibility(self): return db.get_eligibility(self.conn, self.application_id)

    def propose_intents(self): return []
    async def execute(self, intent: Intent): pass
