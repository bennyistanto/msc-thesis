"""Thesis Figure 4.3 (re-layout) - "What does and does not improve under
marginal bias correction" - 2x2 grid of (a) Pearson r, (b) RMSE, (c) NSE,
(d) SDR across the three correction stages.

The temporal-skill panels (r, RMSE, NSE) use the in-sample CPC-UNI values
from Table 4.2; the amplitude panel (SDR) uses the independent BMKG
validation value from Table 4.1. The two references are disclosed in the
figure caption and the surrounding text. The underlying NetCDFs
(data/output/metrics_*) are not re-read because the aggregate values are
already pinned in the tables and unchanged by layout.

Output: paper/thesis/figures/fig_thesis_04_paradox.png
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_04_paradox.png"

METHODS = ["LS", "LSEQM", "LSEQM+DL"]
x = np.arange(len(METHODS))

# temporal skill vs in-sample CPC-UNI (Table 4.2)
r_values = [0.343, 0.345, 0.348]
rmse_values = [13.10, 14.18, 14.07]
nse_values = [-0.273, -0.548, -0.524]
# amplitude vs independent BMKG validation (Table 4.1)
sdr_values = [0.71, 1.03, 1.00]

PANEL_RED = "#d62728"
PANEL_GREEN = "#1a9850"


def annotate_values(ax, vals, fmt, dy=12):
    for xi, v in zip(x, vals):
        ax.annotate(fmt.format(v), xy=(xi, v),
                    xytext=(0, dy), textcoords="offset points",
                    ha="center", fontsize=9)


# 2x2 grid; figure sized for thesis text width (~14 cm = 5.5 in)
fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.6), constrained_layout=True)
ax_r, ax_rmse, ax_nse, ax_sdr = axes.flat

# (a) Pearson r
ax_r.plot(x, r_values, marker="o", color=PANEL_RED, linewidth=2.2,
          markersize=9, markeredgecolor="black", markeredgewidth=0.7)
annotate_values(ax_r, r_values, "{:.3f}")
ax_r.set_xticks(x); ax_r.set_xticklabels(METHODS, fontsize=9)
ax_r.set_ylim(0.30, 0.42)
ax_r.set_ylabel("Pearson $r$", fontsize=10)
ax_r.set_title("(a) Pearson $r$", fontsize=10, fontweight="bold")
ax_r.grid(axis="y", alpha=0.3, linestyle=":")
ax_r.annotate("shift: $+0.005$", xy=(1.0, 0.31), ha="center",
              fontsize=8, color="#555", style="italic")

# (b) RMSE (mm/day) - red because higher is worse
ax_rmse.plot(x, rmse_values, marker="s", color=PANEL_RED, linewidth=2.2,
             markersize=9, markeredgecolor="black", markeredgewidth=0.7)
annotate_values(ax_rmse, rmse_values, "{:.2f}")
ax_rmse.set_xticks(x); ax_rmse.set_xticklabels(METHODS, fontsize=9)
ax_rmse.set_ylim(12.5, 14.6)
ax_rmse.set_ylabel("RMSE (mm/day)", fontsize=10)
ax_rmse.set_title("(b) RMSE", fontsize=10, fontweight="bold")
ax_rmse.grid(axis="y", alpha=0.3, linestyle=":")
ax_rmse.annotate("shift: $+0.97$", xy=(1.0, 12.65), ha="center",
                 fontsize=8, color="#555", style="italic")

# (c) NSE - red because more negative is worse
ax_nse.plot(x, nse_values, marker="^", color=PANEL_RED, linewidth=2.2,
            markersize=10, markeredgecolor="black", markeredgewidth=0.7)
annotate_values(ax_nse, nse_values, "{:.2f}")
ax_nse.set_xticks(x); ax_nse.set_xticklabels(METHODS, fontsize=9)
ax_nse.set_ylim(-0.65, -0.20)
ax_nse.set_ylabel("NSE", fontsize=10)
ax_nse.set_title("(c) NSE", fontsize=10, fontweight="bold")
ax_nse.grid(axis="y", alpha=0.3, linestyle=":")
ax_nse.annotate("shift: $-0.25$", xy=(1.0, -0.62), ha="center",
                fontsize=8, color="#555", style="italic")

# (d) SDR - green because it moves toward 1.0
ax_sdr.plot(x, sdr_values, marker="D", color=PANEL_GREEN, linewidth=2.2,
            markersize=9, markeredgecolor="black", markeredgewidth=0.7)
ax_sdr.axhline(1.0, color="black", linestyle="--", linewidth=0.9, alpha=0.5)
annotate_values(ax_sdr, sdr_values, "{:.2f}")
ax_sdr.set_xticks(x); ax_sdr.set_xticklabels(METHODS, fontsize=9)
ax_sdr.set_ylim(0.65, 1.10)
ax_sdr.set_ylabel("Std-Dev Ratio", fontsize=10)
ax_sdr.set_title("(d) Std-Dev Ratio", fontsize=10, fontweight="bold")
ax_sdr.grid(axis="y", alpha=0.3, linestyle=":")
ax_sdr.annotate("shift: $+0.29$", xy=(1.0, 0.69), ha="center",
                fontsize=8, color="#555", style="italic")

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
