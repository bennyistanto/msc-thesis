"""Thesis Figure H.2 - "Gridded window offset against CPC-UNI, GPM era".

Whole-domain window-offset diagnostic of half-hourly IMERG-L against the gridded
CPC-UNI analysis at 0.5 degree, over the full GPM era (2015 to 2025): native h*
map (~0), harmonised h* map (~-23 h), and the pooled r(h) with per-band
decomposition.

Data: temp/subdaily_lag/gridded_cpc_window_stats_2015_2025.npz
      (the merged 2015-2021 + 2022-2025 sweep)

Source: extracted from the temporal-alignment diagnostic
(temp/subdaily_lag/gridded_cpc_window.py, single-era plot).

Output: paper/thesis/figures/fig_thesis_H2_gridded_gpm.png
"""
from pathlib import Path
import numpy as np
from subdaily_helpers import SUBDAILY, single_era_gridded_figure

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_H2_gridded_gpm.png"

z = np.load(SUBDAILY / "gridded_cpc_window_stats_2015_2025.npz")
single_era_gridded_figure(z["stats_native"], z["stats_harmonised"], z["band"],
                          z["clat"], z["clon"], 2015, 2025, OUT)
print(f"wrote {OUT.name}")
