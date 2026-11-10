# Appendix D. Data source register

Dataset records as they stand in the region configuration, unaltered. Each dataset keeps its own licence.

## Study region boundary

[`MX_Mexicali_2025_ULI.yml:43`](../data/MX_Mexicali_2025_ULI.yml#L43)

- `data`: MX/INEGI-02l-NOMGEO-Mexicali-Condesa-Fraccionamientos.geojson
- `source`: Instituto Nacional de Estadística, Geografía e Informática (INEGI); Centro para el Futuro de las Ciudades (CFC)
- `publication_date`: 2025-07-31
- `url`: https://en.www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/geografia/marcogeo/794551163061/02_bajacalifornia.zip
- `licence`: Términos de Libre Uso de la Información del INEGI https://www.inegi.org.mx/inegi/terminos.html
- `citation`: INEGI (2025). Marco Geoestadístico 2025 - Baja California.  https://en.www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551163061; CFC (2026) Condesa development boundaries.
- `notes`: Dissolved union of MX/INEGI/02_bajacalifornia.zip/conjunto_de_datos/02l.shp -where  "NOMGEO='Mexicali'" and convex hull of MX/CFC/Nvo desarrollo/_Fraccionamientos.geojson, so that the analysis covers 100% of the Condesa development.

## Exclusion region

[`MX_Mexicali_2025_ULI.yml:55`](../data/MX_Mexicali_2025_ULI.yml#L55)

- `data`: MX/exclusion/ca_state.zip
- `source`: https://data.ca.gov/dataset/e212e397-1277-4df3-8c22-40721b095f33/resource/3db1e426-fb51-44f5-82d5-a54d7c6e188b/download/ca_state.zip
- `licence`: public domain
- `citation`: California State boundary in shapefile format from the US Census Bureau's 2023 MAF/TIGER database.
- `notes`: Es necesario tener cuidado para garantizar que la zona de estudio delimitada no se extienda más allá de la frontera con Estados Unidos // Care must be taken to ensure the buffered study region does not expand across the border with the United States, so that road network and amenities outside Mexico are not included in accessibility calculations.  Per https://github.com/healthysustainablecities/global-indicators/issues/610 the network setup is restricted to the main study region (not the buffered region).

## Population

[`MX_Mexicali_2025_ULI.yml:61`](../data/MX_Mexicali_2025_ULI.yml#L61)

- `name`: Global Human Settlements population data: 2025, Mollweide (EU JRC, 2023)
- `data_dir`: MX/CFC/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R6_C8/
- `year_published`: 2023
- `source_url`: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2025_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_POP_E2025_GLOBE_R2023A_54009_100_V1_0_R6_C8.zip
- `licence`: CC BY 4.0
- `citation`: Schiavina, M., Freire, S., Carioli, A., MacManus, K. (2023). GHS-POP R2023A - GHS population grid multitemporal (1975-2030). European Commission, Joint Research Centre (JRC). https://doi.org/10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE
- `notes`: Population is NOT redirected to a custom aggregation; the 100 m grid derived from this raster is a required output scale.

## OpenStreetMap

[`MX_Mexicali_2025_ULI.yml:396`](../data/MX_Mexicali_2025_ULI.yml#L396)

- `data_dir`: MX/mexico-260815.osm.pbf
- `source`: Geofabrik GmbH
- `publication_date`: 20260815
- `url`: https://download.geofabrik.de/north-america/mexico-latest.osm.pbf
- `licence`: ODbL
- `note`: Mexico OpenStreetMap excerpt

## IMIP: public transport stops (pt_any)

[`MX_Mexicali_2025_ULI.yml:168`](../data/MX_Mexicali_2025_ULI.yml#L168)

- `data`: MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "equipamiento_category='transp' AND TIPO != 'TERMINAL INTERIOR DE CARGA (CENTRAL DE SERVICIOS DE CARGA)'"
- `source`: IMIP / CFC
- `publication_date`: 2026-05-18
- `licence`: Provided by IMIP via CFC
- `citation`: As per advice from Juan Ernesto Díaz Noguez

## INEGI DENUE (May 2026)

[`MX_Mexicali_2025_ULI.yml:192`](../data/MX_Mexicali_2025_ULI.yml#L192)

- `data`: MX/INEGI/DENUE_2026/denue_inegi_02_.shp -where "codigo_act IN ('461121','461122','461123','461130','461140','461150','462111','462112')"
- `source`: INEGI, Directorio Estadistico Nacional de Unidades Economicas (DENUE)
- `publication_date`: 2026-05
- `url`: https://www.inegi.org.mx/app/mapa/denue/
- `licence`: Terminos de Libre Uso de la Informacion del INEGI
- `citation`: INEGI (2026). Directorio Estadistico Nacional de Unidades Economicas (DENUE), mayo 2026. Instituto Nacional de Estadistica y Geografia, Mexico.

## Police stations (IMIP) (`imip_police_station`)

- `name`: imip_police_station
- `data`: MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "TIPO = 'INSTALACIONES POLICIALES'"
- `source`: IMIP / CFC
- `licence`: Provided by IMIP via CFC
- `notes`: 27 police facilities in the IMIP equipamiento layer (administración pública).

## Municipal fire stations (IMIP) (`imip_fire_station`)

- `name`: imip_fire_station
- `data`: MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "TIPO = 'ESTACION DE BOMBEROS MUNICIPAL'"
- `source`: IMIP / CFC
- `licence`: Provided by IMIP via CFC
- `notes`: 10 municipal fire stations in the IMIP equipamiento layer (administración pública).

## Outdoor thermal comfort (UTCI) (`utci`)

[`MX_Mexicali_2025_ULI.yml:770`](../data/MX_Mexicali_2025_ULI.yml#L770)

- `data`: MX/UTCI - 2026-08-25/mexicali_utci_2023-07-21.gpkg
- `source`: Rossano Schifanella (WP02); SOLWEIG and the UTCI operational polynomial (Bröde et al. 2012)
- `licence`: Terrain from FABDEM v1 (CC BY-NC-SA 4.0, non-commercial); other inputs CC BY 4.0 or public domain
- `notes`: Modelled day 2023-07-21 (Tmax 48.5 °C).  See README_mexicali_utci.md, sections 3.1 and 5, for forcing and limitations.

## Work package indicators (`external`)

[`MX_Mexicali_2025_ULI.yml:814`](../data/MX_Mexicali_2025_ULI.yml#L814)

- `data`: MX/Update_on_ULI - 2026-09-22/final_indicators.gpkg
- `source`: Mexicali ULI work packages (final_indicators.gpkg; see excel_work_sheet_key.xlsx)

## Custom aggregations

- **`agebs`**: `MX/mexicali_AGEB_population.geojson` — INEGI 2020 AGEB boundaries with census population, as prepared in Mexicali_2025.ipynb.
- **`manzanas`**: `MX/CFC/mexicali_manzanas.gpkg:manzanas` — INEGI 2020 census manzanas with geometries updated by CFC (19,223 manzanas; 940,287 residents; 236.9 km2), prepared by MX/CFC/build_manzanas.py. Replaces MX/CFC/MXL_MZAPob.gpkg:02m, which covered the Condesa development only partially -- 6,274 of its 14,989 lots fell within a manzana, against 12,985 here. 3,497 manzanas have no recorded population (2,772 of them rural) and report a null pop_est rather than zero; they are excluded from population-weighted summaries. Sixteen newly mapped Condesa blocks had no manzana key and carry a synthetic identifier assigned by build_manzanas.py, recognisable by an 'S' where the manzana number would be.
- **`condesa_lotes`**: `MX/CFC/Nvo desarrollo/Lotes_desarrollo_EXE_cleaned_400sqm_or_less.geojson` — Individual lots in the Condesa development (median 120 m2). No population data; however we can assign an assumed value, assuming average household population of 3.2 for Mexicali (2020; https://inegi.org.mx/app/areasgeograficas/?ag=02002#tabMCcollapse-Indicadores).  Note: this data appeared to include more than lots, larger block areas which appeared to be artifacts, so I filtered to those with area <= 400sqm (manually in QGIS).
- **`condesa_fraccionamientos`**: `MX/CFC/Nvo desarrollo/_Fraccionamientos.geojson` — Condesa subdivision polygons (median 7.9 ha). pop_est is summed from condesa_lotes (3.2 people per lot assumed).
- **`region_mexicali`**: `MX/CFC/mexicali_uli_boundaries.gpkg:region_mexicali` — The Mexicali urban area boundary, dissolved, giving a single summary row for the administrative area.
- **`region_condesa`**: `MX/CFC/mexicali_uli_boundaries.gpkg:region_condesa` — The Condesa development, dissolved, giving a single summary row for the development as a whole.

## Google Earth Engine

The GUHVI and large public green space indicators are computed in Google Earth Engine (`gee: true`) from Landsat 8, MODIS and Sentinel-2 collections; the region configuration declares no dataset record for them. The sources GHSCI records are in the data dictionary.
