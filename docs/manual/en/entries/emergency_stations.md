# Police and fire stations (straight line)

[← Back to contents](../README.md)

Stations are read from the IMIP facilities layer, each specification with its own file and filter, clipped to the study region buffered by its maximum distance and outside the exclusion region (California). Coverage is measured in a straight line because an emergency response does not follow footpaths.

| Sample point variable | Area variable (measured value) | Description | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|---|---|
| `sp_euclid_dist_imip_police_station` | `avg_euclid_dist_imip_police_station` | Average straight-line distance (m) to the nearest 'imip police station' (custom destination) | 1,406 m | 4,156 m |
| `sp_euclid_dist_imip_fire_station` | `avg_euclid_dist_imip_fire_station` | Average straight-line distance (m) to the nearest 'imip fire station' (custom destination) | 2,297 m | 6,371 m |

- **`imip_police_station`** (Police stations (IMIP)): `MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "TIPO = 'INSTALACIONES POLICIALES'"`; distances [15000], max_distance 45000. 27 police facilities in the IMIP equipamiento layer (administración pública). (IMIP / CFC; Provided by IMIP via CFC)
- **`imip_fire_station`** (Municipal fire stations (IMIP)): `MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "TIPO = 'ESTACION DE BOMBEROS MUNICIPAL'"`; distances [75000]. 10 municipal fire stations in the IMIP equipamiento layer (administración pública). (IMIP / CFC; Provided by IMIP via CFC)

## Method: practice

**Recipes:** [R5. Straight-line catchments](../03_recipes.md#r5)

**Configuration** ([`MX_Mexicali_2025_ULI.yml:679`](../../data/MX_Mexicali_2025_ULI.yml#L679)):

```yaml
euclidean:
  destinations:
    - name: imip_police_station
      dest_name_full: Police stations (IMIP)
      data: MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "TIPO = 'INSTALACIONES POLICIALES'"
      distances: [15000]
      max_distance: 45000
      source: IMIP / CFC
      licence: Provided by IMIP via CFC
      notes: 27 police facilities in the IMIP equipamiento layer (administración pública).
    - name: imip_fire_station
      dest_name_full: Municipal fire stations (IMIP)
      data: MX/CFC/cleaned/por_estado/02_baja_california/002_mexicali/imip/equipamiento_combined.fgb -where "TIPO = 'ESTACION DE BOMBEROS MUNICIPAL'"
      distances: [75000]
      source: IMIP / CFC
      licence: Provided by IMIP via CFC
      notes: 10 municipal fire stations in the IMIP equipamiento layer (administración pública).
```

**Code (GHSCI):**

- [`process/subprocesses/_euclidean_accessibility.py:66`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_euclidean_accessibility.py#L66) `resolve_spec()`
- [`process/subprocesses/_euclidean_accessibility.py:177`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_euclidean_accessibility.py#L177) `import_destinations()`
- [`process/subprocesses/_euclidean_accessibility.py:247`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_euclidean_accessibility.py#L247) `nearest_distances()`

## Used by

[Fire station within 3 km](fire_3km.md), [Police station within 2 km](police_2km.md)
