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

async def run_with_dropout():
    environment = Environment()
    agent_ids = ['greet','app','verify','emi','elig','lead']
    network = GossipNetwork(agent_ids)
    run_logger = RunLogger()

    app = ApplicationAgent('app', environment, network, run_logger)
    # Drop verification intentionally after half deadline by not scheduling it.
    verify = VerificationAgent('verify', environment, network, run_logger)
    verify.deadline_timestamp -= 9.0  # short lifespan to emulate failure
    emi = EMICalculatorAgent('emi', environment, network, run_logger)
    elig = EligibilityAgent('elig', environment, network, run_logger)
    lead = LeadGenerationAgent('lead', environment, network, run_logger)
    greet = GreetingAgent('greet', environment, network, run_logger)

    peers = {aid: [x for x in agent_ids if x!=aid] for aid in agent_ids}
    tasks = [
        asyncio.create_task(greet.run(peers[greet.agent_id])),
        asyncio.create_task(app.run(peers[app.agent_id])),
        asyncio.create_task(verify.run(peers[verify.agent_id])),
        asyncio.create_task(emi.run(peers[emi.agent_id])),
        asyncio.create_task(elig.run(peers[elig.agent_id])),
        asyncio.create_task(lead.run(peers[lead.agent_id])),
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

    run_logger.flush_csv('verifier_dropout')
    for name, ep in environment.apis.items():
        print(f"{name}: accepts={ep.accept_count} rejects={ep.reject_count}")

if __name__ == '__main__':
    asyncio.run(run_with_dropout())
