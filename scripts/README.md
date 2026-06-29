# Figure scripts

Every data-driven figure in the thesis has one self-contained script here, named
`fig_<chapter>_<name>.py`. Each reads its input data, plots, and writes its PNG
straight into `../figures/`. Run any of them from this directory:

```bash
python fig_04_paradox.py
```

Most scripts read the pipeline outputs in the parent project's `data/output/`
tree. The temporal-alignment figures (3.6, 4.4-4.6, 5.3-5.5, D.1, H.1-H.2) read
the window-offset sweep `.npz` outputs and the half-hourly station cache from the
diagnostic working directory (`temp/subdaily_lag`, part of the data archive); they
share `subdaily_helpers.py`. Two conceptual diagrams (Figures 3.2 and 3.4) are
hand-drawn SVGs, not Python. The data archive is documented in Appendix B of the
thesis (Zenodo DOI cited there).

## Coverage

Every figure in the thesis, mapped to the script that produces it.

| Figure | Title | Script |
| ------ | ----- | ------ |
| 3.1  | BMKG station distribution                         | `fig_03_station_map.py` |
| 3.2  | LSEQM+DL conceptual workflow                      | _SVG - `paper/images/fig_thesis_03_pipeline_copy.svg`_ |
| 3.3  | BCSD reference-parameter disaggregation 0.5->0.1  | `fig_03_bcsd_disaggregation.py` |
| 3.4  | Stage 4 CNN architecture                          | _SVG - `paper/images/fig03_cnn_pipeline.svg`_ |
| 3.5  | Stage demonstration on a synthetic sample         | `fig_03_stage_demonstration.py` |
| 3.6  | Why a -23 h window aligns satellite and gauge     | `fig_03_window_schematic.py` |
| 4.1  | Stage-wise skill (4-panel bars)                   | `fig_04_headline_bars.py` |
| 4.2  | Threshold-stratified verification (POD/FAR/CSI/ETS)| `fig_04_multi_threshold.py` |
| 4.3  | Paradox (r vs RMSE/NSE/SDR)                       | `fig_04_paradox.py` |
| 4.4  | Window-offset correlation recovery by era         | `fig_04_window_era.py` |
| 4.5  | GPM-era window-offset correlation + seasonal stability | `fig_04_window_seasonal.py` |
| 4.6  | Per-station optimal window offset and lift        | `fig_04_window_map.py` |
| 4.7  | CQI spatial maps (LS / LSEQM / LSEQM+DL)          | `fig_04_cqi_spatial.py` |
| 4.8  | CQI improvement (LSEQM -> LSEQM+DL)               | `fig_04_cqi_improvement.py` |
| 4.9  | Taylor diagram by station (seasonal)              | `fig_04_taylor_by_station.py` |
| 4.10 | Monthly temporal stability                        | `fig_04_temporal_stability.py` |
| 4.11 | Bali reproducibility subdomain                    | `fig_04_bali_coverage.py` |
| 5.1  | Theoretical bound schematic                       | `fig_05_bound_schematic.py` |
| 5.2  | Monthly Taylor diagram                            | `fig_05_taylor_monthly.py` |
| 5.3  | Calendar-window convention conflict + resolution  | `fig_05_convention.py` |
| 5.4  | Gridded window offset vs CPC-UNI (full record)    | `fig_05_gridded_cpc.py` |
| 5.5  | Why the recovery is confined to the GPM era       | `fig_05_window_precision.py` |
| 5.6  | Station-density confidence mask                   | `fig_05_confidence_mask.py` |
| D.1  | Per-station sampling stability (noise + selection)| `fig_99_noise_selection.py` |
| G.1  | Difference maps                                   | `fig_G1_differences.py` |
| G.2  | Three-day x three-product panel                   | `fig_G2_three_days.py` |
| G.3  | Four-pillar climatological metric maps            | `fig_G3_pillar_metrics.py` |
| G.4  | Six-product comparison (1 Jan 2025)               | `fig_G4_six_products.py` |
| G.5  | Station-overlay climatology                       | `fig_G5_station_overlay.py` |
| H.1  | Gridded window offset vs CPC-UNI, TRMM-input era  | `fig_H1_gridded_trmm.py` |
| H.2  | Gridded window offset vs CPC-UNI, GPM era         | `fig_H2_gridded_gpm.py` |

(`figures/ipb.png` is the institutional cover logo, not a thesis figure.)

The two hand-drawn diagrams (3.2, 3.4) have their SVG sources in the parent
repository under `paper/images/`. They were exported to PNG and the PNG shipped
in `../figures/`; no Python re-render is provided because the diagrams are
conceptual rather than data-driven.

## Shared utilities

Three helper modules sit alongside the figure scripts. None is itself a
figure-generating script.

- `helpers.py` - spatial-map utilities (Indonesia admin-1 boundaries, world
  admin-0 boundaries, panel-grid layout, precipitation colormap). Imported by
  the CQI and atlas figures.
- `taylor_helpers.py` - Taylor diagram utilities (polar grid, per-station
  aggregation, split legend). Imported by `fig_04_taylor_by_station.py` and
  `fig_05_taylor_monthly.py`.
- `subdaily_helpers.py` - temporal-alignment diagnostic utilities: the
  sufficient-statistics Pearson r, the half-hourly window machinery, the
  timezone-band styling, and the gridded h*-map drawing. Imported by the
  window-offset figures (3.6, 4.4-4.6, 5.3-5.5, D.1, H.1-H.2). The diagnostic's
  sweep `.npz` outputs and half-hourly station cache live in
  `temp/subdaily_lag` (data archive); adjust the `ROOT` constant there to point
  at your local checkout.

## Dependencies

Standard scientific Python stack: numpy, pandas, xarray, scipy, matplotlib, and
geopandas + shapely (spatial-map scripts). Pinned versions are in the parent
repository's `environment.yml` / `requirements.txt`.

## Notes on reproducibility

- Scripts use absolute paths to the data archive on the original workstation.
  Adjust the `ROOT` constant near the top of each script (and of
  `subdaily_helpers.py`) to point at your local checkout before re-running.
- Aggregate-statistic scripts (4.1, 4.3) hard-code the headline numbers reported
  in Tables 4.1-4.2; they do not re-load the NetCDF stack, by design, because
  those numbers are themselves pinned in the thesis.
- Spatial-map scripts re-load and re-aggregate from the NetCDF stack on every run.
- The temporal-alignment figures read the window-offset sweep `.npz` outputs;
  the two day-lag / per-station-distribution figures (5.5, D.1) additionally read
  the half-hourly station cache and recompute on every run. Regenerating the
  sweep outputs from raw inputs requires the half-hourly IMERG-L archive.
