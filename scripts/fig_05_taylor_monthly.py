"""Thesis Figure 5.2 - "Station-Level Taylor Diagram by Month"
(12 polar panels in a 4x3 grid, one per calendar month).

Data: data/output/figures/taylor/taylor_statistics_per_dekad.csv

Source: extracted from notebooks/07_paper_results.ipynb, cell
nb07-0013-fig4-taylor. Shared helpers in taylor_helpers.py.

Output: paper/thesis/figures/fig_thesis_05_taylor_monthly.png
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from taylor_helpers import (
    MONTH_NAMES, PANEL_LETTERS,
    compute_period_stats, plot_one_panel, legend_handles_split,
)

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
TAYLOR_CSV = ROOT / "data" / "output" / "figures" / "taylor" / "taylor_statistics_per_dekad.csv"
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_05_taylor_monthly.png"

print(f"Reading: {TAYLOR_CSV}")
df = pd.read_csv(TAYLOR_CSV)
print(f"  {len(df)} rows, {df['station_id'].nunique()} stations")

# Build the 4x3 polar grid
fig = plt.figure(figsize=(13, 15))
# Apply layout BEFORE capturing positions, otherwise the polar axes are
# pinned to the default subplot grid and any later subplots_adjust is ignored.
fig.subplots_adjust(bottom=0.07, top=0.94, left=0.05, right=0.97,
                    wspace=0.13, hspace=0.30)
axes = []
for i in range(12):
    ax_tmp = fig.add_subplot(4, 3, i + 1)
    pos = ax_tmp.get_position()
    ax_tmp.remove()
    axes.append(fig.add_axes(pos, polar=True))

for i, ax in enumerate(axes):
    month = i + 1
    ps, ag = compute_period_stats(df, {month})
    plot_one_panel(ax, ps, ag, f"({PANEL_LETTERS[i]})",
                   MONTH_NAMES[i], compact=True)

ref_h, tst_h = legend_handles_split()
fig.legend(handles=ref_h, title="Reference products",
           loc="lower center", bbox_to_anchor=(0.30, 0.005),
           ncol=len(ref_h), fontsize=9, framealpha=0.9, title_fontsize=9)
fig.legend(handles=tst_h, title="Bias-corrected products",
           loc="lower center", bbox_to_anchor=(0.75, 0.005),
           ncol=len(tst_h), fontsize=9, framealpha=0.9, title_fontsize=9)
fig.suptitle("Station-Level Taylor Diagram by Month",
             fontsize=14, fontweight="bold", y=0.995)

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
