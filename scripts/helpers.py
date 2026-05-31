"""Common plotting utilities for Appendix G "Spatial Atlas" figures.

Adapted from the Bali coverage-map style (fig_thesis_04_bali_coverage.py):
  - Indonesia admin-1 (province) boundaries drawn within the country.
  - World admin-0 boundaries drawn for neighbouring countries (Malaysia,
    Singapore, Brunei, Timor-Leste, Papua New Guinea, etc.) so the
    Indonesian archipelago is visually framed by its neighbours.
  - Compact layout: minimal padding, tight subplot spacing, panels sized
    to the Indonesian aspect ratio (47 deg wide x 17 deg tall ~ 2.76:1).
  - Each multi-panel figure carries a centred main title at the top.

All figures are portrait A4 (text width ~14 cm = 5.51 in).
Indonesia bounding box: 95-141 deg E, -11 to 6 deg N (aspect ~2.76:1).
"""
import os
import warnings
from pathlib import Path

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import ListedColormap, BoundaryNorm

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
DATA = ROOT / "data"
FIGOUT = ROOT / "paper" / "thesis" / "figures"

# ----- Indonesia bbox (full archipelago) and a slightly padded frame -----
LON_RANGE = (94.5, 141.5)
LAT_RANGE = (-11.2, 6.2)
ASPECT = (LON_RANGE[1] - LON_RANGE[0]) / (LAT_RANGE[1] - LAT_RANGE[0])  # ~2.69

# ----- Precipitation discrete colormap (radar style, mm/day) -----
PRECIP_BOUNDS = [0, 0.1, 1, 2, 5, 10, 20, 50, 100, 200]
PRECIP_COLORS = [
    "#ffffff", "#cfe6ff", "#7fb3ff", "#3a83e0", "#1a52a8",
    "#2da94c", "#f5d800", "#f08c00", "#d52b1e",
]
PRECIP_CMAP = ListedColormap(PRECIP_COLORS)
PRECIP_CMAP.set_over("#7c0042")
PRECIP_NORM = BoundaryNorm(PRECIP_BOUNDS, ncolors=len(PRECIP_COLORS) + 1, extend="max")


_BOUNDARIES_CACHE = {}

def load_boundaries():
    """Return (idn_adm1, world_adm0) GeoDataFrames clipped to Indonesia bbox.
    Cached for the lifetime of the Python process."""
    key = "_default"
    if key in _BOUNDARIES_CACHE:
        return _BOUNDARIES_CACHE[key]
    try:
        import geopandas as gpd
        bbox = (LON_RANGE[0], LAT_RANGE[0], LON_RANGE[1], LAT_RANGE[1])
        idn = gpd.read_file(DATA / "subset" / "bnd" / "idn_bnd_adm1.shp", bbox=bbox)
        wld = gpd.read_file(DATA / "subset" / "bnd" / "wld_bnd_adm0.shp", bbox=bbox)
    except Exception as exc:
        print(f"  [warn] boundary load failed: {exc}")
        idn = wld = None
    _BOUNDARIES_CACHE[key] = (idn, wld)
    return idn, wld


def draw_panel(ax, lon, lat, field, *, cmap=PRECIP_CMAP, norm=PRECIP_NORM,
               idn_adm1=None, world_adm0=None, title=None,
               title_fontsize=7, tick_fontsize=5,
               show_y_ticklabels=True):
    """Draw one map panel with Bali-style boundaries:
       - world admin-0 (neighbouring countries) as thin grey background lines
       - Indonesia admin-1 (provinces) as thin dark lines
    The panel is sized to fit the Indonesian bbox snugly.
    Set show_y_ticklabels=False on inner columns of a grid layout to
    suppress redundant latitude labels.
    Returns the QuadMesh for the caller's colorbar."""
    qm = ax.pcolormesh(lon, lat, field, cmap=cmap, norm=norm,
                       shading="nearest", rasterized=True)
    if world_adm0 is not None:
        world_adm0.boundary.plot(ax=ax, color="0.55", linewidth=0.25, zorder=2)
    if idn_adm1 is not None:
        idn_adm1.boundary.plot(ax=ax, color="0.20", linewidth=0.30, zorder=3)
    ax.set_xlim(*LON_RANGE)
    ax.set_ylim(*LAT_RANGE)
    ax.set_aspect("equal")
    ax.tick_params(labelsize=tick_fontsize, length=1.5, pad=1)
    ax.set_xticks([100, 110, 120, 130, 140])
    ax.set_yticks([-10, -5, 0, 5])
    ax.set_xticklabels([f"{x}E" for x in [100, 110, 120, 130, 140]], fontsize=tick_fontsize)
    if show_y_ticklabels:
        ax.set_yticklabels([f"{y}" + ("N" if y >= 0 else "S") for y in [-10, -5, 0, 5]], fontsize=tick_fontsize)
    else:
        ax.set_yticklabels([])
    if title:
        ax.set_title(title, fontsize=title_fontsize, pad=2)
    return qm


def setup_panel_grid(rows, cols, *, panel_width_cm=None,
                     left=0.04, right=0.98, top=0.92, bottom=0.07,
                     wspace=0.06, hspace=0.10, suptitle=None,
                     suptitle_fontsize=10):
    """Create a portrait figure where each panel's height matches the
    Indonesian aspect (so the maps fill the panel area tightly). Returns
    (fig, axes). The figure height is chosen so the map content area is
    exactly the panel grid times the aspect-derived panel height."""
    # Available text width on portrait A4 with 4 cm / 3 cm side margins.
    if panel_width_cm is None:
        # default: split 14 cm of text width across the columns plus gaps
        text_width_cm = 14.0
        panel_width_cm = text_width_cm / cols
    panel_height_cm = panel_width_cm / ASPECT  # tight to Indonesia aspect

    # Convert to inches (1 cm = 0.3937 in)
    cm_to_in = 0.3937
    fig_width_in = cols * panel_width_cm * cm_to_in / (right - left)
    # add room for inter-panel hspace and suptitle
    title_room_in = 0.30 if suptitle else 0.10
    panel_block_in = (rows * panel_height_cm * cm_to_in
                      + (rows - 1) * hspace * panel_height_cm * cm_to_in)
    fig_height_in = (panel_block_in + title_room_in) / (top - bottom)
    # Cap figure height to fit A4 portrait body (about 9 inches)
    fig_height_in = min(fig_height_in, 9.2)

    fig, axes = plt.subplots(rows, cols, figsize=(fig_width_in, fig_height_in),
                             constrained_layout=False)
    plt.subplots_adjust(left=left, right=right, top=top, bottom=bottom,
                        wspace=wspace, hspace=hspace)
    if suptitle:
        fig.suptitle(suptitle, fontsize=suptitle_fontsize, weight="bold", y=0.985)
    return fig, axes


def add_horizontal_colorbar(fig, qm, label, *, ticks=None,
                            bottom=0.025, height=0.012, left=0.18, width=0.66,
                            extend="max"):
    cax = fig.add_axes([left, bottom, width, height])
    cbar = fig.colorbar(qm, cax=cax, orientation="horizontal", extend=extend)
    if ticks is not None:
        cbar.set_ticks(ticks)
    cbar.ax.tick_params(labelsize=6)
    cbar.set_label(label, fontsize=7)
    return cbar


# ----- data loaders -----

def load_corrected_dekad(stage, month, dekad_token):
    p = DATA / "output" / f"corrected_{stage}" / f"idn_cli_{stage}_corrected_imergl_month{month:02d}_dekad{dekad_token}.nc4"
    return xr.open_dataset(p)


def load_metric(stage, month, dekad_token):
    p = DATA / "output" / f"metrics_{stage}" / f"idn_cli_metricssd_cpc_imergl_{stage}_month{month:02d}_dekad{dekad_token}.nc4"
    return xr.open_dataset(p)


def load_raw(product):
    fname = {
        "imergl": "imergl/idn_imergl.nc4",
        "imergf": "imergf/idn_imergf.nc4",
        "cpcuni": "cpcuni/idn_cpcuni.nc4",
    }[product]
    return xr.open_dataset(DATA / "input" / fname)


def precip_var(ds):
    for v in ("precipitation", "precip"):
        if v in ds.data_vars:
            return ds[v]
    raise KeyError(f"No precipitation variable; vars = {list(ds.data_vars)}")
