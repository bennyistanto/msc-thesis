"""Provenance for the BMKG archive completeness figures in Chapter 3.

Recomputes ledger rows C13 and C15 from the study's own station archive, so the
completeness statistics printed in Section 3.2.5 have a reader-visible source.

    C13  36.2% of 1,380,600 station-days missing (880,702 valid)
    C15  median station missing 24.0%; 51 of 180 stations missing > 50%;
         by-year 22.7% missing (2011, best) to 50.9% (2015, worst)

WHY THIS SCRIPT EXISTS RATHER THAN A CITATION TO THE PARSING NOTEBOOK
--------------------------------------------------------------------
The exploratory notebook that first reviewed this archive counts only NaN. BMKG
codes a missing day as the sentinel value 8888.0, which is not NaN, so a NaN-only
count understates the gap by 76,778 station-days (5.6 percentage points) and
would also treat 8888 as 8888 mm of rain in any rainfall statistic. Every figure
below counts a station-day as missing if it is NaN *or* equal to the sentinel.

Reported alongside, because it is easy to conflate:
    sentinel share of station-days           = 5.6%
    sentinel share of cells carrying a value = 8.0%   (Appendix B quotes this one)

Source: data/input/stations/idn_cli_weatherstation_data_bmkg.csv
        (config.yml -> station_validation.station_data_file)
Layout: columns ID, Date (DD-MM-YYYY), JD, then one column per WMO station id.

Run:
    python paper/thesis/scripts/verify_bmkg_completeness.py
"""
import os

import numpy as np
import pandas as pd

SENTINEL = 8888.0
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
CSV = os.path.join(ROOT, 'data', 'input', 'stations',
                   'idn_cli_weatherstation_data_bmkg.csv')


def main():
    df = pd.read_csv(CSV)
    meta = ('ID', 'Date', 'JD')
    stations = [c for c in df.columns if c not in meta]
    vals = df[stations]

    year = pd.to_datetime(df['Date'], format='%d-%m-%Y').dt.year

    # A station-day is missing if it is NaN or carries the sentinel.
    missing = vals.isna() | (vals == SENTINEL)

    n_stations = len(stations)
    n_days = len(df)
    n_cells = missing.size
    n_missing = int(missing.to_numpy().sum())
    n_valid = n_cells - n_missing
    n_nan = int(vals.isna().to_numpy().sum())
    n_sent = int((vals == SENTINEL).to_numpy().sum())

    print('archive          : %d stations x %d days = %s station-days'
          % (n_stations, n_days, format(n_cells, ',')))
    print('valid            : %s' % format(n_valid, ','))
    print('missing          : %s  (%.1f%%)          [C13]'
          % (format(n_missing, ','), 100 * n_missing / n_cells))
    print('  of which NaN   : %s  (%.1f%%)' % (format(n_nan, ','), 100 * n_nan / n_cells))
    print('  of which 8888  : %s  (%.1f%%  of all station-days;'
          ' %.1f%% of cells carrying a value)'
          % (format(n_sent, ','), 100 * n_sent / n_cells,
             100 * n_sent / (n_cells - n_nan)))
    print()

    # Per-station completeness
    per_station = missing.mean(axis=0) * 100
    print('per-station missing %%: median %.1f%%, mean %.1f%%      [C15]'
          % (per_station.median(), per_station.mean()))
    print('stations missing > 50%%: %d of %d                       [C15]'
          % (int((per_station > 50).sum()), n_stations))
    print('  worst station: %s (%.1f%%)   best: %s (%.1f%%)'
          % (per_station.idxmax(), per_station.max(),
             per_station.idxmin(), per_station.min()))
    print()

    # Per-year completeness: share of that year's station-days that are missing
    by_year = missing.groupby(year.values).mean().mean(axis=1) * 100
    print('per-year missing %%: best %d = %.1f%%, worst %d = %.1f%%   [C15]'
          % (by_year.idxmin(), by_year.min(), by_year.idxmax(), by_year.max()))
    print()
    print('  year  missing%')
    for y, v in by_year.items():
        print('  %4d   %5.1f' % (y, v))


if __name__ == '__main__':
    main()
