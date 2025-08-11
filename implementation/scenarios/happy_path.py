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

async def main():
    environment = Environment()
    agent_ids = ['greet','app','verify','emi','elig','lead']
    network = GossipNetwork(agent_ids)
    run_logger = RunLogger()

    app = ApplicationAgent('app', environment, network, run_logger)
    verify = VerificationAgent('verify', environment, network, run_logger)
    emi = EMICalculatorAgent('emi', environment, network, run_logger)
    elig = EligibilityAgent('elig', environment, network, run_logger)
    lead = LeadGenerationAgent('lead', environment, network, run_logger)
    greet = GreetingAgent('greet', environment, network, run_logger)

    peers = {aid: [x for x in agent_ids if x!=aid] for aid in agent_ids}
    tasks = [asyncio.create_task(a.run(peers[a.agent_id])) for a in [greet, app, verify, emi, elig, lead]]
    await asyncio.gather(*tasks, return_exceptions=True)

    run_logger.flush_csv('happy_path')
    for name, ep in environment.apis.items():
        print(f"{name}: accepts={ep.accept_count} rejects={ep.reject_count}")

if __name__ == '__main__':
    asyncio.run(main())
