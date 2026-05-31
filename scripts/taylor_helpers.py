"""Shared utilities for the Station-Level Taylor diagram figures.

Used by:
  fig_04_taylor_by_station.py   (seasonal: wet vs dry, 2 polar panels)
  fig_05_taylor_monthly.py      (monthly: 12 polar panels)

Both scripts read the same pre-computed CSV
  data/output/figures/taylor/taylor_statistics_per_dekad.csv
(produced by the parent project's analysis pipeline) and render a
six-product polar Taylor plot from the per-station rows. This module
holds the grid drawing, per-station aggregation, and legend builder
that the two figures share.

Source: extracted from notebooks/07_paper_results.ipynb, cell
nb07-0013-fig4-taylor.
"""
from __future__ import annotations
from collections import OrderedDict

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ----- Style / sizing constants -----
MIN_N = 30
MAX_STD_RATIO = 2.0

WET_MONTHS = {10, 11, 12, 1, 2, 3}
DRY_MONTHS = {4, 5, 6, 7, 8, 9}

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PANEL_LETTERS = list("abcdefghijkl")

REFERENCE_KEYS = ["cpc", "imergl", "imergf"]
TEST_KEYS = ["ls", "lseqm", "lseqmdl"]

PRODUCT_STYLES = OrderedDict([
    ("cpc",     {"label": "CPC-UNI",  "marker": "p", "color": "#8c564b", "size": 13, "zorder": 5}),
    ("imergl",  {"label": "IMERG-L",  "marker": "o", "color": "#1f77b4", "size": 12, "zorder": 4}),
    ("imergf",  {"label": "IMERG-F",  "marker": "D", "color": "#17becf", "size": 12, "zorder": 4}),
    ("ls",      {"label": "LS",       "marker": "^", "color": "#2ca02c", "size": 13, "zorder": 6}),
    ("lseqm",   {"label": "LSEQM",    "marker": "s", "color": "#ff7f0e", "size": 12, "zorder": 7}),
    ("lseqmdl", {"label": "LSEQM+DL", "marker": "*", "color": "#d62728", "size": 16, "zorder": 8}),
])
PRODUCT_KEYS = list(PRODUCT_STYLES.keys())


def draw_taylor_grid(ax, *, max_std=MAX_STD_RATIO, compact=False):
    """Draw a polar Taylor grid on `ax` (polar projection). `compact=True`
    yields a smaller, sparser-labelled grid suitable for 12-panel layouts."""
    ax.set_thetamin(0)
    ax.set_thetamax(90)
    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi / 2)

    std_ticks = np.arange(0, max_std + 0.01, 0.5)
    ax.set_rticks(std_ticks)
    ax.set_rlim(0, max_std)
    ax.tick_params(axis="y", labelsize=7 if compact else 8)

    corr_ticks = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
    if compact:
        show = {0.2, 0.4, 0.6, 0.8, 0.9, 0.99}
        labels = [(f"{c:.2f}" if c >= 0.95 else f"{c:.1f}") if c in show else ""
                  for c in corr_ticks]
        fs_lbl = 7
    else:
        labels = [f"{c:.2f}" if c >= 0.95 else f"{c:.1f}" for c in corr_ticks]
        fs_lbl = 8
    corr_angles = [np.arccos(c) for c in corr_ticks]
    ax.set_thetagrids(np.degrees(corr_angles), labels=labels, fontsize=fs_lbl)

    ax.text(np.pi / 4, max_std * (1.06 if compact else 1.07),
            "Corr." if compact else "Correlation",
            fontsize=8 if compact else 10, color="#2ca02c", fontweight="bold",
            ha="center", va="center", rotation=-45, rotation_mode="anchor")

    ax.set_ylabel("Std Dev" if compact else "Standard Deviation",
                  fontsize=8 if compact else 10,
                  labelpad=16 if compact else 20)
    ax.annotate("Std Dev" if compact else "Standard Deviation",
                xy=(0.5, -0.05 if compact else -0.04),
                xycoords="axes fraction",
                ha="center", va="top",
                fontsize=8 if compact else 10)

    # Reference point (perfect agreement: r=1, std_ratio=1)
    ax.plot(0, 1.0, "ko", markersize=6 if compact else 8, zorder=10)

    # Centred RMSE arcs
    for crmse in [0.5, 1.0, 1.5]:
        theta = np.linspace(0, np.pi / 2, 200)
        r_arc = []
        for t in theta:
            costh = np.cos(t)
            disc = costh ** 2 - (1 - crmse ** 2)
            r_arc.append(costh + np.sqrt(disc) if disc >= 0 else np.nan)
        r_arc = np.array(r_arc)
        mask = (r_arc >= 0) & (r_arc <= max_std)
        if mask.any():
            ax.plot(theta[mask], r_arc[mask], "--",
                    color="gray", linewidth=0.4 if compact else 0.5,
                    alpha=0.6, zorder=1)
    ax.grid(True, alpha=0.3)


def compute_period_stats(df, months):
    """Per-station median Taylor statistics for a set of calendar months.

    Returns (per_station, aggregate):
      per_station[key] = list of (corr, std_prd/std_obs) tuples, one per station
      aggregate[key]   = (median_corr, median_std_ratio) across stations
    """
    sdf = df[df["month"].isin(months)]
    per_station = {k: [] for k in PRODUCT_KEYS}
    for sid in sdf["station_id"].unique():
        ss = sdf[sdf["station_id"] == sid]
        for key in PRODUCT_KEYS:
            cc = f"{key}_correlation"
            so = f"{key}_std_obs"
            sp = f"{key}_std_prd"
            nn = f"{key}_n"
            if cc not in ss.columns:
                continue
            valid = ss[ss[cc].notna() & ss[so].notna() & (ss[so] > 0)
                       & ss[sp].notna() & (ss[nn] >= MIN_N)]
            if len(valid) == 0:
                continue
            mc = valid[cc].median()
            mr = (valid[sp] / valid[so]).median()
            if np.isfinite(mc) and np.isfinite(mr):
                per_station[key].append((mc, mr))
    agg = {}
    for key in PRODUCT_KEYS:
        pts = per_station[key]
        if not pts:
            agg[key] = (np.nan, np.nan)
            continue
        agg[key] = (float(np.median([p[0] for p in pts])),
                    float(np.median([p[1] for p in pts])))
    return per_station, agg


def plot_one_panel(ax, per_station, agg, panel_label, label_text, *,
                   compact=False, max_std=MAX_STD_RATIO):
    """Render one Taylor diagram panel: grid + per-station scatter +
    aggregate marker + panel-letter / label-text header."""
    draw_taylor_grid(ax, max_std=max_std, compact=compact)

    # Per-station scatter (faint)
    for key in PRODUCT_KEYS:
        st = PRODUCT_STYLES[key]
        pts = per_station[key]
        thetas, rs = [], []
        for c, r in pts:
            if 0 <= r <= max_std:
                thetas.append(np.arccos(np.clip(c, 0, 1)))
                rs.append(r)
        if thetas:
            ax.scatter(thetas, rs, marker=st["marker"], c=st["color"],
                       s=10 if compact else 18, alpha=0.20 if compact else 0.25,
                       edgecolors="none", zorder=2)

    # Bold aggregate marker per product
    for key in PRODUCT_KEYS:
        st = PRODUCT_STYLES[key]
        mc, mr = agg[key]
        if not (np.isfinite(mc) and np.isfinite(mr)):
            continue
        theta = np.arccos(np.clip(mc, 0, 1))
        ax.plot(theta, mr, marker=st["marker"], color=st["color"],
                markersize=st["size"] * (0.7 if compact else 1.0),
                markeredgecolor="black", markeredgewidth=0.6 if compact else 0.8,
                linestyle="none", zorder=st.get("zorder", 5))

    # Panel header
    if compact:
        ax.text(0.0, 1.04, f"{panel_label} {label_text}",
                transform=ax.transAxes, fontsize=10, fontweight="bold",
                ha="left", va="bottom",
                bbox=dict(boxstyle="round,pad=0.25",
                          facecolor="white", edgecolor="black", linewidth=0.5))
    else:
        ax.text(0.0, 1.08, panel_label,
                transform=ax.transAxes, fontsize=12, fontweight="bold",
                ha="left", va="bottom",
                bbox=dict(boxstyle="round,pad=0.3",
                          facecolor="white", edgecolor="black", linewidth=0.6))
        ax.text(0.5, 1.09, label_text,
                transform=ax.transAxes, fontsize=11, fontweight="bold",
                ha="center", va="bottom")


def legend_handles_split():
    """Return (reference_handles, test_handles) for fig.legend()."""
    ref = [Line2D([0], [0], marker="o", color="w",
                  markerfacecolor="black", markeredgecolor="black",
                  markersize=7, label="REF (BMKG)")]
    for k in REFERENCE_KEYS:
        s = PRODUCT_STYLES[k]
        ref.append(Line2D([0], [0], marker=s["marker"], color="w",
                          markerfacecolor=s["color"], markeredgecolor="black",
                          markersize=min(s["size"], 10), label=s["label"]))
    tst = []
    for k in TEST_KEYS:
        s = PRODUCT_STYLES[k]
        tst.append(Line2D([0], [0], marker=s["marker"], color="w",
                          markerfacecolor=s["color"], markeredgecolor="black",
                          markersize=min(s["size"], 10), label=s["label"]))
    return ref, tst
