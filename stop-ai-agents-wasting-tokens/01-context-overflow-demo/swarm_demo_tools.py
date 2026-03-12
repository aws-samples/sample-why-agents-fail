"""Re-exports from swarm_demo.py for notebook compatibility.

This module exists so that swarm_demo.ipynb can import tools, agents, and the
swarm instance without running the __main__ block in swarm_demo.py.
"""

from swarm_demo import (  # noqa: F401
    fetch_application_logs,
    analyze_error_patterns,
    detect_latency_anomalies,
    generate_incident_report,
    get_error_details,
    collector,
    analyzer,
    reporter,
    swarm,
    MODEL,
)
