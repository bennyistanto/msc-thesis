"""Appendix Figure G.1 - Six-product comparison for a single representative day.

Layout: portrait, 2 columns x 3 rows, tight Bali-style boundaries with
Indonesian admin-1 provinces and neighbour-country admin-0 borders.

Output: paper/thesis/figures/fig_thesis_G4_six_products.png
"""
import sys
from pathlib import Path
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from helpers import (
    draw_panel, setup_panel_grid, add_horizontal_colorbar,
    load_boundaries, load_corrected_dekad, load_raw, precip_var,
    PRECIP_BOUNDS, FIGOUT,
)

DATE = "2025-01-01"
MONTH, DEKAD = 1, "01"

print(f"Loading products for {DATE} ...")
ds_imergl = load_raw("imergl")
ds_imergf = load_raw("imergf")
ds_cpc    = load_raw("cpcuni")
ds_ls     = load_corrected_dekad("ls",      MONTH, DEKAD)
ds_lseqm  = load_corrected_dekad("lseqm",   MONTH, DEKAD)
ds_lsdl   = load_corrected_dekad("lseqmdl", MONTH, DEKAD)

day = lambda ds: precip_var(ds).sel(time=DATE).squeeze()
fields = dict(
    imergl=day(ds_imergl), imergf=day(ds_imergf), cpc=day(ds_cpc),
    ls=day(ds_ls), lseqm=day(ds_lseqm), lsdl=day(ds_lsdl),
)
lon = fields["imergl"].lon.values
lat = fields["imergl"].lat.values
idn, wld = load_boundaries()

fig, axes = setup_panel_grid(
    rows=3, cols=2,
    suptitle=f"Daily precipitation, {DATE} - six-product comparison",
)

panels = [
    (axes[0, 0], fields["imergl"], "(a) IMERG-L (raw Late Run)"),
    (axes[0, 1], fields["imergf"], "(b) IMERG-F (Final Run, gauge-anchored)"),
    (axes[1, 0], fields["ls"],     "(c) LS stage"),
    (axes[1, 1], fields["lseqm"],  "(d) LSEQM stage"),
    (axes[2, 0], fields["lsdl"],   "(e) LSEQM+DL (corrected output)"),
    (axes[2, 1], fields["cpc"],    "(f) CPC-UNI (gauge reference)"),
]

qm = None
for i, (ax, field, title) in enumerate(panels):
    # i % 2 == 1 means right column -> suppress y tick labels
    qm = draw_panel(ax, lon, lat, field.values, idn_adm1=idn,
                    world_adm0=wld, title=title, title_fontsize=6,
                    show_y_ticklabels=(i % 2 == 0))

add_horizontal_colorbar(fig, qm, "Daily precipitation (mm/day)",
                        ticks=PRECIP_BOUNDS)

out = FIGOUT / "fig_thesis_G4_six_products.png"
fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.05)
print(f"  wrote {out} ({out.stat().st_size//1024} KB)")
