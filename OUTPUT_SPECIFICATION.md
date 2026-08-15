# Mexicali Liveability Index — output specification

**Version 1.0 · August 2026.** This describes the format indicator results
must be delivered in. 

---

## 1. What to deliver

For each set of indicators you are allocated:

| | |
|---|---|
| **Results** | One table per spatial scale — GeoPackage (`.gpkg`) or CSV (`.csv`) |
| **Data dictionary** | One table describing every variable you produced (`.csv` or `.xlsx`) |

Nothing else is required. If a scale is not applicable to your data, say so in
the data dictionary rather than omitting it silently.

## 2. Coordinate reference system

**Mexico ITRF2008 / UTM zone 11N — EPSG:6366**, for every spatial output.

Reference geometries for every scale are supplied in
`mexicali_reference_areas.gpkg`, already in this projection. Use them as
given — do not redraw boundaries or build your own grid, or results will not
align with anyone else's.

## 3. Spatial scales

Deliver results at each scale your data genuinely support, for **both** study
areas: the Mexicali urban area and the Condesa development.

| Scale | Layer in the reference geopackage | Areas | Area identifier |
|---|---|---|---|
| 100 m population grid | `grid_100m` | 22,151 | `area_id` (grid cell) |
| Manzana (census block) | `manzanas` | 14,236 | `area_id` = INEGI `CVEGEO` |
| AGEB | `agebs` | 436 | `area_id` = INEGI `CVEGEO` |
| Region | `region` | 2 | `area_id` = `mexicali` or `condesa` |
| Condesa subdivisions | `condesa_fraccionamientos` | 40 | `area_id` |
| Condesa lots | `condesa_lotes` | 14,989 | `area_id` |

Every area is listed, including those for which no value can be calculated, so
that partial coverage is visible rather than silent. Each layer also carries
`area_sqm` and `pop_2025` (GHS-POP 2025, apportioned by area from the grid).

The 100 m grid is the GHS-POP 2025 population grid, transformed from Mollweide
to EPSG:6366 and vectorised. Cells are exactly 100 m × 100 m, and the transform
conserves population counts.

## 4. Table structure

**One row per area, one column per indicator.** Not one row per
indicator-and-area.

| `area_id` | `pct_pop_500m_open_space` | `dist_m_nearest_school` |
|---|---|---|
| `020020001661A041` | 42.6 | 385.2 |
| `020020001661A056` | 0.0 | 1204.7 |

- The first column is **`area_id`**, matching the reference geometry exactly.
  For region tables the region name (`mexicali`, `condesa`) is sufficient.
- Every other column is one indicator.
- Deliver values in their natural units. Do not normalise, rescale or
  index — that happens once, centrally, so that it is done consistently.
- Leave a cell empty where there is genuinely no value. Do not use `0`, `-999`
  or `NA` text to mean "missing".

## 5. Variable naming

- **Lowercase, underscores instead of spaces**: `pct_pop_500m_open_space`.
- No accents, spaces, hyphens or punctuation.
- **Clarity beats brevity.** Up to about 30 characters is fine —
  `mean_summer_temperature_c` is better than `mst`.
- Start with what the number is (`pct_`, `count_`, `dist_m_`, `mean_`), then
  what it describes.

## 6. Data dictionary

One row per variable, with these columns:

| Column | Contents |
|---|---|
| `variable` | The column name exactly as it appears in your results |
| `description` | Plain language, **Spanish or English** — what the number means |
| `units` | e.g. `metres`, `percent`, `count`, `persons per km2`, `dimensionless` |
| `statistic` | one of `value`, `mean`, `median`, `percentage`, `count`, `sum`, `rate`, `index`, `category` |
| `scale` | Which scale(s) the variable is provided at |
| `source` | The dataset the value derives from |

Example:

| variable | description | units | statistic | scale | source |
|---|---|---|---|---|---|
| `pct_pop_500m_open_space` | Percentage of residents within 500 m walking distance of a public open space | percent | percentage | grid_100m, manzanas, agebs, region | OpenStreetMap, April 2026 |
| `mean_summer_temperature_c` | Average daytime land surface temperature, June–August | degrees Celsius | mean | grid_100m, agebs | Landsat 8/9, 2024–2025 |
| `count_pharmacies` | Number of pharmacies located within the area | count | count | manzanas, agebs | DENUE 2025 |

The `units` and `statistic` columns matter: without them a column of numbers
cannot be interpreted, combined or mapped correctly.

Use `value` for a direct measurement rather than an aggregate, and `rate` for a
count or amount per unit of area or population.

Indicators produced with the GHSCI software carry these columns automatically in
the data dictionary it generates, so those can be used as supplied.

## 7. Documenting your sources

For every dataset used, record in the data dictionary or an accompanying note:
the name and custodian, a citation, the URL, the date you retrieved it, and its
licence.

## 8. Two things to know about Condesa

**It is largely unbuilt and unpopulated.** Population products record only a few
hundred residents across the whole development. Population-weighted values there
will be unstable or empty — prefer area-based or per-lot measures, and say when
a source simply does not reach it.

**It extends beyond the urban area boundary.** About 18% of the development lies
outside the mapped Mexicali urban area, so the reference geometries cover the
union of both. Use them as supplied and Condesa is fully covered.

---

## Checklist before sending

- [ ] EPSG:6366
- [ ] One row per area, one column per indicator
- [ ] `area_id` matches the reference geometries exactly
- [ ] Variable names lowercase with underscores
- [ ] Every variable appears in the data dictionary, with units and statistic
- [ ] Values in natural units, not normalised
- [ ] Data sources documented with retrieval date and licence
