"""Thesis Figure 5.4 - Per-station peak hour offset across Indonesia and
the per-station r lift.

Two-row stacked layout for the thesis (single-column page):
  (a) Geographic distribution of the per-station peak offset h* across
      Indonesia, plotted on the ADM0 boundary with the three timezone
      band dividers (112.5, 127.5).
  (b) Per-station dumbbell connector: r at h=0 (UTC day) versus r at h*
      (per-station peak), with the median lift in r reported.

Data:
  temp/subdaily_lag/subdaily_lag_results.npz (precomputed by
  temp/subdaily_lag/build_subdaily_lag.py from half-hourly IMERG-L
  GPM_3IMERGHH_07 vs BMKG daily gauges, January 2020).
  data/downloads/boundary/adm0_polygons.gpkg (Indonesia + neighbours).

Output: paper/thesis/figures/fig_thesis_05_subdaily_map.png
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import geopandas as gpd

ROOT  = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
NPZ   = ROOT / "temp" / "subdaily_lag" / "subdaily_lag_results.npz"
FIGOUT = ROOT / "paper" / "thesis" / "figures"
OUT   = FIGOUT / "fig_thesis_05_subdaily_map.png"
# Same boundary style as the other thesis figures (helpers.load_boundaries):
#   Indonesia adm1 (provinces) thin dark + world adm0 (neighbours) thin grey.
IDN_ADM1 = ROOT / "data" / "subset" / "bnd" / "idn_bnd_adm1.shp"
WLD_ADM0 = ROOT / "data" / "subset" / "bnd" / "wld_bnd_adm0.shp"
BBOX = (94.5, -11.2, 141.5, 6.2)   # Indonesia bbox + small padding

d = np.load(NPZ, allow_pickle=True)
hour_shifts = d["hour_shifts"]
R_per_st    = d["R_per_station"]
sl_st  = d["slider_stations"]
sl_lon = d["slider_lon"]
sl_lat = d["slider_lat"]

# Align main R_per_st to slider station order
lookup = {s: i for i, s in enumerate(sl_st)}
idx = np.array([lookup.get(s, -1) for s in d["stations"]])
keep = np.where(idx >= 0)[0]
R_kept = R_per_st[:, keep]
lon_v  = sl_lon[idx[keep]]
lat_v  = sl_lat[idx[keep]]
valid = np.isfinite(R_kept).any(axis=0)
peak_h_per = np.full(R_kept.shape[1], np.nan)
peak_h_per[valid] = hour_shifts[np.nanargmax(R_kept[:, valid], axis=0)]
peak_r_per = np.full(R_kept.shape[1], np.nan)
peak_r_per[valid] = np.nanmax(R_kept[:, valid], axis=0)
r_at_zero = R_kept[hour_shifts == 0][0]

fig = plt.figure(figsize=(8.0, 9.0))
gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.05], hspace=0.28,
                        left=0.08, right=0.96, top=0.95, bottom=0.07)
ax = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[1, 0])

# --- Top: map ---
# Neighbour countries filled light grey; Indonesia adm1 drawn over white.
idn_adm1 = gpd.read_file(IDN_ADM1, bbox=BBOX)
world_adm0 = gpd.read_file(WLD_ADM0, bbox=BBOX)
neighbours = world_adm0[world_adm0["iso_3"] != "IDN"]
ax.set_facecolor("white")
neighbours.plot(ax=ax, facecolor="#e6e6e6", edgecolor="0.55",
                 linewidth=0.25, zorder=1)
idn_adm1.boundary.plot(ax=ax, color="0.20", linewidth=0.30, zorder=2)
for x in (112.5, 127.5):
    ax.axvline(x, color="0.45", linestyle="--", linewidth=0.7, zorder=3)
ax.text(103.5, 7.4, "WIB (UTC+7)",  ha="center", fontsize=8, color="0.30")
ax.text(120.0, 7.4, "WITA (UTC+8)", ha="center", fontsize=8, color="0.30")
ax.text(134.5, 7.4, "WIT (UTC+9)",  ha="center", fontsize=8, color="0.30")

cmap = plt.get_cmap("RdYlBu_r")
norm = mpl.colors.Normalize(vmin=-28, vmax=-12)
sc = ax.scatter(lon_v[valid], lat_v[valid], c=peak_h_per[valid],
                 cmap=cmap, norm=norm, s=14, edgecolors="black",
                 linewidths=0.20, zorder=4)
ax.set_xlim(94, 142); ax.set_ylim(-12, 8.5)
ax.set_aspect("equal")
ax.set_xlabel("Longitude", fontsize=9.5)
ax.set_ylabel("Latitude", fontsize=9.5)
ax.set_title("(a) Per-station peak hour offset $h^{\\star}$",
              fontsize=10.5, fontweight="bold", loc="left", pad=4)
cb = fig.colorbar(sc, ax=ax, shrink=0.85, pad=0.02, aspect=22)
cb.set_label("$h^{\\star}$ (hours)", fontsize=9)
cb.ax.tick_params(labelsize=8)
ax.grid(True, alpha=0.25, linestyle=":")

ax.text(94.5, -10.8,
         f"Median $h^{{\\star}} = {int(np.nanmedian(peak_h_per)):+d}$ h  |  "
         f"IQR = [{int(np.nanpercentile(peak_h_per,25)):+d}, "
         f"{int(np.nanpercentile(peak_h_per,75)):+d}]",
         fontsize=8.5, color="0.15",
         bbox=dict(boxstyle="round,pad=0.30", facecolor="#fff7d6",
                    edgecolor="0.55", linewidth=0.6, alpha=0.97))

# --- Bottom: per-station lift connector ---
n = R_kept.shape[1]
ord_idx = np.argsort(np.nan_to_num(r_at_zero, nan=-1))
y = np.arange(n)
ax2.hlines(y, r_at_zero[ord_idx], peak_r_per[ord_idx],
            colors="0.75", linewidth=0.6, zorder=1)
ax2.scatter(r_at_zero[ord_idx], y, c="#d62728", s=9,
             label="$r$ at $h = 0$ (UTC day)", zorder=3)
ax2.scatter(peak_r_per[ord_idx], y, c="#1f77b4", s=9,
             label="$r$ at $h = h^{\\star}$ (per-station peak)",
             zorder=3)
ax2.axvline(0.34, color="0.40", linestyle=":", linewidth=1.0)
ax2.text(0.36, 1, "thesis headline $r \\approx 0.34$",
          fontsize=8, color="0.30", va="bottom", style="italic")
ax2.set_xlim(-0.05, 1.0)
ax2.set_ylim(-1, n)
ax2.set_yticks([])
ax2.set_xlabel("Pearson $r$ (January 2020)", fontsize=9.5)
ax2.set_title("(b) Per-station lift: $r$ at $h = 0$ vs at $h = h^{\\star}$",
               fontsize=10.5, fontweight="bold", loc="left", pad=4)

median_lift_val = float(np.nanmedian(peak_r_per - r_at_zero))
ax2.text(0.02, 0.98,
          f"median lift $\\Delta r$ = {median_lift_val:+.2f}\n"
          f"(half-hourly, January 2020, $n = {int(valid.sum())}$ stations)",
          transform=ax2.transAxes,
          fontsize=8.5, color="0.10", ha="left", va="top",
          bbox=dict(boxstyle="round,pad=0.30", facecolor="#fff7d6",
                    edgecolor="0.55", linewidth=0.6, alpha=0.97))
ax2.legend(loc="lower right", fontsize=8.5, frameon=True,
            framealpha=0.95, edgecolor="0.7")
ax2.grid(True, alpha=0.25, linestyle=":", axis="x")

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
