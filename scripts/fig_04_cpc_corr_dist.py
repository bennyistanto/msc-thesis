"""Thesis Figure 4.x - the spatial distribution of the CPC-UNI daily correlation.

The headline r ~ 0.35 (Table 4.2) is the spatial mean of a broad per-pixel
distribution. This figure shows that distribution over the 19,393 land pixels
(filled density) against the 169 cells that host at least one of the 180 BMKG
stations (rug + density),
which sit visibly higher: where the CPC-UNI gauge network is dense the corrected
product tracks the reference more closely.

Values are the per-pixel daily Pearson r of the LSEQM+DL corrected product
against CPC-UNI, de-meaned per pixel per dekad (temporal skill, seasonal cycle
and spatial climatology removed), averaged over the 36 dekads, 2001 to 2025.

Data: temp/figure_regen or scratchpad npz (pr = per-pixel r, bmask = gauge cells).
Output: paper/thesis/figures/fig_thesis_04_cpc_corr_dist.png
"""
from pathlib import Path
import numpy as np
from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_04_cpc_corr_dist.png"
NPZ = ROOT / "temp" / "subdaily_lag" / "cpc_corr_dist.npz"

z = np.load(NPZ)
pr = z["pr"]; bmask = z["bmask"]
whole = pr[np.isfinite(pr)]
gauge = pr[bmask]; gauge = gauge[np.isfinite(gauge)]

BLUE, GREEN, INK = "#3B6EA5", "#2ca02c", "#1F1F1F"
xs = np.linspace(0, 0.75, 400)
kw = gaussian_kde(whole)(xs)
kg = gaussian_kde(gauge)(xs)

fig, ax = plt.subplots(figsize=(8.4, 3.6))
fig.subplots_adjust(left=0.065, right=0.98, top=0.95, bottom=0.15)

ax.fill_between(xs, kw, color=BLUE, alpha=0.30, zorder=1)
ax.plot(xs, kw, color=BLUE, lw=1.8, zorder=2,
        label=f"Whole coverage (19,393 pixels)")
ax.fill_between(xs, kg, color=GREEN, alpha=0.22, zorder=1)
ax.plot(xs, kg, color=GREEN, lw=1.8, zorder=2,
        label=f"Gauge-dense cells ({gauge.size})")
# rug of the gauge cells
ax.plot(gauge, np.full_like(gauge, -0.10), "|", color=GREEN, ms=7, mew=1.0, alpha=0.7, zorder=3)

for v, c in [(np.median(whole), BLUE), (np.median(gauge), GREEN)]:
    ax.axvline(v, color=c, ls="--", lw=1.2, alpha=0.8, zorder=2)

ax.set_xlim(0, 0.75); ax.set_ylim(-0.2, max(kw.max(), kg.max())*1.12)
ax.set_xlabel("Daily Pearson $r$ against CPC-UNI (per pixel)", fontsize=10.5)
ax.set_ylabel("Density", fontsize=10.5)
ax.tick_params(labelsize=9.5)
ax.set_yticks([])
ax.legend(loc="upper left", fontsize=9, framealpha=0.95, edgecolor="0.8")
top = max(kw.max(), kg.max())
ax.text(np.median(whole)-0.008, top*0.66,
        f"whole coverage\nmedian {np.median(whole):.2f}, pooled 0.36", ha="right", va="top",
        fontsize=8.5, color=BLUE)
ax.text(np.median(gauge)+0.010, top*0.72,
        f"gauge-dense cells\nmedian {np.median(gauge):.2f}, pooled 0.51", ha="left", va="top",
        fontsize=8.5, color=GREEN)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT.name} | whole median {np.median(whole):.3f} | gauge median {np.median(gauge):.3f}")
