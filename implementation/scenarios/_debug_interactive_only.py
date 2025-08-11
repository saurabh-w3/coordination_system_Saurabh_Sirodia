import asyncio
from implementation.coordination_framework.env import Environment
from implementation.coordination_framework.gossip import GossipNetwork
from implementation.coordination_framework.logger import RunLogger
from implementation.agents.interactive_application_agent import InteractiveApplicationAgent

async def main():
    print("=== DEBUG: Interactive Application Only ===")
    env = Environment()
    net = GossipNetwork(['app'])
    log = RunLogger()
    app = InteractiveApplicationAgent('app', env, net, log)
    await app.run([])

if __name__ == "__main__":
    asyncio.run(main())
