# Natural blue space

[← Back to contents](../README.md)

Blue space is derived independently of public open space, from OpenStreetMap water tags on both **polygons and lines**: Mexicali's canals and drains are largely mapped as lines and would never enter a polygon-based process. Swimming pools, water parks and private features are excluded. Polygons are sampled along their exterior ring and lines along their length; points are generated every 20 m and those with a street within 30 m are retained (`blue_space_nodes_30m_line`), to which walking distance is measured.

| Sample point variable | Area variable (measured value) | Description | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|---|---|
| `sp_walk_nearest_node_blue_space` | `avg_walk_dist_blue_space` | Average distance (m) along the pedestrian network to the nearest natural blue space -- a river, canal, drain, lake, reservoir, wetland, beach or coast (source: OpenStreetMap or custom data) | 797 m | 590 m |

## Method: practice

**Recipes:** [R2. Network distance to the nearest destination, censored](../03_recipes.md#r2)

**Configuration** ([`MX_Mexicali_2025_ULI.yml:489`](../../data/MX_Mexicali_2025_ULI.yml#L489)):

```yaml
- {name: blue_space, category: blue_space, variant: any, layer: blue_space_nodes_30m_line}
```

**Code (GHSCI):**

- [`process/subprocesses/_06_open_space_areas_setup.py:365`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_06_open_space_areas_setup.py#L365) `blue_space_criteria()`
- [`process/subprocesses/_06_open_space_areas_setup.py:381`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_06_open_space_areas_setup.py#L381) `blue_space_setup()`
- [`process/subprocesses/_06_open_space_areas_setup.py:485`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_06_open_space_areas_setup.py#L485) `blue_space_nodes_setup_query()`

## Used by

[Natural blue space nearby](blue_space.md)
