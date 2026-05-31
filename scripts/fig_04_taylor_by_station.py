"""Thesis Figure 4.6 - "Station-Level Taylor Diagram by Season"
(2 polar panels: wet season Oct-Mar / dry season Apr-Sep).

Data: data/output/figures/taylor/taylor_statistics_per_dekad.csv
      (per-station per-dekad correlation / std_obs / std_prd for the
       six products CPC-UNI, IMERG-L, IMERG-F, LS, LSEQM, LSEQM+DL).

Source: extracted from notebooks/07_paper_results.ipynb, cell
nb07-0013-fig4-taylor. Shared helpers in taylor_helpers.py.

Output: paper/thesis/figures/fig_thesis_04_taylor_by_station.png
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from taylor_helpers import (
    WET_MONTHS, DRY_MONTHS,
    compute_period_stats, plot_one_panel, legend_handles_split,
)

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
TAYLOR_CSV = ROOT / "data" / "output" / "figures" / "taylor" / "taylor_statistics_per_dekad.csv"
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_04_taylor_by_station.png"

print(f"Reading: {TAYLOR_CSV}")
df = pd.read_csv(TAYLOR_CSV)
print(f"  {len(df)} rows, {df['station_id'].nunique()} stations")

# Compute per-period stats
wet_ps, wet_agg = compute_period_stats(df, WET_MONTHS)
dry_ps, dry_agg = compute_period_stats(df, DRY_MONTHS)

# Build the 2-panel polar figure
fig = plt.figure(figsize=(14, 7.5))
ax1 = fig.add_subplot(121)
ax2 = fig.add_subplot(122)
p1, p2 = ax1.get_position(), ax2.get_position()
ax1.remove(); ax2.remove()
ax1 = fig.add_axes(p1, polar=True)
ax2 = fig.add_axes(p2, polar=True)

plot_one_panel(ax1, wet_ps, wet_agg, "(a)", "Wet Season (Oct-Mar)", compact=False)
plot_one_panel(ax2, dry_ps, dry_agg, "(b)", "Dry Season (Apr-Sep)", compact=False)

ref_h, tst_h = legend_handles_split()
fig.legend(handles=ref_h, title="Reference products",
           loc="lower center", bbox_to_anchor=(0.30, -0.04),
           ncol=len(ref_h), fontsize=9, framealpha=0.9, title_fontsize=9)
fig.legend(handles=tst_h, title="Bias-corrected products",
           loc="lower center", bbox_to_anchor=(0.75, -0.04),
           ncol=len(tst_h), fontsize=9, framealpha=0.9, title_fontsize=9)
fig.suptitle("Station-Level Taylor Diagram by Season",
             fontsize=13, fontweight="bold", y=0.99)
fig.subplots_adjust(bottom=0.14, top=0.88, left=0.07, right=0.95, wspace=0.30)

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
