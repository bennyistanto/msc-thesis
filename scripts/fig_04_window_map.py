"""Thesis Figure 4.6 - "Per-station optimal window offset and correlation lift".

(a) Per-station peak offset h* across Indonesia (GPM era 2015-2021);
(b) the per-station lift from the UTC-day window to the matched window, ordered
    by longitude and coloured by timezone band.

Data: temp/subdaily_lag/subdaily_seasonal_results_2015_2021.npz
      data/subset/bnd/{idn_bnd_adm1,wld_bnd_adm0}.shp

Source: extracted from the temporal-alignment diagnostic
(temp/subdaily_lag/build_seasonal_figures.py, fig_station_map).

Output: paper/thesis/figures/fig_thesis_04_window_map.png
"""
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import geopandas as gpd
from subdaily_helpers import SUBDAILY, per_station_hstar_peak, TZC, TZN

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_04_window_map.png"
IDN_ADM1 = ROOT / "data" / "subset" / "bnd" / "idn_bnd_adm1.shp"
WLD_ADM0 = ROOT / "data" / "subset" / "bnd" / "wld_bnd_adm0.shp"

GPM = np.load(SUBDAILY / "subdaily_seasonal_results_2015_2021.npz", allow_pickle=True)
tz = GPM["timezone"]; lon = GPM["lon"]; lat = GPM["lat"]
hstar, peakr, r0, valid = per_station_hstar_peak(GPM["stats_month"].sum(axis=0))

fig = plt.figure(figsize=(8.6, 9.6))
gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.15], hspace=0.20,
                      left=0.10, right=0.99, top=0.95, bottom=0.07)
ax = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[1, 0])

# (a) map of h*
bbox = (94.5, -11.2, 141.5, 6.2)
idn = gpd.read_file(IDN_ADM1, bbox=bbox); wld = gpd.read_file(WLD_ADM0, bbox=bbox)
wld[wld["iso_3"] != "IDN"].plot(ax=ax, facecolor="#e6e6e6", edgecolor="0.55", lw=0.25)
idn.boundary.plot(ax=ax, color="0.20", lw=0.30)
for xln in (112.5, 127.5):
    ax.axvline(xln, color="0.45", ls="--", lw=0.7)
norm = mpl.colors.Normalize(vmin=-28, vmax=-12)
sc = ax.scatter(lon[valid], lat[valid], c=hstar[valid], cmap="RdYlBu_r", norm=norm,
                s=18, edgecolors="black", lw=0.25)
ax.set_xlim(94, 142); ax.set_ylim(-11.8, 8.0); ax.set_aspect("equal")
ax.set_xlabel("Longitude", fontsize=9.5); ax.set_ylabel("Latitude", fontsize=9.5)
ax.text(103.5, 7.0, "WIB", ha="center", fontsize=8.5, color="0.4")
ax.text(120.0, 7.0, "WITA", ha="center", fontsize=8.5, color="0.4")
ax.text(134.5, 7.0, "WIT", ha="center", fontsize=8.5, color="0.4")
ax.set_title("(a) Per-station peak offset $h^\\star$ (GPM era 2015-2021)",
             fontsize=10.5, fontweight="bold", loc="left")
cb = fig.colorbar(sc, ax=ax, shrink=0.85, pad=0.02); cb.set_label("$h^\\star$ (h from UTC midnight)", fontsize=9)
ax.text(94.6, -10.8, f"median $h^\\star={int(np.nanmedian(hstar)):+d}$ h  "
        f"IQR [{int(np.nanpercentile(hstar,25)):+d}, {int(np.nanpercentile(hstar,75)):+d}]",
        fontsize=8.5, color="0.15",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fff7d6", ec="0.55", lw=0.7))

# (b) per-station lift, ordered by longitude, coloured by timezone band
v = valid
lonv = lon[v]; r0v = r0[v]; pkv = peakr[v]; tzv = tz[v]
order = np.argsort(lonv)
y = np.arange(int(v.sum()))
ax2.hlines(y, r0v[order], pkv[order], color="0.78", lw=0.6, zorder=1)
ax2.scatter(r0v[order], y, c="0.45", s=8, marker="o", zorder=2, label="$r$ at $h=0$ (UTC day)")
for z in (7, 8, 9):
    m = tzv[order] == z
    ax2.scatter(pkv[order][m], y[m], c=TZC[z], s=13, zorder=3, label=f"$r$ at $h^\\star$, {TZN[z]}")
for xln in (112.5, 127.5):
    k = int(np.searchsorted(np.sort(lonv), xln))
    ax2.axhline(k - 0.5, color="0.45", ls="--", lw=0.7)
ax2.set_xlim(-0.1, 0.95); ax2.set_ylim(-1, int(v.sum())); ax2.set_yticks([])
ax2.set_xlabel("Pearson $r$ (GPM era)", fontsize=9.5)
ax2.set_ylabel("stations ordered west $\\to$ east (by longitude)", fontsize=9.5)
ax2.set_title("(b) Per-station lift, ordered by longitude and coloured by timezone",
              fontsize=10.5, fontweight="bold", loc="left")
lift = np.nanmedian(pkv - r0v)
ax2.legend(loc="lower right", fontsize=7.6, framealpha=0.95, edgecolor="0.7")
ax2.grid(True, alpha=0.25, ls=":", axis="x")
ax2.text(0.985, 0.30, f"median lift $\\Delta r = {lift:+.2f}$\n"
         f"per-station peak $r$ median {np.nanmedian(pkv):.2f}",
         transform=ax2.transAxes, fontsize=8.0, va="bottom", ha="right",
         bbox=dict(boxstyle="round,pad=0.3", fc="#fff7d6", ec="0.55", lw=0.7))

fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT.name}")
