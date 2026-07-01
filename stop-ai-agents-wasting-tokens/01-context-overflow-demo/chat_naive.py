"""
Interactive chat — WITHOUT Memory Pointer Pattern (the problem).

The naive tool returns the full raw JSON of every log event. That data enters
the LLM context window directly, and every follow-up question re-sends the whole
dataset as input tokens. Watch the "tokens in context" number climb turn after
turn as you keep asking about the same logs.

Run:
    uv run python chat_naive.py

Then try this conversation:
    > Fetch 2 hours of logs for api-gateway and count the errors
    > Which service had the most errors?
    > What about latency — any slow requests?
    (type 'exit' to quit)

Compare against chat_pointer.py, which keeps the data out of context.
"""

import os
import json
import secrets
from datetime import datetime, timedelta

os.environ["OTEL_SDK_DISABLED"] = "true"
import logging, warnings  # silence OpenTelemetry 'Failed to detach context' noise
logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", message="Failed to detach context")

from dotenv import load_dotenv
from strands import Agent, tool
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")


@tool
def naive_fetch_logs(app_name: str, hours: int = 2) -> str:
    """Fetch application logs. Returns full raw JSON — no memory pointer pattern.

    Args:
        app_name: Application name to fetch logs for
        hours: Number of hours of logs to fetch (default 2)
    """
    logs = []
    base = datetime.now() - timedelta(hours=hours)
    for i in range(hours * 100):
        logs.append({
            "timestamp": (base + timedelta(seconds=i)).isoformat(),
            "level": ["INFO", "WARN", "ERROR", "DEBUG"][secrets.randbelow(4)],
            "service": ["api-gateway", "auth-service", "db-connector", "cache-layer"][secrets.randbelow(4)],
            "message": f"Event {i}",
            "duration_ms": secrets.randbelow(4991) + 10,
            "status_code": [200, 201, 400, 404, 500, 503][secrets.randbelow(6)],
        })
    return json.dumps(logs)  # ← Full raw JSON enters LLM context directly


def count_context_tokens(agent) -> int:
    """Estimate tokens currently sitting in the conversation history (context window)."""
    total = 0
    for msg in agent.messages:
        content = msg.get("content", [])
        if isinstance(content, str):
            total += len(content) // 4
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if "text" in block:
                        total += len(block["text"]) // 4
                    elif "toolResult" in block:
                        for item in block["toolResult"].get("content", []):
                            if "text" in item:
                                total += len(item["text"]) // 4
                    elif "toolUse" in block:
                        total += len(json.dumps(block["toolUse"].get("input", {}))) // 4
    return total


def main():
    print("=" * 70)
    print("  CHAT — WITHOUT Memory Pointer (raw JSON enters context)")
    print("=" * 70)
    print("  Ask about api-gateway logs, then follow up. Watch tokens grow.")
    print("  Type 'exit' or 'quit' to stop.\n")

    agent = Agent(model=MODEL, tools=[naive_fetch_logs])

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

        print("\n🤖 agent > ", end="", flush=True)
        agent(user)  # Strands streams the response to stdout

        tokens = count_context_tokens(agent)
        print(f"\n\n📊 Tokens in context now: {tokens:,}  (raw logs re-sent every turn)")


if __name__ == "__main__":
    main()
