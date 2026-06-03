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

See: https://strandsagents.com/docs/user-guide/concepts/multi-agent/swarm/
See: https://strandsagents.com/docs/user-guide/concepts/multi-agent/multi-agent-patterns/
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

# ─────────────────────────────────────────────────────────────────────────────
# How to switch the model provider (token counting works the same on all of them).
#
# Amazon Bedrock — uses boto3, NO extra package needed.
#   Requires configured AWS credentials and model access enabled in the
#   Amazon Bedrock console.
#       from strands.models import BedrockModel
#       MODEL = BedrockModel(
#           model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
#           region_name="us-east-1",
#       )
#   Docs: https://strandsagents.com/docs/user-guide/concepts/model-providers/amazon-bedrock/
#
# Anthropic (direct API) — requires:  pip install 'strands-agents[anthropic]'
#   The API key goes inside client_args (get one at https://console.anthropic.com/).
#       from strands.models.anthropic import AnthropicModel
#       MODEL = AnthropicModel(
#           client_args={"api_key": os.getenv("ANTHROPIC_API_KEY")},
#           model_id="claude-sonnet-4-6",
#           max_tokens=1028,
#       )
#   Docs: https://strandsagents.com/docs/user-guide/concepts/model-providers/anthropic/
# ─────────────────────────────────────────────────────────────────────────────


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

    # 📊 Token counting in a Swarm: each agent has its OWN metrics.
    # We iterate over result.results (collector → analyzer → reporter) and sum
    # each one's accumulated_usage to see the TOTAL cost of the multi-agent system.
    # accumulated_usage is the Strands native metric (same for OpenAI, Bedrock, etc.).
    swarm_tokens = {"input": 0, "output": 0, "total": 0}
    for _node_id, node_result in result.results.items():
        if node_result.result.metrics:
            usage = node_result.result.metrics.accumulated_usage
            swarm_tokens["input"] += usage["inputTokens"]
            swarm_tokens["output"] += usage["outputTokens"]
            swarm_tokens["total"] += usage["totalTokens"]

    print(f"\n{'=' * 60}")
    print(f"  Status: {result.status}")
    print(f"  Agents: {' → '.join(n.node_id for n in result.node_history)}")
    print(f"  Iterations: {result.execution_count}")
    print(f"  Time: {result.execution_time}ms")
    print(f"  💰 Tokens (all agents): {swarm_tokens['input']} in, "
          f"{swarm_tokens['output']} out, {swarm_tokens['total']} total")
    print("=" * 60)
    print("\n  ✅ 145KB+ of logs processed by 3 agents")
    print("  ✅ Data flowed via invocation_state (ToolContext)")
    print("  ✅ No data entered any LLM context window")
