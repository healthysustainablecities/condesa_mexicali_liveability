# Demonstration data

Small, real layers used by
[`notebooks/00b_cookbook.ipynb`](../../notebooks/00b_cookbook.ipynb)
so that every worked example runs immediately after cloning the
repository, with nothing to download.

These are for **learning the tooling only**. They are extracts,
simplified geometry in places, and one column is invented. Do not
use them to produce indicator values.

All layers are EPSG:6366 (Mexico ITRF2008 / UTM zone 11N).

| Layer / file | Features | Contents |
|---|---|---|
| `demo.gpkg (layer "destinations")` | 672 | Everyday destinations as points, with a category column (convenience, fresh_food_market, restaurant, cafe, ...). |
| `demo.gpkg (layer "open_space")` | 404 | Public open space polygons with area in hectares and a space_type column. Geometry simplified to 1 m. |
| `demo.gpkg (layer "land_classes")` | 6 | A categorical land-classification layer: INEGI census block type (AMBITO / TIPOMZA), dissolved to one polygon per class and simplified to 25 m. Stands in for the municipal land use map. |
| `demo.gpkg (layer "streets_condesa")` | 1914 | Street network within 1 km of the Condesa development, with the OpenStreetMap highway class and a FABRICATED has_sidewalk_FABRICATED flag for demonstration only. |
| `demo_population_100m.tif` | 332 x 115 cells | A 100 m raster of population count per cell, clipped to the study extent and reprojected to EPSG:6366. Stands in for any continuous surface (NDVI, land surface temperature, pollutant concentration). |
| `demo_ageb_census.csv` | 436 | A plain attribute table keyed by AGEB CVEGEO, for the recipe where the values already exist per unit. |

## Provenance

**`demo.gpkg (layer "destinations")`**
OpenStreetMap contributors, Geofabrik Mexico extract 10 April 2026, via the GHSCI Mexicali study region. Licence: ODbL-1.0.

**`demo.gpkg (layer "open_space")`**
OpenStreetMap contributors via the GHSCI Mexicali study region open space analysis. Licence: ODbL-1.0.

**`demo.gpkg (layer "land_classes")`**
INEGI Marco Geoestadistico 2020, Mexicali manzanas. Geometry dissolved by class and simplified to 25 m.

**`demo.gpkg (layer "streets_condesa")`**
OpenStreetMap contributors via the GHSCI Mexicali pedestrian network (OSMnx). Licence: ODbL-1.0. The sidewalk column is invented and is not real data.

**`demo_population_100m.tif`**
GHS-POP R2023A epoch 2025, European Commission JRC. Licence: CC-BY-4.0.

**`demo_ageb_census.csv`**
INEGI Censo de Poblacion y Vivienda 2020, Mexicali AGEBs.

## The fabricated column

The `streets_condesa` layer carries
`has_sidewalk_FABRICATED`, which is **invented**. Mexicali has no
sidewalk inventory in OpenStreetMap, and the length-weighted
recipe needs a boolean street attribute to demonstrate. Values
were drawn at random, weighted by road class. The column name
is deliberately conspicuous. Do not report a number derived
from it.
