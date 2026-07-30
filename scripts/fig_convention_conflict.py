"""Figure: IMERG half-hourly daily correlation vs aggregation-window offset h,
against CPC-UNI (calibration) and BMKG (validation), GPM era 2015-2021.
Shows the convention conflict: CPC-UNI peaks at the UTC window, BMKG at -23 h.
Numbers are provisional (Final-HH cache); will be re-locked on Late-HH."""
import sys
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "temp" / "subdaily_lag"))
from build_subdaily_seasonal import windowed_cumsum
from subdaily_stats import r_from_stats
from src.config import initialize_config; initialize_config(str(ROOT / "config.yml"))
from src import config
from src.station_validation import load_station_observations

CACHE = ROOT / "temp" / "subdaily_lag" / "hh_cache"
H = np.arange(-48, 49, 1); SLOTS = 48
T, P, wmo = [], [], None
for y in range(2015, 2022):
    d = np.load(CACHE / f"hh_cache_{y}.npz", allow_pickle=True)
    T.append(d["times"]); P.append(d["precip"]); wmo = d["wmo"].astype(int)
times = pd.DatetimeIndex(np.concatenate(T)); precip = np.concatenate(P, 0).astype("float32")
csum, vcum = windowed_cumsum(precip); slot = pd.Series(np.arange(len(times)), index=times)

obs = load_station_observations(config.STATION_DATA_FILE, config.STATION_FILE).reindex(columns=wmo)
loc = pd.read_csv(config.STATION_FILE, sep=None, engine="python").set_index("ID_WMO").reindex(wmo)
cpc = xr.open_dataset(config.cpc_file)["precip"]
if float(cpc.lat[0]) > float(cpc.lat[-1]): cpc = cpc.reindex(lat=cpc.lat[::-1])
li = np.abs(cpc.lat.values[:, None] - loc.Lat.values[None, :]).argmin(0)
oi = np.abs(cpc.lon.values[:, None] - loc.Lon.values[None, :]).argmin(0)
cpc_st = pd.DataFrame(cpc.values[:, li, oi], index=pd.DatetimeIndex(cpc.time.values), columns=wmo)

dates = pd.date_range("2015-01-01", "2021-12-31"); d0 = dates.normalize(); nt = len(times)
def sweep(ydf):
    Y = ydf.reindex(dates).values; st = np.zeros((len(H), 6))
    for hi, h in enumerate(H):
        i0 = slot.reindex(d0 + pd.Timedelta(hours=int(h))).values
        ok = np.isfinite(i0); i0i = np.where(ok, np.nan_to_num(i0), 0).astype(int)
        end = np.minimum(i0i + SLOTS, nt); full = ok & (i0i + SLOTS <= nt)
        v = vcum[end] - vcum[i0i]; w = csum[end] - csum[i0i]
        good = full[:, None] & (v == SLOTS) & np.isfinite(Y)
        x = np.where(good, w, 0.0); y = np.where(good, Y, 0.0)
        st[hi] = [good.sum(), x.sum(), y.sum(), (x*x).sum(), (y*y).sum(), (x*y).sum()]
    return r_from_stats(st)

r_cpc = sweep(cpc_st)
r_bmkg = sweep(obs)
# CPC relabelled to the local-observation day (+1 day): its peak moves to -23 h
cpc_relabel = cpc_st.copy(); cpc_relabel.index = cpc_relabel.index + pd.Timedelta(days=1)
r_cpc_re = sweep(cpc_relabel)
hc = int(H[np.nanargmax(r_cpc)]); hb = int(H[np.nanargmax(r_bmkg)]); hr = int(H[np.nanargmax(r_cpc_re)])
print(f"CPC native h*={hc:+d} r={np.nanmax(r_cpc):.3f} | BMKG h*={hb:+d} r={np.nanmax(r_bmkg):.3f} "
      f"| CPC relabelled h*={hr:+d} r={np.nanmax(r_cpc_re):.3f}")

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
out = ROOT / "temp" / "subdaily_lag" / "convention_conflict.png"
fig.savefig(out, dpi=180, facecolor="white"); plt.close(fig)
np.savez(ROOT / "temp/subdaily_lag/convention_conflict.npz",
         H=H, r_cpc=r_cpc, r_bmkg=r_bmkg, r_cpc_relabelled=r_cpc_re)
print("wrote", out.name)
