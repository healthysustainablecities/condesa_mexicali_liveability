# Heat exposure (GUHVI)

[← Back to contents](../README.md)

> The GUHVI's heat exposure sub-index (0-100), from land surface temperature; lower is better.

## Identity

| | |
|---|---|
| Identifier | `heat_exposure` |
| Core measure (variable sheet) | Global Urban Heat Vulnerability Index (GUHVI) |
| Sheet / register ID | 382 · #382 |
| Sample point variable | `sp_urban_heat_exposure_index` |
| Area variable (measured value) | `urban_heat_exposure_index` (0–100) |
| Normalised score | `index_uli__heat_exposure` |
| Domains (share of weight) | [Ambient environment](domain_ambient_environment.md) |
| Subdomain | Climate risks |
| Lens | Quality |
| Better when | lower |
| Effective weight in the index | `uli` 2.8% · `uli_plain` 2.4% |
| Status | Scored in the published index |

## Rationale and interpretation

> Mitigating the urban heat island effect by reducing localized temperature increases promotes thermal comfort and supports the physical and mental well-being of city dwellers.
>
> — *Indicator register #382: Urban heat island (Ambient Environment / Risks)*

- Workbook citation: Leya et al., 2022, 'Spatial Variations of Urban Heat Island Development in Khulna City, Bangladesh: Implications for Urban Planning and Development'
- Article list: #18: Jodder (2024), ‘Urban Livability in a Rapidly Urbanizing Mid-Size City: Lessons for Planning in the Global South’
- ⚠ the workbook citation names no author of the listed article; verify before citing (citation_audit.csv)

**How to read it.** Heat exposure index of … (0-100; lower is better).

**Heat exposure** (Global Urban Heat Vulnerability Index (GUHVI); ID 382)
- *How to calculate (variable sheet):* USE GHSCI CALCULATION HERE (Land Surface Temperature)

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

**Configuration** ([`MX_Mexicali_2025_ULI.yml:1217`](../../data/MX_Mexicali_2025_ULI.yml#L1217)):

```yaml
- variable: sp_urban_heat_exposure_index
  name: heat_exposure
  domains: [ambient_environment]
  polarity: negative
  goalposts: {min: 0, max: 100}
  lens: quality
  group: {es: 'Índice Global de Vulnerabilidad Urbana al Calor (GUHVI)', en: 'Global Urban Heat Vulnerability Index (GUHVI)'}
  label: {es: 'Exposición al calor (GUHVI)', en: 'Heat exposure (GUHVI)'}
  reading: {es: 'Índice de exposición al calor de {value} (0-100; menor es mejor)', en: 'Heat exposure index of {value} (0-100; lower is better)'}
  subdomain: {es: 'Riesgos climáticos', en: 'Climate risks'}
  about:
    es: Subíndice de exposición al calor del GUHVI (0-100), a partir de la temperatura de la superficie terrestre; menor es mejor.
    en: The GUHVI's heat exposure sub-index (0-100), from land surface temperature; lower is better.
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
| `uli` | sp_urban_heat_exposure_index | as measured | 0 · 47 · 100 | 0 – 100 | 0.58 / 1.97 / 2.6% | none |
| `uli_plain` | sp_urban_heat_exposure_index | as measured | 0 · 47 · 100 | 0 – 100 | 0.58 / 1.97 / 2.6% | none |

## Recalculation (Reimagina Urbano)

GUHVI sub-indices are normalised within the region by their own minima and maxima; a scenario must use the baseline's minima and maxima so as not to re-scale the whole city.

With the frozen goalposts of the parameters file (`Ref`, `Min`, `Max`, R14), a new score is `r = 100 ± 60·(x − Ref)/(Max − Min)` without re-resolving goalposts; the domain and index are recomputed by R12, less 100. A scenario is then compared with the baseline on the same scale.

## Results

| Measure | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|
| Region value | 49.0 | 33.3 |
| Region score (`uli`) | +0.2 | +8.5 |
| Areas with a value | 14,148 of 14,252 manzanas | 13,265 of 14,988 lots |
| Median (P25–P75), weighted | 45.6 (40.2 – 51.4) | 33.1 (23.1 – 38.5) |
| Range | 0.0 – 100.0 | 17.0 – 68.8 |
| Score: median (P25–P75) (`uli`) | +1.1 (−2.4 – +4.3) | +8.6 (+5.4 – +14.6) |

*Distributions: study region manzanas weighted by census population (2020); Condesa lots weighted equally (3.2 residents assumed per lot). Region values are those GHSCI reports for each region as a whole.*

- Study region: Heat exposure index of 49.0 (0-100; lower is better).
- Condesa: Heat exposure index of 33.3 (0-100; lower is better).
- For the study region as a whole the value is 49.0; in Condesa, 33.3. Condesa's score lies 8.5 points above the study region average (+0.2 for the study region).

## Map

![Heat exposure (GUHVI)](../../figures/en/heat_exposure.png)

*Map. Heat exposure (GUHVI): measured value (0–100) by manzana across the study region and by lot in Condesa (inset). Dashboard classes; the favourable end is the light end (lower is better).*

## Caveats and open questions

- The GUHVI sub-indices are min–max normalised within the region, so 0 and 100 are the least and most exposed places in Mexicali, not absolute thresholds (configuration, composite_indices).
- Heat exposure is derived from land surface temperature alone; the sheet's separate heat exposure core measure (land surface temperature, extreme heat frequency, night-time heat retention) awaits delivery (configuration).
