"""Thesis Figure 3.6 - "Why a -23 h window aligns the satellite with the BMKG
gauge day" - three parallel 24-hour windows on a shared UTC/WIB time axis.

  - IMERG-L "day d" = 00 UTC to 24 UTC of date d  (h = 0 baseline).
  - BMKG "day d" at the textbook 07 LT convention = 00 UTC (d-1) to 00 UTC (d)
    (h = -24, the WMO morning-observation prediction).
  - BMKG "day d" where the gauge actually sits = h = -23, the data peak.

A slide-quality convention schematic; no data is read.

Source: extracted from the temporal-alignment diagnostic
(temp/subdaily_lag/build_timing_illustration.py).

Output: paper/thesis/figures/fig_thesis_03_window_schematic.png
"""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_03_window_schematic.png"

# UTC time axis spans -30 to +26, centred on day d's UTC midnight (t = 0).
# t = 0 means 00 UTC on date d, i.e. 07 WIB on date d.
T_MIN, T_MAX = -30, 26

fig, ax = plt.subplots(figsize=(10.5, 4.7))

for t in range(T_MIN, T_MAX + 1, 6):
    ax.axvline(t, color="0.85", linewidth=0.6, zorder=0)

# Concrete example: date d = 1 Jan 2020, so d-1 = 31 Dec 2019.
for t, label in [(-24, "00 UTC\n31 Dec 2019"),
                 (0,   "00 UTC\n1 Jan 2020"),
                 (24,  "00 UTC\n2 Jan 2020")]:
    ax.axvline(t, color="0.40", linewidth=1.0, linestyle=":", zorder=1)
    ax.text(t, 3.85, label, ha="center", va="bottom", fontsize=8.5, color="0.20")

WINDOWS = [
    {"y": 2.7, "x0":   0, "color": "#1f77b4",
     "label": "IMERG-L \"1 Jan 2020\"  (UTC-day in the daily archive)",
     "subtitle": "covers 07 WIB 1 Jan to 07 WIB 2 Jan", "h": 0, "h_color": "#1f77b4"},
    {"y": 1.7, "x0": -24, "color": "#888888",
     "label": "BMKG \"1 Jan 2020\"  if every station observed at 07 WIB",
     "subtitle": "textbook prediction from SK.32/2006 morning-observation",
     "h": -24, "h_color": "#888888"},
    {"y": 0.7, "x0": -23, "color": "#d62728",
     "label": "BMKG \"1 Jan 2020\"  $-$  where the gauge already sits",
     "subtitle": "IMERG must re-aggregate to this window for $r(h)$ to peak; BMKG never moves",
     "h": -23, "h_color": "#d62728"},
]

for w in WINDOWS:
    ax.add_patch(Rectangle((w["x0"], w["y"] - 0.18), 24, 0.36, facecolor=w["color"],
                           alpha=0.65, edgecolor=w["color"], linewidth=1.0, zorder=3))
    if w["h"] == -23:
        ax.add_patch(Rectangle((w["x0"], w["y"] - 0.18), 24, 0.36, facecolor="none",
                               edgecolor="#1f77b4", linewidth=1.8, linestyle="--", zorder=4))
    ax.text(w["x0"] + 12, w["y"], w["label"], ha="center", va="center", fontsize=8,
            fontweight="bold", color="white", zorder=4)
    ax.text(w["x0"] - 0.6, w["y"], f"$h = {w['h']:+d}$", ha="right", va="center",
            fontsize=10.5, fontweight="bold", color=w["h_color"], zorder=4)
    ax.text(w["x0"] + 12, w["y"] - 0.30, w["subtitle"], ha="center", va="top",
            fontsize=8.5, color="0.30", style="italic", zorder=4)
    if w["h"] == -23:
        ax.text(w["x0"] + 12, w["y"] - 0.55,
                "Red fill = the existing BMKG gauge window (no change to BMKG).  "
                "Blue dashed outline = IMERG re-aggregated with $h = -23$  $\\Rightarrow$  the two windows match.",
                ha="center", va="top", fontsize=8.5, color="0.20", zorder=4)

ax.annotate("", xy=(-23, 2.20), xytext=(0, 2.20),
            arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.8, mutation_scale=18), zorder=5)
ax.text(-11.5, 2.30, "shift 23 h backward", ha="center", va="bottom", fontsize=10.5,
        fontweight="bold", color="#d62728",
        bbox=dict(boxstyle="round,pad=0.30", fc="white", ec="#d62728", lw=0.9, alpha=0.97), zorder=6)

utc_ticks = list(range(T_MIN, T_MAX + 1, 6))
ax.set_xticks(utc_ticks); ax.set_xticklabels([]); ax.tick_params(axis="x", length=4)
for t in utc_ticks:
    ax.text(t, -0.30, f"{t:+d}", ha="center", va="top", fontsize=7.5, color="0.30")
ax.text(T_MIN - 1.5, -0.30, "UTC (h, day $d$=0):", ha="right", va="top",
        fontsize=8.5, color="0.20", fontweight="bold")
for t in utc_ticks:
    ax.text(t, -0.62, f"{((t + 7) % 24):02d}:00", ha="center", va="top", fontsize=7.5, color="0.30")
ax.text(T_MIN - 1.5, -0.62, "WIB (clock):", ha="right", va="top",
        fontsize=8.5, color="0.20", fontweight="bold")

ax.set_xlim(T_MIN - 0.5, T_MAX + 0.5); ax.set_ylim(-1.1, 4.4); ax.set_yticks([])
for spine in ("top", "right", "left", "bottom"):
    ax.spines[spine].set_visible(False)
ax.tick_params(axis="x", which="both", length=0)

plt.subplots_adjust(left=0.10, right=0.985, top=0.97, bottom=0.13)
fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT.name} ({OUT.stat().st_size // 1024} KB)")
