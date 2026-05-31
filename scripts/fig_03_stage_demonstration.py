"""Generate Figure 3.3 (Thesis Chapter 3): Stage-by-stage demonstration on
sample data, illustrating what each LSEQM+DL stage does to the daily series.

3 x 3 grid (9 panels). Clean matplotlib (no XKCD). Includes a dedicated
EQM quantile-mapping mechanism panel that shows the source-to-target
quantile mapping directly via arrows between the CDFs.

Synthetic data; figure caption labels it as illustrative.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from scipy import stats

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
np.random.seed(42)

# ----- Style -----
PAL = {
    'obs':      '#1a237e',  # navy (observed)
    'raw':      '#e65100',  # orange (raw IMERG)
    'ls':       '#880e4f',  # pink (LS)
    'eqm':      '#1565c0',  # blue (EQM)
    'gpd':      '#f57f17',  # amber (GPD)
    'cnn':      '#2e7d32',  # green (CNN / LSEQM+DL)
    'target':   '#555555',
    'grid':     '#cccccc',
}

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size':   9,
    'axes.titlesize': 10,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 7.5,
    'axes.grid': True,
    'grid.alpha': 0.3,
})


# =========================================================================
# Data generation - synthetic but representative tropical daily precip
# =========================================================================
n = 60
day = np.arange(1, n + 1)

# Observed series (BMKG): ~55% wet days, Gamma intensities, 5 heavy events
obs = np.zeros(n)
wet_mask = np.random.rand(n) < 0.55
obs[wet_mask] = np.random.gamma(shape=1.0, scale=8.0, size=wet_mask.sum())
heavy_idx = np.random.choice(np.where(wet_mask)[0], size=5, replace=False)
obs[heavy_idx] = np.random.uniform(40, 90, size=5)

# Raw IMERG: over-detect drizzle, under-shoot heavy, ~12% mean under-bias
raw = obs.copy()
extra_wet = np.random.rand(n) < 0.30
raw[(~wet_mask) & extra_wet] = np.random.gamma(0.7, 2.0, ((~wet_mask) & extra_wet).sum())
raw[heavy_idx] = raw[heavy_idx] * 0.55
raw = raw * np.random.normal(loc=0.95, scale=0.15, size=n)
raw = np.clip(raw, 0, None)
raw = raw * (obs.mean() * 0.88 / max(raw.mean(), 0.1))


# =========================================================================
# Apply the four stages
# =========================================================================
ls = raw * (obs.mean() / raw.mean())


def gamma_qmap(source, target):
    sw = source[source > 0]
    tw = target[target > 0]
    if len(sw) < 3 or len(tw) < 3:
        return source.copy()
    src_p = stats.gamma.fit(sw, floc=0)
    tgt_p = stats.gamma.fit(tw, floc=0)
    out = source.copy()
    mask = out > 0
    u = stats.gamma.cdf(out[mask], *src_p)
    out[mask] = stats.gamma.ppf(np.clip(u, 1e-6, 1 - 1e-6), *tgt_p)
    return out


eqm = gamma_qmap(ls, obs)


def gpd_tail_adjust(source, target, threshold_pct=80):
    out = source.copy()
    tw = target[target > 0]
    if len(tw) < 10:
        return out
    thr = np.percentile(tw, threshold_pct)
    above_idx = np.where(out > thr)[0]
    if len(above_idx) == 0:
        return out
    tgt_exc = tw[tw > thr] - thr
    if len(tgt_exc) < 3:
        return out
    shape, _, scale = stats.genpareto.fit(tgt_exc, floc=0)
    src_exc = out[above_idx] - thr
    u = np.arange(1, len(src_exc) + 1) / (len(src_exc) + 1)
    ranks = src_exc.argsort().argsort()
    mapped = stats.genpareto.ppf(np.clip(u, 1e-6, 1 - 1e-6), shape, loc=0, scale=scale)
    out[above_idx] = thr + mapped[ranks]
    return out


gpd_out = gpd_tail_adjust(eqm, obs, threshold_pct=80)

ALPHA = 0.70
thr_obs = np.percentile(obs[obs > 0], 80)
lseqm_dl = gpd_out.copy()
extreme_mask = lseqm_dl > thr_obs
lseqm_dl[extreme_mask] = (
    ALPHA * lseqm_dl[extreme_mask] +
    (1 - ALPHA) * obs[extreme_mask] * np.random.normal(1.0, 0.05, extreme_mask.sum())
)


# =========================================================================
# Data sanity check (DECISIONS.md §2a)
# =========================================================================
def sanity_check():
    n_obs_wet = (obs > 0).sum()
    n_raw_wet = (raw > 0).sum()
    assert 25 <= n_obs_wet <= 45, f'obs wet days {n_obs_wet} outside expected 25-45'
    assert n_raw_wet >= n_obs_wet, f'raw should over-detect; got {n_raw_wet} vs {n_obs_wet}'
    raw_rb = (raw.mean() - obs.mean()) / obs.mean()
    assert raw_rb < -0.05, f'raw should under-bias; got RB={raw_rb:.3f}'
    ls_rb = (ls.mean() - obs.mean()) / obs.mean()
    assert abs(ls_rb) < 0.01, f'LS should match obs mean; got RB={ls_rb:.3f}'
    q99 = lambda x: np.percentile(x, 99)
    assert q99(gpd_out) / q99(obs) > q99(eqm) / q99(obs), \
        'GPD should lift Q99 closer to obs vs EQM'
    print('  Sanity check PASS')
    print(f'  obs wet days  : {n_obs_wet:>3d}')
    print(f'  raw wet days  : {n_raw_wet:>3d}  (over-detection: +{n_raw_wet - n_obs_wet})')
    print(f'  raw RB        : {raw_rb:+.3f}  (expected: < -0.05)')
    print(f'  LS  RB        : {ls_rb:+.3f}  (expected: ~0)')
    for name, x in [('raw', raw), ('eqm', eqm), ('gpd', gpd_out), ('lseqm_dl', lseqm_dl)]:
        print(f'  Q99 {name:>10s}  : {q99(x):>5.1f}  ratio={q99(x)/q99(obs):.2f}')


sanity_check()


def stage_metrics(s, o):
    rb = (s.mean() - o.mean()) / o.mean()
    sdr = s.std() / o.std()
    q99 = np.percentile(s, 99) / np.percentile(o, 99)
    return rb, sdr, q99


METRICS = {
    'Raw IMERG':  stage_metrics(raw, obs),
    'After LS':   stage_metrics(ls, obs),
    'After EQM':  stage_metrics(eqm, obs),
    'After GPD':  stage_metrics(gpd_out, obs),
    'LSEQM+DL':   stage_metrics(lseqm_dl, obs),
}


# =========================================================================
# Figure: 3 x 3 panels
# =========================================================================
fig, axes = plt.subplots(3, 3, figsize=(15, 12.8), constrained_layout=True)
# Add extra vertical padding so the main title is clearly separated from
# the first-row panel titles.
fig.set_constrained_layout_pads(w_pad=0.05, h_pad=0.12,
                                hspace=0.08, wspace=0.05)
fig.suptitle(
    'Illustrative Effect of the LSEQM+DL Pipeline Stages on a 60-day Sample',
    fontsize=13, fontweight='bold', y=1.025
)
width = 0.40


# --- (a) Raw IMERG vs CPC-UNI reference ---
ax = axes[0, 0]
ax.bar(day - width/2, obs, width, color=PAL['obs'], label='CPC-UNI (reference)', alpha=0.95)
ax.bar(day + width/2, raw, width, color=PAL['raw'], label='IMERG (raw)', alpha=0.90)
ax.set_title('(a) Raw IMERG vs CPC-UNI reference')
ax.set_xlabel('Day')
ax.set_ylabel('Precipitation (mm/day)')
ax.legend(loc='upper right', frameon=True)
ax.set_xlim(0.5, n + 0.5)


# --- (b) Stage 1 LS: mean matched ---
ax = axes[0, 1]
ax.bar(day - width/2, obs, width, color=PAL['obs'], label='CPC-UNI (reference)', alpha=0.95)
ax.bar(day + width/2, ls, width, color=PAL['ls'], label='After LS', alpha=0.90)
ax.axhline(obs.mean(), color=PAL['obs'], lw=1.0, ls='--', alpha=0.7)
ax.axhline(ls.mean(),  color=PAL['ls'],  lw=1.0, ls='--', alpha=0.7)
ax.set_title(f'(b) Stage 1 LS: mean matched\n'
             f'$\\overline{{P}}$ obs={obs.mean():.1f}, LS={ls.mean():.1f}')
ax.set_xlabel('Day')
ax.set_ylabel('Precipitation (mm/day)')
ax.legend(loc='upper right', frameon=True)
ax.set_xlim(0.5, n + 0.5)


# --- (c) Stage 2 EQM mechanism: quantile mapping arrows between source and target CDFs ---
ax = axes[0, 2]
# Fit Gamma to LS-corrected (source) and observed (target) wet-day samples
ls_wet = ls[ls > 0]
obs_wet = obs[obs > 0]
ls_gp = stats.gamma.fit(ls_wet, floc=0)
ob_gp = stats.gamma.fit(obs_wet, floc=0)

# Plot the two Gamma CDFs as smooth curves
x_grid = np.linspace(0, max(ls_wet.max(), obs_wet.max()) * 1.05, 300)
ls_cdf = stats.gamma.cdf(x_grid, *ls_gp)
ob_cdf = stats.gamma.cdf(x_grid, *ob_gp)
ax.plot(x_grid, ls_cdf, color=PAL['ls'], lw=1.8, label='LS source CDF')
ax.plot(x_grid, ob_cdf, color=PAL['obs'], lw=1.8, label='CPC-UNI target CDF')

# Show the quantile mapping at selected quantiles via arrows
for q in [0.4, 0.7, 0.92]:
    src_val = stats.gamma.ppf(q, *ls_gp)
    tgt_val = stats.gamma.ppf(q, *ob_gp)
    # Horizontal line at the quantile level (light)
    ax.plot([src_val, tgt_val], [q, q], color='#666666', lw=0.8, alpha=0.6, zorder=2)
    # Arrow from source value to target value at the same q
    arr = FancyArrowPatch((src_val, q), (tgt_val, q),
                          arrowstyle='->', mutation_scale=12,
                          color='#444444', lw=1.0, zorder=3)
    ax.add_patch(arr)
    # Markers at both ends
    ax.scatter([src_val], [q], color=PAL['ls'], s=30, zorder=4, edgecolor='white', linewidth=0.5)
    ax.scatter([tgt_val], [q], color=PAL['obs'], s=30, zorder=4, edgecolor='white', linewidth=0.5)
    ax.text(tgt_val + 0.5, q + 0.02, f'q={q:.2f}', fontsize=7, color='#444444', ha='left')

ax.set_title('(c) Stage 2 EQM mechanism\nquantile mapping (LS source $\\rightarrow$ Obs target)')
ax.set_xlabel('Wet-day precipitation (mm/day)')
ax.set_ylabel('Cumulative probability')
ax.set_ylim(0, 1.05)
ax.legend(loc='lower right', frameon=True)


# --- (d) Stage 2 EQM applied: bar chart ---
ax = axes[1, 0]
ax.bar(day - width/2, obs, width, color=PAL['obs'], label='CPC-UNI (reference)', alpha=0.95)
ax.bar(day + width/2, eqm, width, color=PAL['eqm'], label='After EQM', alpha=0.90)
ax.set_title('(d) Stage 2 EQM applied\ndistribution aligned')
ax.set_xlabel('Day')
ax.set_ylabel('Precipitation (mm/day)')
ax.legend(loc='upper right', frameon=True)
ax.set_xlim(0.5, n + 0.5)


# --- (e) Stage 3 GPD: wet-day quantile profile (Observed, EQM, GPD overlaid) ---
ax = axes[1, 1]
obs_sorted = np.sort(obs[obs > 0])
eqm_sorted = np.sort(eqm[eqm > 0])
gpd_sorted = np.sort(gpd_out[gpd_out > 0])

qo = np.linspace(0.05, 0.99, len(obs_sorted))
qe = np.linspace(0.05, 0.99, len(eqm_sorted))
qg = np.linspace(0.05, 0.99, len(gpd_sorted))

ax.plot(qo, obs_sorted, color=PAL['obs'], lw=2.0, marker='o', ms=4, label='CPC-UNI (reference)')
ax.plot(qe, eqm_sorted, color=PAL['eqm'], lw=1.5, marker='s', ms=3, alpha=0.85,
        label='After EQM (Gamma only)')
ax.plot(qg, gpd_sorted, color=PAL['gpd'], lw=1.7, marker='^', ms=3.5, alpha=0.95,
        label='After GPD (tail lifted)')
ax.axvline(0.80, color='gray', lw=0.8, ls='--', alpha=0.5)
ax.text(0.80, ax.get_ylim()[1] * 0.05, ' 80th pct threshold',
        ha='left', va='bottom', fontsize=7, color='gray', style='italic')
ax.set_title('(e) Stage 3 GPD\nextreme tail recovered')
ax.set_xlabel('Wet-day quantile')
ax.set_ylabel('Wet-day precipitation (mm/day)')
ax.legend(loc='upper left', frameon=True)


# --- (f) Empirical CDFs across all stages, wet-day only ---
ax = axes[1, 2]


def ecdf(x):
    xs = np.sort(x[x > 0])
    ys = np.arange(1, len(xs) + 1) / (len(xs) + 1)
    return xs, ys


xs, ys = ecdf(obs);      ax.plot(xs, ys, color=PAL['obs'], lw=2.0, label='CPC-UNI')
xs, ys = ecdf(raw);      ax.plot(xs, ys, color=PAL['raw'], lw=1.2, alpha=0.85, label='Raw')
xs, ys = ecdf(ls);       ax.plot(xs, ys, color=PAL['ls'],  lw=1.2, alpha=0.75, label='LS')
xs, ys = ecdf(eqm);      ax.plot(xs, ys, color=PAL['eqm'], lw=1.2, alpha=0.75, label='LSEQM')
xs, ys = ecdf(lseqm_dl); ax.plot(xs, ys, color=PAL['cnn'], lw=1.5, label='LSEQM+DL')
ax.set_title('(f) Wet-day empirical CDFs across stages')
ax.set_xlabel('Wet-day precipitation (mm/day)')
ax.set_ylabel('Cumulative probability')
ax.legend(loc='lower right', frameon=True)


# --- (g) Stage 4 CNN refinement scatter at extreme pixels ---
ax = axes[2, 0]
ax_idx = np.where(gpd_out > thr_obs)[0]
if len(ax_idx) > 0:
    ax.scatter(gpd_out[ax_idx], lseqm_dl[ax_idx],
               c=PAL['cnn'], s=55, edgecolor='white', linewidth=0.5,
               label=f'extreme pixels (n={len(ax_idx)})', zorder=3)
    mn = min(gpd_out[ax_idx].min(), lseqm_dl[ax_idx].min()) - 2
    mx = max(gpd_out[ax_idx].max(), lseqm_dl[ax_idx].max()) + 2
    ax.plot([mn, mx], [mn, mx], color='gray', ls='--', lw=1.0, alpha=0.7,
            label='y = x  (no CNN refinement)')
    ax.set_xlim(mn, mx); ax.set_ylim(mn, mx)
ax.set_title(f'(g) Stage 4 CNN refinement\n($\\alpha$={ALPHA}, extreme pixels only)')
ax.set_xlabel('Value after GPD (LSEQM)')
ax.set_ylabel('Value after CNN blend (LSEQM+DL)')
ax.legend(loc='upper left', frameon=True)


# --- (h) Final LSEQM+DL vs CPC-UNI reference ---
ax = axes[2, 1]
ax.bar(day - width/2, obs, width, color=PAL['obs'], label='CPC-UNI (reference)', alpha=0.95)
ax.bar(day + width/2, lseqm_dl, width, color=PAL['cnn'], label='LSEQM+DL', alpha=0.90)
ax.set_title('(h) Final corrected vs CPC-UNI')
ax.set_xlabel('Day')
ax.set_ylabel('Precipitation (mm/day)')
ax.legend(loc='upper right', frameon=True)
ax.set_xlim(0.5, n + 0.5)


# --- (i) Stage-skill summary (extended y range to avoid cutoff) ---
ax = axes[2, 2]
stages = list(METRICS.keys())
x_pos = np.arange(len(stages))
w = 0.27
rb_vals  = [METRICS[s][0] for s in stages]
sdr_dev  = [METRICS[s][1] - 1 for s in stages]
q99_dev  = [METRICS[s][2] - 1 for s in stages]

ax.bar(x_pos - w, rb_vals, w, color='#880e4f', label='Relative Bias')
ax.bar(x_pos,     sdr_dev, w, color='#1565c0', label='SDR $-$ 1')
ax.bar(x_pos + w, q99_dev, w, color='#f57f17', label='$Q_{99}$ ratio $-$ 1')
ax.axhline(0, color='black', lw=0.8)
ax.set_xticks(x_pos)
ax.set_xticklabels(stages, rotation=20, ha='right')
ax.set_ylabel('Deviation from target (= 0)')
ax.set_title('(i) Stage-skill summary')
ax.legend(loc='best', frameon=True, fontsize=7)
# Compute a tight, symmetric y range that includes all bar tips with padding
all_vals = rb_vals + sdr_dev + q99_dev
ymin = min(all_vals)
ymax = max(all_vals)
span = max(abs(ymin), abs(ymax)) * 1.15
ax.set_ylim(-span, span)


# Save
os.makedirs('paper/thesis/figures', exist_ok=True)
out = 'paper/thesis/figures/fig_thesis_03_stage_demonstration.png'
plt.savefig(out, dpi=300, bbox_inches='tight')
print(f'Saved: {out}')
print(f'Panel (i) y-range: [{-span:.2f}, {span:.2f}]')
