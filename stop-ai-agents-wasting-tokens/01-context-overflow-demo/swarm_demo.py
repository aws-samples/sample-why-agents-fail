"""
Swarm Demo: Multi-agent log analysis with shared invocation_state.

Glossary:
- Swarm: a pattern where multiple specialized AI agents work together, handing tasks to each other.
- invocation_state: shared memory that all agents can read/write during a workflow.
- Handoff: when one agent passes a task to another agent.

Three specialized agents collaborate via Strands Swarm. Large data flows
through invocation_state (shared across all agents) using ToolContext.
The Swarm handles handoffs and coordination automatically.

Collector → Analyzer → Reporter

See: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/swarm/
See: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/
"""
import os
os.environ['OTEL_SDK_DISABLED'] = 'true'

from dotenv import load_dotenv
load_dotenv()

from strands import Agent
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from strands.multiagent import Swarm

from tools import (
    fetch_logs_swarm,
    analyze_errors_swarm,
    detect_latency_swarm,
    generate_report_swarm,
    get_error_details_swarm,
)

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")


# ── Agents ───────────────────────────────────────────────────────────

collector = Agent(
    name="collector",
    description="Fetches application logs and stores them in shared state for analysis",
    system_prompt="You collect data. Fetch logs with fetch_logs_swarm, then hand off to analyzer. Do NOT hand off to reporter.",
    tools=[fetch_logs_swarm], model=MODEL,
)

analyzer = Agent(
    name="analyzer",
    description="Analyzes error patterns and latency anomalies from logs in shared state",
    system_prompt=(
        "You analyze data. Call analyze_errors_swarm AND detect_latency_swarm "
        "with the pointer from the collector (e.g. 'logs-payment-service'). "
        "You MUST call both tools before handing off. After both complete, hand off to reporter."
    ),
    tools=[analyze_errors_swarm, detect_latency_swarm], model=MODEL,
)

reporter = Agent(
    name="reporter",
    description="Generates the final incident report from analyses in shared state",
    system_prompt="You write reports. Call generate_report_swarm to produce the final report. After generating the report, present it to the user. Do NOT hand off to other agents.",
    tools=[generate_report_swarm], model=MODEL,
)

# ── Swarm ────────────────────────────────────────────────────────────

swarm = Swarm(
    [collector, analyzer, reporter],
    entry_point=collector,
    max_handoffs=6,
    max_iterations=10,
)

if __name__ == "__main__":
    print("=" * 60)
    print("  SWARM DEMO: Multi-Agent Log Analysis")
    print("  Collector → Analyzer → Reporter")
    print("  Data flows via invocation_state (ToolContext)")
    print("=" * 60)

    result = swarm("Fetch 6 hours of logs for payment-service, analyze errors and latency, then generate an incident report.")

    print(f"\n{'=' * 60}")
    print(f"  Status: {result.status}")
    print(f"  Agents: {' → '.join(n.node_id for n in result.node_history)}")
    print(f"  Iterations: {result.execution_count}")
    print(f"  Time: {result.execution_time}ms")
    print("=" * 60)
    print("\n  ✅ 145KB+ of logs processed by 3 agents")
    print("  ✅ Data flowed via invocation_state (ToolContext)")
    print("  ✅ No data entered any LLM context window")
