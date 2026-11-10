# Work package indicators (linked)

[← Back to contents](../README.md)

Indicators prepared by the ULI work packages (`final_indicators.gpkg`, 22 September 2026). The file carries no identifiers, so features are identified by geometry against the reference areas: grid cells, AGEBs, lots and subdivisions are identical to them, and manzanas are matched by their largest overlap (several parts of one block are combined as an area-weighted mean). Values are brought down to sample points from the first layer holding one: the grid, then Condesa lots within 15 m and manzanas within 30 m.

| Sample point variable | Area variable (measured value) | Description | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|---|---|
| `sp_ext_ndvi` | `ext_ndvi` | Vegetation cover (NDVI) | 0.08 | 0.05 |
| `sp_ext_major_road_length_300m` | `ext_major_road_length_300m` | Major roads within 300 m | 1,996 m | 414 m |
| `sp_ext_block_perimeter_m` | `ext_block_perimeter_m` | Block size (perimeter) | 677 m | 712 m |
| `sp_ext_economic_sector_diversity` | `ext_economic_sector_diversity` | Job diversity | 0.33 | – |

| Column | Name | Units | Direction |
|---|---|---|---|
| `ext_ndvi` | Vegetation cover (NDVI) | NDVI | higher_is_better |
| `ext_tree_canopy_pct` | Tree canopy cover | % | higher_is_better |
| `ext_avg_walk_dist_park_m` | Distance to parks (work package) | m | lower_is_better |
| `ext_major_road_length_300m` | Major roads within 300 m | m | lower_is_better |
| `ext_pop_affected_flood` | Population exposed to flooding | persons | lower_is_better |
| `ext_flood_area_m2` | Flooded area on main roads | m² | lower_is_better |
| `ext_block_perimeter_m` | Block size (perimeter) | m | lower_is_better |
| `ext_residential_area_ha` | Residential land use | ha | – |
| `ext_commercial_area_ha` | Commercial land use | ha | – |
| `ext_land_use_entropy` | Land use mix | index 0-1 | higher_is_better |
| `ext_economic_sector_diversity` | Job diversity | index 0-1 | higher_is_better |
| `ext_protected_cycling_street_pct` | Protected cycle lane coverage | % | higher_is_better |

- `data`: MX/Update_on_ULI - 2026-09-22/final_indicators.gpkg
- `match`: geometry
- `reference`: MX/Mexicali Liveability/geography/mexicali_reference_areas.gpkg
- `null_as`: {'pop_affected_flood': 0, 'flood_area_m2': 0}
- `source`: Mexicali ULI work packages (final_indicators.gpkg; see excel_work_sheet_key.xlsx)

## Method: practice

**Recipes:** [R7. Linking externally prepared indicators](../03_recipes.md#r7)

**Configuration** ([`MX_Mexicali_2025_ULI.yml:814`](../../data/MX_Mexicali_2025_ULI.yml#L814)):

```yaml
external:
  data: MX/Update_on_ULI - 2026-09-22/final_indicators.gpkg
  match: geometry
  reference: MX/Mexicali Liveability/geography/mexicali_reference_areas.gpkg
  reference_layers: {grid: grid_100m}
  prefix: ext_
  label: {es: Indicadores de los paquetes de trabajo, en: Work package indicators}
  source: Mexicali ULI work packages (final_indicators.gpkg; see excel_work_sheet_key.xlsx)
  null_as: {pop_affected_flood: 0, flood_area_m2: 0}
  columns:
    ndvi:
      label: {es: Cobertura vegetal (NDVI), en: Vegetation cover (NDVI)}
      units: NDVI
      direction: higher_is_better
    tree_canopy_pct:
      label: {es: Cobertura arbórea, en: Tree canopy cover}
      units: '%'
      direction: higher_is_better
    avg_walk_dist_park_m:
      label: {es: Distancia a parques (paquete de trabajo), en: Distance to parks (work package)}
      units: m
      direction: lower_is_better
    major_road_length_300m:
      label: {es: Vialidades principales en 300 m, en: Major roads within 300 m}
      units: m
      direction: lower_is_better
    pop_affected_flood:
      label: {es: Población expuesta a inundaciones, en: Population exposed to flooding}
      units: persons
      direction: lower_is_better
    flood_area_m2:
      label: {es: Área de inundación en vialidades principales, en: Flooded area on main roads}
      units: m²
      direction: lower_is_better
    block_perimeter_m:
      label: {es: Tamaño de manzana (perímetro), en: Block size (perimeter)}
      units: m
      direction: lower_is_better
    residential_area_ha:
      label: {es: Uso de suelo residencial, en: Residential land use}
      units: ha
    commercial_area_ha:
      label: {es: Uso de suelo comercial, en: Commercial land use}
      units: ha
    land_use_entropy:
      label: {es: Mezcla de usos de suelo, en: Land use mix}
      units: index 0-1
      direction: higher_is_better
    economic_sector_diversity:
      label: {es: Diversidad de empleos, en: Job diversity}
      units: index 0-1
      direction: higher_is_better
    protected_cycling_street_pct:
      label: {es: Cobertura de ciclovías protegidas, en: Protected cycle lane coverage}
      units: '%'
      direction: higher_is_better
  areas:
    grid: grid
    agebs: agebs
    manzanas: manzanas
    condesa_lotes: {layer: condesa_lotes, boundary_id: id}
    condesa_fraccionamientos: {layer: condesa_fraccionamientos, boundary_id: fid}
  ## the grid first, as it tiles the region; flood values exist only for
  ## blocks and lots, so points take them from the nearest within the
  ## distance each is aggregated over
  sample_points:
    - {layer: grid}
    - {layer: condesa_lotes, within: 15}
    - {layer: manzanas, within: 30}
```

**Code (GHSCI):**

- [`process/subprocesses/_linkage_indicators.py:403`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_linkage_indicators.py#L403) `match_by_geometry()`
- [`process/subprocesses/_linkage_indicators.py:479`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_linkage_indicators.py#L479) `combine_matched()`
- [`process/subprocesses/_linkage_indicators.py:512`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_linkage_indicators.py#L512) `apply_rules()`
- [`process/subprocesses/_linkage_indicators.py:537`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_linkage_indicators.py#L537) `sample_point_values()`

## Used by

[Vegetation cover (NDVI)](vegetation.md), [Proximity to major roads](major_roads.md), [Block size (perimeter)](block_size.md), [Job diversity](job_diversity.md)
