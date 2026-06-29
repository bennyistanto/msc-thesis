"""Shared utilities for the temporal-alignment diagnostic figures.

The window-offset / calendar-convention figures (Figures 3.6, 4.4-4.6, 5.3-5.5,
D.1, and H.1-H.2) share this module the way the spatial-map figures share
``helpers.py``. It collects the sufficient-statistics Pearson r, the half-hourly
window machinery, the timezone-band styling, and the gridded h*-map drawing.

The diagnostic's intermediate products - the per-station and gridded
window-offset sweep ``.npz`` files and the half-hourly station cache - live in
``<ROOT>/temp/subdaily_lag`` (the diagnostic working directory, part of the data
archive in Appendix B). Adjust ``ROOT`` below to point at your local checkout.

Not a figure-generating script.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
SUBDAILY = ROOT / "temp" / "subdaily_lag"          # sweep .npz outputs + hh_cache/
HOUR_SHIFTS = np.arange(-48, 49, 1)                # integer-hour window offsets
SLOTS_PER_DAY = 48

# ============================================================
# Sufficient-statistics Pearson r (from the window-offset sweep)
# ============================================================
# The sweep stores, per (calendar month, station, offset h), the six additive
# sufficient statistics [n, Sx, Sy, Sxx, Syy, Sxy]. Because they are additive,
# pooling over months / stations / years is just summation.

SEASONS = {
    "DJF": (12, 1, 2), "JFM": (1, 2, 3), "FMA": (2, 3, 4), "MAM": (3, 4, 5),
    "AMJ": (4, 5, 6), "MJJ": (5, 6, 7), "JJA": (6, 7, 8), "JAS": (7, 8, 9),
    "ASO": (8, 9, 10), "SON": (9, 10, 11), "OND": (10, 11, 12), "NDJ": (11, 12, 1),
}
SEASON_ORDER = list(SEASONS)


def r_from_stats(s, min_n=2):
    """Pearson r from stacked sufficient stats; last axis = [n,Sx,Sy,Sxx,Syy,Sxy].

    Returns r with the last axis removed. n<min_n or zero variance -> NaN.
    """
    n = s[..., 0]; Sx = s[..., 1]; Sy = s[..., 2]
    Sxx = s[..., 3]; Syy = s[..., 4]; Sxy = s[..., 5]
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = n * Sxy - Sx * Sy
        vx = n * Sxx - Sx * Sx
        vy = n * Syy - Sy * Sy
        r = cov / np.sqrt(vx * vy)
    return np.where((n >= min_n) & (vx > 0) & (vy > 0), r, np.nan)


def season_stats(stats_month, season):
    """Sum the three calendar-month stat slabs of a running season.

    stats_month: (12, ..., 6) indexed by calendar month - 1. Returns (..., 6).
    """
    return sum(stats_month[m - 1] for m in SEASONS[season])


def pool_stations(stats):
    """Sum sufficient stats over the station axis (axis 0 of (n_st, n_h, 6))."""
    return stats.sum(axis=0)


def peak_offset(r_curve, hour_shifts=HOUR_SHIFTS):
    """Argmax offset h* and peak r of a 1-D r(h) curve; NaN-safe."""
    if not np.isfinite(r_curve).any():
        return np.nan, np.nan
    i = np.nanargmax(r_curve)
    return float(hour_shifts[i]), float(r_curve[i])


def r_at(r_curve, h, hour_shifts=HOUR_SHIFTS):
    """r at a specific offset h (e.g. h=0, the UTC-day baseline)."""
    j = np.where(hour_shifts == h)[0]
    return float(r_curve[j[0]]) if len(j) else np.nan


def per_station_hstar_peak(stats, hour_shifts=HOUR_SHIFTS):
    """Per-station h*, peak r, and r at h=0 from (n_st, n_h, 6) stats."""
    rps = r_from_stats(stats)
    valid = np.isfinite(rps).any(axis=1)
    masked = np.where(np.isfinite(rps), rps, -9.0)
    hstar = np.full(len(rps), np.nan); peakr = np.full(len(rps), np.nan)
    hstar[valid] = hour_shifts[np.nanargmax(masked[valid], axis=1)]
    peakr[valid] = np.nanmax(masked[valid], axis=1)
    r0 = rps[:, hour_shifts == 0].ravel()
    return hstar, peakr, r0, valid


# ============================================================
# Timezone-band styling (WIB / WITA / WIT)
# ============================================================
TZC = {7: "#1f77b4", 8: "#ff7f0e", 9: "#2ca02c"}   # tab10 blue/orange/green
TZLS = {7: "-", 8: "--", 9: "-."}                  # distinct dash per zone
TZN = {7: "WIB (UTC+7)", 8: "WITA (UTC+8)", 9: "WIT (UTC+9)"}


# ============================================================
# Half-hourly window machinery (cache-reading figures: 5.5, D.1)
# ============================================================
def windowed_cumsum(precip):
    """NaN-safe 24-h window sums in mm from a (n_t, n_st) 30-min rain-rate matrix.

    window_total(i0) = csum[i0+48] - csum[i0]   (mm; the *0.5 conversion applied)
    valid_slots(i0)  = vcount[i0+48] - vcount[i0]  (a window needs all 48 slots).
    """
    mm30 = precip * 0.5
    valid = np.isfinite(mm30)
    filled = np.where(valid, mm30, 0.0)
    n_t = precip.shape[0]
    csum = np.zeros((n_t + 1, precip.shape[1]), dtype=np.float64)
    vcum = np.zeros((n_t + 1, precip.shape[1]), dtype=np.int32)
    np.cumsum(filled, axis=0, out=csum[1:])
    np.cumsum(valid, axis=0, out=vcum[1:])
    return csum, vcum


def load_hh_cache(years):
    """Concatenate the yearly half-hourly station-cache shards.

    Returns (times: DatetimeIndex, precip: (n_t, n_st) float32, wmo: int array).
    """
    t, p, wmo = [], [], None
    for y in years:
        d = np.load(SUBDAILY / "hh_cache" / f"hh_cache_{y}.npz", allow_pickle=True)
        t.append(d["times"]); p.append(d["precip"]); wmo = d["wmo"].astype(int)
    return (pd.DatetimeIndex(np.concatenate(t)),
            np.concatenate(p, 0).astype("float32"), wmo)


# ============================================================
# Gridded h*-map drawing (Figures 5.4, H.1, H.2)
# ============================================================
GRID_CMAP, GRID_VMIN, GRID_VMAX = "viridis", -26, 2
# pooled r(h) line styles (native black, harmonised wine; per-band by hue+dash)
GRID_LINES = {
    "all":  dict(color="#222222", lw=2.4, ls="-"),
    "WIB":  dict(color="#0072B2", lw=1.6, ls="--"),
    "WITA": dict(color="#E69F00", lw=1.6, ls="-."),
    "WIT":  dict(color="#009E73", lw=1.6, ls=":"),
}
_BND_DIR = ROOT / "data" / "subset" / "bnd"
_LAND_MASK = ROOT / "data" / "subset" / "iso3" / "idn_subset.nc"


def add_basemap(ax, xlim, ylim, buf=5):
    """Thesis-style basemap: filled neighbour countries + provinces, dark outline.

    Fills sit under the data (low zorder); boundary lines over it (high zorder).
    """
    import geopandas as gpd
    bbox = (xlim[0] - buf, ylim[0] - buf, xlim[1] + buf, ylim[1] + buf)
    try:
        wld = gpd.read_file(_BND_DIR / "wld_bnd_adm0.shp", bbox=bbox)
        wld.plot(ax=ax, facecolor="#e8e8e8", edgecolor="#999999", linewidth=0.4, zorder=1)
    except Exception as e:   # noqa: BLE001
        print("  basemap world skipped:", type(e).__name__, e)
    try:
        a1 = gpd.read_file(_BND_DIR / "idn_bnd_adm1.shp", bbox=bbox)
        a1.plot(ax=ax, facecolor="#fafaf2", edgecolor="none", zorder=2)
        a1.boundary.plot(ax=ax, color="#999999", linewidth=0.3, zorder=4)
    except Exception as e:   # noqa: BLE001
        print("  basemap adm1 skipped:", type(e).__name__, e)
    try:
        a0 = gpd.read_file(_BND_DIR / "idn_bnd_adm0.shp", bbox=bbox)
        a0.boundary.plot(ax=ax, color="#2c2c2c", linewidth=0.8, zorder=5)
    except Exception as e:   # noqa: BLE001
        print("  basemap adm0 skipped:", type(e).__name__, e)


def clip_to_land_01(hs, clat, clon):
    """Upsample the 0.5 deg h* field to the 0.1 deg land grid and mask to land.

    Display-only: values stay the 0.5 deg estimates, shown on the 0.1 deg
    coastline so the map clips cleanly. Returns (lat, lon, masked field).
    """
    mask = xr.open_dataset(_LAND_MASK)["land"]
    if float(mask.lat[0]) > float(mask.lat[-1]):
        mask = mask.reindex(lat=mask.lat[::-1])
    hda = xr.DataArray(hs, coords={"lat": clat, "lon": clon}, dims=("lat", "lon"))
    hs01 = hda.reindex(lat=mask.lat, lon=mask.lon, method="nearest").where(mask.values == 1)
    return mask.lat.values, mask.lon.values, hs01.values


def draw_hstar_map(ax, clat, clon, hs, title):
    """Draw one h* map panel (basemap + h* on the 0.1 deg land grid). Returns the mesh."""
    mlat, mlon, hs01 = clip_to_land_01(hs, clat, clon)
    xlim, ylim = (94, 142), (-11.5, 7.0)
    add_basemap(ax, xlim, ylim)
    m = ax.pcolormesh(mlon, mlat, hs01, cmap=GRID_CMAP, vmin=GRID_VMIN, vmax=GRID_VMAX,
                      shading="nearest", zorder=3)
    ax.axhline(0, color="gray", lw=0.4, ls="--", alpha=0.6, zorder=4.5)
    ax.text(141.5, 0.2, "Equator", fontsize=8, color="gray", ha="right", va="bottom", zorder=6)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal", adjustable="box")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=6, loc="left")
    ax.set_xlabel("Longitude (degrees E)", fontsize=10)
    ax.set_ylabel("Latitude (degrees)", fontsize=10)
    ax.tick_params(labelsize=9)
    return m


def station_cells(clat, clon):
    """Unique 0.5 deg cell indices (raveled nlat x nlon) that contain a BMKG station."""
    loc = pd.read_csv(ROOT / "data/input/stations/idn_cli_weatherstation_location_bmkg.csv",
                      sep=";")
    slat = loc["Lat"].values.astype(float); slon = loc["Lon"].values.astype(float)
    li = np.abs(clat[:, None] - slat[None, :]).argmin(0)
    oi = np.abs(clon[:, None] - slon[None, :]).argmin(0)
    return np.unique(li * len(clon) + oi)


def reduce_cells(stats, min_n=200):
    """Per-cell h* / peak r from gridded (ncell, nH, 6) stats. Returns (hstar, peak)."""
    rc = r_from_stats(stats, min_n=min_n)
    valid = np.isfinite(rc).any(1)
    hstar = np.full(stats.shape[0], np.nan)
    idx = np.where(np.isfinite(rc), rc, -9).argmax(1)
    hstar[valid] = HOUR_SHIFTS[idx[valid]]
    return hstar, rc


def single_era_gridded_figure(stats_native, stats_harmonised, band, clat, clon, y0, y1, out_path):
    """Three-row single-era gridded figure (Figures H.1 and H.2): native h* map,
    harmonised h* map, and pooled r(h) with the per-band decomposition."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    results = {}
    for lab, S in [("native", stats_native), ("harmonised", stats_harmonised)]:
        hstar = reduce_cells(S)[0].reshape(len(clat), len(clon))
        pooled = r_from_stats(S.sum(0))
        pb = {b: r_from_stats(S[band == b].sum(0)) for b in (1, 2, 3)}
        results[lab] = dict(hs=hstar, pooled=pooled,
                            pooled_band={"WIB": pb[1], "WITA": pb[2], "WIT": pb[3]})

    fig = plt.figure(figsize=(11, 13.0), constrained_layout=True)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.35, 1.35, 1.0])
    axa = fig.add_subplot(gs[0]); axb = fig.add_subplot(gs[1]); axc = fig.add_subplot(gs[2])

    m = draw_hstar_map(axa, clat, clon, results["native"]["hs"],
                       f"(a) CPC at native UTC labels: $h^\\star \\approx 0$ "
                       f"(CPC shares the IMERG-L UTC day), {y0}-{y1}")
    draw_hstar_map(axb, clat, clon, results["harmonised"]["hs"],
                   f"(b) CPC harmonised to the local-observation day: "
                   f"$h^\\star \\approx -23$~h, {y0}-{y1}")
    cb = fig.colorbar(m, ax=[axa, axb], shrink=0.85, pad=0.02); cb.set_label("$h^\\star$ (hours)")

    nat, har = results["native"], results["harmonised"]
    axc.plot(HOUR_SHIFTS, nat["pooled"], **GRID_LINES["all"], label="native CPC, all Indonesia")
    axc.plot(HOUR_SHIFTS, har["pooled"], color="#882255", lw=2.4, ls="-",
             label="harmonised CPC, all Indonesia")
    for nm in ("WIB", "WITA", "WIT"):
        axc.plot(HOUR_SHIFTS, har["pooled_band"][nm], **GRID_LINES[nm], label=f"harmonised CPC, {nm}")
    axc.axvline(0, color="0.55", ls=":", lw=1.0); axc.axvline(-23, color="0.55", ls=":", lw=1.0)
    axc.text(0, axc.get_ylim()[0], " $h=0$", fontsize=8, color="0.35", va="bottom", ha="left")
    axc.text(-23, axc.get_ylim()[0], "$h=-23$ ", fontsize=8, color="0.35", va="bottom", ha="right")
    axc.set_xlim(-48, 48)
    axc.set_xlabel("window offset $h$ (hours)")
    axc.set_ylabel("pooled Pearson $r$ vs CPC-UNI")
    axc.set_title("(c) Pooled $r(h)$: native peaks at $h\\approx0$, harmonised at $h\\approx-23$~h",
                  fontsize=12, fontweight="bold", pad=6, loc="left")
    axc.legend(fontsize=8, ncol=2, framealpha=0.95, edgecolor="0.7")
    axc.grid(True, alpha=0.25, ls=":")

    fig.savefig(out_path, dpi=170, facecolor="white")
    plt.close(fig)
