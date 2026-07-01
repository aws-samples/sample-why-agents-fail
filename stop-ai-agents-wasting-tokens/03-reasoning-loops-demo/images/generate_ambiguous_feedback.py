"""
Generate the "Ambiguous Tool Feedback vs Clear States + Hard Limits" comparison.

Two-panel card: the problem (ambiguous feedback → loops) vs the fix (clear
SUCCESS/FAILED states + LimitToolCounts hard ceiling). No DebounceHook.

Run: uv run --with matplotlib python generate_ambiguous_feedback.py
Output: written to ../../images/Ambiguous-Tool-Feedback.png (shared images folder)
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

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "images", "Ambiguous-Tool-Feedback.png")


def draw_panel(ax, x0, title, accent, tint, bullets, symbol):
    """Draw one rounded card panel with a header band and a bulleted list."""
    w, h = 5.5, 5.2
    y0 = 0.4
    # Card
    ax.add_patch(FancyBboxPatch(
        (x0, y0), w, h, boxstyle="round,pad=0.02,rounding_size=0.18",
        linewidth=2, edgecolor=accent, facecolor="white", zorder=2))
    # Header band
    ax.add_patch(FancyBboxPatch(
        (x0, y0 + h - 0.95), w, 0.95, boxstyle="round,pad=0.02,rounding_size=0.18",
        linewidth=0, facecolor=tint, zorder=3))
    ax.text(x0 + w / 2, y0 + h - 0.48, title, ha="center", va="center",
            fontsize=15.5, fontweight="bold", color=accent, zorder=4)
    # Bullets
    y = y0 + h - 1.55
    for text in bullets:
        ax.text(x0 + 0.45, y, symbol, ha="left", va="center",
                fontsize=15, fontweight="bold", color=accent, zorder=4)
        ax.text(x0 + 0.95, y, text, ha="left", va="center",
                fontsize=12.5, color=INK, zorder=4)
        y -= 0.72


fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("white")
ax.set_xlim(0, 12)
ax.set_ylim(0, 6)
ax.axis("off")

draw_panel(
    ax, 0.3, "Ambiguous Tool Feedback", RED, RED_TINT,
    [
        '"Prices may change" — agent retries',
        "Same call, same input, repeated",
        "No terminal state to stop on",
        "Tokens accumulate on every retry",
        "Runs until the iteration limit",
    ],
    "✗",
)

draw_panel(
    ax, 6.2, "Clear States + Hard Limits", GREEN, GREEN_TINT,
    [
        'book_flight() → "SUCCESS" → agent stops',
        "Clear terminal state, no retries",
        "LimitToolCounts caps calls per tool",
        "cancel_tool blocks the extra calls",
        "Bounded, predictable cost per run",
    ],
    "✓",
)

ax.text(6.0, 0.12,
        "LimitToolCounts is the Strands Hooks Cookbook recipe (BeforeToolCallEvent.cancel_tool).",
        ha="center", va="center", fontsize=9, color=GREY)

plt.tight_layout()
plt.savefig(OUT, dpi=100, bbox_inches="tight", facecolor="white")
print(f"Saved: {os.path.abspath(OUT)}")
