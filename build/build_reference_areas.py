"""Build the reference geometries handed to analysis teams.

Reads the GeoPackage produced by the ``MX_Mexicali_2025_ULI`` GHSCI run
and writes ``geography/mexicali_reference_areas.gpkg`` -- geometry,
identifiers and population only, with **no indicator values**.  Teams
join their results to these layers on ``area_id``, so the geometries
must be identical for everyone.

The 100 m grid is the GHS-POP 2025 population grid as reprojected from
Mollweide into EPSG:6366 and vectorised by GHSCI (sum resampling, so
population counts are conserved).  Cells are therefore approximately,
not exactly, 100 m.

Run after the analysis has completed::

    python build/build_reference_areas.py
"""

import os
import sys

import geopandas as gpd
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
CRS = 'EPSG:6366'

CODENAME = 'MX_Mexicali_2025_ULI'
SOURCE = os.path.join(
    os.path.dirname(os.path.dirname(PROJECT_DIR)),
    '_study_region_outputs',
    CODENAME,
    f'{CODENAME}_1600m_buffer.gpkg',
)
TARGET = os.path.join(
    PROJECT_DIR, 'geography', 'mexicali_reference_areas.gpkg'
)

# (output layer, source layer, native identifier column)
LAYERS = [
    ('grid_100m', 'indicators_100m_2025', 'grid_id'),
    ('agebs', 'indicators_agebs', 'cvegeo'),
    ('manzanas', 'indicators_manzanas', 'cvegeo'),
    ('condesa_fraccionamientos', 'indicators_condesa_fraccionamientos', 'fid'),
    ('condesa_lotes', 'indicators_condesa_lotes', 'id'),
]

REGION_LAYERS = [
    ('mexicali', 'indicators_region_mexicali'),
    ('condesa', 'indicators_region_condesa'),
]

KEEP = ['area_id', 'native_id', 'area_sqm', 'pop_2025', 'geometry']


def available(path):
    import pyogrio

    return {name for name, _ in pyogrio.list_layers(path)}


def tidy(frame, area_id, native_id):
    """Reduce a GHSCI indicator layer to identifiers and population."""
    frame = frame.to_crs(CRS).copy()
    frame['area_id'] = area_id
    frame['native_id'] = native_id
    frame['area_sqm'] = frame.geometry.area
    # GHSCI names the population estimate pop_est at every scale.
    frame['pop_2025'] = (
        pd.to_numeric(frame['pop_est'], errors='coerce')
        if 'pop_est' in frame.columns
        else pd.NA
    )
    return frame[KEEP]


def pick_id(frame, preferred):
    """Return a usable identifier series, falling back to ogc_fid."""
    for column in (preferred, 'ogc_fid', 'grid_id'):
        if column and column in frame.columns:
            return frame[column].astype(str), column
    return (
        pd.Series(range(1, len(frame) + 1), index=frame.index).astype(str),
        'row number',
    )


def main():
    if not os.path.exists(SOURCE):
        raise SystemExit(
            f'Analysis output not found:\n  {SOURCE}\n'
            'Run the MX_Mexicali_2025_ULI analysis and generate step first.'
        )
    layers = available(SOURCE)
    os.makedirs(os.path.dirname(TARGET), exist_ok=True)
    if os.path.exists(TARGET):
        os.remove(TARGET)

    print(f'Reading {os.path.basename(SOURCE)}')
    written = []

    for name, source_layer, id_column in LAYERS:
        if source_layer not in layers:
            print(f'  ! {name:26s} missing source layer {source_layer!r}')
            continue
        frame = gpd.read_file(SOURCE, layer=source_layer)
        area_id, used = pick_id(frame, id_column)
        out = tidy(frame, area_id, area_id)
        out.to_file(TARGET, layer=name, driver='GPKG')
        written.append(name)
        population = out['pop_2025'].sum(skipna=True)
        print(
            f'  {name:26s} {len(out):>7,} areas  id={used:<9s} '
            f'pop={population:>10,.0f}'
        )

    # The two reporting regions become one layer of two rows.
    regions = []
    for area_id, source_layer in REGION_LAYERS:
        if source_layer not in layers:
            print(f'  ! region {area_id:19s} missing {source_layer!r}')
            continue
        frame = gpd.read_file(SOURCE, layer=source_layer)
        regions.append(tidy(frame, area_id, area_id))
    if regions:
        region = pd.concat(regions, ignore_index=True)
        region = gpd.GeoDataFrame(region, geometry='geometry', crs=CRS)
        region.to_file(TARGET, layer='region', driver='GPKG')
        written.append('region')
        for _, row in region.iterrows():
            print(
                f'  {"region/" + row["area_id"]:26s} '
                f'{row["area_sqm"] / 1e6:>10,.1f} km2  '
                f'pop={row["pop_2025"]:>10,.0f}'
            )

    _report(written)


def _report(written):
    print(f'\nWritten {TARGET}')
    for name in written:
        frame = gpd.read_file(TARGET, layer=name)
        assert str(frame.crs).upper().endswith('6366'), (
            f'{name} is not EPSG:6366'
        )
        duplicated = frame['area_id'].duplicated().sum()
        if duplicated:
            print(f'  ! {name}: {duplicated} duplicate area_id values')
    print(f'  {len(written)} layers, all EPSG:6366, area_id unique')


if __name__ == '__main__':
    sys.exit(main())
