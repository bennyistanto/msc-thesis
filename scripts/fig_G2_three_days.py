"""Appendix Figure G.2 - Three-day x three-product daily contrast.

Layout: portrait, 3 rows x 3 cols.
  Rows: 1 / 5 / 10 January 2025 (start, middle, end of dekad-1)
  Cols: IMERG-L (raw) | CPC-UNI (gauge reference) | LSEQM+DL (corrected)

Output: paper/thesis/figures/fig_thesis_G2_three_days.png
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import (
    draw_panel, setup_panel_grid, add_horizontal_colorbar,
    load_boundaries, load_corrected_dekad, load_raw, precip_var,
    PRECIP_BOUNDS, FIGOUT,
)

DATES = ["2025-01-01", "2025-01-05", "2025-01-10"]
LABELS = ["1 January 2025", "5 January 2025", "10 January 2025"]
MONTH, DEKAD = 1, "01"

print("Loading products...")
ds_imergl = load_raw("imergl")
ds_cpc    = load_raw("cpcuni")
ds_lsdl   = load_corrected_dekad("lseqmdl", MONTH, DEKAD)

def day(ds, d):
    return precip_var(ds).sel(time=d).squeeze()

lon = ds_imergl.lon.values
lat = ds_imergl.lat.values
idn, wld = load_boundaries()

fig, axes = setup_panel_grid(
    rows=3, cols=3,
    suptitle="Day-to-day variation across three products, dekad-1 January 2025",
)

qm = None
for r, (date, label) in enumerate(zip(DATES, LABELS)):
    for c, (name, ds) in enumerate([
        ("IMERG-L (raw)",        ds_imergl),
        ("CPC-UNI (gauge ref.)", ds_cpc),
        ("LSEQM+DL (corrected)", ds_lsdl),
    ]):
        ax = axes[r, c]
        field = day(ds, date)
        title = name if r == 0 else None
        qm = draw_panel(ax, lon, lat, field.values, idn_adm1=idn,
                        world_adm0=wld, title=title, title_fontsize=6,
                        show_y_ticklabels=(c == 0))
        if c == 0:
            ax.set_ylabel(label, fontsize=6, labelpad=8)

add_horizontal_colorbar(fig, qm, "Daily precipitation (mm/day)",
                        ticks=PRECIP_BOUNDS)

out = FIGOUT / "fig_thesis_G2_three_days.png"
fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.05)
print(f"  wrote {out} ({out.stat().st_size//1024} KB)")
