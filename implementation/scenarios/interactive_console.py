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
