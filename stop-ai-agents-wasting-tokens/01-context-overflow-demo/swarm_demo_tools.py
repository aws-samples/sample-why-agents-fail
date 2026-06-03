"""Re-exports from swarm_demo.py and tools.py for notebook compatibility.

This module exists so that test_multiagent_context_overflow.ipynb can import
tools, agents, and the swarm instance without running the __main__ block.
"""

from tools import (  # noqa: F401
    fetch_logs_swarm,
    analyze_errors_swarm,
    detect_latency_swarm,
    generate_report_swarm,
    get_error_details_swarm,
)

from swarm_demo import (  # noqa: F401
    collector,
    analyzer,
    reporter,
    swarm,
    MODEL,
)

# Friendly aliases so the notebook can import the context-aware swarm tools
# under the names used in its cells.
fetch_application_logs = fetch_logs_swarm
analyze_error_patterns = analyze_errors_swarm
detect_latency_anomalies = detect_latency_swarm
generate_incident_report = generate_report_swarm
get_error_details = get_error_details_swarm
