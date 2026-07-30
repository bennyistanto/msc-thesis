"""Gridded window-offset diagnostic: half-hourly IMERG-L vs CPC-UNI at 0.5 degree,
across all Indonesia. Companion to the BMKG point diagnostic (which gives the
-23 h offset at the 172 gauges); this one uses CPC-UNI as the reference so the
optimal aggregation-window offset can be mapped continuously over the whole
domain, not just where BMKG stations sit.

Why CPC works as the reference
------------------------------
CPC-UNI is a gauge-based daily analysis. Its gridded archive specifies a per-cell
end-of-day (EOD) field that fixes when each daily accumulation closes; for every
Indonesian cell EOD = 24 h, so the daily total closes at 00Z and is referenced to
the UTC calendar day - the SAME window as IMERG-L (NOAA CPC documentation;
verified empirically here: IMERG-vs-CPC at native labels peaks at h* ~= 0). CPC
therefore carries NO window offset against the satellite, unlike the BMKG point
gauges (07:00 local morning observation -> h* = -23 h). This script maps the
offset two ways so the figure shows both halves of the convention story:

  native      CPC at NOAA's UTC-dated labels (shift 0)   -> h* ~= 0   :
              gridded confirmation that CPC = IMERG = UTC day, no offset.
  harmonised  CPC relabelled to the local-observation day (shift -1) -> h* ~= -23 :
              the window CPC needs ONCE it is forced onto the BMKG local-obs day;
              the harmonisation step discussed in the thesis (Section 5.2).

Caveats: CPC is a smoothed 0.5 deg interpolation (peak r is muted vs point BMKG)
and is poorly constrained where its contributing-gauge network is sparse (eastern
Indonesia) - so r(h*) there is low/noisy and h* unreliable. Read the h* maps
together with CPC gauge density.

Method (identical machinery to build_subdaily_seasonal.py)
----------------------------------------------------------
1. Read the half-hourly IMERG-L (48 slots/day, mm/hr) for each available date and
   block-average the 0.1 deg field onto the CPC native 0.5 deg grid.
2. Build a continuous 30-min timeline per year; windowed_cumsum() gives NaN-safe
   24-h window sums for any integer-hour offset h in [-48, +48].
3. For each 0.5 deg cell and offset h, accumulate sufficient statistics
   (n, Sx, Sy, Sxx, Syy, Sxy) over every (year, date), x = IMERG window total,
   y = CPC daily total - separately for the native and harmonised CPC pairing.
   r(h) is exact from the pooled stats (no averaging of r).
4. h*(cell) = argmax_h r(h); pooled r(h) = r over all cells.

Outputs (temp/subdaily_lag/), tag = <y0>_<y1>:
  gridded_cpc_window_hstar_<tag>.nc4   - h*/r_at_hstar for native + harmonised
  gridded_cpc_window_pooled_<tag>.npz  - H, pooled r(h) and per-band, both pairings
  gridded_cpc_window_stats_<tag>.npz   - raw sufficient stats (additive, re-poolable)
  gridded_cpc_window_<tag>.png         - native h* map, harmonised h* map, pooled r(h)

Usage (runs on whatever years are present in the extract folder):
  python gridded_cpc_window.py            # auto-detect available years
  python gridded_cpc_window.py 2015 2021  # restrict to the GPM era
  python gridded_cpc_window.py plot 2015_2021   # regenerate figure from saved outputs
"""
import sys
import glob
import time
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "temp" / "subdaily_lag"))
from build_subdaily_seasonal import windowed_cumsum   # noqa: E402  (mm conversion + cumsum)
from subdaily_stats import r_from_stats               # noqa: E402

from src.config import initialize_config              # noqa: E402
initialize_config(str(ROOT / "config.yml"))
from src import config                                # noqa: E402

# --- configuration ---
HH_DIR = ROOT / "data" / "downloads" / "GPM_3IMERGHHL_07_subset_halfhourly"
PRECIP_VAR = "precipitation"     # half-hourly rain rate, mm/hr, 48 slots/day
SLOTS_PER_DAY = 48
H = np.arange(-48, 49, 1)        # integer-hour offsets to sweep
OUT = ROOT / "temp" / "subdaily_lag"
MIN_N = 200                      # min paired days for a usable cell r

# CPC-UNI is referenced to the UTC calendar day (per-cell EOD = 24 h for all
# Indonesian cells), the SAME window as IMERG-L. At NOAA's native labels the
# IMERG-vs-CPC offset is therefore ~0 (verified empirically). Relabelling CPC by
# -1 day forces it onto the BMKG local-observation day, where the offset becomes
# the -23 h seen at the BMKG gauges. The figure shows both pairings.
SHIFTS = {"native": 0, "harmonised": -1}    # CPC day-label offset (days)
PLOT_ORDER = ["native", "harmonised"]


def hh_file_for(date):
    """Find the half-hourly file for a UTC date by date-glob (robust to the
    exact GPM_3IMERGHHL naming). Returns a path or None."""
    hits = sorted(glob.glob(str(HH_DIR / f"*{date:%Y%m%d}*.nc4")))
    return hits[0] if hits else None


def available_years():
    files = glob.glob(str(HH_DIR / "*.nc4"))
    yrs = set()
    for f in files:
        for tok in Path(f).stem.replace("-", "_").split("_"):
            if len(tok) == 8 and tok.isdigit() and tok.startswith(("19", "20")):
                yrs.add(int(tok[:4]))
    return sorted(yrs)


def build_block_means(sample_ds, clat, clon):
    """Block-mean matrices mapping the IMERG 0.1 deg grid to the CPC 0.5 deg grid
    (nearest-cell membership). Returns (BLm, BOm, cov) where cov is a
    (nclat, nclon) bool mask of CPC cells that actually receive IMERG pixels;
    cells outside the IMERG footprint (grid-edge) are False and set to NaN so
    they never enter the statistics."""
    ilat = sample_ds["lat"].values
    ilon = sample_ds["lon"].values
    lat_bin = np.abs(ilat[:, None] - clat[None, :]).argmin(axis=1)   # (n_ilat,)
    lon_bin = np.abs(ilon[:, None] - clon[None, :]).argmin(axis=1)   # (n_ilon,)
    BL = np.zeros((len(clat), len(ilat))); BL[lat_bin, np.arange(len(ilat))] = 1.0
    BO = np.zeros((len(clon), len(ilon))); BO[lon_bin, np.arange(len(ilon))] = 1.0
    cov = (BL.sum(1) > 0)[:, None] & (BO.sum(1) > 0)[None, :]        # covered cells
    BLm = BL / np.clip(BL.sum(1, keepdims=True), 1, None)            # row-mean
    BOm = BO / np.clip(BO.sum(1, keepdims=True), 1, None)
    return BLm, BOm, cov


def read_hh_day(path, BLm, BOm, cov):
    """Read a half-hourly file (48, nlat, nlon) mm/hr and block-average onto the
    CPC grid -> (48, nclat, nclon), with uncovered cells set to NaN. Returns None
    if the file is malformed."""
    ds = xr.open_dataset(path, decode_timedelta=False)
    vals = ds[PRECIP_VAR].values
    ds.close()
    if vals.ndim != 3 or vals.shape[0] != SLOTS_PER_DAY:
        return None
    # block mean: (j,l) (t,l,m) (k,m) -> (t,j,k)
    agg = np.einsum("jl,tlm,km->tjk", BLm, vals.astype("float32"), BOm,
                    optimize=True).astype("float32")
    return np.where(cov[None], agg, np.nan)


BND_DIR = ROOT / "data" / "subset" / "bnd"
LAND_MASK = ROOT / "data" / "subset" / "iso3" / "idn_subset.nc"


def add_basemap(ax, xlim, ylim, buf=5):
    """Thesis-style basemap (follows scripts/fig_03_station_map.py): filled
    neighbour countries, filled Indonesian provinces, dark national outline.
    Fills sit under the data (low zorder); boundary lines sit over the data
    (high zorder) so admin/national edges stay visible on the coloured cells."""
    import geopandas as gpd
    bbox = (xlim[0] - buf, ylim[0] - buf, xlim[1] + buf, ylim[1] + buf)
    try:
        wld = gpd.read_file(BND_DIR / "wld_bnd_adm0.shp", bbox=bbox)
        wld.plot(ax=ax, facecolor="#e8e8e8", edgecolor="#999999",
                 linewidth=0.4, zorder=1)               # neighbour countries
    except Exception as e:   # noqa: BLE001
        print("  basemap world skipped:", type(e).__name__, e)
    try:
        a1 = gpd.read_file(BND_DIR / "idn_bnd_adm1.shp", bbox=bbox)
        a1.plot(ax=ax, facecolor="#fafaf2", edgecolor="none", zorder=2)   # land base
        a1.boundary.plot(ax=ax, color="#999999", linewidth=0.3, zorder=4)  # province lines over data
    except Exception as e:   # noqa: BLE001
        print("  basemap adm1 skipped:", type(e).__name__, e)
    try:
        a0 = gpd.read_file(BND_DIR / "idn_bnd_adm0.shp", bbox=bbox)
        a0.boundary.plot(ax=ax, color="#2c2c2c", linewidth=0.8, zorder=5)   # national outline
    except Exception as e:   # noqa: BLE001
        print("  basemap adm0 skipped:", type(e).__name__, e)


def clip_to_land_01(hs, clat, clon):
    """Block-upsample the 0.5 deg field to the 0.1 deg land grid (nearest cell)
    and mask to land. Display-only: the values stay the 0.5 deg CPC-native
    estimates, shown on the 0.1 deg coastline so the map clips cleanly."""
    mask = xr.open_dataset(LAND_MASK)["land"]
    if float(mask.lat[0]) > float(mask.lat[-1]):
        mask = mask.reindex(lat=mask.lat[::-1])
    hda = xr.DataArray(hs, coords={"lat": clat, "lon": clon}, dims=("lat", "lon"))
    hs01 = hda.reindex(lat=mask.lat, lon=mask.lon, method="nearest")
    hs01 = hs01.where(mask.values == 1)
    return mask.lat.values, mask.lon.values, hs01.values


# shared map colour scale spanning both pairings: native h* ~= 0 lands at the
# bright end, harmonised h* ~= -23 at the dark end, so one colourbar reads both.
CMAP = "viridis"
VMIN, VMAX = -26, 2
# pooled r(h) line styles: distinct by hue AND dash so the four lines never blur.
LINES = {
    "all":  dict(color="#222222", lw=2.4, ls="-"),
    "WIB":  dict(color="#0072B2", lw=1.6, ls="--"),
    "WITA": dict(color="#E69F00", lw=1.6, ls="-."),
    "WIT":  dict(color="#009E73", lw=1.6, ls=":"),
}


def _draw_map(ax, clat, clon, hs, title):
    mlat, mlon, hs01 = clip_to_land_01(hs, clat, clon)
    xlim, ylim = (94, 142), (-11.5, 7.0)
    add_basemap(ax, xlim, ylim)
    m = ax.pcolormesh(mlon, mlat, hs01, cmap=CMAP, vmin=VMIN, vmax=VMAX,
                      shading="nearest", zorder=3)
    ax.axhline(0, color="gray", lw=0.4, ls="--", alpha=0.6, zorder=4.5)
    ax.text(141.5, 0.2, "Equator", fontsize=8, color="gray",
            ha="right", va="bottom", zorder=6)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=6, loc="left")
    ax.set_xlabel("Longitude (degrees E)", fontsize=10)
    ax.set_ylabel("Latitude (degrees)", fontsize=10)
    ax.tick_params(labelsize=9)
    return m


def plot_gridded(clat, clon, results, y0, y1, tag):
    """Three rows: (a) native CPC h* map (h*~=0), (b) harmonised CPC h* map
    (h*~=-23), (c) pooled r(h) for both pairings. `results` is a dict
    keyed by pairing label, each holding hs / pooled / pooled_band."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(11, 13.0), constrained_layout=True)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.35, 1.35, 1.0])
    axa = fig.add_subplot(gs[0]); axb = fig.add_subplot(gs[1])
    axc = fig.add_subplot(gs[2])

    m = _draw_map(axa, clat, clon, results["native"]["hs"],
                  f"(a) CPC at native UTC labels: $h^\\star \\approx 0$ "
                  f"(CPC shares the IMERG-L UTC day), {y0}-{y1}")
    _draw_map(axb, clat, clon, results["harmonised"]["hs"],
              f"(b) CPC harmonised to the local-observation day: "
              f"$h^\\star \\approx -23$~h, {y0}-{y1}")
    cb = fig.colorbar(m, ax=[axa, axb], shrink=0.85, pad=0.02)
    cb.set_label("$h^\\star$ (hours)")

    # (c) pooled r(h): native (peaks ~0) and harmonised (peaks ~-23)
    nat, har = results["native"], results["harmonised"]
    axc.plot(H, nat["pooled"], **LINES["all"],
             label="native CPC, all Indonesia")
    axc.plot(H, har["pooled"], color="#882255", lw=2.4, ls="-",
             label="harmonised CPC, all Indonesia")
    for nm in ("WIB", "WITA", "WIT"):
        axc.plot(H, har["pooled_band"][nm], **LINES[nm],
                 label=f"harmonised CPC, {nm}")
    axc.axvline(0, color="0.55", ls=":", lw=1.0)
    axc.axvline(-23, color="0.55", ls=":", lw=1.0)
    axc.text(0, axc.get_ylim()[0], " $h=0$", fontsize=8, color="0.35",
             va="bottom", ha="left")
    axc.text(-23, axc.get_ylim()[0], "$h=-23$ ", fontsize=8, color="0.35",
             va="bottom", ha="right")
    axc.set_xlim(-48, 48)
    axc.set_xlabel("window offset $h$ (hours)")
    axc.set_ylabel("pooled Pearson $r$ vs CPC-UNI")
    axc.set_title("(c) Pooled $r(h)$: native peaks at $h\\approx0$, "
                  "harmonised at $h\\approx-23$~h",
                  fontsize=12, fontweight="bold", pad=6, loc="left")
    axc.legend(fontsize=8, ncol=2, framealpha=0.95, edgecolor="0.7")
    axc.grid(True, alpha=0.25, ls=":")

    out = OUT / f"gridded_cpc_window_{tag}.png"
    fig.savefig(out, dpi=170, facecolor="white")
    plt.close(fig)
    print(f"saved {out.name}")


def plot_from_saved(tag):
    """Regenerate the figure from saved outputs (no re-sweep)."""
    hsd = xr.open_dataset(OUT / f"gridded_cpc_window_hstar_{tag}.nc4")
    pz = np.load(OUT / f"gridded_cpc_window_pooled_{tag}.npz")
    yrs = pz["years"]
    results = {}
    for lab in SHIFTS:
        results[lab] = dict(
            hs=hsd[f"h_star_{lab}"].values,
            pooled=pz[f"pooled_{lab}"],
            pooled_band={"WIB": pz[f"pooled_{lab}_wib"],
                         "WITA": pz[f"pooled_{lab}_wita"],
                         "WIT": pz[f"pooled_{lab}_wit"]},
        )
    plot_gridded(hsd.lat.values, hsd.lon.values, results,
                 int(yrs[0]), int(yrs[-1]), tag)


def reduce_one(stats, band):
    """Cell h*/r and pooled curves (all + per band) from one stats array."""
    r_cell = r_from_stats(stats, min_n=MIN_N)               # (ncell, nH)
    valid = np.isfinite(r_cell).any(1)
    hstar = np.full(stats.shape[0], np.nan)
    rstar = np.full(stats.shape[0], np.nan)
    idx = np.where(np.isfinite(r_cell), r_cell, -9).argmax(1)
    hstar[valid] = H[idx[valid]]
    rstar[valid] = np.take_along_axis(r_cell, idx[:, None], 1).ravel()[valid]
    pooled = r_from_stats(stats.sum(0))                     # (nH,)
    pooled_band = {b: r_from_stats(stats[band == b].sum(0)) for b in (1, 2, 3)}
    return hstar, rstar, pooled, pooled_band, int(valid.sum())


def main(y0=None, y1=None):
    # --- CPC native 0.5 deg reference (ascending lat) ---
    cpc = xr.open_dataset(config.cpc_native_file)[config.CPC_PRECIP_VAR]
    if float(cpc.lat[0]) > float(cpc.lat[-1]):
        cpc = cpc.reindex(lat=cpc.lat[::-1])
    clat, clon = cpc.lat.values, cpc.lon.values
    ncell = len(clat) * len(clon)
    print(f"CPC grid: {len(clat)} x {len(clon)} = {ncell} cells (0.5 deg)")

    yrs = available_years()
    if y0:
        yrs = [y for y in yrs if y0 <= y <= (y1 or y0)]
    if not yrs:
        raise FileNotFoundError(
            f"No half-hourly files found in {HH_DIR}. "
            "Download/extract GPM_3IMERGHHL there first.")
    print(f"Years to process: {yrs[0]}-{yrs[-1]} ({len(yrs)} years)")

    # band id per cell (1/2/3 = WIB/WITA/WIT) from longitude: <=112.5, <=127.5, else
    lon2d = np.broadcast_to(clon[None, :], (len(clat), len(clon))).ravel()
    band = np.where(lon2d <= 112.5, 1, np.where(lon2d <= 127.5, 2, 3))

    BLm = BOm = COV = None
    # one sufficient-stats array per CPC pairing (native, harmonised)
    stats = {lab: np.zeros((ncell, len(H), 6), dtype=np.float64) for lab in SHIFTS}

    for yr in yrs:
        t0 = time.time()
        times = pd.date_range(f"{yr}-01-01 00:00", f"{yr}-12-31 23:30", freq="30min")
        precip = np.full((len(times), ncell), np.nan, dtype="float32")
        slot = pd.Series(np.arange(len(times)), index=times)
        n_have = 0
        for d in pd.date_range(f"{yr}-01-01", f"{yr}-12-31"):
            p = hh_file_for(d)
            if p is None:
                continue
            if BLm is None:
                BLm, BOm, COV = build_block_means(xr.open_dataset(p, decode_timedelta=False), clat, clon)
            day = read_hh_day(p, BLm, BOm, COV)
            if day is None:
                continue
            r0 = int(slot[pd.Timestamp(f"{d:%Y-%m-%d} 00:00")])
            precip[r0:r0 + SLOTS_PER_DAY] = day.reshape(SLOTS_PER_DAY, ncell)
            n_have += 1

        if n_have == 0:
            print(f"  {yr}: no usable files, skipped")
            continue

        csum, vcum = windowed_cumsum(precip)                 # (n_t+1, ncell)
        tdates = pd.date_range(f"{yr}-01-01", f"{yr}-12-31")
        # CPC paired both ways: native UTC labels (shift 0) and harmonised to the
        # local-observation day (shift -1). IMERG window x is identical for both.
        ycpc = {lab: cpc.reindex(time=tdates + pd.Timedelta(days=sh)).values.reshape(len(tdates), ncell)
                for lab, sh in SHIFTS.items()}
        d0 = tdates.normalize()
        nt = len(times)
        for hi, h in enumerate(H):
            i0 = slot.reindex(d0 + pd.Timedelta(hours=int(h))).values
            ok = np.isfinite(i0)
            i0i = np.where(ok, np.nan_to_num(i0), 0).astype(int)
            end = np.minimum(i0i + SLOTS_PER_DAY, nt)
            full = ok & (i0i + SLOTS_PER_DAY <= nt)
            vslots = vcum[end] - vcum[i0i]
            wtot = csum[end] - csum[i0i]
            base = full[:, None] & (vslots == SLOTS_PER_DAY)
            for lab in SHIFTS:
                yc = ycpc[lab]
                good = base & np.isfinite(yc)
                x = np.where(good, wtot, 0.0)
                y = np.where(good, yc, 0.0)
                stats[lab][:, hi, 0] += good.sum(0)
                stats[lab][:, hi, 1] += x.sum(0)
                stats[lab][:, hi, 2] += y.sum(0)
                stats[lab][:, hi, 3] += (x * x).sum(0)
                stats[lab][:, hi, 4] += (y * y).sum(0)
                stats[lab][:, hi, 5] += (x * y).sum(0)
        print(f"  {yr}: {n_have} days  ({time.time() - t0:.0f}s)")

    # --- reduce both pairings ---
    results, save_maps, save_pooled = {}, {}, {}
    for lab in SHIFTS:
        hstar, rstar, pooled, pooled_band, nvalid = reduce_one(stats[lab], band)
        results[lab] = dict(
            hs=hstar.reshape(len(clat), len(clon)),
            pooled=pooled,
            pooled_band={"WIB": pooled_band[1], "WITA": pooled_band[2], "WIT": pooled_band[3]},
        )
        save_maps[f"h_star_{lab}"] = (("lat", "lon"), hstar.reshape(len(clat), len(clon)))
        save_maps[f"r_at_hstar_{lab}"] = (("lat", "lon"), rstar.reshape(len(clat), len(clon)))
        save_pooled[f"pooled_{lab}"] = pooled
        save_pooled[f"pooled_{lab}_wib"] = pooled_band[1]
        save_pooled[f"pooled_{lab}_wita"] = pooled_band[2]
        save_pooled[f"pooled_{lab}_wit"] = pooled_band[3]
        print(f"\n[{lab}] domain-pooled peak: h* = {H[np.nanargmax(pooled)]:+.0f} h, "
              f"r = {np.nanmax(pooled):.3f} (cells used: {nvalid}/{ncell})")
        for b, nm in [(1, "WIB"), (2, "WITA"), (3, "WIT")]:
            pr = pooled_band[b]
            print(f"   {nm}: h*={H[np.nanargmax(pr)]:+.0f} h, r={np.nanmax(pr):.3f}")

    # --- save ---
    tag = f"{yrs[0]}_{yrs[-1]}"
    ds_out = xr.Dataset(save_maps, coords={"lat": clat, "lon": clon},
                        attrs={"description": "Gridded window-offset diagnostic, "
                               "IMERG-L HH vs CPC-UNI 0.5deg, native + harmonised pairing",
                               "years": tag, "min_n": MIN_N})
    ds_out.to_netcdf(OUT / f"gridded_cpc_window_hstar_{tag}.nc4")
    np.savez(OUT / f"gridded_cpc_window_pooled_{tag}.npz", H=H,
             years=np.array(yrs), **save_pooled)
    np.savez(OUT / f"gridded_cpc_window_stats_{tag}.npz", H=H,
             stats_native=stats["native"], stats_harmonised=stats["harmonised"],
             band=band, clat=clat, clon=clon, years=np.array(yrs))
    print(f"saved hstar/pooled/stats for {tag}")

    # --- figure ---
    try:
        plot_gridded(clat, clon, results, yrs[0], yrs[-1], tag)
    except Exception as e:
        print("figure skipped:", type(e).__name__, e)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "plot":          # regenerate figure from saved outputs
        plot_from_saved(a[1])
    else:
        main(int(a[0]) if len(a) >= 1 else None, int(a[1]) if len(a) >= 2 else None)
