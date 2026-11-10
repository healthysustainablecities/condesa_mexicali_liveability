# Police station within 2 km

[← Back to contents](../README.md)

> Straight-line distance to the nearest police facility, scored with a 2 km soft threshold.

## Identity

| | |
|---|---|
| Identifier | `police_2km` |
| Core measure (variable sheet) | Personal and road safety |
| Sheet / register ID | 69, 174 · #174 |
| Sample point variable | `sp_euclid_dist_imip_police_station` |
| Area variable (measured value) | `avg_euclid_dist_imip_police_station` (m) |
| Normalised score | `index_uli__police_2km` |
| Domains (share of weight) | [Safety and protection](domain_safety.md) (33%), [Mobility and transport](domain_mobility_transport.md) (33%), [Built environment](domain_built_environment.md) (33%) |
| Subdomain | Safety and protection: Personal safety |
| Lens | Proximity |
| Better when | measured value lower (transformed score higher) |
| Effective weight in the index | `uli` 6.2% · `uli_plain` 6.2% |
| Status | Scored in the published index |

## Rationale and interpretation

> Neighborhoods located near police stations experience enhanced security and stability, allowing residents to live without feeling threatened or harmed.
>
> — *Indicator register #174: Access to police station (Safety / Personal Safety)*

- Workbook citation: Fu et al., 2019, 'The Livable Urban Landscape: GIS and Remote Sensing Extracted Land Use Assessment for Urban Livability in Changchun Proper, China'; Liu et al., 2020, 'Using Multi-Source Data to Assess Livability in Hong Kong at the Community-Based Level: A Combined Subjective-Objective Approach'; Paul & Sen, 2018, 'Livability Assessment within a Metropolis Based on the Impact of Integrated Urban Geographic Factors (IUGFs) on Clustering Urban Centers of Kolkata'
- Article list: #18: Jodder (2024), ‘Urban Livability in a Rapidly Urbanizing Mid-Size City: Lessons for Planning in the Global South’; #20: Basu (2021), ‘Urban livability index assessment based on land-use changes in an Indian medium-sized city (Raiganj)’; #8: Onnom (2018), ‘Development of a Liveable City Index (LCI) Using Multi Criteria Geospatial Modelling for Medium Class Cities in Developing Countries’
- ⚠ the workbook citation names no author of the listed article; verify before citing (citation_audit.csv)

**How to read it.** On average the nearest police station is … away in a straight line (lower is better).

**% of the population with coverage of police stations** (Personal and road safety; ID 69, 174)
- *How to calculate (variable sheet):* % of the population that is within a network buffer of 15 km around a police station
- *Notes (sheet):* Threshold change from 15km to 2km (road network unavailable; 15km covered 100% of municipality with no variation). Euclidean distance. ~64% of grid cells within 2 km. Condesa: 40/40.
- *Doubts (sheet):* For this one we need to define a redius that covers multiple neighborhoods (review SEDESOL)

## Data sources

**Sources declared in the configuration:**

- IMIP equipamiento layer via CFC (27 police facilities); threshold revised by the work package (Alejandro).

**Source recorded by GHSCI (data dictionary)** (`avg_euclid_dist_imip_police_station`):

- Police stations (IMIP): IMIP / CFC, Provided by IMIP via CFC

**Inputs:** [Police and fire stations (straight line)](emergency_stations.md)

## Method: theory

1. Straight-line distance from each sample point to the nearest station, `d` (R5), searched to 45 km; beyond it, no value.
2. Soft access (R10): `s(d) = 1 / (1 + exp(k·(d − t)/t))`, `t = 2,000 m`, `k = 5`; no value → 0.
3. AMPI normalisation (R11), aggregation (R12) and areas (R13).

## Method: practice

**Recipes:** [R1. Sample points and the pedestrian network](../03_recipes.md#r1), [R5. Straight-line catchments](../03_recipes.md#r5), [R10. Transforms: soft thresholds and stepped ladders](../03_recipes.md#r10), [R11. Normalisation: the Adjusted Mazziotta–Pareto Index (AMPI)](../03_recipes.md#r11), [R12. Aggregation: domains, shared indicators and the index](../03_recipes.md#r12), [R13. From sample points to areas](../03_recipes.md#r13), [R14. Frozen goalposts and recalculating a scenario](../03_recipes.md#r14)

**Configuration** ([`MX_Mexicali_2025_ULI.yml:1409`](../../data/MX_Mexicali_2025_ULI.yml#L1409)):

```yaml
- variable: sp_euclid_dist_imip_police_station
  name: police_2km
  domains: [safety, mobility_transport, built_environment]
  transform: {soft_threshold: 2000}
  group: {es: 'Seguridad personal y vial', en: 'Personal and road safety'}
  label: {es: 'Estación de policía a menos de 2 km', en: 'Police station within 2 km'}
  reading: {es: 'En promedio, la estación de policía más cercana está a {value} en línea recta', en: 'On average the nearest police station is {value} away in a straight line'}
  subdomain:
    safety: {es: 'Seguridad personal', en: 'Personal safety'}
  about:
    es: Distancia en línea recta a la instalación policial más cercana, puntuada con un umbral suave de 2 km.
    en: Straight-line distance to the nearest police facility, scored with a 2 km soft threshold.
  sources:
    - 'IMIP equipamiento layer via CFC (27 police facilities); threshold revised by the work package (Alejandro).'
```

**Code (GHSCI):**

- [`process/subprocesses/_euclidean_accessibility.py:247`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_euclidean_accessibility.py#L247) `nearest_distances()`
- [`process/subprocesses/_composite_index.py:1457`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1457) `soft_threshold()`
- [`process/subprocesses/_composite_index.py:1819`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1819) `normalise()`
- [`process/subprocesses/_composite_index.py:1838`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1838) `mpi_aggregate()`

|  | Sample point variable | Transform | Goalposts (scale scored) | inf – sup | skew / kurt. / tied | Flags |
|---|---|---|---|---|---|---|
| `uli` | sp_euclid_dist_imip_police_station | soft access, 2,000 m threshold, k = 5 | 0.115 · 0.611 · 1.108 | 0.000 – 0.993 | −0.63 / −1.26 / 0.1% | none |
| `uli_plain` | sp_euclid_dist_imip_police_station | soft access, 2,000 m threshold, k = 5 | 0.115 · 0.611 · 1.108 | 0.000 – 0.993 | −0.63 / −1.26 / 0.1% | none |

## Recalculation (Reimagina Urbano)

A new station changes `d` at points nearer it than any other: `d = min(d_previous, straight-line distance to the new station)`.

With the frozen goalposts of the parameters file (`Ref`, `Min`, `Max`, R14), a new score is `r = 100 ± 60·(x − Ref)/(Max − Min)` without re-resolving goalposts; the domain and index are recomputed by R12, less 100. A scenario is then compared with the baseline on the same scale.

## Results

| Measure | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|
| Region value | 1,406 m | 4,156 m |
| Region score (`uli`) | +7.9 | −36.1 |
| Areas with a value | 14,216 of 14,252 manzanas | 13,265 of 14,988 lots |
| Median (P25–P75), weighted | 1,284 m (763 m – 2,014 m) | 4,220 m (3,813 m – 4,593 m) |
| Range | 53 m – 8,906 m | 2,537 m – 5,548 m |
| Score: median (P25–P75) (`uli`) | +14.8 (−7.3 – +20.8) | −36.7 (−36.8 – −36.3) |

*Distributions: study region manzanas weighted by census population (2020); Condesa lots weighted equally (3.2 residents assumed per lot). Region values are those GHSCI reports for each region as a whole.*

- Study region: On average the nearest police station is 1,406 m away in a straight line.
- Condesa: On average the nearest police station is 4,156 m away in a straight line.
- For the study region as a whole the value is 1,406 m; in Condesa, 4,156 m. Condesa's score lies 36.1 points below the study region average (+7.9 for the study region).

## Map

![Police station within 2 km](../../figures/en/police_2km.png)

*Map. Police station within 2 km: measured value (m) by manzana across the study region and by lot in Condesa (inset). Dashboard classes; the favourable end is the light end (lower is better).*

## Caveats and open questions

- The threshold was revised from 15 km to 2 km by the work package: 15 km covered the whole municipality with no variation. Straight-line distance, as the road network was unavailable to the work package (sheet note).
