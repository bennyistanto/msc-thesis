"""Thesis Figure 4.2 (re-layout) - "Threshold-stratified verification" - 2x2
grid of (a) POD, (b) FAR, (c) CSI, (d) ETS as functions of precipitation
threshold for LS / LSEQM / LSEQM+DL. Adds the FAR panel that the prior
1x3 layout omitted, completing the WMO TD-1485 contingency-table set.

Data: data/output/station_validation/multi_threshold_summary_*.csv
      (per-method, per-dekad station-medians and inter-quartile bands)
The 36 dekads are pooled per method.

Output: paper/thesis/figures/fig_thesis_04_multi_threshold.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
CSV_DIR = ROOT / "data" / "output" / "station_validation"
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_04_multi_threshold.png"

METHODS = [
    ("ls",      "LS",       "#1f77b4", "o", "--"),
    ("lseqm",   "LSEQM",    "#ff7f0e", "s", "-"),
    ("lseqmdl", "LSEQM+DL", "#d62728", "^", "-"),
]
DEKADS = [(m, d) for m in range(1, 13) for d in ("01", "11", "21")]
THRESHOLDS_TO_PLOT = [1, 5, 10, 20, 50, 100]

# Each panel: metric column root -> (axis, ylim, title, ylabel, target)
PANELS = [
    ("pod", "(a) POD",  (0.0, 1.0), "POD", 1.0),
    ("far", "(b) FAR",  (0.0, 1.0), "FAR", 0.0),
    ("csi", "(c) CSI",  (0.0, 1.0), "CSI", 1.0),
    ("ets", "(d) ETS",  (-0.05, 0.40), "ETS", 1.0),
]


def load_pooled(method):
    """Pool 36 dekads of station medians for one method. Returns DataFrame
    indexed by threshold with median / p25 / p75 columns per metric."""
    frames = []
    for month, dekad in DEKADS:
        fp = CSV_DIR / f"multi_threshold_summary_{method}_month{month:02d}_dekad{dekad}.csv"
        if not fp.exists():
            continue
        df = pd.read_csv(fp)
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no CSVs for method '{method}' under {CSV_DIR}")
    cat = pd.concat(frames, ignore_index=True)
    # Each dekad gives station-median + IQR. Pool across dekads with
    # nanmean (matches temp/figure_regen/regen_fig11_multi_threshold.py):
    # per-dekad medians can be NaN at high thresholds when no station
    # clears the WMO >=10-event bar; nanmean ignores those.
    agg = {}
    for metric in ("pod", "far", "csi", "ets"):
        med_col = f"{metric}_median"
        p25_col = f"{metric}_p25"
        p75_col = f"{metric}_p75"
        out = cat.groupby("threshold_mm").agg({
            med_col: lambda s: float(np.nanmean(s)) if s.notna().any() else np.nan,
            p25_col: lambda s: float(np.nanmean(s)) if s.notna().any() else np.nan,
            p75_col: lambda s: float(np.nanmean(s)) if s.notna().any() else np.nan,
        })
        agg[metric] = out.rename(columns={
            med_col: "med", p25_col: "p25", p75_col: "p75",
        })
    return agg


print("Loading pooled station-validation summaries...")
data = {key: load_pooled(key) for key, *_ in METHODS}

fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.8), constrained_layout=True)
axes_flat = axes.flat

for ax, (metric, title, ylim, ylabel, target) in zip(axes_flat, PANELS):
    for key, label, color, marker, ls in METHODS:
        df = data[key][metric]
        df = df.loc[df.index.isin(THRESHOLDS_TO_PLOT)]
        thr = df.index.values
        med = df["med"].values
        p25 = df["p25"].values
        p75 = df["p75"].values
        ax.fill_between(thr, p25, p75, color=color, alpha=0.15)
        ax.plot(thr, med, marker=marker, linestyle=ls, color=color,
                linewidth=1.6, markersize=6, label=label,
                markeredgecolor="black", markeredgewidth=0.4)
    ax.set_xscale("log")
    ax.set_xticks(THRESHOLDS_TO_PLOT)
    ax.set_xticklabels([str(t) for t in THRESHOLDS_TO_PLOT], fontsize=8)
    ax.set_ylim(*ylim)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_xlabel("Threshold (mm/day)", fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.3, linestyle=":")
    if metric == "pod":
        ax.legend(loc="upper right", fontsize=8, frameon=True)

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
