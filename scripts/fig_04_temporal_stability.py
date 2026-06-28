"""Thesis Figure 4.7 - "Monthly Temporal Stability of Corrections"
(4-panel 2x2 grid: SDR, RMSE, KS p-value, CSI as monthly time series
for the three correction stages LS / LSEQM / LSEQM+DL).

Per month: aggregate the three dekads then average across all 25
years (2001-2025), reporting the per-pixel spatial median for each
metric. The point is to show that the method ordering is preserved
across the seasonal cycle.

Data: data/output/metrics_{ls,lseqm,lseqmdl}/idn_cli_metricssd_*.nc4

Source: extracted from notebooks/07_paper_results.ipynb, cell
nb07-0028-temporal.

Output: paper/thesis/figures/fig_thesis_04_temporal_stability.png
"""
from pathlib import Path
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_04_temporal_stability.png"

METHODS = ["ls", "lseqm", "lseqmdl"]
METHOD_LABELS = ["LS", "LSEQM", "LSEQM+DL"]
DEKADS = [(m, d) for m in range(1, 13) for d in ("01", "11", "21")]

METRIC_VARS = ["stdev_ratio", "rmse", "ks_pvalue", "csi"]


def metrics_path(method, month, dekad):
    return (ROOT / "data" / "output" / f"metrics_{method}" /
            f"idn_cli_metricssd_cpc_imergl_{method}_month{month:02d}_dekad{dekad}.nc4")


def spatial_medians(ds, varnames):
    out = {}
    for v in varnames:
        if v not in ds:
            out[v] = np.nan
            continue
        arr = ds[v].values.ravel()
        arr = arr[np.isfinite(arr)]
        out[v] = float(np.median(arr)) if arr.size else np.nan
    return out


# Aggregate metrics by month (average the 3 dekads within each month)
print("Loading per-dekad metrics...")
monthly = {m: {k: {mo: [] for mo in range(1, 13)} for k in METRIC_VARS}
           for m in METHODS}
for method in METHODS:
    found = 0
    for month, dekad in DEKADS:
        fp = metrics_path(method, month, dekad)
        if not fp.exists():
            continue
        found += 1
        with xr.open_dataset(fp, decode_timedelta=False) as ds:
            meds = spatial_medians(ds, METRIC_VARS)
        for k, v in meds.items():
            if np.isfinite(v):
                monthly[method][k][month].append(v)
    print(f"  {method}: {found} dekadal files")

# Plot 2x2
plot_vars = [
    ("stdev_ratio", "Std. Dev. Ratio", 1.0),
    ("rmse",        "RMSE (mm/day)",    None),
    ("ks_pvalue",   "KS p-value (%)",   None),
    ("csi",         "CSI",              None),
]
method_colors = {"ls": "#4393c3", "lseqm": "#f4a582", "lseqmdl": "#d6604d"}
method_styles = {"ls": "--",      "lseqm": "-.",      "lseqmdl": "-"}
# square marker on LSEQM so its line stays visible where LSEQM+DL coincides with it
method_markers = {"ls": "o",      "lseqm": "s",       "lseqmdl": "o"}

fig, axes = plt.subplots(2, 2, figsize=(12, 9), constrained_layout=True)
month_labels = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

for ax, (var, label, ideal) in zip(axes.ravel(), plot_vars):
    for method, mlabel in zip(METHODS, METHOD_LABELS):
        months_x = list(range(1, 13))
        vals_y = []
        for mo in months_x:
            vlist = monthly[method][var][mo]
            vals_y.append(np.mean(vlist) if vlist else np.nan)
        # KS p-value comes in fraction 0-1; show as percent
        if var == "ks_pvalue":
            vals_y = [v * 100 if np.isfinite(v) else v for v in vals_y]
        ax.plot(months_x, vals_y,
                color=method_colors[method],
                linestyle=method_styles[method],
                marker=method_markers[method],
                markersize=5 if method == "lseqm" else 4,
                label=mlabel, linewidth=1.5,
                zorder=5 if method == "lseqmdl" else 3)
    if ideal is not None:
        ax.axhline(ideal, color="grey", linestyle=":", linewidth=0.8, alpha=0.5)
    ax.set_title(label, fontweight="bold")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_labels)
    ax.set_xlabel("Month")
    ax.set_ylabel(label)
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
