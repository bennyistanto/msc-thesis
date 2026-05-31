"""Thesis Figure 5.3 (re-layout) - "Station Density Confidence Mask"
stacked vertically as 2 rows x 1 column:
  (a) Spatial map of the station-density confidence mask.
  (b) CQI improvement (LSEQM+DL minus LSEQM) by confidence quintile,
      a boxplot showing higher dense-station improvement than sparse.

Data:
  data/output/station_density/confidence_mask_station_density.nc4
  data/output/quality_{lseqm,lseqmdl}/*.nc4

Output: paper/thesis/figures/fig_thesis_05_confidence_mask.png
"""
import sys
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib as mpl

sys.path.insert(0, str(Path(__file__).parent))
from helpers import (
    load_boundaries, LON_RANGE, LAT_RANGE, ASPECT, FIGOUT,
)

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
DEKADS = [(m, d) for m in range(1, 13) for d in ("01", "11", "21")]


def load_cqi_clim(stage):
    files = []
    for month, dekad in DEKADS:
        fp = ROOT / "data" / "output" / f"quality_{stage}" / \
             f"idn_cli_qualitysd_cpc_imergl_{stage}_month{month:02d}_dekad{dekad}.nc4"
        if fp.exists():
            files.append(fp)
    stack = []
    for fp in files:
        with xr.open_dataset(fp) as ds:
            stack.append(ds["continuous_quality"].values)
    return np.nanmean(np.stack(stack, axis=0), axis=0), files[0]


print("Loading confidence mask...")
with xr.open_dataset(ROOT / "data/output/station_density/confidence_mask_station_density.nc4") as ds:
    conf = ds["confidence"].values
    lon = ds.lon.values
    lat = ds.lat.values

print("Loading CQI for LSEQM and LSEQM+DL...")
cqi_lseqm, _ = load_cqi_clim("lseqm")
cqi_dl, _ = load_cqi_clim("lseqmdl")
delta_dl = cqi_dl - cqi_lseqm

# Quintile bins on confidence, only where both fields are valid and conf > 0
valid = np.isfinite(conf) & np.isfinite(delta_dl)
quintile_edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
quintile_labels = ["0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
groups = []
for lo, hi in zip(quintile_edges[:-1], quintile_edges[1:]):
    sel = valid & (conf >= lo) & (conf < hi if hi < 1.0 else conf <= hi)
    groups.append(delta_dl[sel])
print("  quintile sample sizes:", [g.size for g in groups])

idn, wld = load_boundaries()

# Layout: 2 rows. Row 1 = map (~5.5x2.0 in). Row 2 = boxplot (~5.5x2.5 in).
text_width_in = 14.0 * 0.3937       # 5.51 in
map_h_in = text_width_in / ASPECT    # ~2.05 in
fig_h = map_h_in + 2.8 + 1.0
fig = plt.figure(figsize=(text_width_in, fig_h))
gs = fig.add_gridspec(2, 1, height_ratios=[map_h_in, 2.6],
                       left=0.10, right=0.96, top=0.93, bottom=0.10, hspace=0.55)
ax_map = fig.add_subplot(gs[0, 0])
ax_box = fig.add_subplot(gs[1, 0])

# (a) confidence mask map
cmap_a = mpl.colormaps["YlOrRd"].copy()
cmap_a.set_under("#f5f5f5")    # near-zero confidence shaded very pale
norm_a = mpl.colors.Normalize(vmin=0.001, vmax=1.0)
qm = ax_map.pcolormesh(lon, lat, conf, cmap=cmap_a, norm=norm_a,
                        shading="nearest", rasterized=True)
if wld is not None:
    wld.boundary.plot(ax=ax_map, color="0.55", linewidth=0.25, zorder=2)
if idn is not None:
    idn.boundary.plot(ax=ax_map, color="0.20", linewidth=0.30, zorder=3)
ax_map.set_xlim(*LON_RANGE); ax_map.set_ylim(*LAT_RANGE); ax_map.set_aspect("equal")
ax_map.set_xticks([100, 110, 120, 130, 140]); ax_map.set_yticks([-10, -5, 0, 5])
ax_map.set_xticklabels([f"{x}E" for x in [100, 110, 120, 130, 140]], fontsize=6)
ax_map.set_yticklabels([f"{y}" + ("N" if y >= 0 else "S") for y in [-10, -5, 0, 5]], fontsize=6)
ax_map.tick_params(labelsize=6, length=1.5, pad=1)
ax_map.set_title("(a) Station Density Confidence Mask",
                  fontsize=9, fontweight="bold", pad=2)

bbox = ax_map.get_position()
cax = fig.add_axes([bbox.x0 + 0.18, bbox.y0 - 0.045,
                     bbox.width - 0.36, 0.012])
cbar = fig.colorbar(qm, cax=cax, orientation="horizontal", extend="min")
cbar.set_label("Confidence", fontsize=7)
cbar.ax.tick_params(labelsize=6)

# (b) box-and-whisker of delta CQI by confidence quintile
positions = np.arange(len(groups))
bp = ax_box.boxplot(groups, positions=positions, widths=0.55, patch_artist=True,
                     showfliers=False,
                     medianprops=dict(color="black", linewidth=1.0),
                     whiskerprops=dict(linewidth=0.7, color="0.3"),
                     capprops=dict(linewidth=0.7, color="0.3"))
quintile_colors = ["#fff5b8", "#fee08b", "#fdae61", "#f46d43", "#d73027"]
for patch, c in zip(bp["boxes"], quintile_colors):
    patch.set_facecolor(c)
    patch.set_edgecolor("0.3")

ax_box.axhline(0.0, color="0.4", linestyle="--", linewidth=0.7)
ax_box.set_xticks(positions)
ax_box.set_xticklabels(quintile_labels, fontsize=8)
ax_box.set_xlabel("Confidence Quintile", fontsize=9)
ax_box.set_ylabel(r"$\Delta$ CQI (LSEQM+DL $-$ LSEQM)", fontsize=9)
ax_box.set_title("(b) CQI Improvement by Confidence Quintile",
                  fontsize=9, fontweight="bold", pad=2)
ax_box.grid(axis="y", alpha=0.3, linestyle=":")

fig.suptitle("Station Density Confidence Mask and CQI Improvement",
             fontsize=10, fontweight="bold", y=0.99)

OUT = FIGOUT / "fig_thesis_05_confidence_mask.png"
fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
