import collections, random

class PNCounter:
    def __init__(self):
        self.positive = 0
        self.negative = 0
    def increment(self, count: int = 1): self.positive += count
    def decrement(self, count: int = 1): self.negative += count
    def value(self) -> int: return self.positive - self.negative
    def merge(self, other: "PNCounter"):
        self.positive = max(self.positive, other.positive)
        self.negative = max(self.negative, other.negative)

class UsageCRDT:
    def __init__(self):
        self.counters = collections.defaultdict(PNCounter)  # agent_id -> PNCounter
    def increment(self, agent_id: str, count: int = 1):
        self.counters[agent_id].increment(count)
    def total(self) -> int:
        return sum(counter.value() for counter in self.counters.values())
    def merge(self, other: "UsageCRDT"):
        for agent_id, counter in other.counters.items():
            self.counters[agent_id].merge(counter)

class GossipNetwork:
    def __init__(self, agent_ids):
        self.local_views = {
            agent_id: {api: UsageCRDT() for api in ["otp","cibil","itr","vehicle"]}
            for agent_id in agent_ids
        }
        self.reputation = {agent_id: 1.0 for agent_id in agent_ids}

    def gossip_pair(self, agent_a: str, agent_b: str):
        for api in ["otp","cibil","itr","vehicle"]:
            self.local_views[agent_a][api].merge(self.local_views[agent_b][api])
            self.local_views[agent_b][api].merge(self.local_views[agent_a][api])
