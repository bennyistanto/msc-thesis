"""Thesis Figure 4.4 (re-layout) - "CQI Spatial Distribution by Method"
stacked vertically as 3 rows x 1 column (LS / LSEQM / LSEQM+DL).

Reuses scripts/helpers.py (Indonesia adm1 + world adm0 boundary style).

Data: data/output/quality_{stage}/idn_cli_qualitysd_*.nc4
      (variable continuous_quality, 171 x 461 grid). Averaged across 36 dekads.

Output: paper/thesis/figures/fig_thesis_04_cqi_spatial.png
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

STAGES = [
    ("ls",      "LS"),
    ("lseqm",   "LSEQM"),
    ("lseqmdl", "LSEQM+DL"),
]


def load_cqi_climatology(stage):
    """Mean continuous_quality across all 36 dekads for one stage."""
    files = []
    for month, dekad in DEKADS:
        fp = ROOT / "data" / "output" / f"quality_{stage}" / \
             f"idn_cli_qualitysd_cpc_imergl_{stage}_month{month:02d}_dekad{dekad}.nc4"
        if fp.exists():
            files.append(fp)
    if not files:
        raise FileNotFoundError(f"no quality NetCDFs for {stage}")
    stack = []
    for fp in files:
        with xr.open_dataset(fp) as ds:
            stack.append(ds["continuous_quality"].values)
    arr = np.stack(stack, axis=0)
    return np.nanmean(arr, axis=0), files[0]


print("Loading CQI climatology for the 3 correction stages...")
cqi_maps = {}
for stage, _ in STAGES:
    print(f"  {stage}...", end=" ")
    cqi_maps[stage], sample_path = load_cqi_climatology(stage)
    print(f"median={np.nanmedian(cqi_maps[stage]):.3f}")

# Read lat/lon from one sample file
with xr.open_dataset(sample_path) as ds:
    lon = ds.lon.values
    lat = ds.lat.values

idn, wld = load_boundaries()

# CQI colormap: RdYlGn (red bad, green good), 0..1
cmap = mpl.colormaps["RdYlGn"].copy()
norm = mpl.colors.Normalize(vmin=0, vmax=1)

# Portrait 3 rows x 1 col. Each row's map fills full text width.
# Text width = 14 cm; map height = width / aspect (~5.2 cm). With 3 stacked,
# vertical content ~16 cm + headings. Fits comfortably on one A4 page.
text_width_in = 14.0 * 0.3937       # 5.51 in
panel_h_in = text_width_in / ASPECT  # ~2.05 in
fig_h = 3 * panel_h_in + 1.2          # add 1.2 in for title/colorbar/gaps
fig, axes = plt.subplots(3, 1, figsize=(text_width_in, fig_h),
                          constrained_layout=False)
plt.subplots_adjust(left=0.08, right=0.96, top=0.94, bottom=0.10,
                    hspace=0.18)

last_qm = None
for ax, (stage, label) in zip(axes, STAGES):
    qm = ax.pcolormesh(lon, lat, cqi_maps[stage], cmap=cmap, norm=norm,
                        shading="nearest", rasterized=True)
    last_qm = qm
    if wld is not None:
        wld.boundary.plot(ax=ax, color="0.55", linewidth=0.25, zorder=2)
    if idn is not None:
        idn.boundary.plot(ax=ax, color="0.20", linewidth=0.30, zorder=3)
    ax.set_xlim(*LON_RANGE)
    ax.set_ylim(*LAT_RANGE)
    ax.set_aspect("equal")
    ax.set_xticks([100, 110, 120, 130, 140])
    ax.set_yticks([-10, -5, 0, 5])
    ax.tick_params(labelsize=6, length=1.5, pad=1)
    ax.set_xticklabels([f"{x}E" for x in [100, 110, 120, 130, 140]], fontsize=6)
    ax.set_yticklabels([f"{y}" + ("N" if y >= 0 else "S") for y in [-10, -5, 0, 5]], fontsize=6)
    ax.set_title(f"{label} (median CQI = {np.nanmedian(cqi_maps[stage]):.3f})",
                 fontsize=9, fontweight="bold", pad=2)

# Bottom horizontal colorbar
cax = fig.add_axes([0.20, 0.045, 0.60, 0.015])
cbar = fig.colorbar(last_qm, cax=cax, orientation="horizontal")
cbar.set_label("Composite Quality Index (CQI)", fontsize=8)
cbar.ax.tick_params(labelsize=6)

fig.suptitle("CQI Spatial Distribution by Method (climatology, 36 dekads)",
             fontsize=10, fontweight="bold", y=0.99)

OUT = FIGOUT / "fig_thesis_04_cqi_spatial.png"
fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
