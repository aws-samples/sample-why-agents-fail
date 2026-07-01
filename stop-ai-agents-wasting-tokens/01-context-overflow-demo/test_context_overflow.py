"""
Demo: Context Window Overflow — Naive Agent vs Memory Pointer Pattern

Based on IBM Research paper "Solving Context Window Overflow in AI Agents"
https://arxiv.org/html/2511.22729v1

Runs two agents with the SAME query:
  Test 1: Naive agent — raw JSON enters LLM context (high tokens)
  Test 2: Pointer agent — data stays in agent.state (low tokens)

Then prints a comparison table with measured token counts.
"""

import os
import json
import time
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
from strands.agent.conversation_manager import SlidingWindowConversationManager
from tools import fetch_application_logs, analyze_error_patterns

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")

# Same query for both tests — the only variable is whether the tool uses memory pointers
QUERY = (
    "Fetch 2 hours of logs for 'api-gateway' and analyze error patterns. "
    "How many errors occurred and which services had the most?"
)


# ── Naive tool (WITHOUT memory pointer) ──────────────────────────────────────

@tool
def naive_fetch_logs(app_name: str, hours: int = 2) -> str:
    """Fetch application logs. Returns full raw JSON — no memory pointer pattern."""
    log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    services = ["api-gateway", "auth-service", "db-connector", "cache-layer"]
    logs = []
    base = datetime.now() - timedelta(hours=hours)
    for i in range(hours * 100):
        logs.append({
            "timestamp": (base + timedelta(seconds=i)).isoformat(),
            "level": log_levels[secrets.randbelow(len(log_levels))],
            "service": services[secrets.randbelow(len(services))],
            "message": f"Event {i}",
            "duration_ms": secrets.randbelow(4991) + 10,
            "status_code": [200, 201, 400, 404, 500, 503][secrets.randbelow(6)],
        })
    return json.dumps(logs)  # Full raw JSON enters LLM context directly


# ── Token measurement ────────────────────────────────────────────────────────

def count_context_tokens(agent) -> int:
    """Count tokens from all messages in conversation history."""
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


# ── Tests ────────────────────────────────────────────────────────────────────

def run_test_1_naive():
    """Test 1: Agent WITHOUT memory pointer — raw JSON in context."""
    print("\n" + "=" * 70)
    print("TEST 1: WITHOUT MEMORY POINTER (naive agent)")
    print("=" * 70)
    print(f"Query: {QUERY}\n")

    agent = Agent(model=MODEL, tools=[naive_fetch_logs])

    start = time.time()
    response = agent(QUERY)
    elapsed = time.time() - start
    tokens = count_context_tokens(agent)

    print(f"\n⏱️  {elapsed:.1f}s")
    print(f"📊 Tokens in context: {tokens:,}")
    return {"tokens": tokens, "time": elapsed}


def run_test_2_pointer():
    """Test 2: Agent WITH memory pointer — data stays in agent.state."""
    print("\n" + "=" * 70)
    print("TEST 2: WITH MEMORY POINTER PATTERN")
    print("=" * 70)
    print(f"Query: {QUERY}\n")

    agent = Agent(
        model=MODEL,
        conversation_manager=SlidingWindowConversationManager(window_size=40),
        tools=[fetch_application_logs, analyze_error_patterns],
    )

    start = time.time()
    response = agent(QUERY)
    elapsed = time.time() - start
    tokens = count_context_tokens(agent)

    pointer = "logs-api-gateway"
    stored = agent.state.get(pointer)
    data_size = len(json.dumps(stored)) if stored else 0

    print(f"\n⏱️  {elapsed:.1f}s")
    print(f"📊 Tokens in context: {tokens:,}")
    if stored:
        print(f"📦 agent.state['{pointer}']: {data_size:,} bytes — never entered LLM context")
    return {"tokens": tokens, "time": elapsed, "data_size": data_size}


# ── Comparison ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("  CONTEXT OVERFLOW DEMO")
    print("  Naive agent vs Memory Pointer Pattern — same query, measured tokens")
    print("=" * 70)

    r1 = run_test_1_naive()
    r2 = run_test_2_pointer()

    print("\n" + "=" * 70)
    print("  COMPARISON")
    print("=" * 70)

    print(f"\n  {'Approach':<40} {'Tokens':>10} {'Time':>8} {'Data outside context':>22}")
    print("  " + "-" * 82)
    print(f"  {'Test 1 — Naive (no pointer)':<40} {r1['tokens']:>10,} {r1['time']:>6.1f}s {'—':>22}")
    print(f"  {'Test 2 — Memory Pointer Pattern':<40} {r2['tokens']:>10,} {r2['time']:>6.1f}s {r2.get('data_size', 0):>20,} B")

    if r1["tokens"] > r2["tokens"] > 0:
        reduction = (1 - r2["tokens"] / r1["tokens"]) * 100
        ratio = r1["tokens"] // r2["tokens"]
        print(f"\n  → {reduction:.0f}% fewer tokens with Memory Pointer Pattern ({ratio}x)")
        print(f"  → {r2.get('data_size', 0):,} bytes processed — never entered LLM context")

    print(f"\n  Strands Agents: https://strandsagents.com")
    print(f"  IBM Research:   https://arxiv.org/html/2511.22729v1")
