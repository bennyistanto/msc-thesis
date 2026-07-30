"""Merge the 2015-2021 and 2022-2025 gridded-CPC sweeps into a single full
GPM-era (2015-2025) result and figure. Sufficient statistics are additive, so
this is an exact pooling with no re-sweep. Produces the GPM single-era figure
used in the appendix, matching the 2001-2014 TRMM-input figure's style.
"""
import numpy as np
import xarray as xr
from gridded_cpc_window import reduce_one, plot_gridded, OUT, H

A = np.load(OUT / "gridded_cpc_window_stats_2015_2021.npz")
B = np.load(OUT / "gridded_cpc_window_stats_2022_2025.npz")
band = A["band"]; clat = A["clat"]; clon = A["clon"]
tag = "2015_2025"

results, save_maps, save_pooled = {}, {}, {}
for lab in ("native", "harmonised"):
    S = A[f"stats_{lab}"] + B[f"stats_{lab}"]
    hstar, rstar, pooled, pooled_band, nvalid = reduce_one(S, band)
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
    print(f"[{lab}] peak h*={int(H[np.nanargmax(pooled)]):+d} r={np.nanmax(pooled):.3f} "
          f"(cells {nvalid})")

# stats sum so the merged tag can be re-pooled / combined later like the others
stats_native = A["stats_native"] + B["stats_native"]
stats_harmonised = A["stats_harmonised"] + B["stats_harmonised"]
xr.Dataset(save_maps, coords={"lat": clat, "lon": clon},
           attrs={"description": "Gridded window-offset diagnostic, IMERG-L HH vs "
                  "CPC-UNI 0.5deg, native + harmonised, merged full GPM era",
                  "years": tag}).to_netcdf(OUT / f"gridded_cpc_window_hstar_{tag}.nc4")
np.savez(OUT / f"gridded_cpc_window_pooled_{tag}.npz", H=H,
         years=np.arange(2015, 2026), **save_pooled)
np.savez(OUT / f"gridded_cpc_window_stats_{tag}.npz", H=H,
         stats_native=stats_native, stats_harmonised=stats_harmonised,
         band=band, clat=clat, clon=clon, years=np.arange(2015, 2026))
plot_gridded(clat, clon, results, 2015, 2025, tag)
print(f"saved merged full-GPM outputs for {tag}")
