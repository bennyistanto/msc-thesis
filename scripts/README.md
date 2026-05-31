# Figure scripts

One script per figure in the thesis. Run any script from this directory:

```bash
python fig_04_paradox.py
```

Each script reads input data from the parent project's `data/output/`
tree and writes its PNG into `../figures/`. The data archive is
documented in Appendix B of the thesis (Zenodo DOI cited there).

## Coverage

The table below maps every figure in the thesis to the script that
produces it. Two figures (3.2 and 3.3) are hand-drawn diagrams with
no Python source; everything else is a standalone script in this
folder.

| Figure                                       | Script                              |
| -------------------------------------------- | ----------------------------------- |
| 3.1 BMKG station distribution                | `fig_03_station_map.py`             |
| 3.2 LSEQM+DL conceptual workflow             | _none - SVG diagram_                |
| 3.3 Stage 4 CNN architecture                 | _none - SVG diagram_                |
| 3.4 Stage demonstration on synthetic sample  | `fig_03_stage_demonstration.py`     |
| 4.1 Stage-wise skill (4-panel bars)          | `fig_04_headline_bars.py`           |
| 4.2 Multi-threshold verification (POD/FAR/CSI/ETS) | `fig_04_multi_threshold.py`   |
| 4.3 Paradox (r vs RMSE/NSE/SDR)              | `fig_04_paradox.py`                 |
| 4.4 CQI spatial maps (LS / LSEQM / LSEQM+DL) | `fig_04_cqi_spatial.py`             |
| 4.5 CQI improvement (delta map + category)   | `fig_04_cqi_improvement.py`         |
| 4.6 Taylor by station (seasonal)             | `fig_04_taylor_by_station.py`       |
| 4.7 Temporal stability                       | `fig_04_temporal_stability.py`      |
| 4.8 Bali reproducibility subdomain coverage  | `fig_04_bali_coverage.py`           |
| 5.1 Theoretical bound schematic              | `fig_05_bound_schematic.py`         |
| 5.2 Monthly Taylor diagram (12-panel)        | `fig_05_taylor_monthly.py`          |
| 5.3 Station-density confidence mask          | `fig_05_confidence_mask.py`         |
| G.1 Difference maps                          | `fig_G1_differences.py`             |
| G.2 Three-day x three-product panel          | `fig_G2_three_days.py`              |
| G.3 Four-pillar climatological metric maps   | `fig_G3_pillar_metrics.py`          |
| G.4 Six-product comparison (1 Jan 2025)      | `fig_G4_six_products.py`            |
| G.5 Station-overlay climatology              | `fig_G5_station_overlay.py`         |

The two hand-drawn diagrams (Figures 3.2 and 3.3) ship as both `.svg`
(editable in Inkscape) and `.png` (the LaTeX-included raster) in
`../figures/`: `fig_thesis_03_pipeline.svg` for Figure 3.2 and
`fig_thesis_03_cnn_workflow.svg` for Figure 3.3. No Python re-render
is provided because the diagrams are conceptual rather than data-driven.

## Shared utilities

Two helper modules sit alongside the figure scripts. Neither is a
figure-generating script.

- `helpers.py` - spatial-map utilities: Indonesia admin-1 boundaries,
  world admin-0 boundaries, panel-grid layout, precipitation
  colormap. Imported by the CQI and atlas figures.
- `taylor_helpers.py` - Taylor diagram utilities: polar-grid drawing,
  per-station aggregation, split legend builder. Imported by
  `fig_04_taylor_by_station.py` and `fig_05_taylor_monthly.py`.

## Dependencies

Standard scientific Python stack:

- numpy, pandas, xarray, scipy
- matplotlib
- geopandas, shapely (for the spatial-map scripts)

The exact pinned versions used for the thesis figures are recorded in
the parent code repository's `environment.yml` /
`requirements.txt`.

## Notes on reproducibility

- Scripts use absolute paths to the data archive on the original
  workstation. Adjust the `ROOT` constant near the top of each script
  to point at your local checkout if you re-run them.
- Aggregate-statistic scripts (4.1, 4.3) hard-code the headline numbers
  reported in Tables 4.1-4.2; they do not re-load the NetCDF stack.
  This is intentional because those numbers are themselves pinned in
  the thesis.
- Spatial-map scripts re-load and re-aggregate from the NetCDF stack on
  every run.
