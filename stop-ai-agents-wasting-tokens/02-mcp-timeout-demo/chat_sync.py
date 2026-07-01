"""
Interactive chat — SYNCHRONOUS MCP tools (the problem).

Every tool call blocks until the external API responds. Ask it to use slow_api
and the whole chat freezes for ~15 seconds; ask for failing_api and you get a
424 error that kills the turn. There is no way to get an early acknowledgement —
the agent just waits.

The MCP connection is opened once (the `with mcp_client:` block) and kept alive
for the entire conversation, so every turn reuses the same server session.

Run:
    uv run python chat_sync.py

Then try this conversation:
    > Use fast_api to process 'user data'
    > Use slow_api to query the database for 'customer records'   (freezes ~15s)
    > Use failing_api to connect to the external service          (424 error)
    (type 'exit' to quit)

Compare against chat_async.py, which returns a job handle ID immediately.
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


def get_total_tokens(response) -> int:
    """Total token usage for a turn — Strands native metric (works on any provider)."""
    if response.metrics:
        return response.metrics.accumulated_usage["totalTokens"]
    return 0


def main():
    print("=" * 70)
    print("  CHAT — SYNCHRONOUS MCP tools (agent blocks until API responds)")
    print("=" * 70)
    print("  Try fast_api, slow_api (~15s freeze), failing_api (424).")
    print("  Type 'exit' or 'quit' to stop.\n")

    mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command=sys.executable, args=["mcp_server.py"])
        )
    )

    # Keep the MCP session open for the whole conversation. Load the tools once
    # inside the session — passing the client itself would try to start it twice.
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        agent = Agent(model=MODEL, tools=tools)

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
            try:
                response = agent(user)  # blocks until the tool returns
            except Exception as e:
                elapsed = time.time() - start
                print(f"\n\n❌ Error after {elapsed:.1f}s: {type(e).__name__}: {str(e)[:150]}")
                continue
            elapsed = time.time() - start

            tokens = get_total_tokens(response)
            print(f"\n\n⏱️  {elapsed:.1f}s   💰 {tokens:,} tokens")


if __name__ == "__main__":
    main()
