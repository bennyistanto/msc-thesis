"""Thesis Figure 5.3 - "The calendar-window convention conflict and its resolution".

Daily IMERG correlation against CPC-UNI and BMKG versus aggregation-window offset
h at the BMKG station locations (GPM era 2015-2021): (a) the convention conflict
(CPC-UNI peaks at the UTC window, BMKG at -23 h), and (b) its resolution by
relabelling CPC-UNI to the local-observation day.

Data: temp/subdaily_lag/convention_conflict.npz
      (pooled r(h) curves: r_cpc, r_bmkg, r_cpc_relabelled)

Source: extracted from the temporal-alignment diagnostic
(temp/subdaily_lag/fig_convention_conflict.py).

Output: paper/thesis/figures/fig_thesis_05_convention.png
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from subdaily_helpers import SUBDAILY

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_05_convention.png"

d = np.load(SUBDAILY / "convention_conflict.npz")
H = d["H"]; r_cpc = d["r_cpc"]; r_bmkg = d["r_bmkg"]; r_cpc_re = d["r_cpc_relabelled"]
hc = int(H[np.nanargmax(r_cpc)]); hb = int(H[np.nanargmax(r_bmkg)]); hr = int(H[np.nanargmax(r_cpc_re)])

ymax = max(np.nanmax(r_cpc), np.nanmax(r_bmkg)) + 0.10
fig, (axa, axb) = plt.subplots(1, 2, figsize=(11.5, 4.3), sharey=True)

# (a) the conflict
axa.plot(H, r_cpc, color="#1f77b4", lw=2.2, label="vs CPC-UNI (native label)")
axa.plot(H, r_bmkg, color="#d62728", lw=2.2, label="vs BMKG")
axa.axvline(0, color="0.6", ls=":", lw=1.0); axa.axvline(-23, color="0.6", ls=":", lw=1.0)
axa.scatter([hc, hb], [np.nanmax(r_cpc), np.nanmax(r_bmkg)], color=["#1f77b4", "#d62728"], zorder=5)
axa.set_title("(a) Convention conflict", fontsize=10, loc="left")
axa.set_ylabel("daily Pearson $r$ (GPM era, 2015-2021)")
axa.legend(loc="upper right", fontsize=8.5, framealpha=0.95)

# (b) after harmonising CPC to the local-observation day
axb.plot(H, r_cpc_re, color="#1f77b4", lw=2.2, ls="--", label="vs CPC-UNI (relabelled $+1$ day)")
axb.plot(H, r_bmkg, color="#d62728", lw=2.2, label="vs BMKG")
axb.axvline(-23, color="0.6", ls=":", lw=1.0)
axb.scatter([hr, hb], [np.nanmax(r_cpc_re), np.nanmax(r_bmkg)], color=["#1f77b4", "#d62728"], zorder=5)
axb.annotate("both peak at $h=-23$~h:\na single re-windowed product\nfits both references",
             xy=(-23, np.nanmax(r_bmkg)), xytext=(2, np.nanmax(r_bmkg) - 0.20), fontsize=8.5,
             ha="left", arrowprops=dict(arrowstyle="->", color="0.3", lw=1.0))
axb.set_title("(b) After harmonising CPC to the local-observation day", fontsize=10, loc="left")
axb.legend(loc="upper right", fontsize=8.5, framealpha=0.95)

for ax in (axa, axb):
    ax.set_xlim(-48, 48); ax.set_xlabel("aggregation-window offset $h$ (hours)")
    ax.grid(True, alpha=0.25, ls=":")
axa.set_ylim(0, ymax)
fig.tight_layout()
fig.savefig(OUT, dpi=180, facecolor="white")
print(f"wrote {OUT.name}")
