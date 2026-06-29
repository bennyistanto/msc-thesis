"""Thesis Figure H.1 - "Gridded window offset against CPC-UNI, TRMM-input era".

Whole-domain window-offset diagnostic of half-hourly IMERG-L against the gridded
CPC-UNI analysis at 0.5 degree, over the TRMM-input era (2001 to 2013): native h*
map (~0), harmonised h* map (~-23 h), and the pooled r(h) with per-band
decomposition.

Data: temp/subdaily_lag/gridded_cpc_window_stats_2001_2013.npz

Source: extracted from the temporal-alignment diagnostic
(temp/subdaily_lag/gridded_cpc_window.py, single-era plot).

Output: paper/thesis/figures/fig_thesis_H1_gridded_trmm.png
"""
from pathlib import Path
import numpy as np
from subdaily_helpers import SUBDAILY, single_era_gridded_figure

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_H1_gridded_trmm.png"

z = np.load(SUBDAILY / "gridded_cpc_window_stats_2001_2013.npz")
single_era_gridded_figure(z["stats_native"], z["stats_harmonised"], z["band"],
                          z["clat"], z["clon"], 2001, 2013, OUT)
print(f"wrote {OUT.name}")
