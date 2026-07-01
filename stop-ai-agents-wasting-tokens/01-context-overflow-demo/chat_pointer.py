"""
Interactive chat — WITH Memory Pointer Pattern (the fix).

The tool stores the full log dataset in agent.state and returns only a pointer
ID (e.g. "logs-api-gateway"). The raw data never enters the LLM context window.
Downstream tools read the data back by its ID, so you can keep asking follow-up
questions about the same 60KB+ dataset while the context stays tiny.

This chat shows memory RECALL by ID:
  1. Ask the agent to fetch logs → the chat prints a "🆕 Memory saved" banner with
     the exact ID the moment the dataset lands in agent.state. This banner is driven
     by the chat itself (it inspects agent.state), so the ID always appears — it does
     not depend on the model choosing to mention it.
  2. Ask "what memory IDs do you have?" → list_memory_pointers reads agent.state.
  3. Ask a follow-up → the agent recalls the full data by that ID, not by re-fetching.

Run:
    uv run python chat_pointer.py

Then try this conversation:
    > Fetch 2 hours of logs for api-gateway and analyze the errors
    > What memory pointer IDs do you have stored?
    > Using that same data, which service had the most errors?
    > Now detect latency anomalies in those same logs
    (type 'exit' to quit)

Compare against chat_naive.py, where the raw JSON floods the context instead.
"""

import os
import json

os.environ["OTEL_SDK_DISABLED"] = "true"
import logging, warnings  # silence OpenTelemetry 'Failed to detach context' noise
logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", message="Failed to detach context")

from dotenv import load_dotenv
from strands import Agent
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from tools import (
    fetch_application_logs,
    analyze_error_patterns,
    detect_latency_anomalies,
    recall_logs_by_id,
    list_memory_pointers,
)

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")

SYSTEM_PROMPT = (
    "You are a log analysis assistant that uses the Memory Pointer Pattern. "
    "When you fetch logs, the data is stored in agent.state and the fetch tool returns a "
    "line like 'Data stored at: logs-api-gateway'. That value after 'Data stored at:' is the "
    "memory pointer ID. You MUST quote that exact pointer ID back to the user, verbatim, in "
    "every response where you fetched or used it — for example: \"Stored as memory ID "
    "`logs-api-gateway`.\" Never refer vaguely to 'a tool' or 'the data'; always name the ID. "
    "For any follow-up question about the same data, reuse that pointer ID — never re-fetch. "
    "If the user asks to show, give, or get the logs for a memory ID, call recall_logs_by_id "
    "with that ID — it reads the stored data back and returns a preview proving the recall. "
    "If the user asks which datasets or memory IDs you have, call list_memory_pointers."
)


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
    print("  CHAT — WITH Memory Pointer (data recalled by ID, not in context)")
    print("=" * 70)
    print("  Fetch logs, ask for the memory ID, then recall by that ID.")
    print("  Type 'exit' or 'quit' to stop.\n")

    agent = Agent(
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        conversation_manager=SlidingWindowConversationManager(window_size=40),
        tools=[
            fetch_application_logs,
            analyze_error_patterns,
            detect_latency_anomalies,
            recall_logs_by_id,
            list_memory_pointers,
        ],
    )

    # Track which pointer IDs we've already announced so we only banner new ones.
    known_pointers: set[str] = set()

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
        stored = agent.state.get() or {}
        pointers = list(stored.keys())
        stored_bytes = sum(len(json.dumps(v)) for v in stored.values())

        # Guaranteed ID announcement — independent of what the model chose to say.
        # If a new dataset landed in agent.state this turn, surface its ID directly.
        new_pointers = [p for p in pointers if p not in known_pointers]
        for p in new_pointers:
            size = len(json.dumps(stored[p]))
            print(f"\n🆕 Memory saved — recall it by this ID: '{p}'  ({size:,} bytes)")
        known_pointers.update(pointers)

        print(f"\n📊 Tokens in context now: {tokens:,}")
        if pointers:
            print(f"📦 Memory IDs you can recall: {pointers}  "
                  f"({stored_bytes:,} bytes held outside the context window)")


if __name__ == "__main__":
    main()
