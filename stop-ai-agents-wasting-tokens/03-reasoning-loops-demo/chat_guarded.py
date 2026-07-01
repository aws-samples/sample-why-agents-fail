"""
Interactive chat — WITH loop protection (the fix).

Same ambiguous tools and same persistent prompt as chat_loop.py, but one hook is
attached:
  - LimitToolCounts — hard ceiling on how many times each tool may run per turn.
    This is the official recipe from the Strands Hooks Cookbook (see hooks.py).

When the agent tries to loop, you see "🚫 Limit reached!" lines as the hook
cancels the extra calls, and the tool-call count and token total stay bounded.

Run:
    uv run python chat_guarded.py

Then try the same conversation as chat_loop.py:
    > Find me the cheapest flight from NYC to Paris under $400 and a hotel under $200/night
    > Try harder, I need it cheaper
    (type 'exit' to quit)

Compare against chat_loop.py, which has no hook and loops freely.
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
from hooks import LimitToolCounts

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")

# Same prompt as chat_loop.py — the only difference between the two chats is the hook.
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
    print("  CHAT — WITH loop protection (LimitToolCounts, Strands Cookbook)")
    print("=" * 70)
    print("  Same ambiguous tools as chat_loop.py — but the hook caps retries.")
    print("  Type 'exit' or 'quit' to stop.\n")

    limits = LimitToolCounts(max_tool_counts={"search_flights": 3, "check_hotel_price": 3})

    agent = Agent(
        model=MODEL,
        system_prompt=PERSISTENT_PROMPT,
        tools=[search_flights, check_hotel_price],
        hooks=[limits],
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
        print(f"🛡️  Tool counts (this turn's invocation): {limits.tool_counts}  "
              f"(caps: {limits.max_tool_counts})")


if __name__ == "__main__":
    main()
