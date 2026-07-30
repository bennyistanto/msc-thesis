"""Cache the half-hourly IMERG-L station matrix across the full BMKG-gauge era.

One expensive pass over the half-hourly archive (GPM_3IMERGHH_07 subset on the
I: Google-Drive mount) extracts the 48 half-hour slots per UTC day at every BMKG
station, for each year, and writes a resumable per-year shard. Every downstream
r(h) sweep (seasonal pooling, per-station h*, monthly re-validation) then reads
these shards and is pure in-memory slicing - no further Drive I/O.

Scope: 2001-2021, the years for which BMKG daily gauge observations exist
(idn_cli_weatherstation_data_bmkg.csv runs 2001-01-01 to 2021-12-31).

Extraction is vectorised: nearest lat/lon grid index per station is computed once
from a reference file, then each daily file is indexed directly
(precip[:, lat_idx, lon_idx]) instead of 180 per-station .sel() calls.

Each shard (hh_cache_<year>.npz) holds a perfectly regular 30-min timeline for
that whole UTC year (missing files -> NaN rows, timeline stays gapless) so the
sweep can grab any [anchor, anchor+48 slots] window that crosses day or year
boundaries by concatenating consecutive shards.

Precipitation is stored in mm/hr (the file's native unit); the sweep multiplies
by 0.5 to get mm per 30-min before summing to a daily total.

Usage:
  python build_station_hh_cache.py            # all years 2001-2021 (skips done)
  python build_station_hh_cache.py 2020 2020  # single year (test)
  python build_station_hh_cache.py 2001 2010  # an inclusive range
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
# Half-hourly source: IMERG-L Late Run (GPM_3IMERGHHL), the gauge-free Late
# product consistent with the daily IMERG-L pipeline input. Local extract at
# data/downloads/GPM_3IMERGHHL_07_subset_halfhourly (182x472 subset, 2001-2025,
# all 180 stations inside; nearest-cell extraction is grid-agnostic). Replaces
# the earlier Final-Run (GPM_3IMERGHH) extract, which is gauge-contaminated.
HH_DIR = ROOT / "data" / "downloads" / "GPM_3IMERGHHL_07_subset_halfhourly"
LOC_CSV = ROOT / "data/input/stations/idn_cli_weatherstation_location_bmkg.csv"
OUT_DIR = ROOT / "temp" / "subdaily_lag" / "hh_cache"
OUT_DIR.mkdir(parents=True, exist_ok=True)

YEAR_MIN, YEAR_MAX = 2001, 2021   # BMKG daily gauge coverage
SLOTS_PER_DAY = 48
PRECIP_VAR = "precipitation"


def hh_path(date):
    """Half-hourly IMERG-L file for one UTC day."""
    doy = date.timetuple().tm_yday
    return HH_DIR / (f"GPM_3IMERGHHL_07_subset_{date:%Y%m%d}_"
                     f"{date.year}{doy:03d}_halfhourly.nc4")


def load_locations():
    """Station table: ID_WMO, Lon, Lat, timezone (7/8/9), region. Semicolon CSV."""
    df = pd.read_csv(LOC_CSV, sep=";")
    df["ID_WMO"] = df["ID_WMO"].astype(int)
    return df[["ID_WMO", "Lon", "Lat", "timezone", "region"]].reset_index(drop=True)


def nearest_indices(ref_file, lats, lons):
    """Nearest grid index per station, computed once from a reference file."""
    ds = xr.open_dataset(ref_file, decode_timedelta=False)
    grid_lat = ds["lat"].values
    grid_lon = ds["lon"].values
    ds.close()
    lat_idx = np.abs(grid_lat[:, None] - lats[None, :]).argmin(axis=0)
    lon_idx = np.abs(grid_lon[:, None] - lons[None, :]).argmin(axis=0)
    return lat_idx, lon_idx, grid_lat, grid_lon


def build_year(year, loc, lat_idx, lon_idx):
    """Extract one UTC year into a regular (n_hh, n_station) mm/hr matrix."""
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="1D")
    times = pd.date_range(f"{year}-01-01 00:00", f"{year}-12-31 23:30",
                          freq="30min")
    n_st = len(loc)
    precip = np.full((len(times), n_st), np.nan, dtype=np.float32)

    t0 = time.time()
    n_missing = 0
    cold = 0
    for di, d in enumerate(days):
        p = hh_path(d)
        row0 = di * SLOTS_PER_DAY
        if not p.exists():
            n_missing += 1
            continue
        td = time.time()
        ds = xr.open_dataset(p, decode_timedelta=False)
        vals = ds[PRECIP_VAR].values            # (48, nlat, nlon) mm/hr
        ds.close()
        if vals.shape[0] != SLOTS_PER_DAY:       # guard odd files
            n_missing += 1
            continue
        precip[row0:row0 + SLOTS_PER_DAY] = vals[:, lat_idx, lon_idx]
        if time.time() - td > 3.0:               # count cold-cache hits
            cold += 1
        if d.day == 1:
            rate = (time.time() - t0) / max(di, 1)
            print(f"    {d:%Y-%m}  ({di:3d}/{len(days)} days, "
                  f"{rate:.2f}s/day, {cold} cold)", flush=True)

    dt = time.time() - t0
    print(f"  year {year}: {len(days)} days in {dt/60:.1f} min "
          f"({dt/len(days):.2f}s/day), {n_missing} missing, {cold} cold opens",
          flush=True)
    return times.values, precip, n_missing


def main():
    y0 = int(sys.argv[1]) if len(sys.argv) > 1 else YEAR_MIN
    y1 = int(sys.argv[2]) if len(sys.argv) > 2 else YEAR_MAX

    loc = load_locations()
    lats = loc["Lat"].values.astype(float)
    lons = loc["Lon"].values.astype(float)
    print(f"=== HH station cache build, years {y0}-{y1} ===")
    print(f"stations: {len(loc)}  "
          f"(WIB={int((loc.timezone==7).sum())}, "
          f"WITA={int((loc.timezone==8).sum())}, "
          f"WIT={int((loc.timezone==9).sum())})", flush=True)

    # nearest indices from the first existing file
    ref = next((hh_path(d) for d in pd.date_range(f"{y0}-01-01", f"{y1}-12-31")
                if hh_path(d).exists()), None)
    if ref is None:
        raise FileNotFoundError("no half-hourly files found in range")
    lat_idx, lon_idx, _, _ = nearest_indices(ref, lats, lons)
    print(f"nearest-index reference: {ref.name}", flush=True)

    for year in range(y0, y1 + 1):
        shard = OUT_DIR / f"hh_cache_{year}.npz"
        if shard.exists():
            print(f"year {year}: shard exists, skipping", flush=True)
            continue
        times, precip, n_missing = build_year(year, loc, lat_idx, lon_idx)
        np.savez(shard,
                 times=times,
                 precip=precip,
                 wmo=loc["ID_WMO"].values,
                 lon=lons, lat=lats,
                 timezone=loc["timezone"].values,
                 region=loc["region"].values.astype(str),
                 n_missing=n_missing, year=year)
        size_mb = shard.stat().st_size / 1e6
        print(f"  wrote {shard.name} ({size_mb:.1f} MB)", flush=True)

    print("=== done ===", flush=True)


if __name__ == "__main__":
    main()
