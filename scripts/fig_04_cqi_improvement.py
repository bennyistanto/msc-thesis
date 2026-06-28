"""Thesis Figure 4.5 (re-layout) - "CQI Improvement from Hybrid Bias
Correction" stacked vertically as 2 rows x 1 column:
  (a) Per-pixel CQI change LSEQM+DL minus LS (continuous ΔCQI map,
      Gaussian-smoothed sigma=1.5 to match the original figure).
  (b) LSEQM+DL Quality Category map.

Both averaged across 36 dekads. Bin edges, colormap, and smoothing
mirror temp/figure_regen/regen_fig08_cqi_improvement_1x2.py so the
data interpretation is unchanged from the seminar/MDPI version.

Output: paper/thesis/figures/fig_thesis_04_cqi_improvement.png
"""
import sys
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import BoundaryNorm, ListedColormap
from scipy.ndimage import gaussian_filter

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


print("Loading CQI climatology for LS and LSEQM+DL...")
cqi_ls, sample = load_cqi_clim("ls")
cqi_dl, _ = load_cqi_clim("lseqmdl")

with xr.open_dataset(sample) as ds:
    lon = ds.lon.values
    lat = ds.lat.values

delta_raw = cqi_dl - cqi_ls

# Gaussian-smoothed ΔCQI for panel (a) - matches the seminar figure.
nan_mask = ~np.isfinite(delta_raw)
filled = np.where(nan_mask, 0.0, delta_raw)
weight = np.where(nan_mask, 0.0, 1.0)
sm_diff = gaussian_filter(filled, sigma=1.5)
sm_weight = gaussian_filter(weight, sigma=1.5)
sm_weight[sm_weight == 0] = 1.0
delta = sm_diff / sm_weight
delta[nan_mask] = np.nan

# Stats use the RAW delta (not smoothed) - matches the original.
n_total = np.isfinite(delta_raw).sum()
n_pos = (delta_raw > 0.01).sum()
n_neg = (delta_raw < -0.01).sum()
mean_delta = float(np.nanmean(delta_raw))
print(f"  delta CQI > +0.01: {100 * n_pos / n_total:.1f}%")
print(f"  delta CQI < -0.01: {100 * n_neg / n_total:.1f}%")
print(f"  mean delta CQI:    {mean_delta:+.3f}")

# (a) divergent colormap centred on zero
norm_a = mpl.colors.TwoSlopeNorm(vmin=-0.15, vcenter=0.0, vmax=0.15)
cmap_a = mpl.colormaps["RdBu"].copy()

# (b) Category bins and colours mirror the seminar/MDPI figure:
#     Poor <0.30, Marginal 0.30-0.40, Fair-L 0.40-0.50,
#     Fair-H 0.50-0.60, Good 0.60-0.70, Excel. >=0.70.
#     Same 6-tier RdYlGn-style palette as the original.
CAT_EDGES = [0.0, 0.30, 0.40, 0.50, 0.60, 0.70, 1.001]
CAT_LABELS = ["Poor", "Marg.", "Fair-L", "Fair-H", "Good", "Excel."]
CAT_COLORS = ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#91cf60", "#1a9850"]
cmap_b = ListedColormap(CAT_COLORS)
norm_b = BoundaryNorm(CAT_EDGES, ncolors=len(CAT_COLORS))

idn, wld = load_boundaries()

text_width_in = 14.0 * 0.3937       # 5.51 in
panel_h_in = text_width_in / ASPECT  # ~2.05 in
fig_h = 2 * panel_h_in + 1.6
fig, axes = plt.subplots(2, 1, figsize=(text_width_in, fig_h),
                          constrained_layout=False)
plt.subplots_adjust(left=0.08, right=0.96, top=0.93, bottom=0.10,
                    hspace=0.30)


def draw_map(ax, field, *, cmap, norm, title):
    qm = ax.pcolormesh(lon, lat, field, cmap=cmap, norm=norm,
                       shading="nearest", rasterized=True)
    if wld is not None:
        wld.boundary.plot(ax=ax, color="0.55", linewidth=0.25, zorder=2)
    if idn is not None:
        idn.boundary.plot(ax=ax, color="0.20", linewidth=0.30, zorder=3)
    ax.set_xlim(*LON_RANGE); ax.set_ylim(*LAT_RANGE); ax.set_aspect("equal")
    ax.set_xticks([100, 110, 120, 130, 140]); ax.set_yticks([-10, -5, 0, 5])
    ax.set_xticklabels([f"{x}E" for x in [100, 110, 120, 130, 140]], fontsize=8)
    ax.set_yticklabels([f"{y}" + ("N" if y >= 0 else "S") for y in [-10, -5, 0, 5]], fontsize=8)
    ax.tick_params(labelsize=8, length=1.5, pad=1)
    ax.set_title(title, fontsize=8.5, fontweight="normal", pad=6)
    return qm


qm_a = draw_map(axes[0], delta, cmap=cmap_a, norm=norm_a,
                title=r"(a) $\Delta$CQI: LSEQM+DL minus LS")
qm_b = draw_map(axes[1], cqi_dl, cmap=cmap_b, norm=norm_b,
                title="(b) LSEQM+DL Quality Category")

# Annotation box on panel (a) with the percentages
axes[0].text(0.985, 0.97,
              f"$\\Delta$CQI > +0.01: {100 * n_pos / n_total:.1f}%\n"
              f"$\\Delta$CQI < $-$0.01: {100 * n_neg / n_total:.1f}%\n"
              f"Mean: {mean_delta:+.3f}",
              transform=axes[0].transAxes, ha="right", va="top", fontsize=7.5,
              bbox=dict(facecolor="white", edgecolor="0.7", boxstyle="round,pad=0.25"))

# Colorbars
bbox_a = axes[0].get_position()
cax_a = fig.add_axes([bbox_a.x0 + 0.18, bbox_a.y0 - 0.045,
                       bbox_a.width - 0.36, 0.013])
cbar_a = fig.colorbar(qm_a, cax=cax_a, orientation="horizontal",
                       extend="both", ticks=[-0.15, -0.075, 0, 0.075, 0.15])
cbar_a.set_label(r"$\Delta$ CQI", fontsize=9)
cbar_a.ax.tick_params(labelsize=8)

bbox_b = axes[1].get_position()
cax_b = fig.add_axes([bbox_b.x0 + 0.10, bbox_b.y0 - 0.045,
                       bbox_b.width - 0.20, 0.013])
# Tick positions at the midpoint of each category interval.
mid_ticks = [(CAT_EDGES[i] + CAT_EDGES[i + 1]) / 2
             for i in range(len(CAT_LABELS))]
cbar_b = fig.colorbar(qm_b, cax=cax_b, orientation="horizontal",
                       ticks=mid_ticks)
cbar_b.ax.set_xticklabels(CAT_LABELS, fontsize=7.5)

fig.suptitle("CQI Improvement from Hybrid Bias Correction",
             fontsize=9, fontweight="bold", y=0.99)

OUT = FIGOUT / "fig_thesis_04_cqi_improvement.png"
fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
