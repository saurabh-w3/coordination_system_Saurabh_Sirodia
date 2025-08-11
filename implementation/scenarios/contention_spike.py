import asyncio
from implementation.coordination_framework.env import Environment
from implementation.coordination_framework.gossip import GossipNetwork
from implementation.coordination_framework.logger import RunLogger
from implementation.agents.greeting_agent import GreetingAgent
from implementation.agents.application_agent import ApplicationAgent
from implementation.agents.verification_agent import VerificationAgent
from implementation.agents.emi_agent import EMICalculatorAgent
from implementation.agents.eligibility_agent import EligibilityAgent
from implementation.agents.lead_generation_agent import LeadGenerationAgent

async def run_multi(application_count: int = 6):
    environment = Environment()
    agent_ids = []
    agents = []
    run_logger = RunLogger()
    for i in range(application_count):
        agent_ids += [f'greet_{i}',f'app_{i}',f'verify_{i}',f'emi_{i}',f'elig_{i}',f'lead_{i}']
    network = GossipNetwork(agent_ids)

    for i in range(application_count):
        application_id = f'app{i+1}'
        greet = GreetingAgent(f'greet_{i}', environment, network, run_logger, application_id=application_id)
        app = ApplicationAgent(f'app_{i}', environment, network, run_logger, application_id=application_id)
        verify = VerificationAgent(f'verify_{i}', environment, network, run_logger, application_id=application_id)
        verify.token_balance = 4.0
        emi = EMICalculatorAgent(f'emi_{i}', environment, network, run_logger, application_id=application_id)
        elig = EligibilityAgent(f'elig_{i}', environment, network, run_logger, application_id=application_id)
        lead = LeadGenerationAgent(f'lead_{i}', environment, network, run_logger, application_id=application_id)
        agents += [greet, app, verify, emi, elig, lead]

    peers = {aid: [x for x in agent_ids if x!=aid] for aid in agent_ids}
    tasks = [asyncio.create_task(a.run(peers[a.agent_id])) for a in agents]
    await asyncio.gather(*tasks, return_exceptions=True)

    run_logger.flush_csv('contention_spike')
    for name, ep in environment.apis.items():
        print(f"{name}: accepts={ep.accept_count} rejects={ep.reject_count}")

if __name__ == '__main__':
    asyncio.run(run_multi(application_count=6))
