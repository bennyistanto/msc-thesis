"""Thesis Figure 5.3 - Pearson r(h) trajectory and per-station peak distribution.

Two-row stacked layout for the thesis (single-column page):
  (a) r(h) trajectory: pooled mean per timezone band with IQR shading,
      across hour offsets h in [-48, +48].
  (b) Histogram of per-station peak offset h*.

Data:
  temp/subdaily_lag/subdaily_lag_results.npz (precomputed by
  temp/subdaily_lag/build_subdaily_lag.py from half-hourly IMERG-L
  GPM_3IMERGHH_07 vs BMKG daily gauges, January 2020).

Output: paper/thesis/figures/fig_thesis_05_subdaily_chart.png
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
NPZ  = ROOT / "temp" / "subdaily_lag" / "subdaily_lag_results.npz"
FIGOUT = ROOT / "paper" / "thesis" / "figures"
OUT  = FIGOUT / "fig_thesis_05_subdaily_chart.png"

d = np.load(NPZ, allow_pickle=True)
hour_shifts = d["hour_shifts"]
R_global    = d["R_global"]
R_per_st    = d["R_per_station"]
bands       = d["bands"]

def _to_str(b):
    return b.decode() if isinstance(b, (bytes, np.bytes_)) else str(b)
bands_str = np.array([_to_str(b) for b in bands])

band_colors = {"WIB (UTC+7)":  "#1f77b4",
               "WITA (UTC+8)": "#ff7f0e",
               "WIT (UTC+9)":  "#2ca02c"}

fig, axes = plt.subplots(2, 1, figsize=(8.0, 9.0),
                          gridspec_kw={"height_ratios": [1.35, 1.0],
                                        "hspace": 0.32,
                                        "left": 0.10, "right": 0.97,
                                        "top": 0.95, "bottom": 0.07})

# --- Top: r(h) curves ---
ax = axes[0]
ax.axhline(0.0, color="0.85", linewidth=0.6)
ax.axvline(0, color="0.40", linestyle=":", linewidth=1.0)
for b, c in band_colors.items():
    m = bands_str == b
    if m.sum() == 0:
        continue
    mr = np.nanmean(R_per_st[:, m], axis=1)
    q1 = np.nanpercentile(R_per_st[:, m], 25, axis=1)
    q3 = np.nanpercentile(R_per_st[:, m], 75, axis=1)
    ax.fill_between(hour_shifts, q1, q3, color=c, alpha=0.15)
    ax.plot(hour_shifts, mr, color=c, linewidth=2.2,
             label=f"{b}  (n = {m.sum()})")
    pi = np.nanargmax(mr)
    ax.plot(hour_shifts[pi], mr[pi], "o", color=c, markersize=7,
             mec="black", mew=0.7)

r0 = R_global[hour_shifts == 0][0]
rp = np.nanmax(R_global)
hp = hour_shifts[np.nanargmax(R_global)]
ax.axhline(r0, color="0.40", linestyle=":", linewidth=0.7, alpha=0.6)

y_top = max(0.90, float(np.nanmax(R_global)) + 0.20)
ax.set_ylim(-0.05, y_top)
ax.set_xlim(-48, 48)
ax.set_xticks(np.arange(-48, 49, 12))

ax.annotate(f"$r = {r0:.2f}$ at $h = 0$\n(UTC-day baseline)",
             xy=(0, r0), xytext=(34, y_top - 0.03),
             ha="right", va="top",
             arrowprops=dict(arrowstyle="->", color="0.30", lw=0.9,
                              connectionstyle="arc3,rad=-0.25"),
             fontsize=8.5, color="0.10",
             bbox=dict(boxstyle="round,pad=0.30", fc="white",
                        ec="0.60", lw=0.6, alpha=0.97))
ax.annotate(f"$r = {rp:.2f}$  @ $h = {hp}$ h",
             xy=(hp, rp), xytext=(-34, y_top - 0.03),
             arrowprops=dict(arrowstyle="->", color="0.20", lw=0.9,
                              connectionstyle="arc3,rad=0.25"),
             ha="left", va="top",
             fontsize=9, fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.30", fc="#fff7d6",
                        ec="0.55", lw=0.7, alpha=0.97))

ax.set_xlabel("Hour offset $h$  (window = [UTC 00:00 + $h$, +24 h))",
                fontsize=9.5)
ax.set_ylabel("Pearson $r$  (mean per timezone band, IQR shaded)",
                fontsize=9.5)
ax.set_title("(a) $r(h)$ landscape: where the correlation peaks",
              fontsize=10.5, fontweight="bold", loc="left", pad=4)
ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.62),
           fontsize=8.5, frameon=True, framealpha=0.95, edgecolor="0.7")
ax.grid(True, alpha=0.25, linestyle=":")

# --- Bottom: per-station peak histogram ---
ax2 = axes[1]
valid_st = np.isfinite(R_per_st).any(axis=0)
peak_h_per_st = np.full(R_per_st.shape[1], np.nan)
peak_h_per_st[valid_st] = hour_shifts[np.nanargmax(R_per_st[:, valid_st], axis=0)]
for b, c in band_colors.items():
    m = (bands_str == b) & valid_st
    if m.sum() == 0:
        continue
    ax2.hist(peak_h_per_st[m], bins=np.arange(-48.5, 49.5, 1),
              color=c, alpha=0.55, label=f"{b}  (n={m.sum()})")
ax2.axvline(0, color="0.40", linestyle=":", linewidth=1.0)
ax2.set_xlim(-36, 12)
ax2.set_xlabel("Hour offset at which each station's $r$ peaks",
                fontsize=9.5)
ax2.set_ylabel("Station count", fontsize=9.5)
ax2.set_title("(b) Per-station peak distribution",
               fontsize=10.5, fontweight="bold", loc="left", pad=4)
ax2.legend(fontsize=8.5, frameon=True, framealpha=0.95,
            edgecolor="0.7", loc="upper right")
ax2.grid(True, alpha=0.25, linestyle=":", axis="y")

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
