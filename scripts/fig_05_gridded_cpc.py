"""Thesis Figure 5.4 - "Gridded window offset against CPC-UNI over the full record".

Whole-domain window-offset diagnostic of half-hourly IMERG-L against the gridded
CPC-UNI analysis at 0.5 degree:
  (a) CPC-UNI at native UTC labels  -> h* ~= 0 map (full record 2001-2025);
  (b) CPC-UNI harmonised to the local-observation day -> h* ~= -23 map;
  (c) pooled r(h) over the gauged cells (bold, ~0.57) and the whole domain
      (faint, ~0.34), for the GPM (solid) and TRMM-input (dashed) eras.

Data: temp/subdaily_lag/gridded_cpc_window_stats_{2001_2014,2015_2021,2015_2025}.npz
      (gridded window-offset sweep, native + harmonised, per era)

Source: extracted from the temporal-alignment diagnostic
(temp/subdaily_lag/fig_gridded_combined.py).

Output: paper/thesis/figures/fig_thesis_05_gridded_cpc.png
"""
from pathlib import Path
import numpy as np
from subdaily_helpers import (SUBDAILY, HOUR_SHIFTS, r_from_stats, reduce_cells,
                              station_cells, draw_hstar_map)

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_05_gridded_cpc.png"

ALL_TAGS = ["2001_2014", "2015_2025"]   # full record = TRMM-input era + merged full GPM era
GPM_TAG, TRMM_TAG = "2015_2021", "2001_2014"


def full_record_hstar():
    """Per-cell h* maps (native, harmonised) pooled over the full 2001-2025 record.
    The offset is era-stable, so pooling all years de-noises the data-sparse east."""
    Sn = Sh = clat = clon = None
    for t in ALL_TAGS:
        z = np.load(SUBDAILY / f"gridded_cpc_window_stats_{t}.npz")
        Sn = z["stats_native"] if Sn is None else Sn + z["stats_native"]
        Sh = z["stats_harmonised"] if Sh is None else Sh + z["stats_harmonised"]
        clat, clon = z["clat"], z["clon"]
    hn = reduce_cells(Sn)[0].reshape(len(clat), len(clon))
    hh = reduce_cells(Sh)[0].reshape(len(clat), len(clon))
    return clat, clon, hn, hh


def curves(tag, cells):
    """r(h) for native + harmonised, pooled over gauged cells and the whole domain."""
    z = np.load(SUBDAILY / f"gridded_cpc_window_stats_{tag}.npz")
    out = {}
    for pair in ("native", "harmonised"):
        S = z[f"stats_{pair}"]
        out[f"{pair}_gauged"] = r_from_stats(S[cells].sum(0))
        out[f"{pair}_whole"] = r_from_stats(S.sum(0))
    return out


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    clat, clon, hs_nat, hs_har = full_record_hstar()
    cells = station_cells(clat, clon)
    gpm = curves(GPM_TAG, cells); trmm = curves(TRMM_TAG, cells)
    H = HOUR_SHIFTS

    fig = plt.figure(figsize=(11, 13.0), constrained_layout=True)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.3, 1.3, 1.1])
    axa = fig.add_subplot(gs[0]); axb = fig.add_subplot(gs[1]); axc = fig.add_subplot(gs[2])

    m = draw_hstar_map(axa, clat, clon, hs_nat,
                       "(a) CPC at native UTC labels: $h^\\star \\approx 0$ "
                       "(CPC shares the IMERG-L UTC day), full record 2001-2025")
    draw_hstar_map(axb, clat, clon, hs_har,
                   "(b) CPC harmonised to the local-observation day: "
                   "$h^\\star \\approx -23$~h, full record 2001-2025")
    cb = fig.colorbar(m, ax=[axa, axb], shrink=0.85, pad=0.02); cb.set_label("$h^\\star$ (hours)")

    # (c) gauged (bold) vs whole-domain (faint); native black, harmonised wine
    axc.plot(H, gpm["native_gauged"], color="#111111", lw=2.6, ls="-",
             label="native, gauged cells, GPM 2015-2021")
    axc.plot(H, trmm["native_gauged"], color="#111111", lw=2.0, ls="--",
             label="native, gauged cells, TRMM-input 2001-2014")
    axc.plot(H, gpm["native_whole"], color="#9a9a9a", lw=1.5, ls="-",
             label="native, whole domain, GPM (diluted by sparse east)")
    axc.plot(H, trmm["native_whole"], color="#9a9a9a", lw=1.3, ls="--",
             label="native, whole domain, TRMM-input")
    axc.plot(H, gpm["harmonised_gauged"], color="#882255", lw=2.6, ls="-",
             label="harmonised, gauged cells, GPM 2015-2021")
    axc.plot(H, trmm["harmonised_gauged"], color="#882255", lw=2.0, ls="--",
             label="harmonised, gauged cells, TRMM-input 2001-2014")
    axc.axvline(0, color="0.55", ls=":", lw=1.0); axc.axvline(-23, color="0.55", ls=":", lw=1.0)
    axc.set_xlim(-48, 48); axc.set_ylim(0.05, 0.72)
    axc.text(0, 0.065, " $h=0$", fontsize=8, color="0.35", va="bottom", ha="left")
    axc.text(-23, 0.065, "$h=-23$ ", fontsize=8, color="0.35", va="bottom", ha="right")
    axc.set_xlabel("window offset $h$ (hours)")
    axc.set_ylabel("pooled Pearson $r$ vs CPC-UNI")
    axc.set_title("(c) Pooled $r(h)$: gauged cells reach $\\approx0.57$ "
                  "(per-station level), whole domain $\\approx0.34$; offset era-identical",
                  fontsize=11, fontweight="bold", pad=6, loc="left")
    axc.legend(fontsize=7.6, ncol=2, framealpha=0.95, edgecolor="0.7", loc="upper right")
    axc.grid(True, alpha=0.25, ls=":")

    fig.savefig(OUT, dpi=170, facecolor="white")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
