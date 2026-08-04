"""Reference geographies and the shared aggregation crosswalk.

Every work package reports against the same units, read from a single
reference geopackage, and aggregates between scales using a single
shared crosswalk.  This is what makes results from different analysts
additive and comparable; nobody should be building their own grid.

The reference geopackage
------------------------
``geography/mexicali_uli_geographies.gpkg`` holds one layer per
reporting geography (see :data:`uli.vocab.GEO_LEVELS`), each with a
``geo_id``, ``geo_level``, ``area_sqm``, ``population``,
``pop_census_2020``, ``dwellings`` and ``geometry``, all in EPSG:6366.

``population`` is the project denominator, apportioned from the GHS-POP
2025 100 m global population grid.  It is used for every
population-weighted aggregation, because the 2020 INEGI census records
no residents across most of the Condesa new development -- the area the
project most wants an answer for.  ``pop_census_2020`` retains the
INEGI count for reference and comparison.

The crosswalk
-------------
``geography/mexicali_uli_crosswalk.parquet`` is a long table of
overlaps between every pair of reporting geographies:

    from_level, from_id, to_level, to_id, area_sqm,
    share_of_from, population, dwellings

``area_sqm`` is the area of the intersection.  Aggregating a
native-scale result to any other scale is then a weighted groupby --
see :mod:`uli.aggregate`.

Both files are built by :func:`build`, which needs geopandas and the
source data under ``process/data/MX``.  Analysts do not normally run
it; they just call :func:`load` and :func:`crosswalk`.
"""

import os

import numpy as np
import pandas as pd

from . import vocab

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
GEOGRAPHY_DIR = os.path.join(PROJECT_DIR, 'geography')
GEOPACKAGE = os.path.join(
    GEOGRAPHY_DIR, 'mexicali_uli_geographies.gpkg'
)
CROSSWALK = os.path.join(GEOGRAPHY_DIR, 'mexicali_uli_crosswalk.parquet')

# Source data, relative to process/data (i.e. two levels above this
# project directory).  Only used by build().
DATA_DIR = os.path.dirname(os.path.dirname(PROJECT_DIR))
SOURCES = {
    'region': (
        '_study_region_outputs/MX_Mexicali_2025-MZA/'
        'MX_Mexicali_2025-MZA_1600m_buffer.gpkg'
    ),
    'ageb': 'MX/mexicali_AGEB_population.geojson',
    'manzana': 'MX/mexicali_manzanas_population.geojson',
    'condesa_fraccionamiento': (
        'MX/CFC/Nvo desarrollo/_Fraccionamientos.geojson'
    ),
    'condesa_lote': 'MX/CFC/Nvo desarrollo/Lotes_desarrollo_EXE.geojson',
    'ghs_pop_2025': (
        'MX/CFC/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R6_C8/'
        'GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R6_C8.tif'
    ),
    'ghs_pop_2030': (
        'MX/CFC/GHS_POP_E2030_GLOBE_R2023A_54009_100_V1_0_R6_C8/'
        'GHS_POP_E2030_GLOBE_R2023A_54009_100_V1_0_R6_C8.tif'
    ),
}

CITY_ID = 'MX_Mexicali_2025'

# GHS-POP release used as the project population denominator.
GHS_POP_CITATION = (
    'Schiavina, M., Freire, S., Carioli, A., MacManus, K. (2023). '
    'GHS-POP R2023A - GHS population grid multitemporal (1975-2030), '
    '100 m, Mollweide (ESRI:54009). European Commission, Joint '
    'Research Centre (JRC). '
    'https://doi.org/10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE'
)

# --------------------------------------------------------------------
# Condesa planned-occupancy assumptions
# --------------------------------------------------------------------
# The Condesa development is platted and roaded but essentially
# unoccupied: GHS-POP records 372 residents across it in 2025 and 377
# in 2030, and that population is concentrated in the fraccionamientos
# that physically touch existing settlement (364 of the 372 lie within
# 100 m of a populated 2020 manzana), which is the signature of areal
# apportionment from neighbouring cells rather than a measurement of
# Condesa.  No available population product will resolve this, because
# GHS-POP allocates a projected total onto observed built-up surface
# and the development has roads but few roofs.
#
# The planned population is therefore a declared assumption, not an
# estimate: one household per residential lot, at the mean Mexicali
# household size.  Both parameters are recorded in the geopackage
# metadata so that any result derived from them can be re-derived
# under different assumptions.
#
# CONFIRM BEFORE PUBLICATION: household size is taken as the Mexicali
# municipality mean from the INEGI Censo de Poblacion y Vivienda 2020;
# verify against the census tabulation rather than relying on this
# constant.
CONDESA_HOUSEHOLD_SIZE = 3.3

# Lots larger than this are treated as non-residential (commercial,
# civic, open space or undivided parcels) and are given no planned
# population.  2.6% of lots exceed 300 m2; the median lot is 120 m2.
CONDESA_RESIDENTIAL_LOT_MAX_SQM = 300

# Denominator columns carried on every reporting geography.
POPULATION_COLUMNS = (
    'population',
    'population_2030',
    'population_planned',
    'population_scenario_2030',
    'pop_census_2020',
    'dwellings',
)


def available():
    """True if the reference geographies have been built."""
    return os.path.exists(GEOPACKAGE) and os.path.exists(CROSSWALK)


def _require():
    if not available():
        raise FileNotFoundError(
            'Reference geographies not found.  Ask the project lead '
            'for geography/mexicali_uli_geographies.gpkg and '
            'geography/mexicali_uli_crosswalk.parquet, or rebuild '
            'them with `python -m uli.geography build`.'
        )


def load(geo_level, columns=None):
    """Return a reporting geography as a ``GeoDataFrame``."""
    import geopandas as gpd

    if geo_level not in vocab.GEO_LEVELS:
        raise ValueError(
            f'{geo_level!r} is not a reporting geography; expected one '
            f'of {sorted(vocab.GEO_LEVELS)}'
        )
    _require()
    frame = gpd.read_file(GEOPACKAGE, layer=geo_level)
    return frame[columns] if columns else frame


def units(geo_level):
    """Return the non-spatial unit table for a reporting geography."""
    frame = load(geo_level)
    return pd.DataFrame(frame.drop(columns='geometry'))


def crosswalk(from_level=None, to_level=None):
    """Return the overlap crosswalk, optionally filtered.

    Overlaps are stored once per unordered pair of levels; this
    function presents them in whichever direction is asked for, with
    ``share_of_from`` and every denominator column relative to
    ``from_level``.
    """
    _require()
    stored = pd.read_parquet(CROSSWALK)
    weights = [
        column[:-2]
        for column in stored.columns
        if column.endswith('_a') and column not in ('id_a', 'level_a')
    ]
    weights = [w for w in weights if w not in ('share_of',)]

    def oriented(side, other):
        renames = {
            f'level_{side}': 'from_level',
            f'id_{side}': 'from_id',
            f'level_{other}': 'to_level',
            f'id_{other}': 'to_id',
            f'share_of_{side}': 'share_of_from',
        }
        renames.update({f'{w}_{side}': w for w in weights})
        columns = [
            'from_level',
            'from_id',
            'to_level',
            'to_id',
            'area_sqm',
            'share_of_from',
        ] + weights
        return stored.rename(columns=renames)[columns]

    frame = pd.concat(
        [oriented('a', 'b'), oriented('b', 'a')], ignore_index=True
    )
    if from_level is not None:
        frame = frame[frame['from_level'] == from_level]
    if to_level is not None:
        frame = frame[frame['to_level'] == to_level]
    if frame.empty and from_level and to_level:
        raise ValueError(
            f'No crosswalk between {from_level!r} and {to_level!r}.'
        )
    return frame.reset_index(drop=True)


def condesa_ids(geo_level):
    """Return the ids at ``geo_level`` that overlap the Condesa area.

    Used by the validator: an indicator that has no values for any of
    these units does not meet the project's coverage requirement.
    """
    if geo_level == 'condesa_fraccionamiento':
        return set(units('condesa_fraccionamiento')['geo_id'])
    if geo_level == 'condesa_lote':
        return set(units('condesa_lote')['geo_id'])
    link = crosswalk('condesa_fraccionamiento', geo_level)
    return set(link['to_id'])


# --------------------------------------------------------------------
# Build
# --------------------------------------------------------------------
def build(data_dir=None, grid_100m=True, verbose=True):
    """Build the reference geopackage and crosswalk from source data.

    The ULI extent is the union of the GHSCI Mexicali study region and
    the Condesa new-development area, so that the project focus area
    is fully covered even where it falls outside the 2020 census
    urban footprint.
    """
    import geopandas as gpd
    from shapely.geometry import box

    data_dir = data_dir or DATA_DIR
    os.makedirs(GEOGRAPHY_DIR, exist_ok=True)
    crs = vocab.PROJECT_CRS

    def say(message):
        if verbose:
            print(message)

    def read(key, **kwargs):
        return gpd.read_file(
            os.path.join(data_dir, SOURCES[key]), **kwargs
        ).to_crs(crs)

    say('Reading source geographies ...')
    region = read('region', layer='indicators_region')
    ageb = read('ageb')
    manzana = read('manzana')
    fraccionamiento = read('condesa_fraccionamiento')
    lote = read('condesa_lote')

    extent = gpd.GeoSeries(
        [
            region.union_all().union(
                fraccionamiento.union_all().buffer(50)
            )
        ],
        crs=crs,
    )

    layers = {}

    layers['city'] = gpd.GeoDataFrame(
        {
            'geo_id': [CITY_ID],
            'name': ['Mexicali (ULI study extent)'],
            'pop_census_2020': [float(manzana['POBTOT'].fillna(0).sum())],
            'dwellings': [float('nan')],
        },
        geometry=list(extent),
        crs=crs,
    )

    layers['ageb'] = gpd.GeoDataFrame(
        {
            'geo_id': ageb['CVEGEO'].astype(str),
            'name': ageb['AGEB'].astype(str),
            'pop_census_2020': ageb['POBTOT'].fillna(0),
            'dwellings': float('nan'),
        },
        geometry=ageb.geometry,
        crs=crs,
    )

    layers['manzana'] = gpd.GeoDataFrame(
        {
            'geo_id': manzana['CVEGEO'].astype(str),
            'name': (
                manzana['AGEB'].astype(str)
                + '-'
                + manzana['MZA'].astype(str)
            ),
            'pop_census_2020': manzana['POBTOT'].fillna(0),
            'dwellings': float('nan'),
        },
        geometry=manzana.geometry,
        crs=crs,
    )

    say('Building Condesa layers ...')
    fraccionamiento = fraccionamiento.reset_index(drop=True)
    fraccionamiento['geo_id'] = [
        f'CONDESA_F{i + 1:03d}' for i in range(len(fraccionamiento))
    ]
    lote = lote.reset_index(drop=True)
    lote['geo_id'] = [f'CONDESA_L{i + 1:05d}' for i in range(len(lote))]
    lote_in_fracc = gpd.sjoin(
        lote[['geo_id', 'geometry']],
        fraccionamiento[['geo_id', 'geometry']].rename(
            columns={'geo_id': 'fracc_id'}
        ),
        how='left',
        predicate='intersects',
    ).drop_duplicates(subset='geo_id')
    lote_counts = (
        lote_in_fracc.groupby('fracc_id').size().rename('dwellings')
    )

    layers['condesa_fraccionamiento'] = gpd.GeoDataFrame(
        {
            'geo_id': fraccionamiento['geo_id'],
            'name': fraccionamiento['geo_id'],
            'pop_census_2020': 0.0,
            'dwellings': (
                fraccionamiento['geo_id']
                .map(lote_counts)
                .fillna(0)
                .astype(float)
            ),
        },
        geometry=fraccionamiento.geometry,
        crs=crs,
    )

    layers['condesa_lote'] = gpd.GeoDataFrame(
        {
            'geo_id': lote['geo_id'],
            'name': lote['geo_id'],
            'pop_census_2020': 0.0,
            'dwellings': 1.0,
        },
        geometry=lote.geometry,
        crs=crs,
    )

    for size, level in ((1000, 'grid_1000m'), (100, 'grid_100m')):
        if size == 100 and not grid_100m:
            continue
        say(f'Building {level} ...')
        minx, miny, maxx, maxy = extent.total_bounds
        minx, miny = (int(minx // size) * size, int(miny // size) * size)
        cells, ids = [], []
        x = minx
        while x < maxx:
            y = miny
            while y < maxy:
                cells.append(box(x, y, x + size, y + size))
                ids.append(f'{level}_{int(x)}_{int(y)}')
                y += size
            x += size
        grid = gpd.GeoDataFrame(
            {'geo_id': ids, 'name': ids}, geometry=cells, crs=crs
        )
        grid = grid[grid.intersects(extent.iloc[0])].reset_index(
            drop=True
        )
        grid['pop_census_2020'] = float('nan')
        grid['dwellings'] = float('nan')
        layers[level] = grid

    say('Apportioning 2020 census population to grid cells ...')
    for level in [
        lvl for lvl in ('grid_1000m', 'grid_100m') if lvl in layers
    ]:
        layers[level]['pop_census_2020'] = _apportion_population(
            layers[level], layers['manzana'], crs,
            column='pop_census_2020',
        )

    condesa_footprint = fraccionamiento.union_all()

    for epoch, column in ((2025, 'population'), (2030, 'population_2030')):
        say(f'Apportioning GHS-POP {epoch} to every geography ...')
        cells = _ghs_population_cells(
            os.path.join(data_dir, SOURCES[f'ghs_pop_{epoch}']),
            extent,
            crs,
        )
        inside = _within(cells, condesa_footprint)
        # Area-apportioned, not whole-cell: cells straddling the
        # boundary contribute only their overlapping share.
        in_condesa = (
            inside.geometry.area / inside['source_area'] * inside['pop']
        ).sum()
        say(
            f'  {len(cells):,} populated cells, '
            f'{cells["pop"].sum():,.0f} persons over the study extent '
            f'(Condesa: {in_condesa:,.1f})'
        )
        for level in layers:
            layers[level][column] = _apportion_population(
                layers[level], cells, crs
            )
        if epoch == 2030:
            # Population the projection places inside the Condesa
            # footprint, to be superseded by the planned occupancy
            # rather than added to it.
            for level in layers:
                layers[level]['_ghs2030_in_condesa'] = (
                    _apportion_population(layers[level], inside, crs)
                )

    say('Deriving Condesa planned occupancy ...')
    residential = lote[
        lote.geometry.area <= CONDESA_RESIDENTIAL_LOT_MAX_SQM
    ].copy()
    residential['pop'] = CONDESA_HOUSEHOLD_SIZE
    residential['source_area'] = residential.geometry.area
    say(
        f'  {len(residential):,} residential lots of {len(lote):,} '
        f'(<= {CONDESA_RESIDENTIAL_LOT_MAX_SQM} m2) x '
        f'{CONDESA_HOUSEHOLD_SIZE} persons = '
        f'{len(residential) * CONDESA_HOUSEHOLD_SIZE:,.0f} planned '
        'residents'
    )
    lot_counts = residential.copy()
    lot_counts['pop'] = 1.0
    for level in layers:
        layers[level]['population_planned'] = _apportion_population(
            layers[level], residential, crs
        )
        layers[level]['dwellings'] = _apportion_population(
            layers[level], lot_counts, crs
        )
        layers[level]['population_scenario_2030'] = (
            layers[level]['population_2030']
            - layers[level]['_ghs2030_in_condesa']
            + layers[level]['population_planned']
        ).clip(lower=0)
        layers[level] = layers[level].drop(
            columns='_ghs2030_in_condesa'
        )
    say(
        '  scenario 2030 total: '
        f'{layers["city"]["population_scenario_2030"].sum():,.0f} '
        '(GHS-POP 2030 outside Condesa + planned occupancy inside)'
    )

    say('Writing reference geopackage ...')
    if os.path.exists(GEOPACKAGE):
        os.remove(GEOPACKAGE)
    for level, frame in layers.items():
        frame = frame.copy()
        frame['geo_level'] = level
        frame['area_sqm'] = frame.geometry.area
        frame = frame.reindex(
            columns=['geo_id', 'geo_level', 'name', 'area_sqm']
            + list(POPULATION_COLUMNS)
            + ['geometry']
        )
        frame.to_file(GEOPACKAGE, layer=level, driver='GPKG')
        say(f'  {level}: {len(frame):,} units')

    say('Building crosswalk (this takes a few minutes) ...')
    _build_crosswalk(layers, crs, say)
    say(f'Done.\n  {GEOPACKAGE}\n  {CROSSWALK}')


def _within(cells, footprint):
    """Clip population cells to a footprint, keeping their full area.

    ``source_area`` is preserved from the unclipped cell so that a
    later apportionment still divides by the whole cell, not the
    clipped fragment.
    """
    import geopandas as gpd

    clipped = cells.copy()
    clipped['source_area'] = clipped.geometry.area
    clipped['geometry'] = clipped.geometry.intersection(footprint)
    clipped = clipped[~clipped.geometry.is_empty]
    return gpd.GeoDataFrame(clipped, geometry='geometry', crs=cells.crs)


def _apportion_population(target, source, crs, column='pop'):
    """Apportion a source population layer to target units by area.

    Population is a count, so it is split between overlapping targets
    in proportion to the share of each source polygon they cover --
    never averaged.  A ``source_area`` column, if present, is used in
    place of the geometry's own area; this lets a clipped source still
    apportion against its original extent.
    """
    import geopandas as gpd

    keep = ['geo_id', column, 'geometry']
    if 'source_area' in source.columns:
        keep.append('source_area')
    source = source[keep].copy()
    if 'source_area' not in source.columns:
        source['source_area'] = source.geometry.area
    pieces = gpd.overlay(
        target[['geo_id', 'geometry']].rename(
            columns={'geo_id': 'target_id'}
        ),
        source,
        how='intersection',
        keep_geom_type=False,
    )
    if pieces.empty:
        return pd.Series(0.0, index=target.index).values
    pieces['share'] = pieces.geometry.area / pieces['source_area']
    pieces['pop'] = pieces['share'] * pieces[column]
    totals = pieces.groupby('target_id')['pop'].sum()
    return target['geo_id'].map(totals).fillna(0.0).values


def _ghs_population_cells(raster_path, extent, crs):
    """Read GHS-POP cells over the study extent as polygons.

    GHS-POP stores persons per 100 m cell, so cells are polygonised
    and treated as a population layer to be apportioned by area --
    resampling the raster would not conserve the counts.
    """
    import geopandas as gpd
    import rasterio
    from rasterio.windows import from_bounds
    from shapely.geometry import box

    with rasterio.open(raster_path) as source:
        bounds = (
            gpd.GeoSeries(extent, crs=crs)
            .to_crs(source.crs)
            .total_bounds
        )
        window = from_bounds(*bounds, transform=source.transform)
        data = source.read(1, window=window)
        transform = source.window_transform(window)
        nodata = source.nodata
        raster_crs = source.crs

    populated = data > 0
    if nodata is not None:
        populated &= data != nodata
    rows, columns = np.nonzero(populated)
    cells, values = [], []
    for row, column in zip(rows, columns):
        left, top = transform * (column, row)
        right, bottom = transform * (column + 1, row + 1)
        cells.append(box(left, bottom, right, top))
        values.append(float(data[row, column]))
    return gpd.GeoDataFrame(
        {
            'geo_id': [f'ghs_{i}' for i in range(len(cells))],
            'pop': values,
        },
        geometry=cells,
        crs=raster_crs,
    ).to_crs(crs)


def _build_crosswalk(layers, crs, say):
    """Write pairwise overlaps between all reporting geographies.

    Each unordered pair of levels is intersected once; both directional
    shares are stored so that :func:`crosswalk` can serve either
    direction without recomputation.
    """
    import itertools

    import geopandas as gpd

    weights = (
        'population',
        'population_2030',
        'population_scenario_2030',
        'dwellings',
    )

    def prepared(level, suffix):
        frame = layers[level][['geo_id', 'geometry']].rename(
            columns={'geo_id': f'id_{suffix}'}
        )
        frame[f'area_{suffix}'] = frame.geometry.area
        for weight in weights:
            frame[f'{weight}_{suffix}'] = (
                layers[level][weight].fillna(0.0).astype(float).values
            )
        return frame

    records = []
    for level_a, level_b in itertools.combinations(list(layers), 2):
        pieces = gpd.overlay(
            prepared(level_a, 'a'),
            prepared(level_b, 'b'),
            how='intersection',
            keep_geom_type=False,
        )
        if pieces.empty:
            say(f'  {level_a} x {level_b}: no overlap')
            continue
        area = pieces.geometry.area
        share_a = (area / pieces['area_a']).clip(0, 1)
        share_b = (area / pieces['area_b']).clip(0, 1)
        record = {
            'level_a': level_a,
            'id_a': pieces['id_a'].values,
            'level_b': level_b,
            'id_b': pieces['id_b'].values,
            'area_sqm': area.values,
            'share_of_a': share_a.values,
            'share_of_b': share_b.values,
        }
        # Each denominator attributable to the overlap, apportioned by
        # area from whichever side is being aggregated from.
        for weight in weights:
            record[f'{weight}_a'] = (
                share_a * pieces[f'{weight}_a']
            ).values
            record[f'{weight}_b'] = (
                share_b * pieces[f'{weight}_b']
            ).values
        records.append(pd.DataFrame(record))
        say(f'  {level_a} x {level_b}: {len(pieces):,} overlaps')
    frame = pd.concat(records, ignore_index=True)
    frame = frame[frame['area_sqm'] > 1.0].reset_index(drop=True)
    frame.to_parquet(CROSSWALK, index=False)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'build':
        build(grid_100m='--no-100m' not in sys.argv)
    else:
        print(__doc__)
