"""
Generate the "Without Memory Pointer vs Memory Pointer Pattern" comparison card.

Two panels: raw JSON floods the context (problem) vs data stays in agent.state,
only a pointer ID enters context (fix). Sizes reflect the measured demo run
(~65KB of logs for a 2-hour fetch), not a placeholder figure.

Run: uv run --with matplotlib python generate_without_pointer.py
Output: written to ../../images/Without-Memory-Pointer.png (shared images folder)
"""

import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

RED = "#D64545"
RED_TINT = "#FBEAEA"
GREEN = "#2E9E7B"
GREEN_TINT = "#E6F4EF"
INK = "#1A1A1A"
GREY = "#666666"

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "images", "Without-Memory-Pointer.png")


def draw_panel(ax, x0, title, accent, tint, rows, symbol):
    w, h = 5.5, 5.2
    y0 = 0.4
    ax.add_patch(FancyBboxPatch(
        (x0, y0), w, h, boxstyle="round,pad=0.02,rounding_size=0.18",
        linewidth=2, edgecolor=accent, facecolor="white", zorder=2))
    ax.add_patch(FancyBboxPatch(
        (x0, y0 + h - 0.95), w, 0.95, boxstyle="round,pad=0.02,rounding_size=0.18",
        linewidth=0, facecolor=tint, zorder=3))
    ax.text(x0 + w / 2, y0 + h - 0.48, title, ha="center", va="center",
            fontsize=15, fontweight="bold", color=accent, zorder=4)
    y = y0 + h - 1.6
    for left, right in rows:
        ax.text(x0 + 0.45, y, left, ha="left", va="center",
                fontsize=12, color=INK, zorder=4)
        ax.text(x0 + 3.05, y, symbol, ha="left", va="center",
                fontsize=14, fontweight="bold", color=accent, zorder=4)
        ax.text(x0 + 3.45, y, right, ha="left", va="center",
                fontsize=12, color=INK, zorder=4)
        y -= 0.78


fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("white")
ax.set_xlim(0, 12)
ax.set_ylim(0, 6)
ax.axis("off")

draw_panel(
    ax, 0.3, "Without Memory Pointer", RED, RED_TINT,
    [
        ("~65KB logs in context", "Re-sent each turn"),
        ("LLM reasons over raw JSON", "Tokens balloon"),
        ("Large tool output", "Context bloats"),
        ("Follow-up question", "Whole dataset again"),
    ],
    "✗",
)

draw_panel(
    ax, 6.2, "Memory Pointer Pattern", GREEN, GREEN_TINT,
    [
        ("~65KB logs in agent.state", "Never enters context"),
        ("LLM receives pointer ID", "~50 tokens per call"),
        ('Tool returns "logs-app"', "Precise reference"),
        ("recall_logs_by_id(ID)", "Read back by ID"),
    ],
    "✓",
)

ax.text(6.0, 0.12,
        "Measured on gpt-4o-mini, 2h of logs (~65KB). Data recalled by exact pointer ID from agent.state.",
        ha="center", va="center", fontsize=9, color=GREY)

plt.tight_layout()
plt.savefig(OUT, dpi=100, bbox_inches="tight", facecolor="white")
print(f"Saved: {os.path.abspath(OUT)}")
