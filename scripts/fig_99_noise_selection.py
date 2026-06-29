"""Thesis Figure D.1 - "Sampling stability of the per-station window correlation".

Three GPM-era distributions of per-station r showing why a single month is
inflated and why it vanishes with the full record:
  (1) 1 month, fixed -23 h window  - pure sampling noise (median ~0.56, very wide);
  (2) 1 month, best of 97 offsets  - noise + selection bias (median ~0.66, fat tail);
  (3) 7 years, best of 97 offsets  - the precise, unbiased truth (median ~0.56).
The fixed-window single-month median coincides with the 7-year truth at ~0.56
(the unbiasedness point); only the offset selection inflates it.

Data: temp/subdaily_lag/hh_cache/hh_cache_{2015..2021}.npz (single-month sweeps),
      temp/subdaily_lag/subdaily_seasonal_results_2015_2021.npz (7-year peaks),
      data/input/stations/idn_cli_weatherstation_data_bmkg.csv (gauges)

Source: extracted from the temporal-alignment diagnostic
(temp/subdaily_lag/fig_noise_selection.py).

Output: paper/thesis/figures/fig_thesis_99_noise_selection.png
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from subdaily_helpers import (ROOT, SUBDAILY, HOUR_SHIFTS, SLOTS_PER_DAY,
                              r_from_stats, windowed_cumsum, load_hh_cache)

sys.path.insert(0, str(ROOT))
from src.station_validation import load_station_observations  # noqa: E402

OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_99_noise_selection.png"
H = HOUR_SHIFTS

times, precip, wmo = load_hh_cache(range(2015, 2022))
csum, vcum = windowed_cumsum(precip); slot = pd.Series(np.arange(len(times)), index=times)
obs = load_station_observations(
    str(ROOT / "data/input/stations/idn_cli_weatherstation_data_bmkg.csv"),
    str(ROOT / "data/input/stations/idn_cli_weatherstation_location_bmkg.csv")).reindex(columns=wmo)


def month_stats(dates):
    g = obs.reindex(dates).values; d0 = dates.normalize()
    st = np.zeros((len(wmo), len(H), 6))
    for hi, h in enumerate(H):
        i0 = slot.reindex(d0 + pd.Timedelta(hours=int(h))).values
        ok = np.isfinite(i0); i0i = np.where(ok, np.nan_to_num(i0), 0).astype(int)
        end = np.minimum(i0i + SLOTS_PER_DAY, len(times))
        full = np.zeros(len(dates), bool); full[ok] = (i0i[ok] + SLOTS_PER_DAY) <= len(times)
        v = vcum[end] - vcum[i0i]; t = csum[end] - csum[i0i]
        sat = np.full((len(dates), len(wmo)), np.nan)
        gd = full[:, None] & (v == SLOTS_PER_DAY); sat[gd] = t[gd]
        m = np.isfinite(g) & np.isfinite(sat); xm = np.where(m, g, 0.); ym = np.where(m, sat, 0.)
        st[:, hi, 0] = m.sum(0); st[:, hi, 1] = xm.sum(0); st[:, hi, 2] = ym.sum(0)
        st[:, hi, 3] = (xm * xm).sum(0); st[:, hi, 4] = (ym * ym).sum(0); st[:, hi, 5] = (xm * ym).sum(0)
    return st


peak_sm, fixed_sm = [], []
idx = obs.index
for y in range(2015, 2022):
    for mo in range(1, 13):
        dts = idx[(idx.year == y) & (idx.month == mo)]
        if len(dts) < 20:
            continue
        rps = r_from_stats(month_stats(dts), min_n=10)
        valid = np.isfinite(rps).any(1)
        peak_sm.append(np.nanmax(np.where(np.isfinite(rps), rps, -9)[valid], 1))
        fx = rps[:, H == -23].ravel()[valid]; fixed_sm.append(fx[np.isfinite(fx)])
peak_sm = np.concatenate(peak_sm); fixed_sm = np.concatenate(fixed_sm)

g7 = np.load(SUBDAILY / "subdaily_seasonal_results_2015_2021.npz", allow_pickle=True)
r7 = r_from_stats(g7["stats_month"].sum(0)); v7 = np.isfinite(r7).any(1)
pk7 = np.nanmax(np.where(np.isfinite(r7), r7, -9)[v7], 1)

m_fix, m_peak, m_7 = np.median(fixed_sm), np.median(peak_sm), np.median(pk7)
bins = np.arange(0, 1.001, 0.04)
fig, ax = plt.subplots(figsize=(9.2, 5.4))
ax.hist(fixed_sm, bins=bins, density=True, color="0.6", alpha=0.55,
        label="1 month, fixed $-23$ h window\n(sampling noise only)")
ax.hist(peak_sm, bins=bins, density=True, color="#c44e52", alpha=0.50,
        label="1 month, best of 97 offsets\n(noise $+$ selection)")
ax.hist(pk7, bins=bins, density=True, color="#2a6f97", alpha=0.65,
        label="7 years, best of 97 offsets\n(the true value)")
# the fixed single-month median (grey) coincides with the 7-year truth (blue) at
# ~0.56 - the unbiasedness point - so draw grey thick + dotted behind the blue
# dashed line, otherwise the grey line hides under the blue one.
for m, c, ls, lw in [(m_fix, "0.45", ":", 3.0),
                     (m_peak, "#c44e52", "--", 1.8),
                     (m_7, "#2a6f97", "--", 1.8)]:
    ax.axvline(m, color=c, ls=ls, lw=lw)
ax.set_ylim(0, max(7.0, ax.get_ylim()[1]))
yt = ax.get_ylim()[1]
ax.annotate("argmax over 97 offsets\ninflates the high tail",
            xy=(0.84, 1.55), xytext=(0.985, yt * 0.58), fontsize=8.5, color="#7a2a2c",
            ha="right", arrowprops=dict(arrowstyle="->", color="#7a2a2c", lw=1.3))
ax.annotate("one noisy month:\n$r$ scatters widely\n($\\approx$ 10-20 wet days)",
            xy=(0.27, 0.82), xytext=(0.05, yt * 0.55), fontsize=8.5, color="0.30",
            ha="left", arrowprops=dict(arrowstyle="->", color="0.45", lw=1.2))
ax.annotate("7-year truth\n$\\approx 0.56$", xy=(m_7, yt * 0.70),
            xytext=(0.40, yt * 0.74), ha="right", fontsize=9, color="#2a6f97",
            fontweight="bold", arrowprops=dict(arrowstyle="->", color="#2a6f97", lw=1.4))
ax.text(0.02, 0.97,
        "single month, fixed:  median %.2f, IQR [%.2f, %.2f]\n"
        "single month, peak:   median %.2f, %d%% > 0.65\n"
        "seven years, peak:    median %.2f, IQR [%.2f, %.2f]"
        % (m_fix, np.percentile(fixed_sm, 25), np.percentile(fixed_sm, 75),
           m_peak, 100 * np.mean(peak_sm > 0.65), m_7,
           np.percentile(pk7, 25), np.percentile(pk7, 75)),
        transform=ax.transAxes, va="top", ha="left", fontsize=8.5, family="monospace",
        bbox=dict(boxstyle="round,pad=0.4", fc="#fffdf5", ec="0.6", lw=0.7))
ax.set_xlim(0, 1.0); ax.set_xlabel("per-station Pearson $r$", fontsize=10.5)
ax.set_ylabel("probability density", fontsize=10.5)
ax.set_title("Why single-month per-station $r$ is inflated, and why it vanishes with the full record",
             fontsize=11, fontweight="bold")
ax.legend(loc="upper right", fontsize=8.8, framealpha=0.95, edgecolor="0.7")
ax.grid(True, alpha=0.22, ls=":")
fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT.name}")
