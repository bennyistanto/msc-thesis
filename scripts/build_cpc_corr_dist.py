"""Build the data array behind thesis Figure 4.x (CPC-UNI correlation distribution).

Regenerates temp/subdaily_lag/cpc_corr_dist.npz, the input to
fig_04_cpc_corr_dist.py. The original array was produced ad hoc in a session
scratchpad and had no generating script; this recovers the recipe.

Recipe (recovered and verified 2026-07-28):
  pr     = per-pixel daily Pearson r of the LSEQM+DL corrected product against
           CPC-UNI, read from the 36 dekadal spatial-distribution metric files
           data/output/metrics_lseqmdl/idn_cli_metricssd_cpc_imergl_lseqmdl_*.nc4
           and averaged over the 36 dekads (nanmean). Native 0.1 deg grid,
           171 x 461, 19,393 finite land pixels (ledger row C14).
  bmask  = pixels hosting at least one of the 180 BMKG stations, by
           nearest-cell assignment. 169 distinct cells, because several
           stations share a 0.1 deg cell.

The "sd" family is the correct one: "ts" files carry an extra 25-year time
axis and are not what the figure reports. The reference must be cpc, not
imergf or imergl.

Reproduction note: this script matches the archived npz to within 4e-4 in r.
The residual is because the metric files were regenerated after the original
array was built on 2026-07-19; finite count, median, min and max are identical
and the plotted medians (0.346 whole domain, 0.515 at gauge cells) are
unchanged.

Output: temp/subdaily_lag/cpc_corr_dist.npz
"""
from pathlib import Path
import glob
import warnings

import numpy as np
import pandas as pd
import xarray as xr

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
METRICS = ROOT / "data" / "output" / "metrics_lseqmdl"
PATTERN = "idn_cli_metricssd_cpc_imergl_lseqmdl_*.nc4"
STATIONS = ROOT / "data" / "input" / "stations" / "idn_cli_weatherstation_location_bmkg.csv"
OUT = ROOT / "temp" / "subdaily_lag" / "cpc_corr_dist.npz"

files = sorted(glob.glob(str(METRICS / PATTERN)))
if len(files) != 36:
    raise SystemExit(f"expected 36 dekadal metric files, found {len(files)}")

first = xr.open_dataset(files[0], decode_timedelta=False)
lat = first["lat"].values
lon = first["lon"].values

stack = np.stack(
    [xr.open_dataset(f, decode_timedelta=False)["pearson_correlation"].values for f in files]
)
pr = np.nanmean(stack, axis=0)

st = pd.read_csv(STATIONS, sep=";", encoding="utf-8-sig")
latcol = next(c for c in st.columns if c.lower() in ("lat", "latitude"))
loncol = next(c for c in st.columns if c.lower() in ("lon", "long", "longitude"))
station_lat = st[latcol].to_numpy(dtype="float64")
station_lon = st[loncol].to_numpy(dtype="float64")

bmask = np.zeros(pr.shape, dtype=bool)
for sla, slo in zip(station_lat, station_lon):
    i = int(np.abs(lat - sla).argmin())
    j = int(np.abs(lon - slo).argmin())
    bmask[i, j] = True

np.savez(
    OUT,
    pr=pr.ravel(),
    bmask=bmask.ravel(),
    lat=lat,
    lon=lon,
    station_lat=station_lat,
    station_lon=station_lon,
)

flat = pr.ravel()
gauge = flat[bmask.ravel()]
print(
    f"wrote {OUT.name} | grid {pr.shape[0]}x{pr.shape[1]} | "
    f"finite {np.isfinite(flat).sum()} | gauge cells {bmask.sum()} of {len(station_lat)} stations"
)
print(
    f"  whole median {np.nanmedian(flat):.3f} | "
    f"gauge median {np.nanmedian(gauge[np.isfinite(gauge)]):.3f}"
)
