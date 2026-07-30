"""Derive Pearson r and peak-offset summaries from sufficient statistics.

The seasonal sweep (build_subdaily_seasonal.py) stores, for each
(calendar month, station, offset h), the six additive sufficient statistics
[n, Sx, Sy, Sxx, Syy, Sxy] (x = gauge, y = satellite). Because they are additive,
pooling over months (to form a 3-month running season), over stations, or over
the whole year is just summation. These helpers turn pooled stats into r(h)
landscapes and peak offsets h*.
"""
import numpy as np

SEASONS = {
    "DJF": (12, 1, 2), "JFM": (1, 2, 3), "FMA": (2, 3, 4), "MAM": (3, 4, 5),
    "AMJ": (4, 5, 6), "MJJ": (5, 6, 7), "JJA": (6, 7, 8), "JAS": (7, 8, 9),
    "ASO": (8, 9, 10), "SON": (9, 10, 11), "OND": (10, 11, 12), "NDJ": (11, 12, 1),
}
SEASON_ORDER = list(SEASONS.keys())


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
    r = np.where((n >= min_n) & (vx > 0) & (vy > 0), r, np.nan)
    return r


def season_stats(stats_month, season):
    """Sum the 3 calendar-month stat slabs of a running season.

    stats_month: (12, ..., 6) indexed by calendar month - 1.
    Returns (..., 6).
    """
    months = SEASONS[season]
    return sum(stats_month[m - 1] for m in months)


def pool_stations(stats):
    """Sum sufficient stats over the station axis (axis 0 of a (n_st, n_h, 6))."""
    return stats.sum(axis=0)


def peak_offset(r_curve, hour_shifts):
    """Argmax offset h* and peak r of an r(h) curve; NaN-safe. 1-D in h."""
    if not np.isfinite(r_curve).any():
        return np.nan, np.nan
    i = np.nanargmax(r_curve)
    return float(hour_shifts[i]), float(r_curve[i])


def r_at(r_curve, hour_shifts, h):
    """r at a specific offset h (e.g. h=0, the UTC-day baseline)."""
    j = np.where(hour_shifts == h)[0]
    return float(r_curve[j[0]]) if len(j) else np.nan
