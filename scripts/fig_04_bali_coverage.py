"""Generate the Bali subdomain data-coverage map for Chapter 4 §4.9.

Shows the 9x14 IMERG-L grid over Bali: land pixels (corrected) vs
ocean-masked pixels, the 4 BMKG validation stations, and the Bali
coastline clipped from the Indonesia admin boundaries. The backdrop is
the long-term mean IMERG-L daily precipitation, which visualises the
data coverage of the subdomain.

Output: paper/thesis/figures/fig_thesis_04_bali_coverage.png
"""
import os
import warnings
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import geopandas as gpd

warnings.filterwarnings("ignore")
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

D = "data/example_bali/"
BBOX = dict(lon=(114.45, 115.75), lat=(-8.85, -8.05))

# ----- data -----
mask = xr.open_dataset(D + "bali_mask.nc")["land"]            # 9x14, 1=land NaN=ocean
imergl = xr.open_dataset(D + "bali_imergl.nc4")["precipitation"]
mean_pr = imergl.mean("time")                                  # long-term daily mean

# stations (semicolon-delimited single column)
st = pd.read_csv(D + "bali_stations_location.csv", sep=";")
st.columns = [c.strip() for c in st.columns]
slon = st["Lon"].astype(float).values
slat = st["Lat"].astype(float).values
sname = st["Station"].astype(str).values

# admin boundaries, clipped to a small frame around Bali
frame = dict(xmin=114.3, ymin=-8.95, xmax=115.9, ymax=-7.95)
try:
    adm1 = gpd.read_file("data/subset/bnd/idn_bnd_adm1.shp", bbox=tuple(frame.values()))
except Exception as e:
    print("adm1 load failed:", e)
    adm1 = None

# ----- figure -----
fig, ax = plt.subplots(figsize=(9, 5.6))

lon = mask.lon.values
lat = mask.lat.values
mk = mask.values                         # (9, 14), 1=land NaN=ocean
# Show DOMAIN COVERAGE from the land-sea mask (complete), not the
# precipitation mean (which has gaps in the NW). Land pixels = filled,
# ocean = white.
land_layer = np.where(mk == 1, 1.0, np.nan)
from matplotlib.colors import ListedColormap
ax.pcolormesh(lon, lat, land_layer, cmap=ListedColormap(["#4C9F70"]),
              shading="nearest", alpha=0.85)

# 0.1-degree grid lines on pixel edges
dx = 0.1
for x in np.arange(lon.min() - dx/2, lon.max() + dx, dx):
    ax.axvline(x, color="0.7", lw=0.4, zorder=1)
for y in np.arange(lat.min() - dx/2, lat.max() + dx, dx):
    ax.axhline(y, color="0.7", lw=0.4, zorder=1)

# coastline / province boundary
if adm1 is not None:
    adm1.boundary.plot(ax=ax, color="0.25", lw=0.9, zorder=3)

# stations
ax.scatter(slon, slat, s=90, marker="^", facecolor="crimson",
           edgecolor="white", linewidth=0.8, zorder=5,
           label="BMKG validation station (4)")
for x, y, n in zip(slon, slat, sname):
    short = n.replace("Stasiun ", "").replace("Pos Pengamatan ", "")
    ax.annotate(short, (x, y), textcoords="offset points", xytext=(6, 4),
                fontsize=7, color="black", zorder=6)

ax.set_xlim(frame["xmin"], frame["xmax"])
ax.set_ylim(frame["ymin"], frame["ymax"])
ax.set_xlabel("Longitude (degE)", fontsize=9)
ax.set_ylabel("Latitude (degN)", fontsize=9)
ax.tick_params(labelsize=8)

n_land = int((mask.values == 1).sum())
n_tot = mask.values.size
ax.set_title(f"Bali reproducibility subdomain: {mask.sizes['lat']} x "
             f"{mask.sizes['lon']} grid at 0.1 deg, "
             f"{n_land} land / {n_tot - n_land} ocean-masked pixels",
             fontsize=10.5, pad=8)
from matplotlib.patches import Patch
land_handle = Patch(facecolor="#4C9F70", alpha=0.85,
                    label=f"Land pixel ({n_land})")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles=[land_handle] + handles, loc="lower left",
          fontsize=8, framealpha=0.92)

out = "paper/thesis/figures/fig_thesis_04_bali_coverage.png"
plt.tight_layout()
plt.savefig(out, dpi=180, bbox_inches="tight")
print(f"OK: {out} ({os.path.getsize(out)//1024} KB); land={n_land}/{n_tot}, stations={len(st)}")
