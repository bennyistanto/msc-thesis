"""Appendix Figure G.4 - Station-overlay maps for dekad-1 January climatology.

Layout: portrait, 2 rows x 2 cols.
  (a) CPC-UNI   (b) IMERG-L
  (c) LSEQM+DL  (d) IMERG-F

Each panel overlays the BMKG stations as triangles coloured by their own
dekad-1-January climatological mean.

Output: paper/thesis/figures/fig_thesis_G5_station_overlay.png
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap

sys.path.insert(0, str(Path(__file__).parent))
from helpers import (
    draw_panel, setup_panel_grid, add_horizontal_colorbar,
    load_boundaries, load_corrected_dekad, load_raw, precip_var,
    FIGOUT, DATA,
)

# Brighter discrete cmap (turbo-derived) so station triangles contrast
# strongly with the background. 8 bins matching mean_bounds below.
_turbo = plt.get_cmap("turbo")
MEAN_BOUNDS = [0, 1, 2, 5, 10, 15, 20, 30, 50]
MEAN_CMAP = ListedColormap([_turbo(x) for x in np.linspace(0.10, 0.95, len(MEAN_BOUNDS) - 1)])
MEAN_CMAP.set_over(_turbo(0.99))
MEAN_NORM = BoundaryNorm(MEAN_BOUNDS, ncolors=MEAN_CMAP.N + 1, extend="max")

MONTH, DEKAD = 1, "01"


def dekad_filter(ds, m, d_token):
    """Return mean over Jan 1-10 across all years in the dataset."""
    da = precip_var(ds)
    sub = da.where(da.time.dt.month == m, drop=True)
    day_start = int(d_token)
    sub = sub.where((sub.time.dt.day >= day_start)
                    & (sub.time.dt.day <= day_start + 9), drop=True)
    return sub.mean("time")

print("Loading products and computing dekadal climatology...")
ds_cpc    = load_raw("cpcuni")
ds_imergl = load_raw("imergl")
ds_imergf = load_raw("imergf")
ds_lsdl   = load_corrected_dekad("lseqmdl", MONTH, DEKAD)

cpc_mean    = dekad_filter(ds_cpc,    MONTH, DEKAD)
imergl_mean = dekad_filter(ds_imergl, MONTH, DEKAD)
imergf_mean = dekad_filter(ds_imergf, MONTH, DEKAD)
# corrected NetCDF is already restricted to the dekad window
lsdl_mean = precip_var(ds_lsdl).mean("time")

# BMKG stations (wide-format daily data)
print("Loading BMKG stations and computing dekad-1-Jan mean...")
loc = pd.read_csv(DATA / "input" / "stations" / "idn_cli_weatherstation_location_bmkg.csv", sep=";")
loc.columns = [c.strip().lstrip("﻿") for c in loc.columns]
loc["ID_WMO"] = loc["ID_WMO"].astype(str).str.strip()

data_wide = pd.read_csv(DATA / "input" / "stations" / "idn_cli_weatherstation_data_bmkg.csv")
data_wide["Date"] = pd.to_datetime(data_wide["Date"], format="%d-%m-%Y", errors="coerce")
mask = (data_wide["Date"].dt.month == MONTH) & (data_wide["Date"].dt.day.between(1, 10))
data_wide = data_wide[mask]
station_cols = [c for c in data_wide.columns if c not in ("ID", "Date", "JD")]
sub = data_wide[station_cols].apply(pd.to_numeric, errors="coerce")
sub = sub.where(sub < 8000)
station_mean = sub.mean(axis=0).rename("mean_mm")
station_mean.index = station_mean.index.astype(str).str.strip()
station_mean = station_mean.dropna()
df = loc.merge(station_mean, left_on="ID_WMO", right_index=True, how="inner")
print(f"  {len(df)} stations with dekad-1-Jan climatological mean")

lon = ds_cpc.lon.values
lat = ds_cpc.lat.values
idn, wld = load_boundaries()

fig, axes = setup_panel_grid(
    rows=2, cols=2,
    suptitle="Dekad-1-January climatology with BMKG stations overlaid",
)

panels = [
    (axes[0, 0], cpc_mean,    "(a) CPC-UNI"),
    (axes[0, 1], imergl_mean, "(b) IMERG-L"),
    (axes[1, 0], lsdl_mean,   "(c) LSEQM+DL"),
    (axes[1, 1], imergf_mean, "(d) IMERG-F"),
]

qm = None
for i, (ax, field, title) in enumerate(panels):
    qm = draw_panel(ax, lon, lat, field.values, cmap=MEAN_CMAP,
                    norm=MEAN_NORM, idn_adm1=idn, world_adm0=wld,
                    title=title, title_fontsize=7,
                    show_y_ticklabels=(i % 2 == 0))
    ax.scatter(df["Lon"].astype(float), df["Lat"].astype(float),
               c=df["mean_mm"].astype(float), cmap=MEAN_CMAP, norm=MEAN_NORM,
               edgecolors="black", linewidths=0.15, marker="^", s=8, zorder=5)

add_horizontal_colorbar(
    fig, qm,
    "Dekad-1-January mean precip. (mm/day); triangles = BMKG station means",
    ticks=MEAN_BOUNDS,
)

out = FIGOUT / "fig_thesis_G5_station_overlay.png"
fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.05)
print(f"  wrote {out} ({out.stat().st_size//1024} KB)")
