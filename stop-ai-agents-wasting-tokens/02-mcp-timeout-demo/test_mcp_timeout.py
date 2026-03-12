"""
Demo: MCP Tools Timeout — Synchronous vs Async HandleId Pattern

Based on research:
- "Resilient AI Agents With MCP" (Octopus, May 2025)
- OpenAI Community reports on 424 errors and unresponsive states

Runs 4 scenarios against the same MCP server, captures response times,
and compares synchronous (problem) vs async handleId (solution).
"""

import os
import sys
import time
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


def create_mcp_agent():
    """Create agent with MCP tools from mcp_server.py."""
    mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command=sys.executable, args=["mcp_server.py"])
        )
    )
    return Agent(model=MODEL, tools=[mcp_client])


# ── Tests ────────────────────────────────────────────────────────────────────

def run_test_1_fast():
    """Test 1: Fast API — baseline, good UX."""
    print("\n" + "=" * 70)
    print("TEST 1: FAST API (baseline)")
    print("=" * 70)

    agent = create_mcp_agent()
    start = time.time()
    response = agent("Use fast_api to process 'user data'")
    elapsed = time.time() - start

    print(f"⏱️  {elapsed:.1f}s")
    return {"time": elapsed, "status": "ok"}


def run_test_2_slow():
    """Test 2: Slow API — agent blocks for 15+ seconds."""
    print("\n" + "=" * 70)
    print("TEST 2: SLOW API (agent blocks ~15s)")
    print("=" * 70)
    print("⏳ Waiting ~15s for slow API...\n")

    agent = create_mcp_agent()
    start = time.time()
    response = agent("Use slow_api to query database for 'customer records'")
    elapsed = time.time() - start

    print(f"⏱️  {elapsed:.1f}s — agent waited full duration")
    return {"time": elapsed, "status": "slow"}


def run_test_3_failing():
    """Test 3: Failing API — 424 error after delay."""
    print("\n" + "=" * 70)
    print("TEST 3: FAILING API (424 error)")
    print("=" * 70)

    agent = create_mcp_agent()
    start = time.time()
    try:
        response = agent("Use failing_api to connect to external service")
        elapsed = time.time() - start
        print(f"⏱️  {elapsed:.1f}s")
        return {"time": elapsed, "status": "error"}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Error after {elapsed:.1f}s: {type(e).__name__}: {str(e)[:150]}")
        return {"time": elapsed, "status": "error"}


def run_test_4_async():
    """Test 4: Async handleId pattern — immediate response, then poll."""
    print("\n" + "=" * 70)
    print("TEST 4: ASYNC PATTERN (handleId solution)")
    print("=" * 70)

    agent = create_mcp_agent()

    # Step 1: start job — returns handle immediately
    start = time.time()
    response1 = agent("Use start_long_job to process 'large dataset'")
    step1 = time.time() - start
    print(f"Step 1 — handle returned in {step1:.1f}s")

    # Step 2: check status
    start = time.time()
    response2 = agent("Use check_job_status to check the job that was just started")
    step2 = time.time() - start
    total = step1 + step2
    print(f"Step 2 — status in {step2:.1f}s  |  Total: {total:.1f}s")

    return {"time": total, "step1": step1, "status": "ok"}


# ── Comparison ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("  MCP TIMEOUT DEMO")
    print("  Synchronous vs Async HandleId — same agent, measured response times")
    print("=" * 70)

    r1 = run_test_1_fast()
    r2 = run_test_2_slow()
    r3 = run_test_3_failing()
    r4 = run_test_4_async()

    print("\n" + "=" * 70)
    print("  COMPARISON")
    print("=" * 70)

    print(f"\n  {'Scenario':<35} {'Time':>8}  UX")
    print("  " + "-" * 55)
    print(f"  {'1. Fast API (baseline)':<35} {r1['time']:>6.1f}s  ✅ Good")
    print(f"  {'2. Slow API (problem)':<35} {r2['time']:>6.1f}s  ❌ Agent blocked")
    print(f"  {'3. Failing API (424)':<35} {r3['time']:>6.1f}s  ❌ Error")
    print(f"  {'4. Async handleId (solution)':<35} {r4['time']:>6.1f}s  ✅ Immediate")

    if r2["time"] > r4["time"]:
        improvement = r2["time"] - r4["time"]
        pct = 100 * improvement / r2["time"]
        print(f"\n  → Async saved {improvement:.1f}s vs slow API ({pct:.0f}% faster)")
        print(f"  → First response in {r4.get('step1', 0):.1f}s — no timeout risk")

    print(f"\n  Strands MCP Tools: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/mcp-tools/")
    print(f"  Research: https://octopus.com/blog/mcp-timeout-retry")
