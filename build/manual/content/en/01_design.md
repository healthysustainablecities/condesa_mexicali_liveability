# 1. Study design

## Study region

The study region is the union of the Mexicali urban area (the locality `NOMGEO = 'Mexicali'` of INEGI's 2025 geostatistical framework) and the Condesa development, dissolved to a single feature. Only 82% of Condesa falls within the administrative urban boundary, which alone would have clipped 2,419 of its 14,989 lots ({{cfg:study_region_boundary:}}). The study region covers {{fact:study_area_km2}} km², of which Condesa is {{fact:condesa_area_km2}} km².

Areas are summarised only where they lie within the study region (a point on the area's surface inside it). The network is extracted for the study region itself rather than its 1,600 m buffer, so that streets and destinations across the border with the United States do not enter accessibility calculations ({{cfg:exclusion_region:}}; GHSCI issue #610).

## Coordinate reference system

EPSG:6366, Mexico ITRF2008 / UTM zone 11N, in metres ({{cfg:srid: 6366}}).

## Scales

| Scale | Units | Source | How values reach it |
|---|---|---|---|
| Sample points | {{fact:sample_points}} | Every 30 m along the pedestrian network, plus one per Condesa lot ([R1](03_recipes.md#r1)) | Calculated here |
| 100 m grid | {{fact:n_grid}} cells | GHS-POP 2025, reprojected to EPSG:6366 by sum resampling | Mean of the cell's sample points |
| AGEB | {{fact:n_agebs}} | INEGI 2020 census areas | From the grid, weighted by grid population |
| Manzanas (blocks) | {{fact:n_manzanas}} | INEGI 2020 census blocks with geometries updated by CFC | Mean of sample points within 30 m |
| Condesa lots | {{fact:n_lots}} | CFC lots of 400 m² or less | Mean of sample points within 15 m |
| Condesa subdivisions | {{fact:n_fracc}} | CFC fraccionamientos | From the lots, 3.2 residents assumed per lot |
| Region: study region | 1 | Study region boundary | From the grid, weighted by population |
| Region: Condesa | 1 | Condesa boundary | From the lots |

Manzanas are summarised from sample points rather than from the grid because a manzana (median 0.71 ha) is smaller than a 100 m cell; aggregating from the grid would just copy the containing cell ({{cfg:manzanas:}}). Lots are summarised within 15 m so that a lot set deep inside a gated subdivision is not credited with access through a gate it cannot use ({{cfg:sampling:}}).

## Population

- **100 m grid:** GHS-POP R2023A for 2025 (Schiavina et al. 2023), Mollweide, reprojected with sum resampling to conserve counts ({{cfg:population:}}). The grid is deliberately not redirected to census counts, so that the 100 m grid exists as an output.
- **Manzanas and AGEBs:** INEGI Censo 2020 (`POBTOT`). 3,497 manzanas have no recorded population and are excluded from population-weighted summaries.
- **Condesa:** the development is too new for the census, so each lot is assumed to house 3.2 residents (Mexicali's 2020 average household size, INEGI). Sample points are placed in unpopulated areas too (`sampling.sample_unpopulated_areas`), so that Condesa is measured at all.

## Network

The routable pedestrian network is retrieved with OSMnx from OpenStreetMap, at the replication timestamp of the Geofabrik Mexico extract of 15 August 2026, which holds the Condesa streets contributed that day ({{cfg:OpenStreetMap:}}). The definition retains private and gated access, which the GHSCI default excludes, because Condesa's internal streets and those of Mexicali's gated communities are precisely the areas of interest ({{cfg:network:}}). Intersections are OSMnx consolidated intersections with a 12 m tolerance.

## Distances and bands

Walking access is judged at 300 m, the five-minute walk Mexicali's collector-road walkability policy targets, rather than the 500 m used by GHSCI's globally comparable indicators, which are also produced unchanged. Distances are measured in bands of 300, 500, 1,000 and 1,500 m and censored at 1,500 m: a sample point with nothing within 1,500 m has no distance, and is counted as having no access ({{cfg:accessibility:}}).

## Two regions, one analysis

Mexicali and Condesa are analysed in one run, sharing the network, population grid and destinations, so that differences between them are real rather than artefacts of separate analyses. The study region's reference, the mean over all sample points against which every score is measured, includes Condesa.
