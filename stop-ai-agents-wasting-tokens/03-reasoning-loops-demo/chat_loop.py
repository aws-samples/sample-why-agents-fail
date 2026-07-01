"""
Interactive chat — NO loop protection (the problem).

The tools return ambiguous feedback ("prices may change — try again"), and the
system prompt tells the agent to keep retrying for a better deal. With nothing to
stop it, the agent calls the same tools over and over on a single request,
burning tokens. Watch the tool-call count and token total per turn.

Run:
    uv run python chat_loop.py

Then try this conversation:
    > Find me the cheapest flight from NYC to Paris under $400 and a hotel under $200/night
    > Try harder, I need it cheaper
    (type 'exit' to quit)

Compare against chat_guarded.py, where hooks block the duplicate calls.
"""

import os
import time

os.environ["OTEL_SDK_DISABLED"] = "true"
import logging, warnings  # silence OpenTelemetry 'Failed to detach context' noise
logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", message="Failed to detach context")

from dotenv import load_dotenv
from strands import Agent
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from tools import search_flights, check_hotel_price

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")

# Same prompt used in test_reasoning_loops.py Scenario 1 — pushes the agent to retry.
PERSISTENT_PROMPT = (
    "You are a persistent travel agent. Always try to find prices within the user's budget. "
    "If results are over budget, search again — prices fluctuate and you might find better deals on retry."
)


def count_tool_calls(agent) -> int:
    count = 0
    for msg in agent.messages:
        for block in msg.get("content", []):
            if isinstance(block, dict) and "toolUse" in block:
                count += 1
    return count


def get_total_tokens(response) -> int:
    """Total token usage for a turn — Strands native metric (works on any provider)."""
    if response.metrics:
        return response.metrics.accumulated_usage["totalTokens"]
    return 0


def main():
    print("=" * 70)
    print("  CHAT — NO loop protection (ambiguous tools → retries)")
    print("=" * 70)
    print("  Ask for a cheap flight + hotel and watch the tool calls pile up.")
    print("  Type 'exit' or 'quit' to stop.\n")

    agent = Agent(
        model=MODEL,
        system_prompt=PERSISTENT_PROMPT,
        tools=[search_flights, check_hotel_price],
    )

    while True:
        try:
            user = input("\n👤 you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 bye")
            break
        if user.lower() in {"exit", "quit", "q"}:
            print("👋 bye")
            break
        if not user:
            continue

        before = count_tool_calls(agent)
        print("\n🤖 agent > ", end="", flush=True)
        start = time.time()
        response = agent(user)
        elapsed = time.time() - start

        calls = count_tool_calls(agent) - before
        tokens = get_total_tokens(response)
        print(f"\n\n⏱️  {elapsed:.1f}s   🔧 {calls} tool calls this turn   💰 {tokens:,} tokens")
        if calls > 4:
            print("⚠️  Ambiguous feedback caused repeated retries — no stopping signal")


if __name__ == "__main__":
    main()
