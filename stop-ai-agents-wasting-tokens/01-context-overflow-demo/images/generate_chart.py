"""
Generate token usage comparison chart for context overflow demo.

Run: uv run generate_chart.py
Output: context-overflow-tokens.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

RED = "#F28B82"
GREEN = "#5FBFA4"
ORANGE = "#FFB347"
YELLOW = "#FFD966"

strategies = [
    "Baseline\n(No management)",
    "Sliding Window\n(40 messages)",
    "Sliding Window\n(20 messages)",
    "Memory Pointer\nPattern",
]

# Estimated tokens from demo runs (6h fetch, 600 events, ~230KB)
# Baseline: raw logs flood context — count_tokens(230KB) ≈ 57,500
# SW-40: keeps last 40 messages, trims older tool results
# SW-20: more aggressive pruning
# Memory Pointer: pointer string only, data stays in agent.state
tokens = [57_500, 14_000, 7_500, 500]
colors = [RED, ORANGE, YELLOW, GREEN]

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

bars = ax.bar(strategies, tokens, color=colors, width=0.55, zorder=3)

# Value labels on bars
for bar, value in zip(bars, tokens):
    label = f"{value:,}" if value >= 1000 else str(value)
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 600,
        label,
        ha="center", va="bottom",
        fontsize=13, fontweight="bold",
    )

ax.set_title("Token Usage by Context Strategy", fontsize=16, fontweight="bold", pad=16)
ax.set_ylabel("Estimated Tokens", fontsize=12)
ax.set_ylim(0, 68_000)
ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)

legend_patches = [
    mpatches.Patch(color=RED, label="Fails / overflows context"),
    mpatches.Patch(color=ORANGE, label="Sliding window (40 msgs)"),
    mpatches.Patch(color=YELLOW, label="Sliding window (20 msgs)"),
    mpatches.Patch(color=GREEN, label="Memory Pointer — data stays in agent.state"),
]
ax.legend(handles=legend_patches, loc="upper right", fontsize=10, framealpha=0.9)

ax.text(
    0.5, -0.12,
    "Estimated from 6h log fetch — 600 events, ~230KB. count_tokens() uses len(text) // 4.",
    transform=ax.transAxes, ha="center", fontsize=9, color="#666666",
)

plt.tight_layout()
plt.savefig("context-overflow-tokens.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Saved: context-overflow-tokens.png")
