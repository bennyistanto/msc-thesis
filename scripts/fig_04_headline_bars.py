"""Thesis Figure 4.1 (re-layout) - "Stage-Wise Skill at 171 BMKG Stations"
in a 2x2 grid of (a) Relative Bias, (b) Std-Dev Ratio, (c) Q99 Ratio,
(d) CSI across LS / LSEQM / LSEQM+DL.

Values from Table 4.1 (BMKG out-of-sample, pooled across 36 dekads).

Output: paper/thesis/figures/fig_thesis_04_headline_bars.png
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_04_headline_bars.png"

METHODS = ["LS", "LSEQM", "LSEQM+DL"]
COLORS = ["#1f77b4", "#ff7f0e", "#d62728"]   # blue, orange, red
x = np.arange(len(METHODS))

# Values are from Table 4.1 (BMKG out-of-sample, 36 dekads pooled).
rb_values  = [-0.114, 0.009, -0.006]   # relative bias
sdr_values = [0.71, 1.03, 1.00]         # standard deviation ratio
q99_values = [0.71, 1.05, 1.01]         # Q99 ratio
csi_values = [0.53, 0.49, 0.49]         # CSI


def bar_panel(ax, values, *, ylim, ylabel, title, target=None, fmt="{:.2f}"):
    bars = ax.bar(x, values, color=COLORS, edgecolor="black", linewidth=0.6)
    if target is not None:
        ax.axhline(target, color="gray", linestyle="--", linewidth=0.9,
                   alpha=0.7, label=f"Target = {target:g}")
    for xi, v, b in zip(x, values, bars):
        # Place label above the bar; below if the bar extends below zero
        offset = 0.012 * (ylim[1] - ylim[0])
        y = v + offset if v >= 0 else v - offset
        ax.annotate(fmt.format(v), xy=(xi, v), xytext=(0, 4 if v >= 0 else -10),
                    textcoords="offset points", ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(METHODS, fontsize=9)
    ax.set_ylim(*ylim)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.grid(axis="y", alpha=0.3, linestyle=":")


fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.8), constrained_layout=True)
ax_rb, ax_sdr, ax_q99, ax_csi = axes.flat

bar_panel(ax_rb, rb_values, ylim=(-0.15, 0.05),
          ylabel="Relative Bias", title="(a) Relative Bias",
          target=0.0, fmt="{:+.3f}")
bar_panel(ax_sdr, sdr_values, ylim=(0.60, 1.15),
          ylabel="Std-Dev Ratio", title="(b) Std-Dev Ratio",
          target=1.0)
bar_panel(ax_q99, q99_values, ylim=(0.60, 1.15),
          ylabel="$Q_{99}$ Ratio", title=r"(c) $Q_{99}$ Ratio",
          target=1.0)
bar_panel(ax_csi, csi_values, ylim=(0.0, 1.05),
          ylabel="CSI", title="(d) CSI",
          target=1.0)

fig.suptitle("Stage-Wise Skill at 171 Independent BMKG Stations",
             fontsize=11, fontweight="bold")

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
