"""Appendix Figure G.5 - Difference maps for the representative day.

Layout: portrait, 3 rows x 1 col.
  (a) IMERG-L minus CPC-UNI
  (b) LSEQM+DL minus CPC-UNI
  (c) LSEQM+DL minus IMERG-L (net correction effect)

Output: paper/thesis/figures/fig_thesis_G1_differences.png
"""
import sys
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from helpers import (
    draw_panel, setup_panel_grid, load_boundaries,
    load_corrected_dekad, load_raw, precip_var, FIGOUT,
)

DATE = "2025-01-01"
MONTH, DEKAD = 1, "01"

print(f"Loading products for differences on {DATE}...")
ds_imergl = load_raw("imergl")
ds_cpc    = load_raw("cpcuni")
ds_lsdl   = load_corrected_dekad("lseqmdl", MONTH, DEKAD)

def day(ds, d):
    return precip_var(ds).sel(time=d).squeeze()

imergl = day(ds_imergl, DATE)
cpc    = day(ds_cpc, DATE)
lsdl   = day(ds_lsdl, DATE)

diff_panels = [
    (imergl - cpc,    "(a) IMERG-L $-$ CPC-UNI"),
    (lsdl   - cpc,    "(b) LSEQM+DL $-$ CPC-UNI"),
    (lsdl   - imergl, "(c) LSEQM+DL $-$ IMERG-L (net correction effect)"),
]

lon = imergl.lon.values
lat = imergl.lat.values
idn, wld = load_boundaries()

diff_norm = mpl.colors.TwoSlopeNorm(vcenter=0, vmin=-50, vmax=50)

fig, axes = setup_panel_grid(
    rows=3, cols=1, panel_width_cm=11.0, right=0.88,
    suptitle=f"Per-pixel difference maps, {DATE}",
)

qm = None
for ax, (field, title) in zip(axes, diff_panels):
    qm = draw_panel(ax, lon, lat, field.values, cmap="RdBu_r", norm=diff_norm,
                    idn_adm1=idn, world_adm0=wld, title=title)

# Vertical colorbar on the right
bbox_top = axes[0].get_position()
bbox_bot = axes[-1].get_position()
cax = fig.add_axes([0.90, bbox_bot.y0, 0.018, bbox_top.y1 - bbox_bot.y0])
cbar = fig.colorbar(qm, cax=cax, extend="both",
                    ticks=[-50, -20, -10, -5, 0, 5, 10, 20, 50])
cbar.ax.tick_params(labelsize=6)
cbar.set_label("Difference (mm/day)", fontsize=7)

out = FIGOUT / "fig_thesis_G1_differences.png"
fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.05)
print(f"  wrote {out} ({out.stat().st_size//1024} KB)")
