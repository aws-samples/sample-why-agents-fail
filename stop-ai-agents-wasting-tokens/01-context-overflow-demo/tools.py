"""Tools for the context overflow demos.

All tools use the Memory Pointer Pattern: large data is stored outside
the LLM context window and accessed via a lightweight pointer key.

State store used depends on the agent architecture:

  Single-agent (test_context_overflow.py, test_context_overflow.ipynb):
    → agent.state  — data scoped to one agent instance
    Tools: fetch_application_logs, analyze_error_patterns,
           detect_latency_anomalies, generate_incident_report

  Multi-agent / Swarm (swarm_demo.py, test_multiagent_context_overflow.ipynb):
    → invocation_state  — data shared across all agents in the swarm
    Tools: fetch_logs_swarm, analyze_errors_swarm,
           detect_latency_swarm, generate_report_swarm, get_error_details_swarm

See:
  https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/state/
  https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/
"""

from strands import tool, ToolContext
import json
from datetime import datetime, timedelta
import secrets


# ── Shared log generation ─────────────────────────────────────────────────────

def _generate_log_events(app_name: str, hours: int, include_trace: bool = True) -> list:
    """Generate synthetic log events. Used by both single-agent and swarm tools."""
    log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    services = ["api-gateway", "auth-service", "db-connector", "cache-layer"]
    logs = []
    base_time = datetime.now() - timedelta(hours=hours)

    for i in range(hours * 100):
        level = log_levels[secrets.randbelow(len(log_levels))]
        service = services[secrets.randbelow(len(services))]
        event = {
            "timestamp": (base_time + timedelta(seconds=i)).isoformat(),
            "level": level,
            "service": service,
            "message": f"Event {i} from {service}",
            "request_id": f"req-{i:08d}",
            "duration_ms": secrets.randbelow(4991) + 10,  # 10-5000
            "status_code": [200, 201, 400, 404, 500, 503][secrets.randbelow(6)],
        }
        if include_trace and level == "ERROR":
            event["stack_trace"] = "\n".join(
                [f"  at module{j}.function{j}(file{j}.py:{secrets.randbelow(100) + 1})" for j in range(15)]
            )
        logs.append(event)

    return logs


# ── Single-agent tools (test_context_overflow.py) ────────────────────────────
# State store: agent.state — scoped to one agent instance
# Flow: fetch_application_logs → analyze_error_patterns
#                              → detect_latency_anomalies
#                              → generate_incident_report

@tool(context=True)
def fetch_application_logs(
    app_name: str,
    tool_context: ToolContext,
    hours: int = 24,
    include_trace: bool = True,
) -> str:
    """Fetch application logs from monitoring system.

    Returns large dataset of log events that cannot be truncated without
    losing critical information for anomaly detection.

    Args:
        app_name: Application name to fetch logs for
        hours: Number of hours of logs to fetch (default 24)
        include_trace: Include full stack traces (default True)
    """
    logs = _generate_log_events(app_name, hours, include_trace)
    result_str = json.dumps(logs, indent=2)

    # Store in agent.state and return pointer instead of flooding context
    if len(result_str) > 20000:
        pointer = f"logs-{app_name}"
        tool_context.agent.state.set(pointer, logs)
        return f"Fetched {len(logs)} log events for {app_name} ({len(result_str):,} bytes). Data stored at: {pointer}"

    return result_str


@tool(context=True)
def analyze_error_patterns(logs_pointer: str, tool_context: ToolContext, threshold: int = 10) -> str:
    """Analyze error patterns in application logs.

    Requires complete log dataset to detect patterns accurately.
    Cannot work with truncated data.

    Args:
        logs_pointer: Memory pointer to log data in agent.state
        threshold: Minimum occurrences to report (default 10)
    """
    logs = tool_context.agent.state.get(logs_pointer)

    if not logs:
        return f"Error: Invalid pointer '{logs_pointer}'"

    error_logs = [log for log in logs if log["level"] == "ERROR"]

    service_errors = {}
    for log in error_logs:
        service = log["service"]
        service_errors[service] = service_errors.get(service, 0) + 1

    patterns = {
        "total_errors": len(error_logs),
        "error_rate": len(error_logs) / len(logs) * 100,
        "by_service": service_errors,
        "high_frequency": {svc: count for svc, count in service_errors.items() if count >= threshold},
    }

    return json.dumps(patterns, indent=2)


@tool(context=True)
def detect_latency_anomalies(logs_pointer: str, tool_context: ToolContext, percentile: int = 95) -> str:
    """Detect latency anomalies in application logs.

    Requires full dataset to calculate accurate percentiles.

    Args:
        logs_pointer: Memory pointer to log data in agent.state
        percentile: Percentile threshold for anomalies (default 95)
    """
    logs = tool_context.agent.state.get(logs_pointer)

    if not logs:
        return f"Error: Invalid pointer '{logs_pointer}'"

    durations = sorted([log["duration_ms"] for log in logs])
    p_index = int(len(durations) * percentile / 100)
    p_value = durations[p_index]

    anomalies = [
        {"timestamp": log["timestamp"], "service": log["service"], "duration_ms": log["duration_ms"], "request_id": log["request_id"]}
        for log in logs
        if log["duration_ms"] > p_value
    ]

    return json.dumps({"total_requests": len(logs), "p95_latency_ms": p_value, "anomalies_count": len(anomalies), "anomalies": anomalies[:20]}, indent=2)


@tool
def generate_incident_report(error_analysis: str, latency_analysis: str) -> str:
    """Generate incident report from error and latency analysis results.

    Args:
        error_analysis: JSON string with error analysis results
        latency_analysis: JSON string with latency analysis results
    """
    try:
        errors = json.loads(error_analysis)
        latency = json.loads(latency_analysis)
    except json.JSONDecodeError as e:
        return f"Error: could not parse analysis results — {e}"

    report = {
        "report_generated": datetime.now().isoformat(),
        "summary": {
            "total_errors": errors.get("total_errors", 0),
            "error_rate_percent": round(errors.get("error_rate", 0), 2),
            "latency_anomalies": latency.get("anomalies_count", 0),
            "p95_latency_ms": latency.get("p95_latency_ms", 0),
        },
        "recommendations": [],
    }

    if errors.get("error_rate", 0) > 5:
        report["recommendations"].append("HIGH: Error rate exceeds 5% - investigate immediately")

    if latency.get("anomalies_count", 0) > 100:
        report["recommendations"].append("MEDIUM: High number of latency anomalies detected")

    return json.dumps(report, indent=2)


# ── Swarm / multi-agent tools (swarm_demo.py) ─────────────────────────────────
# State store: invocation_state — shared across all agents in the swarm
# Flow: fetch_logs_swarm → analyze_errors_swarm + detect_latency_swarm
#                        → generate_report_swarm
#       get_error_details_swarm (follow-up investigation)

@tool(context=True)
def fetch_logs_swarm(app_name: str, tool_context: ToolContext, hours: int = 6) -> str:
    """Fetch application logs and store in shared invocation_state for other agents.

    Args:
        app_name: Application name
        hours: Hours of logs to fetch
    """
    logs = _generate_log_events(app_name, hours, include_trace=True)
    pointer = f"logs-{app_name}"
    tool_context.invocation_state[pointer] = logs
    size = len(json.dumps(logs))
    return f"Fetched {len(logs)} events ({size:,} bytes). Stored as '{pointer}' in shared state. Hand off to analyzer."


@tool(context=True)
def analyze_errors_swarm(logs_pointer: str, tool_context: ToolContext) -> str:
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
def detect_latency_swarm(logs_pointer: str, tool_context: ToolContext) -> str:
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
def generate_report_swarm(tool_context: ToolContext) -> str:
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
def get_error_details_swarm(logs_pointer: str, tool_context: ToolContext, service: str = None, limit: int = 5) -> str:
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
