"""Thesis Figure 3.1 (replacement) - Study-area data coverage.

Shows, over Indonesia (admin-1 provinces + neighbouring-country admin-0
boundaries):
  - the IMERG-L 0.1 deg land footprint (fine light-blue fill from the ISO3
    land mask, so every habitable and uninhabitable island that carries a
    corrected pixel is visible);
  - the CPC-UNI 0.5 deg native calibration grid overlaid as coarse cell
    outlines (each cell spans ~25 IMERG pixels, so the cells spill past the
    fine coastline - the resolution gap the 0.5->0.1 disaggregation closes);
  - the 180 BMKG validation stations coloured by region;
  - an information box with the pixel/cell/station counts.

Rendered landscape; placed on a portrait page via a sideways (rotated 90)
figure in the thesis, like the workflow figure.

Output: paper/thesis/figures/fig_thesis_03_coverage.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
DATA = ROOT / "data"
FIGOUT = ROOT / "paper" / "thesis" / "figures"

LON_RANGE = (94.5, 141.5)
LAT_RANGE = (-11.2, 6.2)

# ----- IMERG-L 0.1 deg land footprint (from ISO3 mask) -----
mask = xr.open_dataset(DATA / "mask" / "iso3" / "idn_subset.nc")["land"]
mlat = mask["lat"].values
mlon = mask["lon"].values
mland = np.asarray(mask.values) > 0
n_imerg = int(mland.sum())

# ----- CPC-UNI 0.5 deg native grid; cells overlapping Indonesian land -----
cpc = xr.open_dataset(DATA / "input" / "cpcuni" / "idn_cpcuni_native05.nc4")
clat = cpc["lat"].values
clon = cpc["lon"].values
La, Lo = np.where(mland)
ci = np.abs(clat[None, :] - mlat[La][:, None]).argmin(axis=1)
cj = np.abs(clon[None, :] - mlon[Lo][:, None]).argmin(axis=1)
land_cells = sorted(set(zip(ci.tolist(), cj.tolist())))
n_cpc = len(land_cells)

# ----- boundaries -----
bbox = (LON_RANGE[0], LAT_RANGE[0], LON_RANGE[1], LAT_RANGE[1])
idn1 = gpd.read_file(DATA / "subset" / "bnd" / "idn_bnd_adm1.shp", bbox=bbox)
wld = gpd.read_file(DATA / "subset" / "bnd" / "wld_bnd_adm0.shp", bbox=bbox)

# ----- BMKG stations (semicolon-delimited) -----
st = pd.read_csv(DATA / "input" / "stations" /
                 "idn_cli_weatherstation_location_bmkg.csv", sep=";")
st.columns = [c.strip().lstrip("﻿") for c in st.columns]
n_st = len(st)
REGIONS = ["Sumatra", "Kalimantan", "Sulawesi", "Jawa",
           "Bali Nusra", "Maluku", "Papua"]
present = [r for r in REGIONS if r in set(st["region"])]
present += [r for r in sorted(set(st["region"])) if r not in present]
PAL = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3",
       "#ff7f00", "#a65628", "#f781bf", "#999999"]
rcolor = {r: PAL[i % len(PAL)] for i, r in enumerate(present)}

print(f"IMERG-L 0.1deg land pixels: {n_imerg}")
print(f"CPC-UNI 0.5deg land cells : {n_cpc}  (~{n_imerg/n_cpc:.0f} IMERG px each)")
print(f"BMKG stations             : {n_st}  regions={present}")

# ============================ figure ============================
fig, ax = plt.subplots(figsize=(12.5, 5.0))
plt.subplots_adjust(left=0.045, right=0.995, top=0.985, bottom=0.06)

# (1) IMERG 0.1 deg land footprint
ax.pcolormesh(mlon, mlat, np.where(mland, 1.0, np.nan),
              cmap=ListedColormap(["#cfe6ff"]), shading="nearest", zorder=1)

# (2) CPC 0.5 deg native land cells as coarse outlines
rects = [Rectangle((clon[j] - 0.25, clat[i] - 0.25), 0.5, 0.5)
         for i, j in land_cells]
ax.add_collection(PatchCollection(rects, facecolor="none", edgecolor="#c86400",
                                  linewidth=0.35, zorder=2))

# (3) boundaries: neighbours (grey), Indonesia provinces (dark)
wld.boundary.plot(ax=ax, color="0.55", linewidth=0.3, zorder=3)
idn1.boundary.plot(ax=ax, color="0.25", linewidth=0.35, zorder=4)

# (4) BMKG stations by region
for r in present:
    s = st[st["region"] == r]
    ax.scatter(s["Lon"], s["Lat"], s=9, c=rcolor[r], edgecolors="black",
               linewidths=0.25, zorder=5, label=r)

ax.set_xlim(*LON_RANGE)
ax.set_ylim(*LAT_RANGE)
ax.set_aspect("equal")
ax.set_xticks([100, 110, 120, 130, 140])
ax.set_yticks([-10, -5, 0, 5])
ax.set_xticklabels([f"{x}$^\\circ$E" for x in [100, 110, 120, 130, 140]], fontsize=7)
ax.set_yticklabels([f"{abs(y)}$^\\circ$" + ("N" if y >= 0 else "S")
                    for y in [-10, -5, 0, 5]], fontsize=7)
ax.tick_params(length=2, pad=1)

# (5) information box (top-left, over the empty NW ocean corner)
info = (f"Domain: $95$-$141^\\circ$E, $11^\\circ$S-$6^\\circ$N\n"
        f"IMERG-L  $0.1^\\circ$ (~$11$ km): {n_imerg:,} land pixels\n"
        f"CPC-UNI  $0.5^\\circ$ (~$55$ km): {n_cpc:,} land cells\n"
        f"   ($0.5^\\circ$ cell $= 5\\times5 = 25$ IMERG pixels)\n"
        f"BMKG stations: {n_st} ({len(present)} regions)")
ax.text(0.988, 0.97, info, transform=ax.transAxes, ha="right", va="top",
        fontsize=7.2, family="monospace",
        bbox=dict(facecolor="white", edgecolor="0.6",
                  boxstyle="round,pad=0.4", alpha=0.92), zorder=6)

# region legend (bottom, horizontal)
handles = [Line2D([0], [0], marker="o", linestyle="", markersize=5,
                  markerfacecolor=rcolor[r], markeredgecolor="black",
                  markeredgewidth=0.3, label=r) for r in present]
handles += [
    Line2D([0], [0], marker="s", linestyle="", markersize=6,
           markerfacecolor="#cfe6ff", markeredgecolor="none",
           label="IMERG-L $0.1^\\circ$ footprint"),
    Line2D([0], [0], marker="s", linestyle="", markersize=6,
           markerfacecolor="none", markeredgecolor="#c86400",
           label="CPC-UNI $0.5^\\circ$ cell"),
]
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.145),
          ncol=len(handles), fontsize=6.6, frameon=False,
          handletextpad=0.3, columnspacing=1.0)

OUT = FIGOUT / "fig_thesis_03_coverage.png"
fig.savefig(OUT, dpi=220, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
