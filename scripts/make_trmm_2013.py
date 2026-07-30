"""Build the clean pre-GPM / TRMM-input era (2001-2013) gridded-CPC result by
subtracting the 2014 transition year from the 2001-2014 sweep. Sufficient
statistics are additive, so stats(2001-2013) = stats(2001-2014) - stats(2014),
an exact operation with no re-sweep. 2014 is the GPM-transition year (Core
Observatory launched Feb 2014, full constellation ~2015) and is excluded from
the era comparison, consistent with the BMKG-based window figures (Section 4.5,
"the years through 2013 ... a transition the per-year trace places at the 2014
to 2015 boundary"). The 2001-2014 full-record stats are kept for the whole-record
maps in the main-text figure.
"""
import numpy as np
import xarray as xr
from gridded_cpc_window import reduce_one, plot_gridded, OUT, H

A = np.load(OUT / "gridded_cpc_window_stats_2001_2014.npz")
B = np.load(OUT / "gridded_cpc_window_stats_2014_2014.npz")
band = A["band"]; clat = A["clat"]; clon = A["clon"]
tag = "2001_2013"

results, save_maps, save_pooled = {}, {}, {}
for lab in ("native", "harmonised"):
    S = A[f"stats_{lab}"] - B[f"stats_{lab}"]          # drop the 2014 transition year
    if np.any(S[..., 0] < 0):
        raise SystemExit("negative paired-day count after subtraction - tag mismatch")
    hstar, rstar, pooled, pooled_band, nvalid = reduce_one(S, band)
    results[lab] = dict(
        hs=hstar.reshape(len(clat), len(clon)),
        pooled=pooled,
        pooled_band={"WIB": pooled_band[1], "WITA": pooled_band[2], "WIT": pooled_band[3]},
    )
    save_maps[f"h_star_{lab}"] = (("lat", "lon"), hstar.reshape(len(clat), len(clon)))
    save_maps[f"r_at_hstar_{lab}"] = (("lat", "lon"), rstar.reshape(len(clat), len(clon)))
    save_pooled[f"pooled_{lab}"] = pooled
    for bi, bn in ((1, "wib"), (2, "wita"), (3, "wit")):
        save_pooled[f"pooled_{lab}_{bn}"] = pooled_band[bi]
    print(f"[{lab}] peak h*={int(H[np.nanargmax(pooled)]):+d} r={np.nanmax(pooled):.3f} (cells {nvalid})")

sn = A["stats_native"] - B["stats_native"]
sh = A["stats_harmonised"] - B["stats_harmonised"]
xr.Dataset(save_maps, coords={"lat": clat, "lon": clon},
           attrs={"description": "Gridded window-offset diagnostic, IMERG-L HH vs CPC-UNI "
                  "0.5deg, native + harmonised, pre-GPM era (2014 transition excluded)",
                  "years": tag}).to_netcdf(OUT / f"gridded_cpc_window_hstar_{tag}.nc4")
np.savez(OUT / f"gridded_cpc_window_pooled_{tag}.npz", H=H,
         years=np.arange(2001, 2014), **save_pooled)
np.savez(OUT / f"gridded_cpc_window_stats_{tag}.npz", H=H,
         stats_native=sn, stats_harmonised=sh, band=band, clat=clat, clon=clon,
         years=np.arange(2001, 2014))
plot_gridded(clat, clon, results, 2001, 2013, tag)
print(f"saved pre-GPM (2001-2013) outputs for {tag}")
