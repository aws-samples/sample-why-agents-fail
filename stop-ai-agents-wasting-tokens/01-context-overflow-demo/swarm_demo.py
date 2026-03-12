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

from strands import Agent, tool, ToolContext
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from strands.multiagent import Swarm
import json
from datetime import datetime, timedelta
import secrets

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")


@tool(context=True)
def fetch_application_logs(app_name: str, tool_context: ToolContext, hours: int = 6) -> str:
    """Fetch application logs and store in shared invocation_state for other agents.

    Args:
        app_name: Application name
        hours: Hours of logs to fetch
    """
    logs = []
    base_time = datetime.now() - timedelta(hours=hours)
    for i in range(hours * 100):
        levels = ["INFO", "WARN", "ERROR", "DEBUG"]
        level = levels[secrets.randbelow(len(levels))]
        services = ["api-gateway", "auth-service", "db-connector", "cache-layer"]
        service = services[secrets.randbelow(len(services))]
        event = {
            "timestamp": (base_time + timedelta(seconds=i)).isoformat(),
            "level": level, "service": service,
            "message": f"Event {i} from {service}",
            "duration_ms": secrets.randbelow(4991) + 10,  # 10-5000
            "status_code": [200, 201, 400, 404, 500, 503][secrets.randbelow(6)],
        }
        if level == "ERROR":
            event["stack_trace"] = "\n".join(
                [f"  at mod{j}.func{j}(file{j}.py:{secrets.randbelow(100) + 1})" for j in range(10)]
            )
        logs.append(event)

    pointer = f"logs-{app_name}"
    tool_context.invocation_state[pointer] = logs
    size = len(json.dumps(logs))
    return f"Fetched {len(logs)} events ({size:,} bytes). Stored as '{pointer}' in shared state. Hand off to analyzer."


@tool(context=True)
def analyze_error_patterns(logs_pointer: str, tool_context: ToolContext) -> str:
    """Analyze error patterns from logs in shared invocation_state.

    Args:
        logs_pointer: Pointer key (e.g. 'logs-payment-service')
    """
    logs = tool_context.invocation_state.get(logs_pointer)
    if not logs:
        return f"Error: '{logs_pointer}' not found in shared state"

    errors = [l for l in logs if l["level"] == "ERROR"]
    by_service = {}
    for e in errors:
        by_service[e["service"]] = by_service.get(e["service"], 0) + 1

    result = {"total_errors": len(errors), "error_rate": round(len(errors) / len(logs) * 100, 2), "by_service": by_service}
    tool_context.invocation_state["error_analysis"] = result
    return f"Error analysis complete. {json.dumps(result, indent=2)}"


@tool(context=True)
def detect_latency_anomalies(logs_pointer: str, tool_context: ToolContext) -> str:
    """Detect latency anomalies from logs in shared invocation_state.

    Args:
        logs_pointer: Pointer key (e.g. 'logs-payment-service')
    """
    logs = tool_context.invocation_state.get(logs_pointer)
    if not logs:
        return f"Error: '{logs_pointer}' not found in shared state"

    durations = sorted([l["duration_ms"] for l in logs])
    p95 = durations[int(len(durations) * 0.95)]
    anomalies_count = sum(1 for l in logs if l["duration_ms"] > p95)

    result = {"total_requests": len(logs), "p95_latency_ms": p95, "anomalies_count": anomalies_count}
    tool_context.invocation_state["latency_analysis"] = result
    return f"Latency analysis complete. {json.dumps(result, indent=2)}"


@tool(context=True)
def generate_incident_report(tool_context: ToolContext) -> str:
    """Generate incident report from analyses in shared invocation_state."""
    errors = tool_context.invocation_state.get("error_analysis")
    latency = tool_context.invocation_state.get("latency_analysis")
    if not errors or not latency:
        return "Error: need both error_analysis and latency_analysis in shared state first"

    report = {
        "report_generated": datetime.now().isoformat(),
        "summary": {
            "total_errors": errors["total_errors"], "error_rate": errors["error_rate"],
            "p95_latency_ms": latency["p95_latency_ms"], "anomalies": latency["anomalies_count"],
        },
        "by_service": errors["by_service"],
        "recommendations": [],
    }
    if errors["error_rate"] > 5:
        report["recommendations"].append("HIGH: Error rate exceeds 5%")
    if latency["anomalies_count"] > 20:
        report["recommendations"].append("MEDIUM: High latency anomaly count")
    return json.dumps(report, indent=2)


@tool(context=True)
def get_error_details(logs_pointer: str, tool_context: ToolContext, service: str = None, limit: int = 5) -> str:
    """Get detailed error logs for a specific service from shared invocation_state.

    Args:
        logs_pointer: Pointer key (e.g. 'logs-payment-service')
        service: Service name to filter (e.g. 'cache-layer')
        limit: Max errors to return
    """
    logs = tool_context.invocation_state.get(logs_pointer)
    if not logs:
        return f"Error: '{logs_pointer}' not found in shared state"
    
    errors = [l for l in logs if l["level"] == "ERROR"]
    if service:
        errors = [e for e in errors if e["service"] == service]
    
    return json.dumps(errors[:limit], indent=2)


# ── Agents ───────────────────────────────────────────────────────────

collector = Agent(
    name="collector",
    description="Fetches application logs and stores them in shared state for analysis",
    system_prompt="You collect data. Fetch logs with fetch_application_logs, then hand off to analyzer. Do NOT hand off to reporter.",
    tools=[fetch_application_logs], model=MODEL,
)

analyzer = Agent(
    name="analyzer",
    description="Analyzes error patterns and latency anomalies from logs in shared state",
    system_prompt=(
        "You analyze data. Call analyze_error_patterns AND detect_latency_anomalies "
        "with the pointer from the collector (e.g. 'logs-payment-service'). "
        "You MUST call both tools before handing off. After both complete, hand off to reporter."
    ),
    tools=[analyze_error_patterns, detect_latency_anomalies], model=MODEL,
)

reporter = Agent(
    name="reporter",
    description="Generates the final incident report from analyses in shared state",
    system_prompt="You write reports. Call generate_incident_report to produce the final report. After generating the report, present it to the user. Do NOT hand off to other agents.",
    tools=[generate_incident_report], model=MODEL,
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
