"""Appendix Figure G.3 - Four-pillar climatological metric maps x three stages.

Layout: portrait, 4 rows x 3 cols.
  Rows: relative bias / KS p-value / Q99 ratio / CSI (one per pillar)
  Cols: LS | LSEQM | LSEQM+DL

Output: paper/thesis/figures/fig_thesis_G3_pillar_metrics.png
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

sys.path.insert(0, str(Path(__file__).parent))
from helpers import (
    draw_panel, setup_panel_grid, load_boundaries, load_metric, FIGOUT,
)

MONTH, DEKAD = 1, "01"

print("Loading metrics for dekad 1 Jan...")
metrics = {stage: load_metric(stage, MONTH, DEKAD)
           for stage in ("ls", "lseqm", "lseqmdl")}


def q99_ratio(ds):
    test, ref = ds["p99_test"], ds["p99_ref"]
    return (test / ref.where(ref > 0)).clip(0, 2)


# (variable-or-callable, row label, norm, cmap, colorbar ticks)
PILLARS = [
    ("relative_bias", "Rel. bias",
        mpl.colors.TwoSlopeNorm(vcenter=0, vmin=-0.5, vmax=0.5),
        "RdBu_r", [-0.5, -0.25, 0, 0.25, 0.5]),
    ("ks_pvalue", "KS $p$-value",
        mpl.colors.Normalize(vmin=0, vmax=1),
        "viridis", [0, 0.25, 0.5, 0.75, 1.0]),
    (q99_ratio, "$Q_{99}$ ratio",
        mpl.colors.TwoSlopeNorm(vcenter=1.0, vmin=0.0, vmax=2.0),
        "RdBu_r", [0, 0.5, 1.0, 1.5, 2.0]),
    ("csi", "CSI",
        mpl.colors.Normalize(vmin=0, vmax=1),
        "viridis", [0, 0.25, 0.5, 0.75, 1.0]),
]

STAGES = [("ls", "LS"), ("lseqm", "LSEQM"), ("lseqmdl", "LSEQM+DL")]

lon = metrics["ls"].lon.values
lat = metrics["ls"].lat.values
idn, wld = load_boundaries()

fig, axes = setup_panel_grid(
    rows=4, cols=3,
    right=0.88,
    suptitle="Per-pixel climatological metrics x three correction stages, dekad-1 January",
)

for r, (var, name, norm, cmap, ticks) in enumerate(PILLARS):
    last_qm = None
    for c, (stage, sname) in enumerate(STAGES):
        ax = axes[r, c]
        ds = metrics[stage]
        field = var(ds) if callable(var) else ds[var]
        last_qm = draw_panel(
            ax, lon, lat, field.values,
            cmap=cmap, norm=norm, idn_adm1=idn, world_adm0=wld,
            title=(sname if r == 0 else None),
            title_fontsize=7,
            show_y_ticklabels=(c == 0),
        )
        if c == 0:
            ax.set_ylabel(name, fontsize=7, labelpad=8)
    # row-level vertical colorbar on the right
    bbox = axes[r, -1].get_position()
    cax = fig.add_axes([0.895, bbox.y0 + 0.005, 0.015, bbox.height - 0.01])
    cbar = fig.colorbar(last_qm, cax=cax, ticks=ticks, extend="both")
    cbar.ax.tick_params(labelsize=5)

out = FIGOUT / "fig_thesis_G3_pillar_metrics.png"
fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.05)
print(f"  wrote {out} ({out.stat().st_size//1024} KB)")
