"""Seasonal r(h) sweep from the cached HH station matrix (2001-2021).

Reads the per-year shards written by build_station_hh_cache.py and the daily
BMKG gauge observations, and computes the Pearson r(h) landscape - how the
satellite-vs-gauge daily correlation depends on the 24-hour aggregation-window
offset h - resolved by calendar month, by 3-month running season, and per
station.

Design
------
For each target date d and hour offset h, the satellite daily total is the sum
of the 48 half-hour slots in [d 00:00 UTC + h, +24 h). With a cumulative sum
over the continuous 30-min timeline, that window total is csum[i0+48]-csum[i0],
so a whole month of offsets is computed without a per-date Python loop.

Correlation is pooled exactly via SUFFICIENT STATISTICS. For each
(calendar month M, station s, offset h) we accumulate, over every (year, date)
pair in month M:
    n, Sx, Sy, Sxx, Syy, Sxy        (x = gauge, y = satellite)
Pearson r = (n*Sxy - Sx*Sy) / sqrt((n*Sxx - Sx^2)(n*Syy - Sy^2)).
Because sufficient statistics are additive, ANY pooling is exact:
  - a single calendar month            -> that month's stats
  - a 3-month running season (DJF..NDJ)-> sum of its 3 months' stats
  - pooled across stations             -> sum over the station axis
  - the full annual landscape          -> sum of all 12 months
No correlation is ever averaged; pairs are pooled.

A second, lighter accumulator keyed by (year, month, h) pooled across stations
supports the inter-annual stability question (does h* drift year to year?).

Timezone band uses the authoritative `timezone` column (7/8/9 = WIB/WITA/WIT).

The pooled-year window is a CLI argument so the same sweep can be run on the
full record (which exposes the era-dependence of the recovery: early TRMM-era
IMERG barely resolves the diurnal cycle, the GPM era resolves it sharply) and
then re-pooled on the GPM era for the clean seasonal climatology and map.

Usage:
  python build_subdaily_seasonal.py            # full record 2001-2021
  python build_subdaily_seasonal.py 2015 2021  # GPM-era climatology

Outputs: temp/subdaily_lag/subdaily_seasonal_results_<y0>_<y1>.npz
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
sys.path.insert(0, str(ROOT))
from src.station_validation import load_station_observations  # noqa: E402

CACHE_DIR = ROOT / "temp" / "subdaily_lag" / "hh_cache"
OBS_CSV = ROOT / "data/input/stations/idn_cli_weatherstation_data_bmkg.csv"
LOC_CSV = ROOT / "data/input/stations/idn_cli_weatherstation_location_bmkg.csv"
OUT_DIR = ROOT / "temp" / "subdaily_lag"
OUT_TMPL = "subdaily_seasonal_results_{y0}_{y1}.npz"

HOUR_SHIFTS = np.arange(-48, 49, 1)     # 97 integer-hour offsets
SLOTS_PER_DAY = 48
YEAR_MIN, YEAR_MAX = 2001, 2021
TZ_NAME = {7: "WIB (UTC+7)", 8: "WITA (UTC+8)", 9: "WIT (UTC+9)"}

# 3-month running seasons (calendar month numbers, 1-12)
SEASONS = {
    "DJF": (12, 1, 2), "JFM": (1, 2, 3), "FMA": (2, 3, 4), "MAM": (3, 4, 5),
    "AMJ": (4, 5, 6), "MJJ": (5, 6, 7), "JJA": (6, 7, 8), "JAS": (7, 8, 9),
    "ASO": (8, 9, 10), "SON": (9, 10, 11), "OND": (10, 11, 12), "NDJ": (11, 12, 1),
}
SEASON_ORDER = list(SEASONS.keys())


def load_cache():
    """Concatenate per-year shards into one continuous 30-min timeline."""
    shards = sorted(CACHE_DIR.glob("hh_cache_*.npz"))
    if not shards:
        raise FileNotFoundError(f"no shards in {CACHE_DIR}; run the cache build first")
    times, precip = [], []
    meta = None
    for sh in shards:
        d = np.load(sh, allow_pickle=True)
        times.append(d["times"])
        precip.append(d["precip"])
        if meta is None:
            meta = {k: d[k] for k in ("wmo", "lon", "lat", "timezone", "region")}
    times = pd.DatetimeIndex(np.concatenate(times))
    precip = np.concatenate(precip, axis=0).astype(np.float32)   # mm/hr
    print(f"cache: {precip.shape[0]} half-hours x {precip.shape[1]} stations, "
          f"{times[0].date()} to {times[-1].date()}", flush=True)
    return times, precip, meta


def windowed_cumsum(precip):
    """Return (csum, vcount) for NaN-safe 24-h window sums in mm.

    window_total(i0) = csum[i0+48] - csum[i0]   (mm, since *0.5 applied)
    valid_slots(i0)  = vcount[i0+48] - vcount[i0]
    A window is valid only if all 48 slots are present.
    """
    mm30 = precip * 0.5                      # mm per 30-min
    valid = np.isfinite(mm30)
    filled = np.where(valid, mm30, 0.0)
    n_t, n_st = precip.shape
    csum = np.zeros((n_t + 1, n_st), dtype=np.float64)
    vcum = np.zeros((n_t + 1, n_st), dtype=np.int32)
    np.cumsum(filled, axis=0, out=csum[1:])
    np.cumsum(valid, axis=0, out=vcum[1:])
    return csum, vcum


def main():
    t_start = time.time()
    y0 = int(sys.argv[1]) if len(sys.argv) > 1 else YEAR_MIN
    y1 = int(sys.argv[2]) if len(sys.argv) > 2 else YEAR_MAX
    out_npz = OUT_DIR / OUT_TMPL.format(y0=y0, y1=y1)
    print(f"=== seasonal sweep, pooled years {y0}-{y1} ===", flush=True)

    times, precip, meta = load_cache()
    wmo = meta["wmo"].astype(int)
    tz = meta["timezone"].astype(int)
    n_st = len(wmo)

    # gauge daily obs, aligned to the cache station order
    obs = load_station_observations(str(OBS_CSV), str(LOC_CSV))
    obs = obs.loc[(obs.index.year >= y0) & (obs.index.year <= y1)]
    obs = obs.reindex(columns=wmo)            # align order, NaN where absent
    print(f"gauge obs: {obs.shape[0]} days x {obs.notna().any().sum()} "
          f"stations with data", flush=True)

    csum, vcum = windowed_cumsum(precip)
    slot_pos = pd.Series(np.arange(len(times)), index=times)   # timestamp -> row

    n_h = len(HOUR_SHIFTS)
    # accumulator A: (month, station, h, 6 sufficient stats) pooled over years
    # stats order: n, Sx, Sy, Sxx, Syy, Sxy   (x=gauge, y=satellite)
    A = np.zeros((12, n_st, n_h, 6), dtype=np.float64)
    # accumulator B: (year, month, h, 6) pooled over stations (inter-annual)
    years = np.arange(y0, y1 + 1)
    Bacc = np.zeros((len(years), 12, n_h, 6), dtype=np.float64)

    obs_dates = obs.index
    for M in range(1, 13):
        tdates = obs_dates[obs_dates.month == M]
        gauge = obs.loc[tdates].values                      # (n_d, n_st) mm
        # anchor row index for each (date, h); reject windows leaving the timeline
        d0 = tdates.normalize()
        for hi, h in enumerate(HOUR_SHIFTS):
            anchor = d0 + pd.Timedelta(hours=int(h))
            i0 = slot_pos.reindex(anchor).values            # float, NaN if absent
            ok = np.isfinite(i0)
            i0i = np.where(ok, np.nan_to_num(i0), 0).astype(int)
            full = np.zeros(len(tdates), dtype=bool)
            full[ok] = (i0i[ok] + SLOTS_PER_DAY) <= (len(times))
            sat = np.full((len(tdates), n_st), np.nan)
            valid_slots = (vcum[np.minimum(i0i + SLOTS_PER_DAY, len(times))]
                           - vcum[i0i])                     # (n_d, n_st)
            wtot = csum[np.minimum(i0i + SLOTS_PER_DAY, len(times))] - csum[i0i]
            good = full[:, None] & (valid_slots == SLOTS_PER_DAY)
            sat[good] = wtot[good]

            x = gauge
            y = sat
            m = np.isfinite(x) & np.isfinite(y)             # (n_d, n_st)
            xm = np.where(m, x, 0.0)
            ym = np.where(m, y, 0.0)
            # per-station sufficient stats over dates
            n_ = m.sum(axis=0)
            Sx = xm.sum(axis=0); Sy = ym.sum(axis=0)
            Sxx = (xm * xm).sum(axis=0); Syy = (ym * ym).sum(axis=0)
            Sxy = (xm * ym).sum(axis=0)
            A[M - 1, :, hi, 0] += n_
            A[M - 1, :, hi, 1] += Sx
            A[M - 1, :, hi, 2] += Sy
            A[M - 1, :, hi, 3] += Sxx
            A[M - 1, :, hi, 4] += Syy
            A[M - 1, :, hi, 5] += Sxy
            # inter-annual: per year, pooled across stations
            yr = tdates.year.values
            for yi, Y in enumerate(years):
                ym_ = (yr == Y)
                if not ym_.any():
                    continue
                mm_ = m[ym_]
                xx = np.where(mm_, x[ym_], 0.0); yy = np.where(mm_, y[ym_], 0.0)
                Bacc[yi, M - 1, hi, 0] += mm_.sum()
                Bacc[yi, M - 1, hi, 1] += xx.sum()
                Bacc[yi, M - 1, hi, 2] += yy.sum()
                Bacc[yi, M - 1, hi, 3] += (xx * xx).sum()
                Bacc[yi, M - 1, hi, 4] += (yy * yy).sum()
                Bacc[yi, M - 1, hi, 5] += (xx * yy).sum()
        print(f"  month {M:2d}: {len(tdates)} dates swept "
              f"({time.time()-t_start:.0f}s elapsed)", flush=True)

    np.savez(out_npz,
             hour_shifts=HOUR_SHIFTS,
             stats_month=A,              # (12, n_st, n_h, 6)
             stats_year_month=Bacc,      # (n_year, 12, n_h, 6)
             years=years,
             season_names=np.array(SEASON_ORDER),
             season_months=np.array([SEASONS[s] for s in SEASON_ORDER]),
             wmo=wmo, lon=meta["lon"], lat=meta["lat"],
             timezone=tz, region=meta["region"].astype(str),
             pooled_years=np.array([y0, y1]))
    print(f"wrote {out_npz}  ({time.time()-t_start:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
