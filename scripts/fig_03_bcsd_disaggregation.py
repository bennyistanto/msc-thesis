"""Generate the BCSD spatial-disaggregation figure for Chapter 3 (CPC / EQM).

Answers the seminar question "how does a 0.5 deg reference correct a 0.1 deg
product?" using the real Bali subdomain. Four panels:
  (a) Grid mismatch: one CPC 0.5 deg cell spans a 5x5 block of IMERG 0.1 deg pixels.
  (b) CPC wet-day-mean rainfall fitted at native 0.5 deg (blocky).
  (c) The same parameter bilinearly disaggregated to 0.1 deg (smooth) - the
      actual src interpolate_cpc_params_to_imerg_grid output.
  (d) Per-pixel quantile mapping at one 0.1 deg pixel against its own
      interpolated CPC Gamma distribution.

The point: the CORRECTION (distribution parameters) is disaggregated, not the
data. IMERG keeps its 0.1 deg detail; only the climatological target is smoothed
from the 0.5 deg reference.

Output: paper/thesis/figures/fig_thesis_03_bcsd_disaggregation.png
"""
import os, sys, warnings
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import ListedColormap
from scipy.stats import gamma as gamma_dist
import geopandas as gpd
warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(ROOT); sys.path.insert(0, ROOT)
from src.distribution_fitting import (
    fit_cpc_parameters_on_native_grid, interpolate_cpc_params_to_imerg_grid)

D = "data/example_bali/"
FRAME = dict(xmin=114.4, xmax=115.8, ymin=-8.9, ymax=-8.0)

# Bali coastline / province outline (same source as Fig 4.8), for location sense
try:
    adm1 = gpd.read_file("data/subset/bnd/idn_bnd_adm1.shp",
                         bbox=(114.3, -8.95, 115.9, -7.95))
except Exception as e:
    print("adm1 load failed:", e); adm1 = None

# ---- data ----
# sortby lat -> all ascending. bali_mask.nc is stored lat-descending while
# bali_imergl is ascending; mixing them flips the data top-to-bottom against
# the (geographic) admin boundary. Force a single consistent orientation.
cpc05  = xr.open_dataset(D + "bali_cpcuni_native05.nc4")["precip"].sortby("lat")   # 4x6 @0.5
imergl = xr.open_dataset(D + "bali_imergl.nc4")["precipitation"].sortby("lat")     # 9x14 @0.1
mask   = xr.open_dataset(D + "bali_mask.nc")["land"].sortby("lat")                 # 9x14

# one dekad across all years (Jan dekad 1 = days 1-10), as the pipeline fits it
def dekad(da):
    t = da["time"].dt
    return da.isel(time=((t.month == 1) & (t.day >= 1) & (t.day <= 10)).values)
cpc05_dk  = dekad(cpc05)
imergl_dk = dekad(imergl)

# ---- run the REAL BCSD parameter pipeline ----
p05 = fit_cpc_parameters_on_native_grid(cpc05_dk)
p01 = interpolate_cpc_params_to_imerg_grid(p05, imergl.lat.values, imergl.lon.values)

# display parameter: wet-day mean rainfall = gamma shape * scale (mm/day)
M05 = (p05["gamma_shape"] * p05["gamma_scale"]).values                  # 4x6
M01 = (p01["gamma_shape"] * p01["gamma_scale"]).values                  # 9x14
M01 = np.where(mask.values == 1, M01, np.nan)                          # land only
vmin, vmax = np.nanmin(M01), np.nanmax(M01)

lat05, lon05 = cpc05.lat.values, cpc05.lon.values
lat01, lon01 = imergl.lat.values, imergl.lon.values
def edges(c, d):  # cell-centre array -> edge array
    return np.concatenate([[c[0] - d/2], (c[:-1] + c[1:]) / 2, [c[-1] + d/2]])
ex05, ey05 = edges(lon05, 0.5), edges(lat05, 0.5)
ex01, ey01 = edges(lon01, 0.1), edges(lat01, 0.1)

CMAP = "YlGnBu"
plt.rcParams.update({"font.size": 10})
fig, axs = plt.subplots(2, 2, figsize=(11.5, 7.6), constrained_layout=True)
a, b, c, d = axs[0, 0], axs[0, 1], axs[1, 0], axs[1, 1]

# ---- (a) grid mismatch ----
land = np.where(mask.values == 1, 1.0, np.nan)
a.pcolormesh(lon01, lat01, land, cmap=ListedColormap(["#cfe8dc"]), shading="nearest")
for x in ex01: a.axvline(x, color="0.78", lw=0.4, zorder=1)
for y in ey01: a.axhline(y, color="0.78", lw=0.4, zorder=1)
for x in ex05:
    if FRAME["xmin"] <= x <= FRAME["xmax"]: a.axvline(x, color="#b2182b", lw=1.8, zorder=4)
for y in ey05:
    if FRAME["ymin"] <= y <= FRAME["ymax"]: a.axhline(y, color="#b2182b", lw=1.8, zorder=4)
# highlight one 0.5 deg cell (centre 114.75, -8.25) = 5x5 0.1 deg pixels
a.add_patch(Rectangle((114.5, -8.5), 0.5, 0.5, fill=False, edgecolor="#b2182b",
                      lw=2.4, zorder=5))
a.text(114.75, -8.25, "1 CPC cell\n= 5x5 IMERG\npixels", ha="center", va="center",
       fontsize=8.5, zorder=6, color="#7a1620",
       bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
a.set_title("(a) Grid mismatch:\nCPC 0.5 deg (red) vs IMERG 0.1 deg", fontsize=10)

# ---- (b) params fit at 0.5 deg (blocky) ----
pm = b.pcolormesh(ex05, ey05, M05, cmap=CMAP, vmin=vmin, vmax=vmax, shading="flat")
for x in ex05:
    if FRAME["xmin"] <= x <= FRAME["xmax"]: b.axvline(x, color="0.3", lw=0.7)
for y in ey05:
    if FRAME["ymin"] <= y <= FRAME["ymax"]: b.axhline(y, color="0.3", lw=0.7)
b.set_title("(b) CPC parameters fit at 0.5 deg\n(wet-day mean rain, blocky)", fontsize=10)

# ---- (c) bilinearly disaggregated to 0.1 deg (smooth) ----
c.pcolormesh(ex01, ey01, M01, cmap=CMAP, vmin=vmin, vmax=vmax, shading="flat")
c.set_title("(c) Bilinearly disaggregated to 0.1 deg\n(smooth, no block edges)", fontsize=10)

for axx in (a, b, c):
    if adm1 is not None:
        adm1.boundary.plot(ax=axx, color="0.2", lw=0.9, zorder=3)
    axx.set_xlim(FRAME["xmin"], FRAME["xmax"]); axx.set_ylim(FRAME["ymin"], FRAME["ymax"])
    axx.set_aspect("equal")                                  # square 0.1 deg pixels
    axx.set_xlabel("Longitude (degE)", fontsize=8.5); axx.tick_params(labelsize=7.5)
a.set_ylabel("Latitude (degN)", fontsize=8.5); c.set_ylabel("Latitude (degN)", fontsize=8.5)
cb = fig.colorbar(pm, ax=[b, c], shrink=0.85, pad=0.02)
cb.set_label("wet-day mean (mm/day)", fontsize=8.5); cb.ax.tick_params(labelsize=7.5)

# ---- (d) per-pixel quantile mapping at one 0.1 deg pixel ----
li, lj = 4, 6
while not (mask.values[li, lj] == 1): lj += 1
sh, sc = p01["gamma_shape"].values[li, lj], p01["gamma_scale"].values[li, lj]
iv = imergl_dk.values[:, li, lj]; iv = iv[~np.isnan(iv)]; iwet = np.sort(iv[iv > 1.0])
Fi = np.arange(1, len(iwet) + 1) / (len(iwet) + 1)
xmax = max(iwet.max(), gamma_dist.ppf(0.99, sh, scale=sc))
xg = np.linspace(0.1, xmax, 200)
d.plot(xg, gamma_dist.cdf(xg, sh, scale=sc), color="#2166ac", lw=2.2,
       label="CPC Gamma CDF (interpolated)")
d.step(iwet, Fi, where="post", color="#b2182b", lw=1.6, label="IMERG wet-day CDF (raw)")
q = 0.6; x_im = float(np.quantile(iwet, q)); x_cpc = float(gamma_dist.ppf(q, sh, scale=sc))
d.annotate("", xy=(x_cpc, q), xytext=(x_im, q),
           arrowprops=dict(arrowstyle="-|>", color="black", lw=1.8))
d.plot([x_im, x_im], [0, q], ":", color="0.45", lw=1.0)
d.plot([x_cpc, x_cpc], [0, q], ":", color="0.45", lw=1.0)
d.text((x_im + x_cpc) / 2, q + 0.05, "map at equal $F$", ha="center", fontsize=8.5)
d.set_xlim(0, xmax); d.set_ylim(0, 1.02)
d.set_xlabel("daily rainfall (mm/day)", fontsize=8.5)
d.set_ylabel("cumulative probability", fontsize=8.5)
d.tick_params(labelsize=7.5); d.legend(fontsize=8, loc="lower right")
d.set_title("(d) Quantile mapping at one 0.1 deg pixel\nagainst its interpolated CPC distribution",
            fontsize=10)

out = "paper/thesis/figures/fig_thesis_03_bcsd_disaggregation.png"
plt.savefig(out, dpi=180)
print(f"OK: {out} ({os.path.getsize(out)//1024} KB)")
print(f"   0.5deg cells fit: {np.isfinite(M05).sum()}/{M05.size}; "
      f"0.1deg land pixels: {int((mask.values==1).sum())}; "
      f"param range {vmin:.1f}-{vmax:.1f} mm/day; QM pixel ({li},{lj}) "
      f"shape={sh:.2f} scale={sc:.2f}")
