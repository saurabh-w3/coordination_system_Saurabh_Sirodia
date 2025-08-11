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

# import asyncio, time, os
# from .application_agent import ApplicationAgent
# from implementation.coordination_framework.intent_types import Intent
# from implementation.coordination_framework.normalize_with_llm import normalize_with_llm

# class InteractiveApplicationAgent(ApplicationAgent):
#     async def _ask_input(self, prompt: str) -> str:
#         loop = asyncio.get_event_loop()
#         return await loop.run_in_executor(None, lambda: input(prompt))

#     async def execute(self, intent: Intent):
#         if not intent.action.startswith('ask_'):
#             return
#         field = intent.action.split('ask_')[1]

#         # 1) ask user for raw input
#         user_raw = await self._ask_input(f"\n[Application] Please provide {field}: ")

#         # 2) build small context for normalizer
#         context = {
#             "country": "IN",
#             "currency": "INR",
#             "known_fields": self.get_fields(),
#             "field_name": field
#         }

#         # 3) call LLM normalizer
#         result = normalize_with_llm(field, user_raw, context)
#         normalized = result.get("normalized_value", user_raw)
#         needs_clar = bool(result.get("needs_clarification", False))
#         question = result.get("clarification_question") or ""
#         confidence = float(result.get("confidence", 0.0))
#         notes = result.get("notes", "")

#         # 4) if LLM wants a clarification, ask once and re-normalize
#         if needs_clar:
#             followup_raw = await self._ask_input(f"[Application] {question} ")
#             result2 = normalize_with_llm(field, followup_raw, context)
#             normalized = result2.get("normalized_value", followup_raw)
#             confidence = float(result2.get("confidence", confidence))
#             notes = f"{notes} | clarif: {result2.get('notes','')}"

#         # 5) write normalized value
#         self.set_field_if_allowed(field, normalized)

#         # 6) console trace
#         if os.getenv("INTERACTIVE_VERBOSE") == "1":
#             print(f"[Application] {field} raw='{user_raw}' -> normalized='{normalized}' (conf={confidence:.2f}) {notes}")

#         # log
#         self.run_logger.log(time.time(), self.agent_id, f'field_{field}', 1, 'interactive')
#         await asyncio.sleep(0.01)
