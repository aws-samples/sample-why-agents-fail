"""Tools for the NATIVE Memory Pointer Pattern demo.

Contrast with tools.py:

  tools.py (manual pattern)
    - Each tool is "pointer-aware": it calls agent.state.set()/get() by hand
    - fetch returns a pointer string; analyze receives a logs_pointer argument
    - The pattern lives inside the tools

  native_tools.py (this file)
    - Tools are ordinary functions that just return their data
    - NO knowledge of pointers, agent.state, or storage
    - Strands' ContextOffloader plugin intercepts large results transparently
      via AfterToolCallEvent, stores them, and leaves a preview + reference

The native approach keeps the offloading concern OUT of your tool code, so the
same tools work with or without context management.

See:
  https://strandsagents.com/docs/user-guide/concepts/context-management/
"""

import json
import secrets
from datetime import datetime, timedelta

from strands import tool


# ── Shared log generation ─────────────────────────────────────────────────────

def _generate_log_events(app_name: str, hours: int, include_trace: bool = True) -> list:
    """Generate synthetic log events for the demo."""
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


# ── Ordinary tools — no pointer logic, no agent.state ─────────────────────────

@tool
def fetch_application_logs(app_name: str, hours: int = 24, include_trace: bool = True) -> str:
    """Fetch application logs from the monitoring system as JSON.

    Returns the full log dataset. This tool does NOT manage context — it simply
    returns its data. The ContextOffloader plugin (if attached to the agent)
    intercepts the result when it is large and offloads it automatically.

    Args:
        app_name: Application name to fetch logs for
        hours: Number of hours of logs to fetch (default 24)
        include_trace: Include full stack traces on ERROR events (default True)
    """
    logs = _generate_log_events(app_name, hours, include_trace)
    return json.dumps(logs, indent=2)


@tool
def count_errors_by_service(app_name: str, hours: int = 24) -> str:
    """Count ERROR-level events grouped by service for an application.

    This is a SELECTIVE tool: it computes the answer server-side and returns a
    small summary, so the full dataset never needs to enter the LLM context.
    Pairing selective tools like this with the ContextOffloader is what delivers
    real token savings — the offloader is the safety net, selective tools are
    the win.

    Args:
        app_name: Application name to analyze
        hours: Number of hours of logs to analyze (default 24)
    """
    logs = _generate_log_events(app_name, hours)
    errors = [log for log in logs if log["level"] == "ERROR"]

    by_service: dict[str, int] = {}
    for log in errors:
        by_service[log["service"]] = by_service.get(log["service"], 0) + 1

    summary = {
        "app_name": app_name,
        "total_events": len(logs),
        "total_errors": len(errors),
        "error_rate_pct": round(len(errors) / len(logs) * 100, 2),
        "errors_by_service": by_service,
    }
    return json.dumps(summary, indent=2)
