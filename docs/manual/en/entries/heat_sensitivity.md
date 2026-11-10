# Heat sensitivity (GUHVI)

[← Back to contents](../README.md)

> The GUHVI's heat sensitivity sub-index (0-100), from albedo, vegetation, local climate zones, population density and the vulnerable population; lower is better.

## Identity

| | |
|---|---|
| Identifier | `heat_sensitivity` |
| Core measure (variable sheet) | Global Urban Heat Vulnerability Index (GUHVI) |
| Sheet / register ID | – |
| Sample point variable | `sp_urban_heat_sensitivity_index` |
| Area variable (measured value) | `urban_heat_sensitivity_index` (0–100) |
| Normalised score | `index_uli__heat_sensitivity` |
| Domains (share of weight) | [Ambient environment](domain_ambient_environment.md) |
| Subdomain | Climate risks |
| Lens | Quality |
| Better when | lower |
| Effective weight in the index | `uli` 2.8% · `uli_plain` 2.4% |
| Status | Scored in the published index |

## Rationale and interpretation

*Pending: Not recorded in the project register.*

**How to read it.** Heat sensitivity index of … (0-100; lower is better).

**Heat sensitivity** (Global Urban Heat Vulnerability Index (GUHVI); ID –)
- *How to calculate (variable sheet):* USE GHSCI CALCULATION HERE (Land Surface Albedo, Normalised Difference Vegetation Index, Local Climate Zones, Population Density, Vulnerable Population Percentage)

## Data sources

**Sources declared in the configuration:**

- Turner et al. (2025) Urban Climate 64, 102716; computed in Google Earth Engine by GHSCI.

**Inputs:** [Global Urban Heat Vulnerability Index (GUHVI) and its inputs](guhvi.md)

## Method: theory

1. A sub-index of the Global Urban Heat Vulnerability Index (GUHVI; Turner et al. 2025), computed in Google Earth Engine on an analysis grid and min–max normalised to 0–100 within the region (R8).
2. Each sample point takes the value of the cell containing it.
3. AMPI normalisation (R11) with fixed goalposts of 0 and 100 (the sub-index's own scale), aggregation (R12) and areas (R13).

## Method: practice

**Recipes:** [R1. Sample points and the pedestrian network](../03_recipes.md#r1), [R8. Earth Engine: heat vulnerability and large green space](../03_recipes.md#r8), [R11. Normalisation: the Adjusted Mazziotta–Pareto Index (AMPI)](../03_recipes.md#r11), [R12. Aggregation: domains, shared indicators and the index](../03_recipes.md#r12), [R13. From sample points to areas](../03_recipes.md#r13), [R14. Frozen goalposts and recalculating a scenario](../03_recipes.md#r14)

**Configuration** ([`MX_Mexicali_2025_ULI.yml:1232`](../../data/MX_Mexicali_2025_ULI.yml#L1232)):

```yaml
- variable: sp_urban_heat_sensitivity_index
  name: heat_sensitivity
  domains: [ambient_environment]
  polarity: negative
  goalposts: {min: 0, max: 100}
  lens: quality
  group: {es: 'Índice Global de Vulnerabilidad Urbana al Calor (GUHVI)', en: 'Global Urban Heat Vulnerability Index (GUHVI)'}
  label: {es: 'Sensibilidad al calor (GUHVI)', en: 'Heat sensitivity (GUHVI)'}
  reading: {es: 'Índice de sensibilidad al calor de {value} (0-100; menor es mejor)', en: 'Heat sensitivity index of {value} (0-100; lower is better)'}
  subdomain: {es: 'Riesgos climáticos', en: 'Climate risks'}
  about:
    es: Subíndice de sensibilidad al calor del GUHVI (0-100), a partir del albedo, la vegetación, las zonas climáticas locales, la densidad de población y la población vulnerable; menor es mejor.
    en: The GUHVI's heat sensitivity sub-index (0-100), from albedo, vegetation, local climate zones, population density and the vulnerable population; lower is better.
  sources:
    - 'Turner et al. (2025) Urban Climate 64, 102716; computed in Google Earth Engine by GHSCI.'
```

**Code (GHSCI):**

- [`process/subprocesses/_earth_engine_indicators.py:846`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_earth_engine_indicators.py#L846) `guhvi_analysis()`
- [`process/subprocesses/_earth_engine_indicators.py:1105`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_earth_engine_indicators.py#L1105) `normalise_band()`
- [`process/subprocesses/_composite_index.py:1819`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1819) `normalise()`
- [`process/subprocesses/_composite_index.py:1838`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1838) `mpi_aggregate()`

|  | Sample point variable | Transform | Goalposts (scale scored) | inf – sup | skew / kurt. / tied | Flags |
|---|---|---|---|---|---|---|
| `uli` | sp_urban_heat_sensitivity_index | as measured | 0 · 58 · 100 | 0 – 81 | −0.79 / −0.15 / 2.6% | none |
| `uli_plain` | sp_urban_heat_sensitivity_index | as measured | 0 · 58 · 100 | 0 – 81 | −0.79 / −0.15 / 2.6% | none |

## Recalculation (Reimagina Urbano)

GUHVI sub-indices are normalised within the region by their own minima and maxima; a scenario must use the baseline's minima and maxima so as not to re-scale the whole city.

With the frozen goalposts of the parameters file (`Ref`, `Min`, `Max`, R14), a new score is `r = 100 ± 60·(x − Ref)/(Max − Min)` without re-resolving goalposts; the domain and index are recomputed by R12, less 100. A scenario is then compared with the baseline on the same scale.

## Results

| Measure | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|
| Region value | 59.7 | 33.8 |
| Region score (`uli`) | −4.7 | +14.7 |
| Areas with a value | 14,148 of 14,252 manzanas | 13,265 of 14,988 lots |
| Median (P25–P75), weighted | 67.3 (57.3 – 74.2) | 35.1 (30.3 – 39.1) |
| Range | 4.2 – 81.2 | 10.5 – 48.5 |
| Score: median (P25–P75) (`uli`) | −5.4 (−9.5 – +0.6) | +13.9 (+11.6 – +16.8) |

*Distributions: study region manzanas weighted by census population (2020); Condesa lots weighted equally (3.2 residents assumed per lot). Region values are those GHSCI reports for each region as a whole.*

- Study region: Heat sensitivity index of 59.7 (0-100; lower is better).
- Condesa: Heat sensitivity index of 33.8 (0-100; lower is better).
- For the study region as a whole the value is 59.7; in Condesa, 33.8. Condesa's score lies 14.7 points above the study region average (−4.7 for the study region).

## Map

![Heat sensitivity (GUHVI)](../../figures/en/heat_sensitivity.png)

*Map. Heat sensitivity (GUHVI): measured value (0–100) by manzana across the study region and by lot in Condesa (inset). Dashboard classes; the favourable end is the light end (lower is better).*

## Caveats and open questions

- Min–max normalised within the region (see heat exposure).
