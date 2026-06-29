"""Thesis Figure 4.4 - "Window-offset correlation recovery by satellite era".

Per-year Pearson r at the UTC-day window (h=0) versus each year's best-matched
window, with the peak offset h* below: the calendar-window recovery emerges only
once IMERG resolves the diurnal cycle, at the 2014/15 GPM-constellation
transition.

Data: temp/subdaily_lag/subdaily_seasonal_results_2001_2021.npz
      (per-year/month/offset sufficient-statistics window-offset sweep)

Source: extracted from the temporal-alignment diagnostic
(temp/subdaily_lag/build_seasonal_figures.py, fig_era_curve).

Output: paper/thesis/figures/fig_thesis_04_window_era.png
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from subdaily_helpers import (SUBDAILY, HOUR_SHIFTS, r_from_stats, r_at, peak_offset)

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_04_window_era.png"

FULL = np.load(SUBDAILY / "subdaily_seasonal_results_2001_2021.npz", allow_pickle=True)
H = HOUR_SHIFTS
B = FULL["stats_year_month"]; years = FULL["years"]
By = B.sum(axis=1)                                       # (n_year, n_h, 6)

r0 = np.array([r_at(r_from_stats(By[i]), 0) for i in range(len(years))])
pk = np.array([peak_offset(r_from_stats(By[i]))[1] for i in range(len(years))])
hs = np.array([peak_offset(r_from_stats(By[i]))[0] for i in range(len(years))])

fig, (ax, ax2) = plt.subplots(2, 1, figsize=(8.0, 6.6), sharex=True,
                              gridspec_kw={"height_ratios": [2.0, 1.0], "hspace": 0.12,
                                           "left": 0.10, "right": 0.97, "top": 0.92, "bottom": 0.09})
ax.fill_between(years, r0, pk, color="#d9b3ff", alpha=0.55, label="recoverable by window alignment")
ax.plot(years, pk, "-o", color="#5a189a", lw=2.0, ms=4, label="peak $r$ (window-aligned, $h=h^\\star$)")
ax.plot(years, r0, "-o", color="#d62728", lw=2.0, ms=4, label="$r$ at $h=0$ (UTC-day archive)")
ax.axvline(2014.5, color="0.4", ls="--", lw=1.0)
ax.text(2014.7, 0.05, "GPM era →", fontsize=9, color="0.3")
ax.text(2013.3, 0.05, "← TRMM-era input", fontsize=9, color="0.3", ha="right")
ax.set_ylim(0, 0.7); ax.set_ylabel("Pearson $r$  (all months pooled)", fontsize=10)
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95, edgecolor="0.7")
ax.set_title("The calendar-window recovery emerges only when IMERG resolves "
             "the diurnal cycle", fontsize=10.5, fontweight="bold", loc="left")
ax.grid(True, alpha=0.25, ls=":")

# near-optimal band: offsets within 0.02 of each year's peak r
hlo, hhi = [], []
for i in range(len(years)):
    rc = r_from_stats(By[i]); pkr = np.nanmax(rc)
    near = H[np.isfinite(rc) & (rc >= pkr - 0.02)]
    hlo.append(near.min()); hhi.append(near.max())
ax2.fill_between(years, hlo, hhi, color="0.6", alpha=0.30, lw=0, label="offsets within 0.02 of peak $r$")
ax2.plot(years, hs, "-s", color="0.25", lw=1.6, ms=4, label="peak offset $h^\\star$")
ax2.axhline(-23, color="#5a189a", ls=":", lw=1.0)
ax2.text(2001.2, -26, "convention offset $\\approx -23$ h", fontsize=8.5, color="#5a189a")
ax2.axvline(2014.5, color="0.4", ls="--", lw=1.0)
ax2.set_ylim(-40, 5); ax2.set_xlim(2000.5, 2021.5)
ax2.set_xticks(range(2001, 2022, 2)); ax2.set_yticks([-30, -20, -10, 0])
ax2.set_ylabel("optimal offset $h^\\star$ (hours)", fontsize=10); ax2.set_xlabel("Year", fontsize=10)
ax2.set_title("Peak offset $h^\\star$: noisy when undetectable, locks to "
              "$-22/-23$ h in the GPM era", fontsize=9.5, loc="left")
ax2.legend(loc="lower right", fontsize=8, framealpha=0.9, ncol=2)
ax2.grid(True, alpha=0.25, ls=":")

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT.name}")
