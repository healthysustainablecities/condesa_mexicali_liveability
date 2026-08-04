# Mexicali Urban Liveability Index — distributed calculation plan

**Version 1.0 · 4 August 2026**

A suite of spatial liveability indicators for Mexicali, Baja California, and
from them a composite liveability index. Outputs also supply layers to the
**Reimagina Urbana** platform.

The indicator set was assembled from a review of the liveability literature,
classified by domain, subdomain, category and subject, and narrowed to
**81 indicators** that are plausibly relevant to health and wellbeing in
Mexicali and feasible with available data. Indicators are *adapted* from the
reviewed articles rather than copied, which is why each requires independent
health evidence: the source article establishes that an indicator has been
used, not that it matters.

Calculation is distributed across a team. This document sets out how the work
is divided and what each contributor delivers. The reasoning behind these
arrangements is recorded separately in [`DECISIONS.md`](DECISIONS.md).

---

## 1. Work packages

Indicators are grouped by **data source and method family**, since that
determines who can do the work and what tooling they need.

| Code | Work package | Lead | Indicators | Method family |
|---|---|---|---|---|
| `WP01` | Destination access and network measures (GHSCI) | Carl Higgs | 39 | GHSCI pedestrian network pipeline |
| `WP02` | Thermal comfort and urban heat | Rossano Schifanella | 7 | Remote sensing and climate |
| `WP03` | Air quality | *TBC* | 6 | Monitoring network, satellite, interpolation |
| `WP04` | Greenness and land cover | *TBC* | 5 | Remote sensing, spectral indices |
| `WP05` | Environmental hazards and safety incidents | *TBC* | 8 | Hazard mapping and incident registries |
| `WP06` | Urban form and land use | *TBC* | 7 | Cadastral and morphometric |
| `WP07` | Street and active travel infrastructure | *TBC* | 4 | Street-segment attributes and audit |
| `WP08` | Housing, economy and public services | *TBC* | 4 | Census, ENIGH/ENVI, DENUE, administrative |
| `WP00` | Composite index and population exposure | Carl Higgs | 1 | Synthesis; not an analyst task |

One indicator (#238 road density) is out of scope. Assignments are declared in
[`uli/work_packages.yml`](uli/work_packages.yml) and drive the register, the
notebooks and the validator, so revising them is a one-line edit followed by
`python build/build_notebooks.py`.

Each work package has a scaffolded notebook in [`notebooks/`](notebooks/),
generated from the indicator workbook, with a brief per indicator reproducing
everything the team has already recorded.

---

## 2. What each contributor delivers

Two files per indicator, in a fixed shape so that results from different
people, data and resolutions can be combined without renegotiation:

```
outputs/<work_package>/<indicator_code>/
    <indicator_code>_results.csv       # long table: measure × geography × unit
    <indicator_code>_metadata.yml      # why, from what, how
```

Written and checked by `uli.write_indicator(results, metadata)`, which
validates first and refuses to publish a failing deliverable. Full
specification: [`schema/ULI_output_schema.md`](schema/ULI_output_schema.md).

### Requirements

**Health evidence.** At least one citation, *independent of the article the
indicator was adapted from*, demonstrating a meaningful health or wellbeing
benefit — with the specific claim, evidence type, population, exposure,
outcome and **effect size with uncertainty**. Systematic reviews,
meta-analyses, cohort studies and reputable guidance (WHO, UN-Habitat, PAHO,
Secretaría de Salud) are preferred.

**Named mechanism.** Every indicator declares one or more `health_pathways`:
physical activity for transport or recreation, social interaction, heat, air
pollution, injury risk, and so on. An indicator whose author cannot name a
pathway should not be computed.

**Revised rationale.** The workbook's draft "reason this matters" text is
rewritten to state the pathway, name the population most affected, cite the
evidence found, and say something specific to Mexicali.

**Evidence-based thresholds.** Where the evidence supports a threshold
different from the source article's, the evidence-based one is used and
recorded in `threshold_justification`. Where no threshold evidence exists,
project defaults (300, 500, 800, 1000, 1600 m) keep results comparable.

**Arid-city context.** Most built-environment and health literature comes from
temperate, high-income cities. Where the transfer to a city with summer maxima
above 45 °C is doubtful, it is recorded in `rationale.arid_context`.

**Documented data sources.** For every dataset: citation, URL, date retrieved,
licence (and whether it may be redistributed via Reimagina Urbana), spatial
resolution, temporal coverage, and whether it covers Condesa.

**Natural units.** Values are delivered unnormalised and not reverse-coded,
with a declared `direction` and, where the evidence supports one, a
`benchmark`. Normalisation and weighting happen once, centrally.

**Honest scale.** `native_scale` records where the calculation actually
happened. Values known only at a coarse scale are replicated downward and
flagged as such.

---

## 3. Reporting geographies

All supplied in `geography/mexicali_uli_geographies.gpkg`, EPSG:6366. Nobody
builds their own.

| Level | Units | Median area | Required |
|---|---|---|---|
| `city` | 1 | 210 km² | ✔ |
| `grid_1000m` | 302 | 1 km² | ✔ |
| `ageb` | 436 | 36 ha | ✔ |
| `condesa_fraccionamiento` | 40 | 7.9 ha | ✔ |
| `grid_100m` | 22,355 | 1 ha | preferred |
| `manzana` | 14,236 | 0.65 ha | ✔ |
| `condesa_lote` | 14,989 | 120 m² | optional |

Contributors compute once at the finest scale their data genuinely support,
then call `uli.harmonise()`, which produces every reporting geography from that
one calculation using a shared crosswalk — aggregating upward with the
appropriate weighting and replicating downward with a flag.

The study extent is the union of the GHSCI Mexicali study region and the
Condesa new development.

---

## 4. Population

Four denominators are carried on every unit, because the right one depends on
the question:

| Basis | What it is | Study extent | Condesa |
|---|---|---|---|
| `pop_census_2020` | INEGI census | 852,506 | 0 |
| `population` | GHS-POP 2025 — observed today | 823,260 | 372 |
| `population_2030` | GHS-POP 2030 — projection as published | 842,287 | 377 |
| `population_planned` | Condesa at full occupancy (declared assumption) | 48,170 | 48,032 |
| `population_scenario_2030` | GHS-POP 2030 outside Condesa **+** planned occupancy inside | **890,079** | 48,032 |

`population` (GHS-POP 2025) is the default weighting basis. Choosing between
bases is a reporting-step decision made once for the project, not by each
contributor — indicators of urban fabric and exposure are properties of place,
and who lives there is applied afterwards.

---

## 5. Condesa

The Condesa new development in south-east Mexicali is a project focus area and
must be covered by every indicator.

It is platted and roaded — 43 km of street network across 27 of its 40
fraccionamientos — but essentially unbuilt: no destinations, and 2020 census
geography covers only 44% of its area. Population products see almost nobody
there, and the 2030 projection does not change that.

Consequences for the work:

- `condesa_fraccionamiento` is a **required** reporting geography, and
  `uli.validate` treats coverage below 80% as an error.
- **Compute on the 100 m grid where the data allow it.** A manzana-native
  calculation reaches 33 of the 40 fraccionamientos; a `grid_100m`-native one
  reaches all 40.
- Contributors record whether their **source** reaches Condesa
  (`data_sources[].condesa_coverage`) and what they did about it
  (`method.condesa_treatment`). Where a source does not reach it, those rows
  are marked `no_data` rather than omitted.
- Population weighting falls back to area weighting where there is no
  population, and a planned-occupancy denominator is available for scenario
  reporting.

---

## 6. Assembly

Once the indicators are delivered, three things happen centrally, in
[`notebooks/09_composite_index.ipynb`](notebooks/09_composite_index.ipynb):

**Population exposure.** What share of the population experiences what,
reported for the study area, for Condesa and for the rest of the city, under
whichever population basis the question calls for. Population with no value is
reported separately rather than counted as unexposed.

**Equity.** Distributional statistics — population-weighted quantiles,
absolute and relative gaps, concentration indices, threshold shares — computed
from the finest-scale results with one implementation for every indicator.

**The composite index.** Normalisation and weighting applied once. Only
measures flagged `include_in_index` are used, and only where they actually vary
at the reporting scale. *How the index is calculated is still to be decided;*
a provisional equal-weight, min-max implementation exists so the pipeline can
be exercised end to end.

The only composites built inside a work package are those produced by the core
GHSCI workflow: the walkability index and its components (street connectivity,
population density, access to daily living amenities) and the level of cycling
traffic stress network. Everything else is delivered as measured.

---

## 7. Getting started

| If you are… | Read |
|---|---|
| A contributor starting a work package | [`docs/analyst_guide.md`](docs/analyst_guide.md), then [`notebooks/00_overview_and_schema.ipynb`](notebooks/00_overview_and_schema.ipynb) |
| Checking what you were assigned | [`indicator_register.csv`](indicator_register.csv) |
| Writing code that produces results | [`schema/ULI_output_schema.md`](schema/ULI_output_schema.md) |
| Wondering why something is the way it is | [`DECISIONS.md`](DECISIONS.md) |

---

## 8. Outstanding

1. Leads for WP03–WP08.
2. Which equity statistics the index reports.
3. How the composite index is calculated — normalisation, weighting, and
   whether city-constant indicators are reported only as context.
4. Sequencing of WP02 and WP01: the walkability index is to be tailored to the
   arid context using thermal comfort outputs, which makes WP02 an input to
   WP01 rather than a parallel stream.
5. Confirmation of the Mexicali mean household size used for the Condesa
   planned-occupancy assumption.
