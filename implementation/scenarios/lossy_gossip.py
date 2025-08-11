import asyncio, random
from implementation.coordination_framework.env import Environment
from implementation.coordination_framework.gossip import GossipNetwork
from implementation.coordination_framework.logger import RunLogger
from implementation.agents.greeting_agent import GreetingAgent
from implementation.agents.application_agent import ApplicationAgent
from implementation.agents.verification_agent import VerificationAgent
from implementation.agents.emi_agent import EMICalculatorAgent
from implementation.agents.eligibility_agent import EligibilityAgent
from implementation.agents.lead_generation_agent import LeadGenerationAgent

async def run_lossy():
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

    # Wrap agents to occasionally skip gossip exchange by reducing peers list on the fly
    peers = {aid: [x for x in agent_ids if x!=aid] for aid in agent_ids}
    async def run_with_loss(agent):
        lossy_peers = peers[agent.agent_id][:]
        if random.random() < 0.5 and lossy_peers:
            lossy_peers = lossy_peers[:-1]  # drop one neighbor to simulate loss
        await agent.run(lossy_peers)

    await asyncio.gather(*[
        run_with_loss(greet), run_with_loss(app), run_with_loss(verify),
        run_with_loss(emi), run_with_loss(elig), run_with_loss(lead)
    ])

    run_logger.flush_csv('lossy_gossip')
    for name, ep in environment.apis.items():
        print(f"{name}: accepts={ep.accept_count} rejects={ep.reject_count}")

if __name__ == '__main__':
    asyncio.run(run_lossy())
