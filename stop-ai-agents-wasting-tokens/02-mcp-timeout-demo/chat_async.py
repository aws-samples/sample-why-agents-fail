"""
Interactive chat — ASYNC handleId MCP pattern (the fix).

Instead of blocking, start_long_job returns a job handle ID (e.g.
"JOB_STARTED: 0295ac17") in under 2 seconds. You then recall the result by that
ID with check_job_status — the same recall-by-ID idea as the memory pointer,
applied to a long-running operation. No freeze, no 424 timeout.

The MCP connection is opened once and kept alive for the whole conversation, so
the background job keeps running between your turns and is ready when you poll.

Run:
    uv run python chat_async.py

Then try this conversation:
    > Use start_long_job to process 'large dataset'   (returns a handle ID fast)
    > Check the status of that job                     (still PROCESSING)
    ...wait ~10s, keep chatting...
    > Check the status of that job again               (COMPLETED with result)
    (type 'exit' to quit)

Compare against chat_sync.py, where slow_api freezes the whole chat.
"""

import os
import sys
import time

os.environ["OTEL_SDK_DISABLED"] = "true"
import logging, warnings  # silence OpenTelemetry 'Failed to detach context' noise
logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", message="Failed to detach context")

from dotenv import load_dotenv
from strands import Agent
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")

SYSTEM_PROMPT = (
    "You are an assistant that runs long jobs asynchronously. "
    "Use start_long_job to begin work — it returns a job handle ID immediately. "
    "Always tell the user the exact job handle ID you received. "
    "When the user asks about a job, call check_job_status with that handle ID. "
    "Never block waiting for a job to finish; report the current status and let the user poll again."
)


def get_total_tokens(response) -> int:
    """Total token usage for a turn — Strands native metric (works on any provider)."""
    if response.metrics:
        return response.metrics.accumulated_usage["totalTokens"]
    return 0


def main():
    print("=" * 70)
    print("  CHAT — ASYNC handleId MCP pattern (recall a job by its ID)")
    print("=" * 70)
    print("  Start a job (instant handle ID), then poll its status by that ID.")
    print("  Type 'exit' or 'quit' to stop.\n")

    mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command=sys.executable, args=["mcp_server.py"])
        )
    )

    # Keep the MCP session open for the whole conversation so the background job
    # keeps running between turns and is ready when you poll for it by ID. Load
    # the tools once inside the session — passing the client itself would try to
    # start it twice.
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        agent = Agent(model=MODEL, system_prompt=SYSTEM_PROMPT, tools=tools)

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
            start = time.time()
            response = agent(user)
            elapsed = time.time() - start

            tokens = get_total_tokens(response)
            print(f"\n\n⏱️  {elapsed:.1f}s   💰 {tokens:,} tokens")


if __name__ == "__main__":
    main()
