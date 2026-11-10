# Convenience stores within 300 m

[← Back to contents](../README.md)

> Walking distance to the nearest convenience store, scored with a 300 m soft threshold.

## Identity

| | |
|---|---|
| Identifier | `convenience` |
| Core measure (variable sheet) | Daily essential-services access |
| Sheet / register ID | 132 · #132 |
| Sample point variable | `sp_walk_nearest_node_denue_food_retail` |
| Area variable (measured value) | `avg_walk_dist_denue_food_retail` (m) |
| Normalised score | `index_uli__convenience` |
| Domains (share of weight) | [Social infrastructure](domain_social_infrastructure.md) (33%), [Mobility and transport](domain_mobility_transport.md) (33%), [Economic development](domain_economic_development.md) (33%) |
| Subdomain | Social infrastructure: Public services; Mobility and transport: Active mobility; Economic development: Food environment |
| Lens | Proximity |
| Better when | measured value lower (transformed score higher) |
| Effective weight in the index | `uli` 3.6% · `uli_plain` 3.6% |
| Status | Scored in the published index |

## Rationale and interpretation

> The availability of minimarts is an indicator of local food access, supporting the convenient provision of daily necessities that shape urban life quality.
>
> — *Indicator register #132: Access to minimarts (Economic Development / Food Environment)*

- Workbook citation: Lowe et al., 2015, 'Planning healthy, liveable and sustainable cities: how can indicators inform policy?'; Alderton et al., 2019, 'What is the meaning of urban liveability for a city in a low-to-middle-income country? Contextualising liveability for Bangkok, Thailand'
- Article list: #13: Alderton (2021), ‘Measuring and monitoring liveability in a low-to-middle income country: a proof-of-concept for Bangkok, Thailand and lessons from an international partnership’

**How to read it.** … of the population live within 300 m of a convenience store; on average the nearest is … away (lower is better).

**Access to convenience stores** (Daily essential-services access; ID 132)
- *How to calculate (variable sheet):* Walking distance access to convenience stores and minimart

**Percentage of population with access to convenience stores** (Daily essential-services access; ID 132)
- *How to calculate (variable sheet):* USE GHSCI CALCULATION HERE (Distance (m) along the pedestrian network to the nearest convenience store (source: OpenStreetMap or custom data))

## Data sources

**Sources declared in the configuration:**

- INEGI (2026) Directorio Estadístico Nacional de Unidades Económicas (DENUE), May 2026.

**Source recorded by GHSCI (data dictionary)** (`avg_walk_dist_denue_food_retail`):

- OpenStreetMap: Geofabrik GmbH, 20260815, ODbL, https://download.geofabrik.de/north-america/mexico-latest.osm.pbf, OpenStreetMap Contributors.  Geofabrik GmbH (2026). https://download.geofabrik.de/north-america/mexico-latest.osm.pbf; INEGI, Directorio Estadistico Nacional de Unidades Economicas (DENUE): 2026-05, Terminos de Libre Uso de la Informacion del INEGI, https://www.inegi.org.mx/app/mapa/denue/, INEGI (2026). Directorio Estadistico Nacional de Unidades Economicas (DENUE), mayo 2026. Instituto Nacional de Estadistica y Geografia, Mexico.

**Destination filter:**

- `denue_food_retail` (Food retail, any (DENUE)): `MX/INEGI/DENUE_2026/denue_inegi_02_.shp` — Destination filter: `"(codigo_act LIKE '4611%' AND codigo_act NOT IN ('461211','461212','461213','461220')) OR codigo_act LIKE '4621%'"`

**Inputs:** [DENUE destinations by SCIAN code](denue_destinations.md)

## Method: theory

1. Distance along the pedestrian network from each sample point to the nearest destination, `d` (R2), censored at the largest band searched (1,500 m): a point with no destination within it has no value.
2. Soft access score (R10): `s(d) = 1 / (1 + exp(k·(d − t)/t))`, with `t = 300 m` and `k = 5`; `s = 0.5` at the threshold, ≈ 0.99 beside the destination, ≈ 0.007 at `2t`; no value → `s = 0`.
3. AMPI normalisation (R11) of `s` against the study region's goalposts, then aggregation to domains and index (R12) and to areas (R13).

## Method: practice

**Recipes:** [R1. Sample points and the pedestrian network](../03_recipes.md#r1), [R2. Network distance to the nearest destination, censored](../03_recipes.md#r2), [R10. Transforms: soft thresholds and stepped ladders](../03_recipes.md#r10), [R11. Normalisation: the Adjusted Mazziotta–Pareto Index (AMPI)](../03_recipes.md#r11), [R12. Aggregation: domains, shared indicators and the index](../03_recipes.md#r12), [R13. From sample points to areas](../03_recipes.md#r13), [R14. Frozen goalposts and recalculating a scenario](../03_recipes.md#r14)

**Configuration** ([`MX_Mexicali_2025_ULI.yml:1506`](../../data/MX_Mexicali_2025_ULI.yml#L1506)):

```yaml
- variable: sp_walk_nearest_node_denue_food_retail
  name: convenience
  domains: [social_infrastructure, mobility_transport, economic_development]
  transform: {soft_threshold: 300}
  group: {es: 'Acceso a servicios esenciales cotidianos', en: 'Daily essential-services access'}
  label: {es: 'Tiendas de conveniencia a menos de 300 m', en: 'Convenience stores within 300 m'}
  reading: {es: '{access} de la población vive a menos de 300 m de una tienda de conveniencia; en promedio, la más cercana está a {value}', en: '{access} of the population live within 300 m of a convenience store; on average the nearest is {value} away'}
  subdomain:
    social_infrastructure: {es: 'Servicios públicos', en: 'Public services'}
    mobility_transport: {es: 'Movilidad activa', en: 'Active mobility'}
    economic_development: {es: 'Ambiente de alimentación', en: 'Food environment'}
  about:
    es: Distancia a pie a la tienda de conveniencia más cercana, puntuada con un umbral suave de 300 m.
    en: Walking distance to the nearest convenience store, scored with a 300 m soft threshold.
  sources:
    - 'INEGI (2026) Directorio Estadístico Nacional de Unidades Económicas (DENUE), May 2026.'
```

[`MX_Mexicali_2025_ULI.yml:496`](../../data/MX_Mexicali_2025_ULI.yml#L496):

```yaml
- {name: denue_food_retail, category: food_retail, variant: lenient, layer: destinations, where: "dest_name = 'denue_food_retail'"}
```

**Code (GHSCI):**

- [`process/subprocesses/_accessibility_spec.py:806`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L806) `_banded_distances()`
- [`process/subprocesses/setup_sp.py:888`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/setup_sp.py#L888) `create_full_nodes()`
- [`process/subprocesses/_composite_index.py:1457`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1457) `soft_threshold()`
- [`process/subprocesses/_composite_index.py:1819`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1819) `normalise()`
- [`process/subprocesses/_composite_index.py:1838`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1838) `mpi_aggregate()`

|  | Sample point variable | Transform | Goalposts (scale scored) | inf – sup | skew / kurt. / tied | Flags |
|---|---|---|---|---|---|---|
| `uli` | sp_walk_nearest_node_denue_food_retail | soft access, 300 m threshold, k = 5 | 0.179 · 0.675 · 1.172 | 0.000 – 0.993 | −0.94 / −0.77 / 0.5% | none |
| `uli_plain` | sp_walk_nearest_node_denue_food_retail | soft access, 300 m threshold, k = 5 | 0.179 · 0.675 · 1.172 | 0.000 – 0.993 | −0.94 / −0.77 / 0.5% | none |

## Recalculation (Reimagina Urbano)

A destination added or removed, or a change to the pedestrian network, changes `d` only at points whose nearest destination changes: a multi-source Dijkstra from the affected destinations, limited to 1,500 m, taking the minimum with the previous distance, suffices.

With the frozen goalposts of the parameters file (`Ref`, `Min`, `Max`, R14), a new score is `r = 100 ± 60·(x − Ref)/(Max − Min)` without re-resolving goalposts; the domain and index are recomputed by R12, less 100. A scenario is then compared with the baseline on the same scale.

## Results

| Measure | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|
| Region value | 181 m | 341 m |
| Region score (`uli`) | +8.0 | −4.2 |
| Areas with a value | 14,209 of 14,252 manzanas | 13,265 of 14,988 lots |
| Median (P25–P75), weighted | 136 m (99 m – 203 m) | 210 m (140 m – 527 m) |
| Range | 16 m – 1,594 m | 10 m – 1,660 m |
| Nothing within the distance searched | 0.0% | 0.0% |
| Score: median (P25–P75) (`uli`) | +14.3 (+6.3 – +16.9) | +8.2 (−38.5 – +15.6) |

*Distributions: study region manzanas weighted by census population (2020); Condesa lots weighted equally (3.2 residents assumed per lot). Region values are those GHSCI reports for each region as a whole.*

*A mean distance is taken over the sample points that found a destination within the distance searched; the row "Nothing within the distance searched" gives the share of population in areas that found none.*

- Study region: 87.2% of the population live within 300 m of a convenience store; on average the nearest is 181 m away.
- Condesa: 67.4% of the population live within 300 m of a convenience store; on average the nearest is 341 m away.
- For the study region as a whole the value is 181 m; in Condesa, 341 m. Condesa's score lies 4.2 points below the study region average (+8.0 for the study region).

## Map

![Convenience stores within 300 m](../../figures/en/convenience.png)

*Map. Convenience stores within 300 m: measured value (m) by manzana across the study region and by lot in Condesa (inset). Dashboard classes; the favourable end is the light end (lower is better).*

## Caveats and open questions

- Labelled "convenience stores", the destination is DENUE food retail of any kind (abarrotes and misceláneas, confectionery, prepared food, self-service and department stores), which includes the fresh food retailers.
