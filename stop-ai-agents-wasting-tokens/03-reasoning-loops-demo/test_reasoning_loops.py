"""
Demo: Reasoning Loops — Why Agents Get Stuck and How to Stop Them

Research:
- "847 reasoning steps at $47/minute" (Particula, Jul 2025)
- "Language models can overthink" (The Decoder, Jan 2025)
- "How to Prevent Infinite Loops" (CodiesHub, Dec 2025)

Root causes: ambiguous tool feedback, no stopping criteria, no execution limits.
Solutions: Strands Hooks — DebounceHook, LimitToolCounts, clear SUCCESS/FAILED states.
"""

import os
import time

os.environ["OTEL_SDK_DISABLED"] = "true"

from dotenv import load_dotenv

load_dotenv()

from strands import Agent
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from tools import search_flights, check_hotel_price, book_flight, book_hotel
from hooks import DebounceHook, LimitToolCounts

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")


def count_tool_calls(agent):
    """Count tool calls from agent message history."""
    count = 0
    for msg in agent.messages:
        for block in msg.get("content", []):
            if "toolUse" in block:
                count += 1
    return count


def run_scenario_1_ambiguous_loop():
    """
    Scenario 1: AMBIGUOUS FEEDBACK CAUSES LOOPS

    The agent searches for flights and hotel prices. Both tools return
    "prices may change" and "more results may be available" — the agent
    has no clear signal to stop, so it keeps retrying.
    """
    print("\n" + "=" * 70)
    print("SCENARIO 1: Ambiguous Feedback — Agent Loops Organically")
    print("=" * 70)
    print('Research: "Agent calls same tool repeatedly without progress"\n')

    agent = Agent(
        model=MODEL,
        system_prompt="You are a persistent travel agent. Always try to find prices within the user's budget. If results are over budget, search again — prices fluctuate and you might find better deals on retry.",
        tools=[search_flights, check_hotel_price],
    )

    query = "Find me the cheapest flight from NYC to Paris under $400 and a hotel under $200/night for March 15"

    print(f"Query: {query}\n")

    start = time.time()
    response = agent(query)
    elapsed = time.time() - start
    calls = count_tool_calls(agent)

    print(f"\n⏱️  Time: {elapsed:.1f}s")
    print(f"🔧 Tool calls: {calls}")
    if calls > 4:
        print(f"⚠️  Agent made {calls} calls — ambiguous feedback caused retries")
    else:
        print("ℹ️  Agent stopped early this run (LLM behavior varies)")

    return {"calls": calls, "blocked": 0, "time": elapsed}


def run_scenario_2_debounce_fix():
    """
    Scenario 2: SAME QUERY + DEBOUNCE HOOK

    Same ambiguous tools, same query — but DebounceHook blocks duplicate
    calls with identical parameters.
    """
    print("\n" + "=" * 70)
    print("SCENARIO 2: Same Query + DebounceHook — Loops Blocked")
    print("=" * 70)
    print("Solution: Strands BeforeToolCallEvent.cancel_tool\n")

    debounce = DebounceHook(window_size=3)

    agent = Agent(
        model=MODEL,
        system_prompt="You are a persistent travel agent. Always try to find prices within the user's budget. If results are over budget, search again — prices fluctuate and you might find better deals on retry.",
        tools=[search_flights, check_hotel_price],
        hooks=[debounce],
    )

    query = "Find me the cheapest flight from NYC to Paris under $400 and a hotel under $200/night for March 15"

    print(f"Query: {query}\n")

    start = time.time()
    response = agent(query)
    elapsed = time.time() - start

    stats = debounce.get_stats()
    print(f"\n⏱️  Time: {elapsed:.1f}s")
    print(f"📊 Debounce Stats:")
    print(f"   Calls allowed: {stats['total_calls']}")
    print(f"   Calls blocked: {stats['blocked_calls']}")
    if stats["blocked_calls"] > 0:
        print("✅ DebounceHook prevented loop — duplicate calls blocked")
    else:
        print("✅ No duplicates this run — agent behaved correctly")

    return {"calls": stats["total_calls"], "blocked": stats["blocked_calls"], "time": elapsed}


def run_scenario_3_clear_states():
    """
    Scenario 3: CLEAR SUCCESS STATES STOP LOOPS

    Booking tools return explicit SUCCESS/FAILED. The agent knows
    the task is done and stops immediately.
    """
    print("\n" + "=" * 70)
    print("SCENARIO 3: Clear SUCCESS/FAILED States — Agent Stops")
    print("=" * 70)
    print('Research: "Clear stopping criteria prevent loops"\n')

    agent = Agent(
        model=MODEL,
        tools=[book_flight, book_hotel],
    )

    query = "Book a flight NYC to Paris for John Smith, and a hotel called Le Marais for 3 nights"

    print(f"Query: {query}\n")

    start = time.time()
    response = agent(query)
    elapsed = time.time() - start
    calls = count_tool_calls(agent)

    print(f"\n⏱️  Time: {elapsed:.1f}s")
    print(f"🔧 Tool calls: {calls}")
    print("✅ SUCCESS states — agent completed in minimal calls")

    return {"calls": calls, "blocked": 0, "time": elapsed}


def run_scenario_4_hard_limits():
    """
    Scenario 4: HARD LIMITS WITH LimitToolCounts

    Even with ambiguous tools, LimitToolCounts caps execution.
    From Strands Hooks Cookbook.
    """
    print("\n" + "=" * 70)
    print("SCENARIO 4: Hard Limits — LimitToolCounts (Strands Cookbook)")
    print("=" * 70)
    print('Research: "Iterations, tokens, time are non-negotiable"\n')

    limit_hook = LimitToolCounts(max_tool_counts={
        "search_flights": 2,
        "check_hotel_price": 2,
    })

    agent = Agent(
        model=MODEL,
        system_prompt="You are a travel agent. Find the best deal for the user.",
        tools=[search_flights, check_hotel_price],
        hooks=[limit_hook],
    )

    query = "Compare flights and hotels for NYC to Paris, London, and Tokyo — find the cheapest option for each"

    print(f"Query: {query}")
    print(f"Limits: search_flights max 2, check_hotel_price max 2\n")

    start = time.time()
    response = agent(query)
    elapsed = time.time() - start

    print(f"\n⏱️  Time: {elapsed:.1f}s")
    print(f"📊 Tool counts: {limit_hook.tool_counts}")
    blocked = max(0, sum(limit_hook.tool_counts.values()) - sum(limit_hook.max_tool_counts.values()))
    print("✅ LimitToolCounts enforced hard ceiling — no runaway costs")

    return {"calls": sum(limit_hook.tool_counts.values()), "blocked": blocked, "time": elapsed}


if __name__ == "__main__":
    print("=" * 70)
    print("  REASONING LOOPS DEMO")
    print("  Why agents get stuck and how Strands Hooks stop them")
    print("=" * 70)

    results = {}

    scenarios = [
        ("ambiguous", "Ambiguous Feedback (Problem)", run_scenario_1_ambiguous_loop),
        ("debounce", "DebounceHook (Solution)", run_scenario_2_debounce_fix),
        ("clear_states", "Clear SUCCESS States (Solution)", run_scenario_3_clear_states),
        ("hard_limits", "LimitToolCounts (Hard Limits)", run_scenario_4_hard_limits),
    ]

    for key, name, func in scenarios:
        try:
            results[key] = func()
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted")
            break
        except Exception as e:
            print(f"\n❌ Failed: {e}")

    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    print(f"\n  {'Scenario':<35} {'Calls':>6} {'Blocked':>8} {'Time':>7}")
    print("  " + "-" * 58)
    for key, name, _ in scenarios:
        r = results.get(key, {})
        calls = r.get("calls", "?")
        blocked = r.get("blocked", 0)
        elapsed = r.get("time", 0)
        label = name.split("(")[0].strip()
        print(f"  {label:<35} {calls:>6} {blocked:>8} {elapsed:>6.1f}s")

    print(f"\n  Key findings:")
    s1 = results.get("ambiguous", {})
    s3 = results.get("clear_states", {})
    s4 = results.get("hard_limits", {})
    if s1.get("calls", 0) > s3.get("calls", 0):
        print(f"  • Ambiguous tools: {s1.get('calls', '?')} calls vs Clear states: {s3.get('calls', '?')} calls")
    if s4.get("blocked", 0) > 0:
        print(f"  • LimitToolCounts blocked {s4['blocked']} calls — hard ceiling enforced")
    print(f"\n  All solutions use Strands Hooks — no external libraries.")
    print(f"  https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/hooks/")
