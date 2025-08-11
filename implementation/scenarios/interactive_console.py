# # # implementation/scenarios/interactive_console.py

# # import asyncio
# # import os
# # import time
# # import random

# # from implementation.coordination_framework.env import Environment
# # from implementation.coordination_framework.gossip import GossipNetwork
# # from implementation.coordination_framework.logger import RunLogger
# # from implementation.coordination_framework import db

# # # Optional: warn if LLM isn't available so you don't wonder about "fallback/no-llm"
# # try:
# #     from implementation.coordination_framework.llm_support import create_llm
# # except Exception:
# #     create_llm = None


# # async def main():
# #     print("=== Interactive Auto Credit Loan ===")

# #     # Helpful default: show step-by-step console traces from agents
# #     os.environ.setdefault("INTERACTIVE_VERBOSE", "1")

# #     # Friendly warning if LLM isn't wired (normalizer will echo raw values)
# #     if create_llm is not None:
# #         try:
# #             llm = create_llm()
# #             if llm is None:
# #                 print("[warning] No LLM configured. Export OPENAI_API_KEY (and optionally OPENAI_MODEL) "
# #                       "to enable prompt-based normalization. You'll see 'fallback/no-llm'.")
# #         except Exception as e:
# #             print(f"[warning] LLM init error: {e}. Normalization will fallback to echo.")

# #     # Build simulated environment and unique application
# #     environment = Environment()
# #     # add a small random suffix to ensure uniqueness if you start multiple sessions in the same second
# #     application_id = f"session_{int(time.time())}_{random.randint(1000, 9999)}"

# #     # Agents (each agent id is namespaced by application_id)
# #     agent_ids = [
# #         f"greet_{application_id}",
# #         f"app_{application_id}",
# #         f"verify_{application_id}",
# #         f"emi_{application_id}",
# #         f"elig_{application_id}",
# #         f"lead_{application_id}",
# #     ]

# #     # Import agents (done here so you can edit agents without restarting Python)
# #     from implementation.agents.greeting_agent import GreetingAgent
# #     from implementation.agents.interactive_application_agent import InteractiveApplicationAgent
# #     from implementation.agents.verification_agent import VerificationAgent
# #     from implementation.agents.emi_agent import EMICalculatorAgent
# #     from implementation.agents.eligibility_agent import EligibilityAgent
# #     from implementation.agents.lead_generation_agent import LeadGenerationAgent

# #     network = GossipNetwork(agent_ids)
# #     run_logger = RunLogger()

# #     greet = GreetingAgent(agent_ids[0], environment, network, run_logger, application_id=application_id)
# #     app = InteractiveApplicationAgent(agent_ids[1], environment, network, run_logger, application_id=application_id)
# #     verify = VerificationAgent(agent_ids[2], environment, network, run_logger, application_id=application_id)
# #     emi = EMICalculatorAgent(agent_ids[3], environment, network, run_logger, application_id=application_id)
# #     elig = EligibilityAgent(agent_ids[4], environment, network, run_logger, application_id=application_id)
# #     lead = LeadGenerationAgent(agent_ids[5], environment, network, run_logger, application_id=application_id)

# #     # Give yourself time to type comfortably; agents won't run that long because we stop early once a lead exists
# #     soft_deadline_seconds = int(os.getenv("INTERACTIVE_AGENT_DEADLINE_SECONDS", "600"))  # 10 minutes
# #     for a in (greet, app, verify, emi, elig, lead):
# #         a.deadline_timestamp = time.time() + soft_deadline_seconds

# #     # Wire peers and start tasks
# #     peers = {aid: [x for x in agent_ids if x != aid] for aid in agent_ids}
# #     agents = [greet, app, verify, emi, elig, lead]
# #     tasks = [asyncio.create_task(a.run(peers[a.agent_id])) for a in agents]

# #     # Wait policy:
# #     # - End immediately when a lead row appears (happy path),
# #     # - OR end after prolonged inactivity (user stopped typing),
# #     # - OR end at a hard max wait (safety cap).
# #     conn = db.initialize_database()

# #     # Helper: count of fields collected for THIS application (used for idle detection)
# #     def get_field_count() -> int:
# #         cur = conn.execute("SELECT COUNT(*) FROM applications WHERE app_id=?", (application_id,))
# #         row = cur.fetchone()
# #         return int(row[0] if row and row[0] is not None else 0)

# #     # Helper: check whether any lead exists for THIS application
# #     def lead_exists() -> bool:
# #         cur = conn.execute("SELECT COUNT(*) FROM leads WHERE app_id=?", (application_id,))
# #         row = cur.fetchone()
# #         return (int(row[0]) if row and row[0] is not None else 0) > 0

# #     # Tunables (env overrides available)
# #     max_wait = int(os.getenv("INTERACTIVE_MAX_WAIT_SECONDS", "900"))   # 15 min hard cap
# #     idle_wait = int(os.getenv("INTERACTIVE_IDLE_SECONDS", "240"))      # 4 min of no new fields

# #     start_ts = time.time()
# #     last_count = get_field_count()
# #     last_change_ts = start_ts

# #     # Main wait loop
# #     while True:
# #         # 1) If a lead exists, we can finish immediately (no long waits)
# #         if lead_exists():
# #             break

# #         # 2) Track user progress (new fields entered)
# #         current_count = get_field_count()
# #         if current_count != last_count:
# #             last_count = current_count
# #             last_change_ts = time.time()

# #         now = time.time()
# #         if now - start_ts > max_wait:
# #             print("[interactive] Max wait reached, ending session.")
# #             break
# #         if now - last_change_ts > idle_wait:
# #             print("[interactive] No input for a while, ending session.")
# #             break

# #         await asyncio.sleep(0.25)

# #     # Cancel all agents and surface any errors
# #     for t in tasks:
# #         t.cancel()
# #     results = await asyncio.gather(*tasks, return_exceptions=True)
# #     for idx, r in enumerate(results):
# #         if isinstance(r, Exception):
# #             import traceback
# #             print(f"[ERROR] Task {idx} raised: {repr(r)}")
# #             traceback.print_exception(r)

# #     # Persist logs and show API stats
# #     run_logger.flush_csv("interactive_console")
# #     for name, ep in environment.apis.items():
# #         print(f"{name}: accepts={ep.accept_count} rejects={ep.reject_count}")

# #     # Final application summary
# #     fields = db.get_fields(conn, application_id)
# #     proofs = db.get_proofs(conn, application_id)
# #     emi_val = db.get_emi(conn, application_id)
# #     status, conf = db.get_eligibility(conn, application_id)

# #     print("\n--- Final Application Summary ---")
# #     print("Application ID:", application_id)
# #     print("Fields:", fields)
# #     print("Proofs:", proofs)
# #     print("EMI:", emi_val)
# #     print("Eligibility:", status, conf)

# #     # Print leads for this application
# #     try:
# #         cur = conn.execute(
# #             "SELECT bank, status, meta, created_at FROM leads WHERE app_id=? ORDER BY created_at DESC",
# #             (application_id,),
# #         )
# #         leads = cur.fetchall()
# #     except Exception:
# #         leads = []

# #     if leads:
# #         print("Leads:")
# #         for row in leads:
# #             print("  ", row)
# #     else:
# #         print("Leads: none")

# #     print("=== Done ===")


# # if __name__ == "__main__":
# #     asyncio.run(main())


# # implementation/scenarios/interactive_console.py
# # Interactive runner: fresh app_id every run, idle-aware wait, early-stop on lead,
# # surfaces exceptions, prints a final summary, and exits cleanly.

# import asyncio
# import os
# import time
# import random
# import sys

# from implementation.coordination_framework.env import Environment
# from implementation.coordination_framework.gossip import GossipNetwork
# from implementation.coordination_framework.logger import RunLogger
# from implementation.coordination_framework import db

# try:
#     from implementation.coordination_framework.llm_support import create_llm
# except Exception:
#     create_llm = None


# async def main():
#     print("=== Interactive Auto Credit Loan ===")

#     # Show live traces from agents by default
#     os.environ.setdefault("INTERACTIVE_VERBOSE", "1")

#     # Friendly warning if LLM isn’t available (so you don’t wonder about fallback/no-llm)
#     if create_llm is not None:
#         try:
#             if create_llm() is None:
#                 print("[warning] No LLM configured. Export OPENAI_API_KEY (and optionally OPENAI_MODEL) "
#                       "to enable prompt-based normalization. You'll see 'fallback/no-llm'.")
#         except Exception as e:
#             print(f"[warning] LLM init error: {e}. Normalization will fallback to echo.")

#     # Simulated environment + unique application id (no need to rm state.sqlite)
#     environment = Environment()
#     application_id = f"session_{int(time.time())}_{random.randint(1000,9999)}"

#     # Import agents (local import so edits don’t require a new Python process)
#     from implementation.agents.greeting_agent import GreetingAgent
#     from implementation.agents.interactive_application_agent import InteractiveApplicationAgent
#     from implementation.agents.verification_agent import VerificationAgent
#     from implementation.agents.emi_agent import EMICalculatorAgent
#     from implementation.agents.eligibility_agent import EligibilityAgent
#     from implementation.agents.lead_generation_agent import LeadGenerationAgent

#     agent_ids = [
#         f"greet_{application_id}",
#         f"app_{application_id}",
#         f"verify_{application_id}",
#         f"emi_{application_id}",
#         f"elig_{application_id}",
#         f"lead_{application_id}",
#     ]

#     network = GossipNetwork(agent_ids)
#     run_logger = RunLogger()

#     greet = GreetingAgent(agent_ids[0], environment, network, run_logger, application_id=application_id)
#     app = InteractiveApplicationAgent(agent_ids[1], environment, network, run_logger, application_id=application_id)
#     verify = VerificationAgent(agent_ids[2], environment, network, run_logger, application_id=application_id)
#     emi = EMICalculatorAgent(agent_ids[3], environment, network, run_logger, application_id=application_id)
#     elig = EligibilityAgent(agent_ids[4], environment, network, run_logger, application_id=application_id)
#     lead = LeadGenerationAgent(agent_ids[5], environment, network, run_logger, application_id=application_id)

#     # Soft per-agent deadline (we will stop earlier when a lead exists)
#     soft_deadline_seconds = int(os.getenv("INTERACTIVE_AGENT_DEADLINE_SECONDS", "900"))  # 15 min
#     now = time.time()
#     for a in (greet, app, verify, emi, elig, lead):
#         a.deadline_timestamp = now + soft_deadline_seconds

#     peers = {aid: [x for x in agent_ids if x != aid] for aid in agent_ids}
#     agents = [greet, app, verify, emi, elig, lead]
#     tasks = [asyncio.create_task(a.run(peers[a.agent_id])) for a in agents]

#     # Helper DB functions
#     conn = db.initialize_database()

#     def get_field_count() -> int:
#         cur = conn.execute("SELECT COUNT(*) FROM applications WHERE app_id=?", (application_id,))
#         row = cur.fetchone()
#         return int(row[0] if row and row[0] is not None else 0)

#     def lead_exists() -> bool:
#         cur = conn.execute("SELECT COUNT(*) FROM leads WHERE app_id=?", (application_id,))
#         row = cur.fetchone()
#         return (int(row[0]) if row and row[0] is not None else 0) > 0

#     # Idle-aware wait loop: finish on lead, or on prolonged inactivity, or hard timeout
#     max_wait = int(os.getenv("INTERACTIVE_MAX_WAIT_SECONDS", "900"))   # 15 min cap
#     idle_wait = int(os.getenv("INTERACTIVE_IDLE_SECONDS", "240"))      # 4 min no new fields => end

#     start_ts = time.time()
#     last_count = get_field_count()
#     last_change_ts = start_ts

#     while True:
#         if lead_exists():
#             break
#         current_count = get_field_count()
#         if current_count != last_count:
#             last_count = current_count
#             last_change_ts = time.time()

#         now = time.time()
#         if now - start_ts > max_wait:
#             print("[interactive] Max wait reached, ending session.")
#             break
#         if now - last_change_ts > idle_wait:
#             print("[interactive] No input for a while, ending session.")
#             break

#         await asyncio.sleep(0.25)

#     # Signal agents to stop prompting BEFORE cancellation (InteractiveApplicationAgent will honor this flag)
#     try:
#         setattr(app, "halt_prompts", True)
#     except Exception:
#         pass

#     # Cancel tasks and surface exceptions
#     for t in tasks:
#         t.cancel()
#     results = await asyncio.gather(*tasks, return_exceptions=True)
#     for idx, r in enumerate(results):
#         if isinstance(r, Exception):
#             import traceback
#             print(f"[ERROR] Task {idx} raised: {repr(r)}")
#             traceback.print_exception(r)

#     # Persist logs and API stats
#     run_logger.flush_csv("interactive_console")
#     for name, ep in environment.apis.items():
#         print(f"{name}: accepts={ep.accept_count} rejects={ep.reject_count}")

#     # Final summary
#     fields = db.get_fields(conn, application_id)
#     proofs = db.get_proofs(conn, application_id)
#     emi_val = db.get_emi(conn, application_id)
#     status, conf = db.get_eligibility(conn, application_id)

#     print("\n--- Final Application Summary ---")
#     print("Application ID:", application_id)
#     print("Fields:", fields)
#     print("Proofs:", proofs)
#     print("EMI:", emi_val)
#     print("Eligibility:", status, conf)

#     try:
#         cur = conn.execute(
#             "SELECT bank, status, meta, created_at FROM leads WHERE app_id=? ORDER BY created_at DESC",
#             (application_id,),
#         )
#         leads = cur.fetchall()
#     except Exception:
#         leads = []

#     if leads:
#         print("Leads:")
#         for row in leads:
#             print("  ", row)
#     else:
#         print("Leads: none")

#     print("=== Done ===")

#     # Hard stop guard:
#     # If your InteractiveApplicationAgent still uses input() via run_in_executor,
#     # a thread may be stuck on stdin. As a last resort, hard-exit to avoid Ctrl+C.
#     if os.getenv("INTERACTIVE_HARD_EXIT", "0") == "1":
#         os._exit(0)  # noqa: E999  (intentional hard exit)


# if __name__ == "__main__":
#     asyncio.run(main())

# implementation/scenarios/interactive_console.py
# Interactive runner: fresh app_id each run, idle-aware waiting, early-stop on lead,
# surfaces exceptions, prints final summary, and hard-exits to avoid lingering input() threads.

import asyncio
import time
import random
import os

from implementation.coordination_framework.env import Environment
from implementation.coordination_framework.gossip import GossipNetwork
from implementation.coordination_framework.logger import RunLogger
from implementation.coordination_framework import db

# Tunables baked into the script (no env required)
AGENT_SOFT_DEADLINE_SECONDS = 900   # 15 minutes per agent (soft; we stop earlier on lead)
IDLE_WAIT_SECONDS = 240             # 4 minutes of no new fields => end
MAX_WAIT_SECONDS = 900              # 15 minute hard cap
HARD_EXIT_AFTER_SUMMARY = True      # ensure process exits even if input() thread is waiting

async def main():
    print("=== Interactive Auto Credit Loan ===")

    # Build environment and unique application id (no need to delete state.sqlite)
    environment = Environment()
    application_id = f"session_{int(time.time())}_{random.randint(1000,9999)}"

    # Import agents locally
    from implementation.agents.greeting_agent import GreetingAgent
    from implementation.agents.interactive_application_agent import InteractiveApplicationAgent
    from implementation.agents.verification_agent import VerificationAgent
    from implementation.agents.emi_agent import EMICalculatorAgent
    from implementation.agents.eligibility_agent import EligibilityAgent
    from implementation.agents.lead_generation_agent import LeadGenerationAgent

    agent_ids = [
        f"greet_{application_id}",
        f"app_{application_id}",
        f"verify_{application_id}",
        f"emi_{application_id}",
        f"elig_{application_id}",
        f"lead_{application_id}",
    ]

    network = GossipNetwork(agent_ids)
    run_logger = RunLogger()

    greet = GreetingAgent(agent_ids[0], environment, network, run_logger, application_id=application_id)
    app = InteractiveApplicationAgent(agent_ids[1], environment, network, run_logger, application_id=application_id)
    verify = VerificationAgent(agent_ids[2], environment, network, run_logger, application_id=application_id)
    emi = EMICalculatorAgent(agent_ids[3], environment, network, run_logger, application_id=application_id)
    elig = EligibilityAgent(agent_ids[4], environment, network, run_logger, application_id=application_id)
    lead = LeadGenerationAgent(agent_ids[5], environment, network, run_logger, application_id=application_id)

    # Soft per-agent deadline
    now = time.time()
    for a in (greet, app, verify, emi, elig, lead):
        a.deadline_timestamp = now + AGENT_SOFT_DEADLINE_SECONDS

    peers = {aid: [x for x in agent_ids if x != aid] for aid in agent_ids}
    agents = [greet, app, verify, emi, elig, lead]
    tasks = [asyncio.create_task(a.run(peers[a.agent_id])) for a in agents]

    # DB helpers
    conn = db.initialize_database()

    def get_field_count() -> int:
        cur = conn.execute("SELECT COUNT(*) FROM applications WHERE app_id=?", (application_id,))
        row = cur.fetchone()
        return int(row[0] if row and row[0] is not None else 0)

    def lead_exists() -> bool:
        cur = conn.execute("SELECT COUNT(*) FROM leads WHERE app_id=?", (application_id,))
        row = cur.fetchone()
        return (int(row[0]) if row and row[0] is not None else 0) > 0

    # Idle-aware wait loop
    start_ts = time.time()
    last_count = get_field_count()
    last_change_ts = start_ts

    while True:
        if lead_exists():
            break
        current_count = get_field_count()
        if current_count != last_count:
            last_count = current_count
            last_change_ts = time.time()

        now_loop = time.time()
        if now_loop - start_ts > MAX_WAIT_SECONDS:
            print("[interactive] Max wait reached, ending session.")
            break
        if now_loop - last_change_ts > IDLE_WAIT_SECONDS:
            print("[interactive] No input for a while, ending session.")
            break

        await asyncio.sleep(0.25)

    # Ask the interactive agent to stop prompting (if it honors this flag), then cancel tasks
    try:
        setattr(app, "halt_prompts", True)
    except Exception:
        pass

    for t in tasks:
        t.cancel()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for idx, r in enumerate(results):
        if isinstance(r, Exception):
            import traceback
            print(f"[ERROR] Task {idx} raised: {repr(r)}")
            traceback.print_exception(r)

    # Logs and API stats
    run_logger.flush_csv("interactive_console")
    for name, ep in environment.apis.items():
        print(f"{name}: accepts={ep.accept_count} rejects={ep.reject_count}")

    # Final summary
    fields = db.get_fields(conn, application_id)
    proofs = db.get_proofs(conn, application_id)
    emi_val = db.get_emi(conn, application_id)
    status, conf = db.get_eligibility(conn, application_id)

    print("\n--- Final Application Summary ---")
    print("Application ID:", application_id)
    print("Fields:", fields)
    print("Proofs:", proofs)
    print("EMI:", emi_val)
    print("Eligibility:", status, conf)

    try:
        cur = conn.execute(
            "SELECT bank, status, meta, created_at FROM leads WHERE app_id=? ORDER BY created_at DESC",
            (application_id,),
        )
        leads = cur.fetchall()
    except Exception:
        leads = []

    if leads:
        print("Leads:")
        for row in leads:
            print("  ", row)
    else:
        print("Leads: none")

    print("=== Done ===")

    # Ensure clean process exit even if an input() thread is blocked
    if HARD_EXIT_AFTER_SUMMARY:
        os._exit(0)

if __name__ == "__main__":
    asyncio.run(main())
