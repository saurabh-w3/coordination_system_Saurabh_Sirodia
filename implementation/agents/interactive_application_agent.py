import asyncio, time
from .application_agent import ApplicationAgent
from implementation.coordination_framework.intent_types import Intent

class InteractiveApplicationAgent(ApplicationAgent):
    async def _ask_input(self, prompt: str) -> str:
        # Run blocking input in a thread to avoid freezing the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: input(prompt))

    async def execute(self, intent: Intent):
        if intent.action.startswith('ask_'):
            field = intent.action.split('ask_')[1]
            prompt = f"\n[Application] Please provide {field}: "
            # user_value = await self._ask_input(f"Please provide {field}: ")
            user_value = await self._ask_input(prompt)

            if field in {"age","loan_amount","tenure_months"}:
                try:
                    user_value = int(user_value)
                except Exception:
                    pass
            self.set_field_if_allowed(field, user_value)
            self.run_logger.log(time.time(), self.agent_id, f'field_{field}', 1, 'interactive')
            await asyncio.sleep(0.01)

