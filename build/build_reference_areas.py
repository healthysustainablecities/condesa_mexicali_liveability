"""Build the reference geometries handed to analysis teams.

Writes ``geography/mexicali_reference_areas.gpkg`` (EPSG:6366) --
geometry, identifiers and population only, with **no indicator
values**.  Teams join their results to these layers on ``area_id``, so
the geometries must be identical for everyone.

Geometry and identifiers come from the **source** datasets rather than
the GHSCI output tables.  GHSCI deletes areas with no source units
within their aggregation catchment, so its tables hold 11,702 of the
14,989 Condesa lots, 37 of 40 fraccionamientos, 14,185 of 14,236
manzanas and 435 of 436 AGEBs.  Those omissions are legitimate for
indicator values -- there is genuinely nothing to report -- but a
reference layer must list every area, or teams have nothing to join
partial results onto and the gaps become invisible.

Population is apportioned by area from the 100 m GHS-POP 2025 grid
produced by the run, so it is consistent across every scale and
available for areas GHSCI dropped.

Run after the analysis has completed::

    python build/build_reference_areas.py
"""

import os
import sys

import geopandas as gpd
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
DATA = os.path.dirname(os.path.dirname(PROJECT_DIR))
CRS = 'EPSG:6366'

CODENAME = 'MX_Mexicali_2025_ULI'
RUN_GPKG = os.path.join(
    DATA, '_study_region_outputs', CODENAME, f'{CODENAME}_1600m_buffer.gpkg'
)
TARGET = os.path.join(
    PROJECT_DIR, 'geography', 'mexicali_reference_areas.gpkg'
)
BOUNDARIES = os.path.join(DATA, 'MX', 'CFC', 'mexicali_uli_boundaries.gpkg')
CONDESA = os.path.join(DATA, 'MX', 'CFC', 'Nvo desarrollo')

# (layer, source path, layer within source, identifier column)
SOURCES = [
    (
        'agebs',
        os.path.join(DATA, 'MX', 'mexicali_AGEB_population.geojson'),
        None,
        'CVEGEO',
    ),
    # MXL_MZAPob is preferred over mexicali_manzanas_population.geojson:
    # population is recorded for all but 61 manzanas rather than all but
    # 682, and it adds 61 rural manzanas.  It has 580 fewer records
    # overall, the difference being near-empty urban blocks (687 records
    # holding 85 people between them).  Supplied in Mexico ITRF2008 LCC
    # and reprojected here.
    (
        'manzanas',
        os.path.join(DATA, 'MX', 'CFC', 'MXL_MZAPob.gpkg'),
        '02m',
        'CVEGEO',
    ),
    (
        'condesa_fraccionamientos',
        os.path.join(CONDESA, '_Fraccionamientos.geojson'),
        None,
        'FID',
    ),
    (
        'condesa_lotes',
        os.path.join(CONDESA, 'Lotes_desarrollo_EXE.geojson'),
        None,
        'ID',
    ),
]

COLUMNS = ['area_id', 'area_name', 'area_sqm', 'pop_2025', 'geometry']


def apportion_population(target, grid):
    """Area-apportioned GHS-POP 2025 population for each target area.

    Population is a count, so each grid cell's total is split between
    the areas overlapping it in proportion to the share of the cell
    they cover.
    """
    pieces = gpd.overlay(
        target[['area_id', 'geometry']],
        grid,
        how='intersection',
        keep_geom_type=False,
    )
    if pieces.empty:
        return pd.Series(0.0, index=target.index).values
    share = pieces.geometry.area / pieces['cell_area']
    pieces['pop'] = share * pieces['pop_est']
    totals = pieces.groupby('area_id')['pop'].sum()
    return target['area_id'].map(totals).fillna(0.0).values


def tidy(frame, area_id, area_name, grid):
    frame = frame.to_crs(CRS).copy()
    frame['area_id'] = area_id.astype(str)
    frame['area_name'] = area_name
    frame['area_sqm'] = frame.geometry.area
    frame['pop_2025'] = apportion_population(frame, grid)
    return frame[COLUMNS]


def main():
    if not os.path.exists(RUN_GPKG):
        raise SystemExit(
            f'Analysis output not found:\n  {RUN_GPKG}\n'
            'Run the MX_Mexicali_2025_ULI analysis and generate step first.'
        )
    os.makedirs(os.path.dirname(TARGET), exist_ok=True)
    if os.path.exists(TARGET):
        os.remove(TARGET)

    print('Reading the 100 m population grid ...')
    grid = gpd.read_file(RUN_GPKG, layer='indicators_100m_2025').to_crs(CRS)
    grid = grid[['grid_id', 'pop_est', 'geometry']].copy()
    grid['cell_area'] = grid.geometry.area
    print(
        f'  {len(grid):,} cells, {grid["pop_est"].sum():,.0f} persons, '
        f'{grid["cell_area"].median():,.0f} m2 cells'
    )

    written = {}

    # The grid is itself a reporting scale.
    grid_layer = grid.rename(columns={'grid_id': 'area_id'}).copy()
    grid_layer['area_id'] = grid_layer['area_id'].astype(str)
    grid_layer['area_name'] = None
    grid_layer['area_sqm'] = grid_layer['cell_area']
    grid_layer['pop_2025'] = grid_layer['pop_est']
    grid_layer[COLUMNS].to_file(TARGET, layer='grid_100m', driver='GPKG')
    written['grid_100m'] = len(grid_layer)

    for layer, path, source_layer, id_column in SOURCES:
        frame = (
            gpd.read_file(path, layer=source_layer)
            if source_layer
            else gpd.read_file(path)
        )
        out = tidy(frame, frame[id_column], None, grid)
        out.to_file(TARGET, layer=layer, driver='GPKG')
        written[layer] = len(out)

    # The two reporting regions, as one layer of two rows.
    regions = []
    for area_id, source_layer in (
        ('mexicali', 'region_mexicali'),
        ('condesa', 'region_condesa'),
    ):
        frame = gpd.read_file(BOUNDARIES, layer=source_layer)
        regions.append(
            tidy(
                frame,
                pd.Series([area_id] * len(frame), index=frame.index),
                area_id.title(),
                grid,
            )
        )
    region = gpd.GeoDataFrame(
        pd.concat(regions, ignore_index=True), geometry='geometry', crs=CRS
    )
    region.to_file(TARGET, layer='region', driver='GPKG')
    written['region'] = len(region)

    print(f'\nWritten {TARGET}\n')
    print(f'{"layer":28s} {"areas":>8s} {"population":>12s}  unique ids')
    for layer in written:
        frame = gpd.read_file(TARGET, layer=layer)
        unique = 'yes' if not frame['area_id'].duplicated().any() else 'NO'
        assert str(frame.crs).endswith('6366'), f'{layer} is not EPSG:6366'
        print(
            f'{layer:28s} {len(frame):>8,} '
            f'{frame["pop_2025"].sum():>12,.0f}  {unique}'
        )


if __name__ == '__main__':
    sys.exit(main())
