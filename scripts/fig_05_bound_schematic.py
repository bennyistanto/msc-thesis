"""Generate a 2-panel schematic for Chapter 5 Discussion §5.1.

Panel A: same paired time series before and after marginal correction.
         Shows: rank order at each pixel is preserved; spread is widened
         to match the gauge; day-by-day pairing is unchanged.
Panel B: bar chart of the bound. Three stages on the x-axis. Pearson r
         (left y-axis) stays flat at 0.34; SDR (right y-axis) moves to 1.

Output: paper/thesis/figures/fig_thesis_05_bound_schematic.png
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

# --- repo root (scripts/ is 4 levels below: root/paper/thesis/scripts) ---
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

# --- synthetic example: one pixel, 30 daily values ---
rng = np.random.default_rng(42)
n_days = 30
gauge = rng.gamma(shape=1.5, scale=4.0, size=n_days)
# Raw satellite: under-spread + offset, but day-by-day correlated with gauge at r~0.34
noise = rng.normal(0, 1.0, size=n_days)
raw_sat = 0.5 * gauge + 0.3 * gauge.std() * noise + 0.4
# Corrected satellite: same rank order as raw, spread matched to gauge
ranks = np.argsort(np.argsort(raw_sat))
gauge_sorted = np.sort(gauge)
corrected_sat = gauge_sorted[ranks]  # rank-preserved remap to gauge marginal

# Compute headline numbers shown on Panel B (rounded values from thesis Ch 4)
stages = ['Raw\n(IMERG-L)', 'LSEQM', 'LSEQM+DL']
pearson_r = [0.343, 0.345, 0.348]   # thesis Ch 4 numbers
sdr = [0.71, 1.03, 1.00]            # thesis Ch 4 numbers

# --- figure ---
fig, (axA, axB) = plt.subplots(2, 1, figsize=(8.5, 9.0),
                                gridspec_kw={'height_ratios': [1.1, 1.0]})
fig.subplots_adjust(top=0.92, bottom=0.07, left=0.10, right=0.90, hspace=0.28)

# Panel A: paired time series
days = np.arange(1, n_days + 1)
axA.plot(days, gauge, 'o-', color='#1f77b4', label='Gauge (target)',
         linewidth=1.6, markersize=4)
axA.plot(days, raw_sat, 's--', color='#d62728', label='Raw IMERG-L',
         linewidth=1.2, markersize=3.5, alpha=0.85)
axA.plot(days, corrected_sat, '^:', color='#2ca02c',
         label='LSEQM+DL (rank-preserved)', linewidth=1.2, markersize=4)
axA.set_xlabel('Day of dekad', fontsize=9)
axA.set_ylabel('Daily precipitation (mm/day)', fontsize=9)
axA.set_title('(a) Day-by-day pairing is fixed by the satellite',
              fontsize=10, pad=8)
axA.set_ylim(0, 14)
axA.legend(loc='upper right', fontsize=8, framealpha=0.9)
axA.grid(alpha=0.3)
axA.tick_params(labelsize=8)

# Annotate: indicate that ranks are preserved
axA.text(0.02, 0.97,
         'Both red and green follow the same\nday-by-day '
         'ordering: rank-preserved.\nGreen matches gauge spread; red '
         'does not.',
         transform=axA.transAxes, fontsize=8, va='top', ha='left',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow',
                   edgecolor='gray', alpha=0.85))

# Panel B: bound visualisation
x = np.arange(len(stages))
bar_w = 0.35
axB.bar(x - bar_w/2, pearson_r, bar_w, color='#d62728',
        label='Pearson $r$ (left axis)', alpha=0.85)
axB.set_ylabel('Pearson $r$', color='#d62728', fontsize=9)
axB.set_ylim(0, 1.05)
axB.tick_params(axis='y', labelcolor='#d62728', labelsize=8)
axB.axhline(0.348, color='#d62728', linestyle=':', linewidth=1, alpha=0.5)
axB.text(1.825, 0.40, 'bound\n$\\approx 0.35$', color='#d62728', fontsize=8,
         ha='center', va='bottom')

axB2 = axB.twinx()
axB2.bar(x + bar_w/2, sdr, bar_w, color='#2ca02c',
         label='SDR (right axis)', alpha=0.85)
axB2.set_ylabel('Standard deviation ratio', color='#2ca02c', fontsize=9)
axB2.set_ylim(0, 1.2)
axB2.axhline(1.0, color='#2ca02c', linestyle=':', linewidth=1, alpha=0.5)
axB2.tick_params(axis='y', labelcolor='#2ca02c', labelsize=8)
axB2.text(-0.45, 1.04, 'target = 1.0', color='#2ca02c', fontsize=8,
          ha='left')

axB.set_xticks(x)
axB.set_xticklabels(stages, fontsize=8)
axB.set_title('(b) One metric moves, one does not',
              fontsize=10, pad=8)

# Suptitle
fig.suptitle('Theoretical bound under marginal correction: '
             'rank preservation $\\Rightarrow$ flat $r$, '
             'spread match $\\Rightarrow$ SDR $\\to 1$',
             fontsize=10, y=0.975)

out = 'paper/thesis/figures/fig_thesis_05_bound_schematic.png'
plt.savefig(out, dpi=180, bbox_inches='tight')
print(f'OK: {out} ({os.path.getsize(out)//1024} KB)')
