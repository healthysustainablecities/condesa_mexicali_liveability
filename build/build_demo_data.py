"""Build the small demonstration dataset used by the cookbook.

The worked examples must run immediately after a plain ``git clone``,
so they cannot reach outside the repository for data.  This script
extracts a handful of small, real layers from the GHSCI Mexicali study
region outputs and the INEGI census geometries, and writes them to
``data/demo/``.

Every layer is real data, and every layer's provenance is written to
``data/demo/README.md``.  The one exception is the ``has_sidewalk``
column on the street layer, which is **fabricated** so that the
length-weighted recipe has something to demonstrate; it is labelled as
such wherever it appears, and must never be used as a finding.

Run from the project root, on a machine that has the GHSCI outputs::

    python build/build_demo_data.py

Analysts never run this; the outputs are committed.
"""

import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
DEMO_DIR = os.path.join(PROJECT_DIR, 'data', 'demo')
sys.path.insert(0, PROJECT_DIR)

from uli import geography, vocab  # noqa: E402

DATA_DIR = geography.DATA_DIR
GHSCI = os.path.join(
    DATA_DIR,
    '_study_region_outputs/MX_Mexicali_2025-MZA/'
    'MX_Mexicali_2025-MZA_1600m_buffer.gpkg',
)
MANZANAS = os.path.join(
    DATA_DIR, 'MX/mexicali_manzanas_population.geojson'
)
GHS_POP = os.path.join(DATA_DIR, geography.SOURCES['ghs_pop_2025'])

CRS = vocab.PROJECT_CRS


def say(message):
    print(message)


GEOPACKAGE = 'demo.gpkg'


def write(frame, layer, description, provenance):
    """Write one layer of the demo geopackage.

    A single geopackage rather than loose files: it is the same shape
    as the reference geographies analysts already have to read, so
    there is one file-reading pattern to learn, not two.
    """
    path = os.path.join(DEMO_DIR, GEOPACKAGE)
    frame.to_file(path, layer=layer, driver='GPKG')
    say(f'  layer {layer}: {len(frame):,} features')
    return {
        'file': f'{GEOPACKAGE} (layer "{layer}")',
        'features': len(frame),
        'description': description,
        'provenance': provenance,
    }


def main():
    os.makedirs(DEMO_DIR, exist_ok=True)
    package = os.path.join(DEMO_DIR, GEOPACKAGE)
    if os.path.exists(package):
        os.remove(package)
    catalogue = []
    say('Building demonstration layers ...')

    # ---- points ----------------------------------------------------
    destinations = gpd.read_file(GHSCI, layer='destinations').to_crs(CRS)
    destinations = destinations[['dest_name', 'geometry']].rename(
        columns={'dest_name': 'category'}
    )
    catalogue.append(
        write(
            destinations,
            'destinations',
            'Everyday destinations as points, with a category column '
            '(convenience, fresh_food_market, restaurant, cafe, ...).',
            'OpenStreetMap contributors, Geofabrik Mexico extract '
            '10 April 2026, via the GHSCI Mexicali study region. '
            'Licence: ODbL-1.0.',
        )
    )

    # ---- polygons --------------------------------------------------
    open_space = gpd.read_file(GHSCI, layer='aos_public').to_crs(CRS)
    open_space = open_space[
        ['aos_id', 'aos_ha_public', 'has_water_feature', 'geometry']
    ].copy()
    open_space['space_type'] = np.where(
        open_space['has_water_feature'].fillna(False).astype(bool),
        'blue_space',
        'green_or_open_space',
    )
    open_space.geometry = open_space.geometry.simplify(1.0)
    catalogue.append(
        write(
            open_space,
            'open_space',
            'Public open space polygons with area in hectares and a '
            'space_type column. Geometry simplified to 1 m.',
            'OpenStreetMap contributors via the GHSCI Mexicali study '
            'region open space analysis. Licence: ODbL-1.0.',
        )
    )

    # ---- categorical polygons --------------------------------------
    manzanas = gpd.read_file(MANZANAS).to_crs(CRS)
    classes = manzanas[['AMBITO', 'TIPOMZA', 'geometry']].copy()
    classes['land_class'] = (
        classes['AMBITO'].fillna('Sin dato').astype(str)
        + ' / '
        + classes['TIPOMZA'].fillna('Sin dato').astype(str)
    )
    classes = classes.dissolve(by='land_class').reset_index()
    # Aggressive simplification: this layer only has to behave
    # like a land use map, not be one.
    classes.geometry = classes.geometry.simplify(25.0).buffer(0)
    catalogue.append(
        write(
            classes[['land_class', 'geometry']],
            'land_classes',
            'A categorical land-classification layer: INEGI census '
            'block type (AMBITO / TIPOMZA), dissolved to one polygon '
            'per class and simplified to 25 m. Stands in for the '
            'municipal land use map.',
            'INEGI Marco Geoestadistico 2020, Mexicali manzanas. '
            'Geometry dissolved by class and simplified to 25 m.',
        )
    )

    # ---- lines -----------------------------------------------------
    condesa = geography.load('condesa_fraccionamiento')
    area = condesa.union_all().buffer(1000)
    edges = gpd.read_file(GHSCI, layer='edges').to_crs(CRS)
    edges = edges[edges.intersects(area)][['highway', 'geometry']].copy()
    edges['highway'] = edges['highway'].astype(str).str.strip('[]\'"')
    # Fabricated attribute: a plausible but INVENTED sidewalk flag, so
    # that network_share has something to demonstrate.  Larger roads
    # are made more likely to have one.  Not a finding.
    rng = np.random.default_rng(42)
    likelihood = edges['highway'].map(
        {
            'primary': 0.85,
            'secondary': 0.8,
            'tertiary': 0.7,
            'residential': 0.45,
            'unclassified': 0.3,
        }
    ).fillna(0.25)
    edges['has_sidewalk_FABRICATED'] = (
        rng.random(len(edges)) < likelihood
    ).astype(int)
    edges.geometry = edges.geometry.simplify(1.0)
    catalogue.append(
        write(
            edges,
            'streets_condesa',
            'Street network within 1 km of the Condesa development, '
            'with the OpenStreetMap highway class and a FABRICATED '
            'has_sidewalk_FABRICATED flag for demonstration only.',
            'OpenStreetMap contributors via the GHSCI Mexicali '
            'pedestrian network (OSMnx). Licence: ODbL-1.0. The '
            'sidewalk column is invented and is not real data.',
        )
    )

    # ---- raster ----------------------------------------------------
    import rasterio
    from rasterio.mask import mask
    from rasterio.warp import calculate_default_transform, reproject

    city = geography.load('city')
    with rasterio.open(GHS_POP) as source:
        shape = city.to_crs(source.crs).geometry.iloc[0]
        data, transform = mask(source, [shape], crop=True)
        profile = source.profile.copy()
        profile.update(
            height=data.shape[1], width=data.shape[2],
            transform=transform, compress='deflate',
        )
        dst_transform, width, height = calculate_default_transform(
            source.crs, CRS, data.shape[2], data.shape[1],
            *rasterio.transform.array_bounds(
                data.shape[1], data.shape[2], transform
            ),
        )
        out = np.empty((height, width), dtype='float32')
        reproject(
            source=data[0], destination=out,
            src_transform=transform, src_crs=source.crs,
            dst_transform=dst_transform, dst_crs=CRS,
            src_nodata=source.nodata, dst_nodata=-200.0,
        )
    path = os.path.join(DEMO_DIR, 'demo_population_100m.tif')
    with rasterio.open(
        path, 'w', driver='GTiff', height=height, width=width,
        count=1, dtype='float32', crs=CRS, transform=dst_transform,
        nodata=-200.0, compress='deflate',
    ) as destination:
        destination.write(out, 1)
    size = os.path.getsize(path) / 1024
    say(f'  demo_population_100m.tif: {width}x{height}, {size:,.0f} KB')
    catalogue.append(
        {
            'file': 'demo_population_100m.tif',
            'kb': round(size),
            'features': f'{width} x {height} cells',
            'description': (
                'A 100 m raster of population count per cell, clipped '
                'to the study extent and reprojected to EPSG:6366. '
                'Stands in for any continuous surface (NDVI, land '
                'surface temperature, pollutant concentration).'
            ),
            'provenance': (
                'GHS-POP R2023A epoch 2025, European Commission JRC. '
                'Licence: CC-BY-4.0.'
            ),
        }
    )

    # ---- a plain table ---------------------------------------------
    ageb = gpd.read_file(
        os.path.join(DATA_DIR, 'MX/mexicali_AGEB_population.geojson')
    )
    table = pd.DataFrame(
        {
            'CVEGEO': ageb['CVEGEO'].astype(str),
            'pop_total': ageb['POBTOT'],
            'pop_65_plus': ageb['POB65_MAS'],
            'pct_65_plus': (
                100 * ageb['POB65_MAS'] / ageb['POBTOT'].replace(0, np.nan)
            ).round(2),
        }
    )
    path = os.path.join(DEMO_DIR, 'demo_ageb_census.csv')
    table.to_csv(path, index=False, encoding='utf-8')
    say(f'  demo_ageb_census.csv: {len(table):,} rows')
    catalogue.append(
        {
            'file': 'demo_ageb_census.csv',
            'features': len(table),
            'description': (
                'A plain attribute table keyed by AGEB CVEGEO, for the '
                'recipe where the values already exist per unit.'
            ),
            'provenance': (
                'INEGI Censo de Poblacion y Vivienda 2020, Mexicali '
                'AGEBs.'
            ),
        }
    )

    _write_readme(catalogue)
    total = sum(
        os.path.getsize(os.path.join(DEMO_DIR, name))
        for name in os.listdir(DEMO_DIR)
        if not name.endswith('.md')
    )
    say(f'\nTotal {total / 1024:,.0f} KB in {DEMO_DIR}')


def _write_readme(catalogue):
    lines = [
        '# Demonstration data',
        '',
        'Small, real layers used by',
        '[`notebooks/00b_cookbook.ipynb`](../../notebooks/00b_cookbook.ipynb)',
        'so that every worked example runs immediately after cloning the',
        'repository, with nothing to download.',
        '',
        'These are for **learning the tooling only**. They are extracts,',
        'simplified geometry in places, and one column is invented. Do not',
        'use them to produce indicator values.',
        '',
        'All layers are EPSG:6366 (Mexico ITRF2008 / UTM zone 11N).',
        '',
        '| Layer / file | Features | Contents |',
        '|---|---|---|',
    ]
    for item in catalogue:
        lines.append(
            f'| `{item["file"]}` | {item["features"]} | '
            f'{" ".join(str(item["description"]).split())} |'
        )
    lines += ['', '## Provenance', '']
    for item in catalogue:
        lines.append(f'**`{item["file"]}`**')
        lines.append(f'{" ".join(str(item["provenance"]).split())}')
        lines.append('')
    lines += [
        '## The fabricated column',
        '',
        'The `streets_condesa` layer carries',
        '`has_sidewalk_FABRICATED`, which is **invented**. Mexicali has no',
        'sidewalk inventory in OpenStreetMap, and the length-weighted',
        'recipe needs a boolean street attribute to demonstrate. Values',
        'were drawn at random, weighted by road class. The column name',
        'shouts about it on purpose. Never report a number derived from',
        'it.',
        '',
    ]
    with open(
        os.path.join(DEMO_DIR, 'README.md'), 'w', encoding='utf-8'
    ) as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    main()
