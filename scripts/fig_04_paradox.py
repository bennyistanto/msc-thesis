"""Thesis Figure 4.3 - "What does and does not improve under marginal bias
correction" - 2x2 grid of (a) Pearson r, (b) RMSE, (c) NSE, (d) SDR across the
three correction stages, drawn as BAR charts over a categorical method axis.

Bars, not lines: the x-axis is three distinct methods, not a time series, so a
line plot invites a spurious time-series reading (thesis-exam feedback 7).

The temporal-skill panels (r, RMSE, NSE) use the in-sample CPC-UNI values
(ledger S23/S21/S22); the amplitude panel (SDR) uses the independent BMKG
validation value (ledger S2). The two references differ by panel, so each panel
states its reference in its title rather than relying on the caption alone.

Bars start at zero so the vertical extent is proportional to the value and a
small change reads as a small change; the earlier line version zoomed the r
axis to 0.30-0.42, which inflated the +0.005 shift into an apparent jump.

Output: paper/thesis/figures/fig_thesis_04_paradox.png
"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_04_paradox.png"

METHODS = ["LS", "LSEQM", "LSEQM+DL"]
x = np.arange(len(METHODS))

# temporal skill vs in-sample CPC-UNI (ledger S23/S21/S22)
r_values = [0.343, 0.345, 0.348]
rmse_values = [13.10, 14.18, 14.07]
nse_values = [-0.273, -0.548, -0.524]
# amplitude vs independent BMKG validation (ledger S2)
sdr_values = [0.71, 1.03, 1.00]

RED = "#d62728"     # a temporal-skill metric that does not improve
GREEN = "#1a9850"   # the amplitude metric that does improve
BARW = 0.62


def bars(ax, vals, color, title, ref, fmt, valpos="above"):
    ax.bar(x, vals, BARW, color=color, edgecolor="black", linewidth=0.6, zorder=3)
    for xi, v in zip(x, vals):
        if valpos == "above":
            va, off = "bottom", 3
        else:
            va, off = "top", -3
        ax.annotate(fmt.format(v), xy=(xi, v), xytext=(0, off),
                    textcoords="offset points", ha="center", va=va, fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(METHODS, fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold", pad=20)
    ax.text(0.5, 1.02, ref, transform=ax.transAxes, ha="center", va="bottom",
            fontsize=8, color="#555", style="italic")
    ax.grid(axis="y", alpha=0.3, linestyle=":", zorder=0)


fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.22), constrained_layout=True)
ax_r, ax_rmse, ax_nse, ax_sdr = axes.flat

bars(ax_r, r_values, RED, "(a) Pearson $r$", "vs CPC-UNI (in-sample)", "{:.3f}")
ax_r.set_ylim(0, 0.42)
ax_r.set_ylabel("Pearson $r$", fontsize=10)

bars(ax_rmse, rmse_values, RED, "(b) RMSE", "vs CPC-UNI (in-sample)", "{:.2f}")
ax_rmse.set_ylim(0, 15.5)
ax_rmse.set_ylabel("RMSE (mm/day)", fontsize=10)

bars(ax_nse, nse_values, RED, "(c) NSE", "vs CPC-UNI (in-sample)", "{:.2f}",
     valpos="below")
ax_nse.set_ylim(-0.65, 0)
ax_nse.set_ylabel("NSE", fontsize=10)

bars(ax_sdr, sdr_values, GREEN, "(d) Std-Dev Ratio", "vs BMKG (independent)",
     "{:.2f}")
ax_sdr.axhline(1.0, color="black", linestyle="--", linewidth=0.9, alpha=0.6, zorder=2)
ax_sdr.set_ylim(0, 1.2)
ax_sdr.set_ylabel("Std-Dev Ratio", fontsize=10)

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print("wrote %s (%d KB)" % (OUT, OUT.stat().st_size // 1024))
