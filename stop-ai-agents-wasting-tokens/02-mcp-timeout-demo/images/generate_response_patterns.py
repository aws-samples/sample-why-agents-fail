"""
Generate the "MCP Tool Response Patterns" timeline across the four scenarios.

One row per scenario: API → elapsed time → outcome. All English, seconds as "s".

Run: uv run --with matplotlib python generate_response_patterns.py
Output: written to ../../images/MCP-Tool-Response-Patterns.png (shared images folder)
"""

import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

GREEN = "#2E9E7B"
RED = "#D64545"
AMBER = "#E8A33D"
INK = "#1A1A1A"
GREY = "#666666"

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "images", "MCP-Tool-Response-Patterns.png")

# (label, elapsed text, outcome text, outcome color, ok?)
rows = [
    ("fast_api",        "1s",   "Good UX",       GREEN, True),
    ("slow_api",        "15s",  "Agent blocked", RED,   False),
    ("failing_api",     "5s",   "424 error",     AMBER, False),
    ("async handleId",  "<2s",  "Immediate",     GREEN, True),
]

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("white")
ax.set_xlim(0, 12)
ax.set_ylim(0, 6)
ax.axis("off")

n = len(rows)
top = 5.3
gap = 1.25

for i, (api, elapsed, outcome, color, ok) in enumerate(rows):
    y = top - i * gap

    # API chip (left)
    ax.add_patch(FancyBboxPatch(
        (0.4, y - 0.32), 2.5, 0.64, boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=1.6, edgecolor="#4A6FA5", facecolor="#EEF3FA", zorder=3))
    ax.text(1.65, y, api, ha="center", va="center", fontsize=12.5,
            fontweight="bold", color=INK, family="monospace", zorder=4)

    # Arrow with elapsed time
    ax.annotate("", xy=(8.1, y), xytext=(3.1, y),
                arrowprops=dict(arrowstyle="-|>", lw=2.4, color=INK), zorder=3)
    ax.text(5.6, y + 0.28, elapsed, ha="center", va="center",
            fontsize=12, fontweight="bold", color=GREY, zorder=4)

    # Outcome marker + label (right)
    mark = "✓" if ok else "✗"
    ax.text(8.5, y, mark, ha="center", va="center", fontsize=17,
            fontweight="bold", color=color, zorder=4)
    ax.text(9.0, y, outcome, ha="left", va="center", fontsize=13,
            fontweight="bold", color=color, zorder=4)

ax.text(0.4, top + 0.55, "MCP Tool Response Patterns", ha="left", va="center",
        fontsize=17, fontweight="bold", color=INK)
ax.text(6.0, 0.15,
        "Representative timings on gpt-4o-mini — the async handleId pattern responds immediately, then polls by ID.",
        ha="center", va="center", fontsize=9, color=GREY)

plt.tight_layout()
plt.savefig(OUT, dpi=100, bbox_inches="tight", facecolor="white")
print(f"Saved: {os.path.abspath(OUT)}")
