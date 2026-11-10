# Public transport stops

[← Back to contents](../README.md)

Mexicali has no GTFS feed, so the IMIP facilities layer is the local source of stops (transport category, excluding the inland freight terminal). With `replace` at its default (false), they are pooled with stops identified in OpenStreetMap under the same destination name, `pt_any`.

| Sample point variable | Area variable (measured value) | Description | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|---|---|
| `sp_walk_nearest_node_pt_any` | `avg_walk_dist_pt_any` | Average distance (m) along the pedestrian network to the nearest public transport stop (best result of GTFS and OpenStreetMap/custom sources) | 882 m | 1,432 m |

## Method: practice

**Recipes:** [R2. Network distance to the nearest destination, censored](../03_recipes.md#r2)

**Configuration** ([`MX_Mexicali_2025_ULI.yml:168`](../../data/MX_Mexicali_2025_ULI.yml#L168)):

```yaml
pt_any:
  data: MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "equipamiento_category='transp' AND TIPO != 'TERMINAL INTERIOR DE CARGA (CENTRAL DE SERVICIOS DE CARGA)'"
  source: IMIP / CFC
  publication_date: 2026-05-18
  url: ""
  licence: "Provided by IMIP via CFC"
  citation: As per advice from Juan Ernesto Díaz Noguez
```

## Used by

[Public transport within 300 m](public_transport.md)
