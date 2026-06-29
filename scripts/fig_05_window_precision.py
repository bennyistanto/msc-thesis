"""Thesis Figure 5.5 - "Why the window recovery is confined to the GPM era".

(a) Day-offset cross-correlation between the satellite daily total (at each era's
    own best window) and the gauge daily total: a day-precise product correlates
    only at offset 0; a temporally imprecise product spreads it across days.
(b) The r(h) window-shift curve for each era - re-windowing recovers daily r only
    when the underlying signal is sharp (the GPM era).

Data: temp/subdaily_lag/subdaily_seasonal_results_2001_2021.npz (era r(h) curves),
      temp/subdaily_lag/hh_cache/hh_cache_{year}.npz (for the day-lag profiles),
      data/input/stations/idn_cli_weatherstation_data_bmkg.csv (gauges)

Source: extracted from the temporal-alignment diagnostic
(temp/subdaily_lag/fig_pregpm_explainer.py + build_era_diagnostics.py).

Output: paper/thesis/figures/fig_thesis_05_window_precision.png
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from subdaily_helpers import (ROOT, SUBDAILY, HOUR_SHIFTS, r_from_stats,
                              windowed_cumsum, load_hh_cache)

sys.path.insert(0, str(ROOT))
from src.station_validation import load_station_observations  # noqa: E402

OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_05_window_precision.png"

H = HOUR_SHIFTS
LAGS = np.arange(-3, 4)
FULL = np.load(SUBDAILY / "subdaily_seasonal_results_2001_2021.npz", allow_pickle=True)
B = FULL["stats_year_month"]; YEARS = FULL["years"]
OBS = load_station_observations(
    str(ROOT / "data/input/stations/idn_cli_weatherstation_data_bmkg.csv"),
    str(ROOT / "data/input/stations/idn_cli_weatherstation_location_bmkg.csv"))

ERAS = {"Pre-GPM (2001-2013)": list(range(2001, 2014)),
        "GPM era (2015-2021)": list(range(2015, 2022))}
COL = {"Pre-GPM (2001-2013)": "#c44e52", "GPM era (2015-2021)": "#2a6f97"}


def pooled_rh(years):
    """Pooled r(h) for an era from sufficient stats (sum over its years + months)."""
    idx = [np.where(YEARS == y)[0][0] for y in years if y in YEARS]
    return r_from_stats(B[idx].sum(axis=(0, 1)))


def daily_at(times, precip, csum, vcum, slot, dates, h):
    a = dates + pd.Timedelta(hours=int(h)); i0 = slot.reindex(a).values
    ok = np.isfinite(i0); i0i = np.where(ok, np.nan_to_num(i0), 0).astype(int)
    end = np.minimum(i0i + 48, len(times))
    v = vcum[end] - vcum[i0i]; tt = csum[end] - csum[i0i]
    out = np.full((len(dates), precip.shape[1]), np.nan)
    g = ok[:, None] & (v == 48); out[g] = tt[g]
    return out


def day_lag_profile(sat_df, gauge_df):
    prof = []
    for L in LAGS:
        gs = gauge_df.shift(L).values.ravel(); ss = sat_df.values.ravel()
        m = np.isfinite(gs) & np.isfinite(ss)
        prof.append(np.corrcoef(gs[m], ss[m])[0, 1] if m.sum() > 2 else np.nan)
    return np.array(prof)


rh = {}; lag = {}
for nm, yrs in ERAS.items():
    r = pooled_rh(yrs); rh[nm] = r
    h_star = int(H[np.nanargmax(np.where(np.isfinite(r), r, -9))])
    times, precip, wmo = load_hh_cache(yrs)
    csum, vcum = windowed_cumsum(precip); slot = pd.Series(np.arange(len(times)), index=times)
    dates = pd.date_range(f"{yrs[0]}-01-03", f"{yrs[-1]}-12-29", freq="1D")
    sat = daily_at(times, precip, csum, vcum, slot, dates, h_star)
    satdf = pd.DataFrame(sat, index=dates, columns=wmo)
    gdf = OBS.reindex(index=dates, columns=wmo)
    lag[nm] = day_lag_profile(satdf, gdf)

keep = np.abs(LAGS) <= 2
xl = LAGS[keep]

fig, axes = plt.subplots(2, 1, figsize=(8.0, 9.0),
                         gridspec_kw={"hspace": 0.28, "left": 0.11, "right": 0.97,
                                      "top": 0.95, "bottom": 0.06})

# (a) day-offset bars
ax = axes[0]
w = 0.38
for i, nm in enumerate(ERAS):
    ax.bar(xl + (i - 0.5) * w, lag[nm][keep], width=w, color=COL[nm],
           edgecolor="black", linewidth=0.4, label=nm)
ax.axvline(0, color="0.6", ls=":", lw=1.0)
ax.set_xticks(xl)
ax.set_xticklabels(["2 days\nbefore", "1 day\nbefore", "same\nday", "1 day\nafter",
                    "2 days\nafter"], fontsize=8.5)
ax.set_ylabel("correlation of satellite vs gauge daily rain", fontsize=9.5)
ax.set_title("(a) Which day does the satellite place the rain on?",
             fontsize=10.5, fontweight="bold", loc="left", pad=18)
ax.annotate("GPM: tall only on the\nSAME day = day-precise",
            xy=(0.18, lag["GPM era (2015-2021)"][LAGS == 0][0]),
            xytext=(1.05, 0.52), fontsize=8.5, color=COL["GPM era (2015-2021)"],
            ha="left", arrowprops=dict(arrowstyle="->", color=COL["GPM era (2015-2021)"], lw=1.1))
ax.annotate("Pre-GPM: nearly as tall on the\nday BEFORE = rain smeared across\ndays, so no window can fix it",
            xy=(-1.18, lag["Pre-GPM (2001-2013)"][LAGS == -1][0]),
            xytext=(-2.3, 0.50), fontsize=8.5, color=COL["Pre-GPM (2001-2013)"],
            ha="left", arrowprops=dict(arrowstyle="->", color=COL["Pre-GPM (2001-2013)"], lw=1.1))
ax.set_ylim(0, 0.68); ax.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
ax.grid(True, alpha=0.25, ls=":", axis="y")

# (b) r(h) consequence
ax = axes[1]
for nm in ERAS:
    ax.plot(H, rh[nm], color=COL[nm], lw=2.3, label=nm)
ax.axvline(0, color="0.6", ls=":", lw=1.0)
r0g = rh["GPM era (2015-2021)"][H == 0][0]; pkg = np.nanmax(rh["GPM era (2015-2021)"])
pkp = np.nanmax(rh["Pre-GPM (2001-2013)"])
ax.annotate(f"GPM: {r0g:.2f} (UTC) lifts to {pkg:.2f}\nwhen the window is matched",
            xy=(-23, pkg - 0.01), xytext=(-38, 0.685), fontsize=8.5, ha="left", va="top",
            color=COL["GPM era (2015-2021)"], arrowprops=dict(arrowstyle="->",
            color=COL["GPM era (2015-2021)"], lw=1.1))
ax.annotate(f"Pre-GPM: flat near {pkp:.2f}\nat every window = nothing to recover",
            xy=(6, 0.345), xytext=(20, 0.46), fontsize=8.5, ha="center",
            color=COL["Pre-GPM (2001-2013)"], arrowprops=dict(arrowstyle="->",
            color=COL["Pre-GPM (2001-2013)"], lw=1.1))
ax.set_xlim(-48, 48); ax.set_ylim(0, 0.74)
ax.set_xlabel("hours the satellite 24-h window is shifted ($h$)", fontsize=9.5)
ax.set_ylabel("pooled Pearson $r$ vs gauge", fontsize=9.5)
ax.set_title("(b) So re-windowing recovers daily $r$ only in the GPM era",
             fontsize=10.5, fontweight="bold", loc="left", pad=18)
ax.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
ax.grid(True, alpha=0.25, ls=":")

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT.name}")
