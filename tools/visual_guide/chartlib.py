"""Minimal matplotlib style matching figlib.py (serif, same colours). Use with .venv/bin/python.

save(fig, outdir, name) writes name.svg and name.png (PNG is about 3x the logical width).
source_line(fig, text) puts the italic source line at the bottom, like figlib.source().
tier_label(fig, label) puts the tier badge at the top right.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLUE, GREEN, RED, GRAY, INK = "#1E5BB8", "#2E7D32", "#C62828", "#777777", "#222222"
DARK = "#444444"
TIER_COLORS = {"T1 RK3588": BLUE, "T2 chung": GREEN, "T3 đo": RED}

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "svg.fonttype": "none",       # keep text as text in SVG; the font then falls back like figlib
    "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.edgecolor": "#666666", "axes.linewidth": 0.9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#DDDDDD", "grid.linewidth": 0.7, "axes.axisbelow": True,
    "legend.frameon": True, "legend.edgecolor": "#999999", "legend.fancybox": False,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
})


def source_line(fig, text, y=0.012):
    fig.text(0.012, y, text, fontsize=9.5, color=DARK, style="italic", ha="left", va="bottom")


def tier_label(fig, label, x=0.988, y=0.985):
    c = TIER_COLORS[label]
    fig.text(x, y, label, fontsize=11, fontweight="bold", color=c, ha="right", va="top",
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=c, lw=1.6))


def save(fig, outdir, name):
    """Logical width = figure inches x 100 px; PNG dpi 300 gives 3x that."""
    fig.savefig(os.path.join(outdir, name + ".svg"))
    fig.savefig(os.path.join(outdir, name + ".png"), dpi=300)
    print(f"{name}: {fig.get_figwidth() * 100:.0f} px logical + png")
