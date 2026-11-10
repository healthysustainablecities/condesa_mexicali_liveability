# Public open space and large public green space

[← Back to contents](../README.md)

GHSCI identifies areas of open space from OpenStreetMap polygons (rules in `configuration/osm_open_space.yml`), clusters them into contiguous areas and retains those with public access. Water is excluded from public open space, so that a canal cannot chain contiguous parks into one enormous area. Access is measured to points every 20 m along the area's perimeter that a street passes within 30 m of (`aos_public_any_nodes_30m_line`).

A **large public green space** (LPUGS) is a public open space of at least 1 ha with annual mean NDVI ≥ 0.2 (Sentinel-2), identified in Google Earth Engine; its entry points are the subset of access points belonging to those areas.

| Sample point variable | Area variable (measured value) | Description | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|---|---|
| `sp_walk_nearest_node_public_open_space_any` | `avg_walk_dist_public_open_space_any` | Average distance (m) along the pedestrian network to the nearest public open space (source: OpenStreetMap) | 469 m | 849 m |
| `sp_access_large_public_green_space_score` | `pct_access_500m_large_public_green_space_score` | Percentage of population with access within 500 m of a large public green space of at least 1 hectare (source: OpenStreetMap, Google Earth Engine) | 8.2% | 0.0% |

## Method: practice

**Recipes:** [R2. Network distance to the nearest destination, censored](../03_recipes.md#r2), [R3. Banded access, and distance from a disamenity](../03_recipes.md#r3), [R8. Earth Engine: heat vulnerability and large green space](../03_recipes.md#r8)

**Configuration** ([`MX_Mexicali_2025_ULI.yml:475`](../../data/MX_Mexicali_2025_ULI.yml#L475)):

```yaml
- {name: public_open_space_any,   category: pos,  variant: lenient, layer: aos_public_any_nodes_30m_line}
```

**Code (GHSCI):**

- [`process/subprocesses/_06_open_space_areas_setup.py:43`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_06_open_space_areas_setup.py#L43) `aos_setup_queries()`
- [`process/subprocesses/_earth_engine_indicators.py:282`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_earth_engine_indicators.py#L282) `lpugs_analysis()`
- [`process/subprocesses/_earth_engine_indicators.py:664`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_earth_engine_indicators.py#L664) `lpugs_indicators()`

## Used by

[Parks within 300 m](parks.md), [Large public green space within 500 m](lpugs.md)
