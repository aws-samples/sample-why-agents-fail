"""
Demo: Native Memory Pointer Pattern in Strands

The manual Memory Pointer Pattern (test_context_overflow.py) stores large data in
agent.state by hand. Strands now ships the same idea as a first-class plugin:
ContextOffloader. It intercepts large tool results at execution time, stores them
in a backend, and leaves a small preview + reference in context — no pointer logic
inside your tools.

This script runs the SAME query three ways and measures tokens in context:

  Test 1: No context management — raw JSON enters the LLM context (high tokens)
  Test 2: ContextOffloader plugin (FileStorage) — large results offloaded to disk
  Test 3: context_manager="auto" — one line composes Summarizing + ContextOffloader

This demo uses Strands Agents. The same context-management ideas (offloading large
tool outputs, summarizing history) are general agent concepts and carry over to
other agent frameworks.

Docs: https://strandsagents.com/docs/user-guide/concepts/context-management/
"""

import os
import json
import time
import shutil

os.environ["OTEL_SDK_DISABLED"] = "true"

from dotenv import load_dotenv
from strands import Agent
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from strands.vended_plugins.context_offloader import ContextOffloader, FileStorage

from native_tools import fetch_application_logs, count_errors_by_service

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")

# Same query for all three tests — the only variable is the context-management strategy
QUERY = (
    "Fetch 2 hours of logs for 'api-gateway', then tell me how many errors occurred "
    "and which service had the most."
)

ARTIFACT_DIR = "./artifacts"


# ── Token measurement ────────────────────────────────────────────────────────

def count_context_tokens(agent) -> int:
    """Approximate tokens across all messages in the conversation history (chars/4)."""
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

def run_test_1_no_management():
    """Test 1: No context management — the raw log JSON lands in the context window."""
    print("\n" + "=" * 70)
    print("TEST 1: NO CONTEXT MANAGEMENT (baseline)")
    print("=" * 70)
    print(f"Query: {QUERY}\n")

    agent = Agent(model=MODEL, tools=[fetch_application_logs, count_errors_by_service])

    start = time.time()
    agent(QUERY)
    elapsed = time.time() - start
    tokens = count_context_tokens(agent)

    print(f"\n⏱️  {elapsed:.1f}s")
    print(f"📊 Tokens in context: {tokens:,}")
    return {"label": "1 — No management", "tokens": tokens, "time": elapsed}


def run_test_2_context_offloader():
    """Test 2: ContextOffloader plugin — large tool results offloaded to FileStorage."""
    print("\n" + "=" * 70)
    print("TEST 2: ContextOffloader PLUGIN (native Memory Pointer Pattern)")
    print("=" * 70)
    print(f"Query: {QUERY}\n")

    storage = FileStorage(artifact_dir=ARTIFACT_DIR)
    agent = Agent(
        model=MODEL,
        tools=[fetch_application_logs, count_errors_by_service],
        # Offload any tool result over ~800 tokens; keep a ~200-token preview in context
        plugins=[ContextOffloader(storage=storage, max_result_tokens=800, preview_tokens=200)],
    )

    start = time.time()
    agent(QUERY)
    elapsed = time.time() - start
    tokens = count_context_tokens(agent)

    # Count artifacts written to disk (the data that never stayed in context)
    artifacts = [
        f for f in os.listdir(ARTIFACT_DIR)
        if not f.startswith(".")
    ] if os.path.isdir(ARTIFACT_DIR) else []

    print(f"\n⏱️  {elapsed:.1f}s")
    print(f"📊 Tokens in context: {tokens:,}")
    print(f"📦 Artifacts offloaded to {ARTIFACT_DIR}/: {len(artifacts)} file(s) — retrievable by reference")
    return {"label": "2 — ContextOffloader", "tokens": tokens, "time": elapsed, "artifacts": len(artifacts)}


def run_test_3_auto():
    """Test 3: context_manager="auto" — Summarizing + ContextOffloader in one line."""
    print("\n" + "=" * 70)
    print('TEST 3: context_manager="auto" (one-line setup)')
    print("=" * 70)
    print(f"Query: {QUERY}\n")

    agent = Agent(
        model=MODEL,
        tools=[fetch_application_logs, count_errors_by_service],
        context_manager="auto",
    )

    start = time.time()
    agent(QUERY)
    elapsed = time.time() - start
    tokens = count_context_tokens(agent)

    print(f"\n⏱️  {elapsed:.1f}s")
    print(f"📊 Tokens in context: {tokens:,}")
    print(f"⚙️  Composed: {type(agent.conversation_manager).__name__} + ContextOffloader (in-memory)")
    return {"label": "3 — context_manager=auto", "tokens": tokens, "time": elapsed}


# ── Comparison ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Start from a clean artifacts directory so the count reflects this run only
    if os.path.isdir(ARTIFACT_DIR):
        shutil.rmtree(ARTIFACT_DIR)

    print("=" * 70)
    print("  NATIVE MEMORY POINTER PATTERN — Strands ContextOffloader")
    print("  Same query, three context-management strategies, measured tokens")
    print("=" * 70)

    results = [
        run_test_1_no_management(),
        run_test_2_context_offloader(),
        run_test_3_auto(),
    ]

    print("\n" + "=" * 70)
    print("  COMPARISON")
    print("=" * 70)
    print(f"\n  {'Strategy':<32} {'Tokens':>10} {'Time':>8}")
    print("  " + "-" * 52)
    for r in results:
        print(f"  {r['label']:<32} {r['tokens']:>10,} {r['time']:>6.1f}s")

    baseline = results[0]["tokens"]
    best = min(results[1:], key=lambda r: r["tokens"])
    if baseline > best["tokens"] > 0:
        reduction = (1 - best["tokens"] / baseline) * 100
        print(f"\n  → Best native strategy: {best['label']} — {reduction:.0f}% fewer tokens than baseline")

    print("\n  Manual pattern (agent.state):  test_context_overflow.py")
    print("  Native pattern (ContextOffloader):  this file")
    print("  Strands context management:  https://strandsagents.com/docs/user-guide/concepts/context-management/")
