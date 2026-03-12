"""
Generate MCP response time comparison chart for timeout demo.

Run: uv run generate_chart.py
Output: mcp-response-times.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

RED = "#F28B82"
GREEN = "#5FBFA4"
ORANGE = "#FFB347"
GRAY = "#BDBDBD"

scenarios = [
    "Fast API\n(baseline)",
    "Slow API\n(blocks agent)",
    "Failing API\n(424 error)",
    "Async Pattern\n(solution)",
]

# Times from mcp_server.py:
# fast_api: sleep(1) + overhead ≈ 2s total
# slow_api: sleep(15) + overhead ≈ 17s total
# failing_api: sleep(5) then raises error ≈ 7s total
# async (start_long_job): returns handleId immediately ≈ 2s
times = [2, 17, 7, 2]
colors = [GREEN, RED, ORANGE, GREEN]
labels = ["✓ Good UX", "✗ Agent stuck", "✗ 424 error", "✓ Immediate response"]

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

bars = ax.barh(scenarios, times, color=colors, height=0.5, zorder=3)

# Value labels
for bar, value, label in zip(bars, times, labels):
    ax.text(
        bar.get_width() + 0.3,
        bar.get_y() + bar.get_height() / 2,
        f"{value}s  —  {label}",
        va="center", fontsize=12, fontweight="bold",
    )

ax.set_title("MCP Tool Response Time by Pattern", fontsize=16, fontweight="bold", pad=16)
ax.set_xlabel("Response Time (seconds)", fontsize=12)
ax.set_xlim(0, 28)
ax.xaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)

# Threshold line at 7s (424 error threshold from research)
ax.axvline(x=7, color="#999999", linestyle=":", linewidth=1.5, zorder=2)
ax.text(7.2, 3.6, "424 error\nthreshold", fontsize=9, color="#999999", va="top")

legend_patches = [
    mpatches.Patch(color=GREEN, label="Good UX — responds quickly"),
    mpatches.Patch(color=ORANGE, label="Fails after delay"),
    mpatches.Patch(color=RED, label="Agent blocked — poor UX"),
]
ax.legend(handles=legend_patches, loc="lower right", fontsize=10, framealpha=0.9)

ax.text(
    0.5, -0.12,
    "Times from mcp_server.py — fast_api sleep(1), slow_api sleep(15), failing_api sleep(5) + error, async returns handleId immediately.",
    transform=ax.transAxes, ha="center", fontsize=9, color="#666666",
)

plt.tight_layout()
plt.savefig("mcp-response-times.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Saved: mcp-response-times.png")
