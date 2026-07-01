"""
Demo: Conversation Management — the built-in default for context engineering.

Before you reach for advanced patterns (memory pointers, RAG, multi-agent),
Strands Agents ships a conversation manager that curates the context window
for you. This demo compares the four built-in options on the SAME conversation
and the SAME recall question, measuring native token usage each time.

Strategies (from the "Conversation Management" slide):
  1. None (baseline)     — keep the full history, nothing is dropped
  2. Sliding Window      — keep only the most recent messages
  3. Summarization       — summarize older messages, keep few (or no) recent ones
  4. Combination         — summary of older messages + recent ones kept verbatim

The probe: the user states a key fact early ("deploy budget is $500/month"),
then many filler turns bury it. At the end we ask "what is my budget?" and check
whether each strategy still remembers — and how many tokens the query costs.

This demo uses Strands Agents. The same conversation-management concepts
(sliding window, summarization, combination) are general agent patterns and
carry over to other agent frameworks.
"""

import os
from dotenv import load_dotenv
from strands import Agent
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from strands.agent.conversation_manager import (
    NullConversationManager,
    SlidingWindowConversationManager,
    SummarizingConversationManager,
)

# Suppress noisy OpenTelemetry warnings
os.environ["OTEL_SDK_DISABLED"] = "true"

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")

# The recall question asked at the end of every conversation.
RECALL_QUESTION = (
    "What is my monthly deploy budget? "
    "Reply with only the dollar amount, or say 'unknown' if it is not in our conversation."
)

# The key fact the user states in turn 1. Sliding Window will trim it away;
# Summarization and Combination should preserve it.
KEY_FACT = "500"


# ── The conversation ─────────────────────────────────────────────────────────
# Turn 1 states the budget. Turns 2-12 are filler that bury it far in the past.
# Seeded directly into agent.messages (no LLM calls) so the setup is deterministic
# and free — the only real model calls are the recall question and, for the
# summarizing strategies, the one-time summary generation.

CONVERSATION = [
    ("Our monthly deploy budget is $500. Keep that in mind for everything.",
     "Understood — I'll keep your $500/month deploy budget in mind."),
    ("We ship a Python service on AWS.", "Got it, a Python service on AWS."),
    ("The team has four engineers.", "Noted, four engineers."),
    ("We use GitHub Actions for CI.", "Understood, GitHub Actions for CI."),
    ("Production runs in us-east-1.", "Noted, production in us-east-1."),
    ("Staging runs in us-west-2.", "Got it, staging in us-west-2."),
    ("We deploy on Fridays.", "Understood, Friday deploys."),
    ("Alerts go to the #ops Slack channel.", "Noted, alerts to #ops."),
    ("We keep 30 days of logs.", "Got it, 30-day log retention."),
    ("Our database is Postgres.", "Understood, Postgres."),
    ("We cache with Redis.", "Noted, Redis for caching."),
    ("Load tests run every Monday.", "Got it, Monday load tests."),
]


def seed_history(agent: Agent) -> None:
    """Append the fixed conversation to an agent's history without calling the LLM."""
    for user_msg, assistant_msg in CONVERSATION:
        agent.messages.append({"role": "user", "content": [{"text": user_msg}]})
        agent.messages.append({"role": "assistant", "content": [{"text": assistant_msg}]})


# ── Native token measurement ──────────────────────────────────────────────────

def total_tokens(response) -> int:
    """Total tokens for a query, from Strands' native metrics (provider-agnostic).

    accumulated_usage["totalTokens"] = input (system prompt + tools + managed
    history + question) + output (answer). It can be None if a provider does not
    report usage, so we guard for that.
    """
    if response.metrics and response.metrics.accumulated_usage:
        return response.metrics.accumulated_usage["totalTokens"]
    return 0


# ── Run one strategy ───────────────────────────────────────────────────────────

def run_strategy(name: str, manager, summarize: bool) -> dict:
    """Seed the conversation, apply the manager, then ask the recall question.

    Args:
        name: Human-readable strategy name for the report.
        manager: A fresh conversation manager instance.
        summarize: True for the summarizing strategies. Summarization only runs on
            context overflow in production; here we call reduce_context() explicitly
            so the compaction is visible without needing a full 128K-token overflow.
    """
    print("\n" + "=" * 70)
    print(f"STRATEGY: {name}")
    print("=" * 70)

    # 1. Build the full history on a staging agent, then let the manager curate it.
    staging = Agent(model=MODEL, conversation_manager=manager)
    seed_history(staging)
    before = len(staging.messages)

    if summarize:
        # Summarizing managers compact reactively (on overflow). Trigger it here.
        staging.conversation_manager.reduce_context(staging)
    else:
        # Sliding Window / None curate after each turn via apply_management.
        staging.conversation_manager.apply_management(staging)

    managed = list(staging.messages)
    after = len(managed)
    print(f"History: {before} messages → {after} after management")

    # Show what survived: is the budget fact still anywhere in the kept context?
    kept_text = " ".join(
        block.get("text", "")
        for msg in managed
        for block in msg.get("content", [])
        if isinstance(block, dict)
    )
    fact_in_context = KEY_FACT in kept_text
    print(f"Budget fact still in context: {'yes' if fact_in_context else 'no'}")

    # 2. Ask the recall question on a fresh agent carrying only the managed history,
    #    so accumulated_usage reflects exactly this one query's context size.
    #    callback_handler=None keeps the streamed answer out of stdout for clean output.
    recall_agent = Agent(model=MODEL, callback_handler=None)
    recall_agent.messages = managed
    response = recall_agent(RECALL_QUESTION)

    answer = str(response).strip()
    tokens = total_tokens(response)
    remembered = KEY_FACT in answer
    print(f"Answer: {answer}")
    print(f"Remembered budget: {'✅ yes' if remembered else '❌ no'}")
    print(f"📊 Query tokens (native): {tokens:,}")

    return {"name": name, "tokens": tokens, "remembered": remembered, "kept": after}


def main():
    print("\n" + "=" * 70)
    print("  Conversation Management — four built-in strategies, one question")
    print('  From the "Conversation Management" slide: None / Sliding / Summarize / Combine')
    print("=" * 70)
    print(f"\n  The user states the budget in turn 1, then {len(CONVERSATION) - 1} turns bury it.")
    print(f"  Question at the end: {RECALL_QUESTION}")

    results = [
        run_strategy(
            "1. None (baseline) — keep the full history",
            NullConversationManager(),
            summarize=False,
        ),
        run_strategy(
            "2. Sliding Window — keep only the most recent messages (window_size=6)",
            SlidingWindowConversationManager(window_size=6),
            summarize=False,
        ),
        run_strategy(
            "3. Summarization — summarize old, keep none recent (ratio=0.8, preserve=0)",
            SummarizingConversationManager(summary_ratio=0.8, preserve_recent_messages=0),
            summarize=True,
        ),
        run_strategy(
            "4. Combination — summarize old + keep recent (ratio=0.5, preserve=4)",
            SummarizingConversationManager(summary_ratio=0.5, preserve_recent_messages=4),
            summarize=True,
        ),
    ]

    # ── Comparison table ────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  COMPARISON")
    print("=" * 70)
    print(f"\n  {'Strategy':<44} {'Kept':>5} {'Tokens':>9} {'Recall':>8}")
    print("  " + "-" * 68)
    for r in results:
        recall = "✅" if r["remembered"] else "❌"
        print(f"  {r['name'][:44]:<44} {r['kept']:>5} {r['tokens']:>9,} {recall:>7}")

    print("\n  Takeaways:")
    print("  • None    — remembers everything, but every query pays for the full history.")
    print("  • Sliding — cheapest context, but trims the early budget fact → wrong answer.")
    print("  • Summarize / Combine — compact AND keep the fact. Combination is the")
    print("    recommended default: a summary of old turns plus recent turns kept verbatim.")


if __name__ == "__main__":
    main()
