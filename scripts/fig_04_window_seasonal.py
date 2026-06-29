"""Thesis Figure 4.5 - "GPM-era window-offset correlation and seasonal stability".

(a) GPM-era (2015-2021) r(h) by timezone band, mean per band with IQR shading;
(b) the season-invariance of the peak offset h* across the twelve three-month
running seasons.

Data: temp/subdaily_lag/subdaily_seasonal_results_2015_2021.npz

Source: extracted from the temporal-alignment diagnostic
(temp/subdaily_lag/build_seasonal_figures.py, fig_seasonal_landscape).

Output: paper/thesis/figures/fig_thesis_04_window_seasonal.png
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from subdaily_helpers import (SUBDAILY, HOUR_SHIFTS, r_from_stats, season_stats,
                              pool_stations, peak_offset, per_station_hstar_peak,
                              SEASON_ORDER, TZC, TZLS, TZN)

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_04_window_seasonal.png"

GPM = np.load(SUBDAILY / "subdaily_seasonal_results_2015_2021.npz", allow_pickle=True)
H = HOUR_SHIFTS
A = GPM["stats_month"]; tz = GPM["timezone"]

fig, (ax, ax2) = plt.subplots(2, 1, figsize=(8.0, 8.6),
                              gridspec_kw={"height_ratios": [1.45, 1.0], "hspace": 0.30,
                                           "left": 0.10, "right": 0.97, "top": 0.94, "bottom": 0.07})

# (a) r(h) by band, annual GPM-era pooling
rps = r_from_stats(A.sum(axis=0))
ax.axhline(0.0, color="0.85", lw=0.6)
ax.axvline(0, color="0.4", ls=":", lw=1.0); ax.axvline(-23, color="#5a189a", ls=":", lw=1.0)
for z in (7, 8, 9):
    sel = tz == z
    mr = np.nanmean(rps[sel], axis=0)
    q1 = np.nanpercentile(rps[sel], 25, axis=0); q3 = np.nanpercentile(rps[sel], 75, axis=0)
    ax.fill_between(H, q1, q3, color=TZC[z], alpha=0.15)
    ax.plot(H, mr, color=TZC[z], ls=TZLS[z], lw=2.2, label=f"{TZN[z]} (n={sel.sum()})")
    pi = int(np.nanargmax(mr)); ax.plot(H[pi], mr[pi], "o", color=TZC[z], ms=6, mec="black", mew=0.6)
ax.set_xlim(-48, 48); ax.set_xticks(range(-48, 49, 12)); ax.set_ylim(-0.05, 0.75)
ax.set_xlabel("Hour offset $h$  (window = [UTC 00:00 + $h$, +24 h))", fontsize=9.5)
ax.set_ylabel("Pearson $r$ (mean per band, IQR shaded)", fontsize=9.5)
ax.text(-23, 0.70, "$h^\\star=-23$ h", fontsize=9, color="#5a189a", ha="center")
ax.set_title("(a) GPM era (2015-2021): $r(h)$ peaks at $-23$ h, all bands",
             fontsize=10.5, fontweight="bold", loc="left")
ax.legend(loc="upper right", fontsize=8.5, framealpha=0.95, edgecolor="0.7")
ax.grid(True, alpha=0.25, ls=":")

# (b) h*(season) stability across 12 running seasons
x = np.arange(len(SEASON_ORDER))
pooled_h = []; band_h = {z: [] for z in (7, 8, 9)}
for s in SEASON_ORDER:
    sm = season_stats(A, s)
    pooled_h.append(peak_offset(r_from_stats(pool_stations(sm)))[0])
    hstar, _, _, valid = per_station_hstar_peak(sm)
    for z in (7, 8, 9):
        band_h[z].append(np.nanmedian(hstar[(tz == z) & valid]))
ax2.axhline(-23, color="#5a189a", ls=":", lw=1.0)
for z in (7, 8, 9):
    ax2.plot(x, band_h[z], color=TZC[z], ls=TZLS[z], marker="o", lw=1.4, ms=4, label=TZN[z])
ax2.plot(x, pooled_h, "-D", color="0.15", lw=2.0, ms=5, label="pooled")
ax2.set_xticks(x); ax2.set_xticklabels(SEASON_ORDER, rotation=45, fontsize=8)
ax2.set_ylim(-30, -14)
ax2.set_ylabel("optimal window offset $h^\\star$ (hours)", fontsize=9.5)
ax2.set_xlabel("three-month running season", fontsize=9.5)
ax2.set_title("(b) $h^\\star$ is season-invariant (12 running seasons)",
              fontsize=10.5, fontweight="bold", loc="left")
ax2.legend(loc="lower left", fontsize=8, framealpha=0.95, edgecolor="0.7", ncol=2)
ax2.grid(True, alpha=0.25, ls=":")

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT.name}")
