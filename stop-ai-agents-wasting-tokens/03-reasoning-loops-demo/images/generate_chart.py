"""
Generate tool call comparison chart for reasoning loops demo.

Run: uv run generate_chart.py
Output: reasoning-loops-calls.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

RED = "#F28B82"
GREEN = "#5FBFA4"
BLUE = "#7BB3F0"

scenarios = [
    "Ambiguous Feedback\n(no hook)",
    "Clear SUCCESS\nStates",
    "LimitToolCounts\n(hard ceiling)",
]

# Illustrative values based on demo behavior:
# Scenario 1: agent retries same tool repeatedly — ~6 allowed, 0 blocked
# Scenario 2: SUCCESS state stops agent quickly — ~2 allowed, 0 blocked
# Scenario 3: hard limit enforced — 3 allowed per tool, extras blocked
allowed = [6, 2, 6]
blocked = [0, 0, 2]

x = np.arange(len(scenarios))
width = 0.38

fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

bars_allowed = ax.bar(x - width / 2, allowed, width, label="Calls allowed", color=RED, zorder=3)
bars_blocked = ax.bar(x + width / 2, blocked, width, label="Calls blocked", color=GREEN, zorder=3)

# Value labels
for bar in bars_allowed:
    if bar.get_height() > 0:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                str(int(bar.get_height())), ha="center", va="bottom",
                fontsize=13, fontweight="bold")

for bar in bars_blocked:
    if bar.get_height() > 0:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                str(int(bar.get_height())), ha="center", va="bottom",
                fontsize=13, fontweight="bold")
    else:
        ax.text(bar.get_x() + bar.get_width() / 2, 0.15,
                "0", ha="center", va="bottom",
                fontsize=13, color="#999999")

ax.set_title("Tool Calls: Allowed vs Blocked by Strategy", fontsize=16, fontweight="bold", pad=16)
ax.set_ylabel("Number of Tool Calls", fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(scenarios, fontsize=11)
ax.set_ylim(0, 9)
ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)

legend_patches = [
    mpatches.Patch(color=RED, label="Calls allowed (executed)"),
    mpatches.Patch(color=GREEN, label="Calls blocked (by hook)"),
]
ax.legend(handles=legend_patches, loc="upper right", fontsize=11, framealpha=0.9)

ax.text(
    0.5, -0.12,
    "Illustrative — actual counts vary by LLM run. LimitToolCounts uses Strands BeforeToolCallEvent.cancel_tool.",
    transform=ax.transAxes, ha="center", fontsize=9, color="#666666",
)

plt.tight_layout()
plt.savefig("reasoning-loops-calls.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Saved: reasoning-loops-calls.png")
