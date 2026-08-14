# Mexicali Urban Liveability Index — output schema

**Version 1.0.0** · Applies to every indicator delivered by every work package.

The purpose of this schema is narrow and specific: results calculated by
different people, from different data, at different native resolutions, must be
ingestible **without renegotiation** into (a) the composite liveability index
and (b) the Reimagina Urbana platform. Anything that does not serve that
purpose is deliberately left to the analyst.

Two documents are delivered per indicator:

| File | What it is |
|---|---|
| `<indicator_code>_results.csv.gz` | A long (tidy) table of values — one row per measure × geography × unit, gzipped |
| `<indicator_code>_metadata.yml` | Everything needed to interpret, cite, reproduce and licence those values |

Both are validated by `uli.validate.check()` against
`schema/indicator_results.schema.json` and
`schema/indicator_metadata.schema.json`.

---

## 1. Concepts

**Indicator** — a high-level construct from the ULI workbook, identified by its
workbook `#` (e.g. `91`, *Access to public green space*) and a stable
snake_case `indicator_code`.

**Lens (*enfoque*)** — one of the six analytical approaches the team defined
for looking at an indicator: `proximity`, `accessibility`, `quantity`,
`density`, `diversity`, `quality`. Equity was removed from the lens list in
August 2026 and is derived centrally instead — see §6.

**Measure** — a specific, computable operationalisation: an indicator seen
through one lens, with its parameters fixed. This is the unit of delivery.
`measure_id` is `<indicator_code>__<lens>[_<parameter>]`, for example:

```
access_to_public_green_space__proximity
access_to_public_green_space__accessibility_500m
access_to_public_green_space__density_sqm_per_capita
vegetation_percent__quantity
```

An indicator produces **one or more** measures. Do not invent a measure the
data cannot support; two well-founded measures beat six speculative ones.

**Measure family** — where several workbook rows turn out to be one construct
seen through different lenses or time periods, give their measures a shared
`measure_family` slug and distinguish them with `temporal_basis` (see
`uli.vocab.TEMPORAL_BASES`) and `threshold`. Air quality is the canonical case:
#292 is the index value (`annual_mean`), #8 is that value against a standard
(`threshold_share`), #293 is how often the standard is met
(`threshold_compliance_days`), #173 the same for PM2.5
(`threshold_exceedance_days`). One method, one set of data sources, four
measures — not four indicators. The same applies to mean summer temperature
versus days above a comfort threshold, and to flood extent versus annual
average days of flooding.

**Native scale** — the geography at which the calculation *actually* happened,
before anything was aggregated or replicated. Recording this honestly is the
single most important thing in this schema.

---

## 2. Reporting geographies

All geographies are supplied in `geography/mexicali_uli_geographies.gpkg`,
in **EPSG:6366** (Mexico ITRF2008 / UTM zone 11N). Do not build your own; use
`uli.geography.load(level)`.

| `geo_level` | Units | `geo_id` | Required? |
|---|---|---|---|
| `city` | 1 | `MX_Mexicali_2025` | **Yes** |
| `grid_1000m` | 302 | `grid_1000m_<x>_<y>` | **Yes** |
| `ageb` | 436 | INEGI 13-char `CVEGEO` | **Yes** |
| `condesa_fraccionamiento` | 40 | `CONDESA_F###` | **Yes** |
| `grid_100m` | 22,355 | `grid_100m_<x>_<y>` | Preferred |
| `manzana` | 14,236 | INEGI 16-char `CVEGEO` | **Yes** |
| `condesa_lote` | 14,989 | `CONDESA_L#####` | Optional |

Listed coarse to fine by median unit area — note that AGEBs (median 36 ha) are
finer than the 1 km grid, and manzanas (median 0.65 ha) finer than the 100 m
grid. `uli.aggregate` uses this ordering to decide what may be aggregated and
what must be replicated.

The study extent is the union of the GHSCI Mexicali study region **and** the
Condesa new development, because part of Condesa falls outside it. See §7.

Every unit at every level carries `area_sqm`, `dwellings` and five population
columns:

| Column | What it is |
|---|---|
| `population` | GHS-POP 2025 — the default aggregation weight |
| `population_2030` | GHS-POP 2030, the projection as published |
| `population_planned` | Condesa at full occupancy: one household per residential lot (declared assumption) |
| `population_scenario_2030` | GHS-POP 2030 outside Condesa **+** planned occupancy inside |
| `pop_census_2020` | INEGI 2020, for reference |

GHS-POP cells are polygonised and apportioned by area rather than resampled,
so counts are conserved. `dwellings` holds lot counts, which exist only for the
Condesa layers.

Analysts do not choose between these. `uli.harmonise` weights by `population`;
which basis a *reported statistic* uses is a reporting-step decision made once
in `uli.exposure` (see §7).

Note that grid cells at the study edge extend slightly beyond the study
extent, so grid population totals are marginally higher than the city total.
This is immaterial for weighting, which uses relative weights only.

---

## 3. The results table

Exactly these columns, in this order, UTF-8, comma-separated:

| Column | Type | Description |
|---|---|---|
| `indicator_id` | integer | Workbook `#` of the parent indicator |
| `indicator_code` | string | Stable snake_case slug |
| `measure_id` | string | `<indicator_code>__<lens>[_<parameter>]` |
| `geo_level` | enum | One of the reporting geographies above |
| `geo_id` | string | Unit id, exactly as in the reference geopackage |
| `value` | number \| empty | The measured value |
| `denominator` | number \| empty | Population, area (m²) or other base underlying the value |
| `native_scale` | enum | Geography the value was actually computed at |
| `aggregation_method` | enum | How it was carried to this `geo_level` |
| `coverage` | 0–1 | Share of the unit with valid input data |
| `quality_flag` | enum | `ok`, `low_coverage`, `imputed`, `suppressed`, `not_applicable`, `no_data` |
| `note` | string \| empty | Optional free text for this row |

Rules:

- **One row per `measure_id` × `geo_level` × `geo_id`.** No duplicates.
- `value` is empty **only** when `quality_flag` is `suppressed`,
  `not_applicable` or `no_data` — and must be empty in those cases.
- **Do not normalise, rescale, rank or z-score.** Deliver values in their
  natural units. Normalisation happens once, centrally, when the composite is
  built; doing it twice is unrecoverable.
- **Do not reverse-code.** A high value that is bad stays high; declare
  `direction: lower_is_better` in the metadata instead.
- No infinities. A count per capita in a zero-population unit is
  `not_applicable`, not `inf`.

### Aggregation methods

| Value | Use for |
|---|---|
| `native` | Computed directly at this scale |
| `population_weighted_mean` | Anything people experience (access, exposure, comfort) |
| `area_weighted_mean` | Land cover, coverage and exposure surfaces |
| `length_weighted_mean` | Street-network attributes (sidewalks, lighting) |
| `dwelling_weighted_mean` | Where dwellings are the relevant population proxy |
| `sum` | Counts and totals |
| `areal_share` | Share of unit area covered by a feature |
| `majority` | Modal category |
| `replicated` | A coarse value copied down to finer units — **carries no variation at that scale** |
| `zonal_statistic` | Raster summarised within the unit |
| `nearest_feature` | Value from the nearest measurement site (declare the max distance) |
| `interpolated` | Value from a fitted spatial surface |

`uli.harmonise()` chooses correctly for you: it aggregates up with the method
you name and replicates down, labelling each row accordingly.

---

## 4. The metadata document

Full field list: `schema/indicator_metadata.schema.json`. The five blocks:

**`indicator`** — identity, classification, work package, `role` (`leaf` or
`composite`), analyst, and `adapted_from` (the ULI review article the indicator
came from, resolved from the workbook's article list by article number).
`adapted_from` is *provenance, not evidence*, and should be verified against
the actual paper before publication.

**`rationale`** — the revised "reason this matters" statement, at least one
`health_pathways` entry, an optional `arid_context` note, and an `evidence`
list of **at least one citation independent of `adapted_from`** demonstrating a
meaningful health or wellbeing benefit. Each evidence entry records the claim,
citation, DOI/URL, evidence type, population, exposure, outcome, effect size
with uncertainty, and any threshold the evidence supports.

**`measures`** — for each measure: operational definition, unit, `value_type`,
`direction`, threshold and its justification, benchmark, native scale,
aggregation method, and `include_in_index`.

**`data_sources`** — for each source: citation, URL, **date retrieved**,
**licence** (and whether it may be redistributed via Reimagina Urbana),
resolution, temporal coverage, and **whether it covers Condesa**.

**`method`** — reproducible summary, software, notebook path, parameters,
assumptions, limitations, and `condesa_treatment`.

---

## 5. Directory layout

```
outputs/
  WP04_greenness_and_land_cover/
    vegetation_percent/
      vegetation_percent_results.csv.gz
      vegetation_percent_metadata.yml
      vegetation_percent_validation.json
```

Results are gzipped. A full delivery is around 37,000 rows — 5 MB as plain
CSV and roughly 400 MB across the indicator set, which is more than a git
repository should carry; compressed it is about 0.3 MB each and 26 MB in
total, so deliverables can simply be committed. `pandas` handles the
compression from the file extension, so nothing else changes.

Written by `uli.write_indicator(results, metadata)`, which validates first and
refuses to publish a failing deliverable unless you pass `allow_failure=True`.

---

## 6. What analysts do *not* do

Three things are deliberately centralised, because doing them per-analyst makes
results incomparable:

1. **Normalisation and weighting for the composite index.** Deliver raw values
   plus `direction` and, where you have one, an evidence-based `benchmark`.
2. **The `equity` lens.** Distributional equity is a property of a
   distribution, not a separate measurement. It is computed centrally from the
   finest-scale results (population-weighted quantiles, gaps, concentration
   indices) using the same code for every indicator, so that "equity" means the
   same thing across domains.
3. **Compositing.** The only composites built inside a work package are those
   produced by the core GHSCI workflow: the walkability index and its
   components (street connectivity, population density, access to daily living
   amenities) and the level of cycling traffic stress network. Every other
   indicator is delivered as measured; any further compositing happens
   centrally at the index step.

---

## 7. Condesa coverage requirement

The Condesa new development in south-east Mexicali is a project focus area, and
three measured facts make this a real risk rather than a formality:

- About **20% of the Condesa fraccionamiento area falls outside** the GHSCI
  Mexicali study region boundary as previously configured.
- Only **44% of the Condesa area is covered by census manzana polygons** at
  all, so a manzana-native calculation reaches just **33 of the 40**
  fraccionamientos, while a `grid_100m`-native one reaches all 40.
- **It is platted and roaded but essentially unbuilt**: 43 km of street network
  across 27 of the 40 fraccionamientos, zero destinations, and almost no
  population visible to satellite-derived products. GHS-POP 2025 records 372
  residents; the 2030 projection records 377. The census records none.

So any indicator relying on population weighting returns nothing, or nearly
nothing, exactly where the project most wants an answer.

The schema responds in five ways:

1. `condesa_fraccionamiento` is a **required** reporting geography, and
   `condesa_lote` (14,989 lots) is available as an optional finer one.
2. `uli.aggregate` falls back from population weighting to **area weighting**
   for units with no population weight, recording the change in
   `aggregation_method`.
3. Aggregation emits an explicit `no_data` row for every unit the source never
   reached, so absence is recorded rather than inferred.
4. A **planned-occupancy** denominator (`population_planned`, 48,170 residents
   at one household per residential lot) supports scenario reporting. It is a
   declared assumption, not an estimate, and results derived from it are
   conditional.
5. `uli.validate` raises an **error** — not a warning — when fewer than 80% of
   the Condesa fraccionamientos have a value.

Contributors decide one thing: the **native scale**. Compute on the 100 m grid
where the data allow it. If an indicator genuinely cannot cover Condesa (e.g. a
survey with no sample there), say so in `method.condesa_treatment` and mark
those rows `no_data` rather than leaving them absent.

---

## 8. Versioning

`schema_version` follows semantic versioning. Additive, backward-compatible
changes bump the minor version; anything that would invalidate an already
delivered file bumps the major version and is announced to all work packages
before it takes effect.
