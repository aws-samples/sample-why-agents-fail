"""Tools for demonstrating context overflow with large, indivisible datasets.

Glossary:
- Context overflow: when data is too large for the AI model to process at once.
- Memory Pointer Pattern: storing large data separately and passing lightweight
  references (pointers) instead of the full data through the model.
- LLM context window: the maximum amount of text an AI model can process in one request.

Uses Strands ToolContext + agent.state for the Memory Pointer Pattern.
agent.state is a native key-value store on the agent instance that tools can
read/write without passing data through the LLM context window.

See: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/state/
"""

from strands import tool, ToolContext
import json
from datetime import datetime, timedelta
import secrets


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
    num_events = hours * 100

    log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    services = ["api-gateway", "auth-service", "db-connector", "cache-layer"]

    logs = []
    base_time = datetime.now() - timedelta(hours=hours)

    for i in range(num_events):
        timestamp = base_time + timedelta(seconds=i)
        level = log_levels[secrets.randbelow(len(log_levels))]
        service = services[secrets.randbelow(len(services))]

        event = {
            "timestamp": timestamp.isoformat(),
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
    errors = json.loads(error_analysis)
    latency = json.loads(latency_analysis)

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
