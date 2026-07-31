"""Generate the 3-panel Figure 5.1 for Chapter 5 Discussion §5.1.

REAL DATA. An earlier version illustrated the mechanism on a synthetic Gamma
draw built as raw = 0.5*gauge + small noise, which forces r = 0.93 and so showed
the corrected product landing on the gauge's rain days - the opposite of the
r = 0.34 reported in Table 4.1. The argument is now demonstrated on the archive
itself, zooming out top to bottom:  reality -> mechanism -> consequence.

Panel A: ONE month = THREE dekads. Kalianget (Jawa), January 2021. The gauge
         peaks on days 4 and 6, the satellite on day 7. January is fitted as
         three dekads, each with its own correction mapping: within every dekad
         the corrected series re-orders NOTHING (0, 0, 0 reversals), and the only
         4 crossings across the month fall at the dekad hand-overs. Spread moves
         to the gauge (0.69 -> 0.95). Rank preservation is a within-dekad
         property, and this panel shows it holding dekad by dekad.
Panel B: THE SAME dekad-of-year across ALL years (1 to 10 Jan, 2001 to 2021,
         n = 195). One dekad-of-year is fitted with ONE correction mapping, so a
         single curve is meaningful here. Corrected against raw is a rising
         curve: one satellite value gives one corrected value. Gauge against raw
         is a cloud. No re-shaping of the horizontal axis turns a cloud into a
         line, which is why r cannot move (0.368 -> 0.357 on this sample).
Panel C: ALL 172 stations (Table 4.1, 36 dekads, 2001 to 2021): r flat, SDR -> 1.

Measured at this station over Jan dekad 1 (n = 195), raw sorted ascending:
  LSEQM     : 0 of 194 re-orderings -> exactly monotone (pure marginal QM)
  LSEQM+DL  : 6 of 194 re-orderings, ~1 mm spread at equal raw. The 3x3
              convolution mixes neighbouring pixels on the 21.5% of days it
              touches, so the product is not strictly a function of the pixel
              value. It still buys no timing skill (r 0.368 -> 0.357). This is
              the quantitative form of the "small rank-changing contribution of
              the spatial CNN refinement" qualifier in the section proposition.
Over the full record at this station, ZERO rank reversals occur within a dekad;
Spearman falls below 1 only where dry-day matching maps raw>0 to exactly 0 and
creates ties (~43% of days; raw IMERG-L is dry on only 0.2%).

Station selected by scanning all 175 stations with a valid paired record: its
full record (n = 6414) gives r 0.344 -> 0.332, matching the Table 4.1 headline
of 0.343 -> 0.348. Runner-up: 97570 Sudjarwo Tjondro Negoro (Papua), Apr 2009
dekad 2 (rho = 1.000, spread 0.667 -> 1.021).

Output: paper/thesis/figures/fig_thesis_05_bound_schematic.png
"""
import os
import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import spearmanr
import matplotlib.pyplot as plt

# --- repo root (scripts/ is 4 levels below: root/paper/thesis/scripts) ---
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

WMO = 96973                     # Kalianget, Jawa
CORR_DIR = 'data/output/corrected_lseqmdl/'
DEKAD_FILE = CORR_DIR + 'idn_cli_lseqmdl_corrected_imergl_month01_dekad01.nc4'
# January is fitted as THREE dekads, each with its own correction mapping.
JAN_FILES = [CORR_DIR + f'idn_cli_lseqmdl_corrected_imergl_month01_dekad{d}.nc4'
             for d in ('01', '11', '21')]
RAW_FILE = 'data/input/imergl/idn_imergl.nc4'
WINDOW = pd.date_range('2021-01-01', '2021-01-31')     # a full month = 3 dekads
STATION = 'Kalianget (Jawa)'

# --- station location and gauge series ---
loc = pd.read_csv('data/input/stations/idn_cli_weatherstation_location_bmkg.csv',
                  sep=';', encoding='utf-8-sig')
srow = loc[loc['ID_WMO'].astype(int) == WMO].iloc[0]
slat, slon = float(srow['Lat']), float(srow['Lon'])

obs = pd.read_csv('data/input/stations/idn_cli_weatherstation_data_bmkg.csv')
obs['Date'] = pd.to_datetime(obs['Date'], format='%d-%m-%Y')
obs = obs.set_index('Date').replace(8888.0, np.nan)
gauge_all = pd.to_numeric(obs[str(WMO)], errors='coerce')


def at_pixel(path, days):
    """Daily value at the station pixel."""
    ds = xr.open_dataset(path)
    if ds.lat[0] > ds.lat[-1]:
        ds = ds.reindex(lat=ds.lat[::-1])
    v = (ds['precipitation'].sel(time=days)
         .isel(lat=int(np.abs(ds.lat.values - slat).argmin()),
               lon=int(np.abs(ds.lon.values - slon).argmin()))
         .values.astype(float))
    ds.close()
    return v


# every day of Jan dekad 1 across the record: ONE correction mapping
dsc = xr.open_dataset(DEKAD_FILE)
dek_days = pd.to_datetime(dsc.time.values)
dsc.close()
dek_days = dek_days[dek_days.isin(gauge_all.dropna().index)]

corr_d = at_pixel(DEKAD_FILE, dek_days)
raw_d = at_pixel(RAW_FILE, dek_days)
gauge_d = gauge_all.loc[dek_days].values.astype(float)
m = np.isfinite(raw_d) & np.isfinite(corr_d) & np.isfinite(gauge_d)
raw_d, corr_d, gauge_d = raw_d[m], corr_d[m], gauge_d[m]
r_rg = np.corrcoef(raw_d, gauge_d)[0, 1]
r_cg = np.corrcoef(corr_d, gauge_d)[0, 1]

# Panel (a): a full month, assembled across the three January dekad files. The
# first dekad of it is the same sample panel (b) generalises over 21 years.
def corrected_month(days):
    out = pd.Series(index=days, dtype=float)
    for f in JAN_FILES:
        ds = xr.open_dataset(f)
        t = pd.to_datetime(ds.time.values)
        ds.close()
        hit = days.intersection(t)
        if len(hit):
            out.loc[hit] = at_pixel(f, hit)
    return out.values


gauge_w = gauge_all.loc[WINDOW].values.astype(float)
raw_w = at_pixel(RAW_FILE, WINDOW)
corr_w = corrected_month(WINDOW)
dek_w = np.clip((WINDOW.day.values - 1) // 10, 0, 2)

# Rank preservation is a within-dekad property: each dekad carries its own
# mapping, so crossings can only appear where one mapping hands over to the next.
rev_in = []
for k in (0, 1, 2):
    s = dek_w == k
    a, b = raw_w[s], corr_w[s]
    o = np.argsort(a)
    rev_in.append(int((np.diff(b[o]) < -1e-6).sum()))
o_all = np.argsort(raw_w)
rev_all = int((np.diff(corr_w[o_all]) < -1e-6).sum())
ok = np.isfinite(gauge_w)
sdr_raw_w = raw_w[ok].std() / gauge_w[ok].std()
sdr_corr_w = corr_w[ok].std() / gauge_w[ok].std()
assert sum(rev_in) == 0, f'a dekad re-orders values: {rev_in}'

stages = ['Raw (IMERG-L)', 'LSEQM', 'LSEQM+DL']
pearson_r = [0.343, 0.345, 0.348]   # Table 4.1
sdr = [0.71, 1.03, 1.00]            # Table 4.1

BLUE, RED, GREEN = '#1f77b4', '#d62728', '#2ca02c'

# Three stacked WIDE panels: the figure spans the full textwidth, so wide and
# short saves about an inch of page height over the old portrait stack. Panel (b)
# gets the most height: it is the only panel whose horizontal and vertical axes
# carry the same quantity, so squashing it would flatten the 45-degree curve that
# carries the argument.
fig, (axA, axB, axC) = plt.subplots(
    3, 1, figsize=(8.6, 7.7), gridspec_kw={'height_ratios': [1.00, 1.28, 0.88]})
fig.subplots_adjust(top=0.965, bottom=0.058, left=0.088, right=0.905, hspace=0.44)

# ---------- (a) one dekad ----------
days = WINDOW.day.values
axA.plot(days, gauge_w, 'o-', color=BLUE, label='Gauge (BMKG, target)', lw=1.4, ms=3.5)
axA.plot(days, raw_w, 's--', color=RED, label='Raw IMERG-L', lw=1.1, ms=3, alpha=0.9)
axA.plot(days, corr_w, '^:', color=GREEN, label='LSEQM+DL', lw=1.1, ms=3.5)
axA.set_xlabel('Day of January 2021', fontsize=8.5)
axA.set_ylabel('Precipitation\n(mm/day)', fontsize=8.5)
axA.set_title(f'(a) Satellite and gauge peak on different days: {STATION}, January 2021',
              fontsize=9.5, loc='left', pad=5)
axA.set_xticks(np.arange(1, 32, 2))
# headroom for a one-row legend with the note tucked directly beneath it
# Extra headroom: the upper third of the panel is reserved for a stacked
# top-centre block - dekad labels, then the legend, then the note - so the data
# occupies the lower two thirds unobstructed.
axA.set_ylim(0, float(np.nanmax([np.nanmax(gauge_w), raw_w.max(), corr_w.max()])) * 2.05)
top = axA.get_ylim()[1]
# Each dekad is fitted with its own mapping: mark the hand-over points.
for xb in (10.5, 20.5):
    axA.axvline(xb, color='0.55', ls='--', lw=0.8, zorder=1)
for xc, lbl in ((5.5, 'dekad 1'), (15.5, 'dekad 2'), (26.0, 'dekad 3')):
    axA.text(xc, top * 0.985, lbl, fontsize=6.8, color='0.4', ha='center', va='top')
axA.grid(alpha=0.3)
axA.tick_params(labelsize=7.5)
# legend centred below the dekad labels
axA.legend(loc='upper center', fontsize=7.2, framealpha=0.9, ncol=3,
           bbox_to_anchor=(0.5, 0.905))
# note centred below the legend
axA.text(0.5, 0.70,
         f'Each dekad is fitted with its own mapping; within each, the corrected '
         f'series re-orders nothing\n({rev_in[0]}, {rev_in[1]} and {rev_in[2]} '
         f'reversals). The {rev_all} crossings across the month fall only at the '
         f'dekad hand-overs. Spread moves {sdr_raw_w:.2f} to {sdr_corr_w:.2f}.',
         transform=axA.transAxes, fontsize=7.2, va='top', ha='center')

# ---------- (b) the mechanism ----------
axB.scatter(raw_d, gauge_d, s=20, color=BLUE, alpha=0.55, edgecolors='none',
            label=f'Gauge   ($r$ = {r_rg:.2f})', zorder=2)
o = np.argsort(raw_d)
axB.plot(raw_d[o], corr_d[o], '-', color=GREEN, lw=1.4, alpha=0.85, zorder=3)
axB.scatter(raw_d, corr_d, s=16, marker='^', color=GREEN, edgecolors='none',
            label='LSEQM+DL', zorder=4)
axB.set_xlabel('Raw IMERG-L (mm/day)', fontsize=8.5)
axB.set_ylabel('Corrected / gauge\n(mm/day)', fontsize=8.5)
axB.set_title('(b) The correction can only re-value, not re-order: '
              f'every 1 to 10 January, 2001 to 2021 ($n$ = {m.sum()})',
              fontsize=9.5, loc='left', pad=5)
# headroom so the note sits in clear space at the top instead of across the
# curve and the cloud, which both top out near 78 mm
axB.set_ylim(0, float(max(corr_d.max(), gauge_d.max())) * 1.45)
axB.grid(alpha=0.3)
axB.tick_params(labelsize=7.5)
axB.legend(loc='upper left', fontsize=7.2, framealpha=0.9, ncol=2)
axB.text(0.985, 0.905,
         'One satellite value gives one corrected value (green curve); the gauge is '
         'a cloud around it.\nNo re-shaping of the horizontal axis turns a cloud into '
         f'a line, so $r$ holds: {r_rg:.2f} to {r_cg:.2f}.',
         transform=axB.transAxes, fontsize=7.2, va='top', ha='right')

# ---------- (c) the consequence ----------
x = np.arange(len(stages))
bar_w = 0.32
axC.bar(x - bar_w/2, pearson_r, bar_w, color=RED, alpha=0.85)
axC.set_ylabel('Pearson $r$', color=RED, fontsize=8.5)
axC.set_ylim(0, 1.15)
axC.set_xlim(-0.6, 2.6)
axC.tick_params(axis='y', labelcolor=RED, labelsize=7.5)
axC.axhline(0.348, color=RED, linestyle=':', linewidth=1, alpha=0.6)
axC.text(-0.55, 0.40, 'bound $\\approx 0.35$', color=RED, fontsize=7.5,
         ha='left', va='bottom')
axC2 = axC.twinx()
axC2.bar(x + bar_w/2, sdr, bar_w, color=GREEN, alpha=0.85)
axC2.set_ylabel('Std. deviation ratio', color=GREEN, fontsize=8.5)
axC2.set_ylim(0, 1.32)
axC2.axhline(1.0, color=GREEN, linestyle=':', linewidth=1, alpha=0.6)
axC2.tick_params(axis='y', labelcolor=GREEN, labelsize=7.5)
axC2.text(2.55, 1.04, 'target = 1.0', color=GREEN, fontsize=7.5, ha='right')
axC.set_xticks(x)
axC.set_xticklabels(stages, fontsize=8.5)
axC.set_title('(c) So $r$ stays flat while spread reaches the gauge: '
              '172 stations, 36 dekads, 2001 to 2021',
              fontsize=9.5, loc='left', pad=5)

out = 'paper/thesis/figures/fig_thesis_05_bound_schematic.png'
plt.savefig(out, dpi=200, bbox_inches='tight')
print(f'OK: {out} ({os.path.getsize(out)//1024} KB) | '
      f'panel a within-dekad reversals={rev_in} across-month={rev_all} '
      f'sdr {sdr_raw_w:.3f}->{sdr_corr_w:.3f} | '
      f'panel b n={m.sum()} r {r_rg:.3f}->{r_cg:.3f}')
