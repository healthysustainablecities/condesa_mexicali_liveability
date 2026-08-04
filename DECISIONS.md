# Decisions record

Why the Mexicali ULI distributed calculation plan is arranged as it is: the
issues raised while designing it, what was decided, and the evidence behind
each decision.

This is the working record. The plan itself — what to do, without the
reasoning — is
[`DISTRIBUTED_CALCULATION_PLAN.md`](DISTRIBUTED_CALCULATION_PLAN.md).

**Status: decisions taken 4 August 2026.** §14 lists what remains open.

---

## 1. Work packages

The original proposal was a three-way split: GHSCI indicators, thermal comfort,
and everything else "at the discretion of analysts" grouped by *Indicator /
Category*. Groups 1 and 2 were well defined; group 3 was too fragmented to
assign — 30 distinct categories, several near-synonyms, and one
(`Pedestrian Infrastructure`) spanning street lighting, sidewalks, the
walkability index and traffic crash fatalities.

Group 3 is instead split **by data source and method family**, because that is
what determines who can do the work and what tooling they need.

| Code | Work package | Lead | n | Method family |
|---|---|---|---|---|
| `WP00` | Composite liveability index | Carl Higgs | 1 | Synthesis, not an analyst task |
| `WP01` | Destination access and network measures (GHSCI) | Carl Higgs | 39 | GHSCI pedestrian network pipeline |
| `WP02` | Thermal comfort and urban heat | Rossano Schifanella | 7 | Remote sensing + climate |
| `WP03` | Air quality | TBC | 6 | Monitoring network + satellite, interpolation |
| `WP04` | Greenness and land cover | TBC | 5 | Remote sensing, spectral indices |
| `WP05` | Environmental hazards and safety incidents | TBC | 8 | Hazard mapping + incident registries |
| `WP06` | Urban form and land use | TBC | 8 | Cadastral and morphometric |
| `WP07` | Street and active travel infrastructure | TBC | 4 | Street-segment attributes and audit |
| `WP08` | Housing, economy and public services | TBC | 4 | Census, ENIGH/ENVI, DENUE, administrative |

82 indicators. Assignments live in [`uli/work_packages.yml`](uli/work_packages.yml)
and drive both the register and the notebooks, so revising them is a one-line
edit plus `python build/build_notebooks.py`.

Two moves follow from the decisions below: **#362 street connectivity and #340
population density** sit in WP01, because they are inputs to the GHSCI
walkability index; **#405 land use type** sits in WP06 with land use mix,
because both come from the same municipal land use classification, while WP04
keeps land *cover* from imagery.

---

## 2. Repeated constructs: resolved three ways

Because indicators were harvested per source article, some constructs appeared
more than once. Each case turned out to need a different answer.

**Land use type — collapsed.** #119, #120 and #405 were three rows for one
thing. Removed from the workbook; **#405 is now the parent covering the
permutations**, delivered once with the land use classes as measure
parameters.

**Air quality — one construct, four lenses and time bases.** #292 is an index
value, #8 evaluates that value against a standard, #293 counts how often the
standard is met across a year, #173 does the same for PM2.5. These are
genuinely distinct measurements, so they stay as separate rows — but computing
them as four unrelated indicators would produce four inconsistent methods.

The schema now names the missing dimension. Each measure may declare a
**`temporal_basis`** (`annual_mean`, `seasonal_mean`,
`threshold_exceedance_days`, `threshold_compliance_days`, `threshold_share`, …)
and a shared **`measure_family`** slug:

| Row | What it is | Lens | `temporal_basis` |
|---|---|---|---|
| #292 Air quality | the index value | `quality` | `annual_mean` |
| #8 Good air quality | that value against a standard | `quality` | `threshold_share` |
| #293 Days with good air quality | how often the standard is met | `quantity` | `threshold_compliance_days` |
| #173 Days PM2.5 over WHO | the same, for one pollutant | `quantity` | `threshold_exceedance_days` |

One method, one set of data sources, four measures, one family. The same
pattern covers mean summer temperature versus days above a comfort threshold
(WP02), and flood extent versus annual average days of flooding (WP05) — which
is why this is a schema feature rather than an air quality workaround.

**Green and open space — kept distinct.** #91 public green space (open space
meeting a greenness threshold), #187 public open space, and #162 parks (a
category of green space) are nested but technically different concepts. All
three are delivered as part of the underlying indicator suite for users to
explore; **`include_in_index` per measure** controls which enter the composite,
so distinctness costs nothing.

---

## 3. Compositing

The workbook's draft composite columns have been removed. Compositing is now
explicit and minimal:

- **Built inside a work package (WP01, core GHSCI workflow):** the walkability
  index and its components — street connectivity, population density, access to
  daily living amenities — and the level of cycling traffic stress network.
  These are named in `uli.templates.GHSCI_COMPOSITES` and get
  `role: composite` in their metadata.
- **Everything else** is delivered as measured. Any further compositing happens
  centrally at the index step.

This removes the cross-work-package dependency deadlock the draft hierarchy
would have created.

One overlap to settle in passing: road density (#238, WP06) covers much the
same ground as the intersection density GHSCI produces for WP01. Noted in the
WP06 method notes.

---

## 4. Population denominator: GHS-POP, with a 2030 scenario

**Decision: GHS-POP is the project population denominator**, apportioned by
area to every reporting geography — cells are polygonised rather than
resampled, so counts are conserved. The 2020 INEGI census is retained as
`pop_census_2020` for reference.

Four bases are carried, because the right one depends on the question:

| Basis | What it is | Study extent | Condesa |
|---|---|---|---|
| `pop_census_2020` | INEGI census | 852,506 | 0 |
| `population` | GHS-POP 2025, observed today | 823,260 | 372 |
| `population_2030` | GHS-POP 2030, projection as published | 842,287 | 377 |
| `population_planned` | Condesa at full occupancy | 48,170 | 48,032 |
| `population_scenario_2030` | GHS-POP 2030 outside Condesa **+** planned occupancy inside | 890,079 | 48,032 |

Choosing between bases is a **reporting-step decision**, made once in
`uli.exposure`, not by each contributor. Urban fabric and exposure indicators
are properties of place; who lives there is applied afterwards.

### Why 2030 does not solve Condesa — tested, not assumed

The question was raised whether GHS-POP 2030, or a coarser GHS-POP grid
sub-sampled to fraccionamientos, would supply Condesa with a defensible
population. Neither works.

**The 2030 tile was downloaded and run.** It adds **19,760 people city-wide
(+2.3%) and 5 to Condesa** (372 to 377). Condesa's share of the city is
unchanged at 0.044%. GHS-POP disaggregates a projected total onto observed
built-up surface, so the projection grows cells that already have roofs; it
does not discover a subdivision.

**What population it does record is borrowed from next door.** Of the 372
persons, 364 sit in fraccionamientos within 100 m of an already-populated 2020
manzana, 7.9 in the 100-500 m band, and none beyond 500 m; the rank
correlation with distance to existing settlement is -0.43. That is the
signature of areal apportionment from neighbouring cells, not occupancy.

**A coarser grid would be worse.** Sub-sampling a 1 km product to
fraccionamientos cannot add information — it would spread the neighbours'
population across Condesa by areal interpolation, producing a
confident-looking number that is entirely borrowed. The same artefact,
amplified.

**The development is real but unbuilt.** OpenStreetMap (April 2026) shows
**43.3 km of street network across 27 of the 40 fraccionamientos** at ~26
km/km², and **zero destinations**. The subdivisions are platted and roaded;
the houses are not there yet. GHS-POP tracks roofs, not roads — within
Condesa its correlation with road density is only 0.41.

So ~zero residents is not a data gap. It is an accurate description.

### The planned-occupancy assumption

`population_planned` is therefore a **declared assumption, not an estimate**:
one household per residential lot, at the Mexicali mean household size.

- 14,597 of 14,989 lots are at most 300 m² and treated as residential; the
  median lot is 120 m². The 392 larger lots (2.6% of lots, 27% of the area)
  are treated as non-residential and given no population.
- Household size 3.3 gives **48,170 planned residents, 5.4% of the scenario
  city**.
- Both parameters live in `uli.geography`, so any derived result can be
  re-derived under different assumptions.

The Condesa layers carry no attributes of their own — `_Fraccionamientos`,
`_Accesos` and `Lotes_desarrollo_EXE` have only identifiers — so lot counts
are the only planning information available. If IMIP or the developer holds
authorised dwelling counts, they should replace this assumption.

**Scenario results are conditional and must be reported as such**: they answer
"if Condesa is fully occupied by 2030, on top of the projected city, what will
people experience?", not "what do people experience?".

One limitation to note: AGEB and manzana capture only ~39,500 and ~37,200 of
the 48,170 planned residents, because 2020 census geography does not extend
over the whole development. **Scenario statistics belong on the grids or the
Condesa layers, not on census geography.**

What would genuinely resolve occupancy, in descending order of defensibility:
CESPM/CFE utility connections or IMIP occupancy certificates; INEGI 2025
intercensal coverage; or building footprints counted against platted lots.

---

## 5. Condesa coverage

The most consequential finding of the review, and invisible until measured.
The Condesa new development is a project focus area, and:

- About **20% of its area falls outside** the GHSCI study region boundary as
  previously configured.
- Only **44% of its area is covered by census manzana polygons**. A
  manzana-native calculation therefore reaches **33 of 40** fraccionamientos;
  a `grid_100m`-native one reaches **all 40**.
- **It is still essentially unpopulated in the data.** GHS-POP 2025 records
  **372 residents across the entire Condesa area**, with **15 of the 40
  fraccionamientos at zero**. The census records none. The development
  post-dates every available population product.

That last point is worth being explicit about: moving to GHS-POP was the right
call and fixes currency across the city, but it does not make Condesa
population-weightable. Nothing will, until the area is occupied and observed.

Implemented:

1. The ULI study extent is the **union** of the GHSCI study region and Condesa.
2. `condesa_fraccionamiento` (40) is a **required** reporting geography;
   `condesa_lote` (14,989 lots) is available as an optional finer one.
3. Population weighting **falls back to area weighting** where the population
   weight is zero, recording the substitution in `aggregation_method`.
4. `dwelling_weighted_mean` weights by lot count for per-capita measures — a
   rate per 372 people is not meaningful; a rate per 14,989 lots is.
5. Aggregation emits an explicit `no_data` row for every unit the source never
   reached, so absence is recorded rather than inferred.
6. `uli.validate` treats Condesa coverage below 80% as an **error**.
7. A planned-occupancy denominator supports scenario reporting (§4).

Contributors are told, in both the guide and every notebook, to compute on the
100 m grid where the data allow it. That is the only Condesa decision they
carry: the population denominator is a reporting-step concern, decided once
in `uli.exposure`, because urban fabric and exposure indicators are properties
of place and who lives there is applied afterwards.

---

## 6. Equity: derived centrally

Equity is a property of the distribution of any other lens across the
population, not a separate measurement. Seven analysts each inventing an equity
measure would produce seven incomparable numbers.

The `Equity` column has been removed from the workbook's lens list. Equity is
computed centrally from the finest-scale results using one implementation for
every indicator — population-weighted quantiles, absolute and relative gaps,
concentration indices, threshold shares. The GHSCI codebase already has this
machinery in `longitudinal.py`.

---

## 7. Units and polarity: no contributor normalisation

Analysts deliver values in **natural units**, with a declared `direction`
(`higher_is_better` / `lower_is_better` / `non_monotonic`) and, where the
evidence supports one, a `benchmark`. Reverse-coding is prohibited — a high
value that is bad stays high and is declared `lower_is_better`.

Normalisation and weighting happen once, centrally, at the index step.
Rescaling before delivery cannot be undone and silently changes the weighting
of the composite.

---

## 8. Native scale and city constants

`native_scale` is mandatory on every row. Values known only at a coarse scale
are **replicated** downward and flagged, so a city-level survey value cannot
masquerade as fine-grained variation. The validator warns when a large share of
an indicator's rows are replicated.

**The composite index uses spatially varying indicators only.** City-constant
indicators are reported as context alongside it, not averaged into it — a
composite that mixes them is driven entirely by the varying ones while
appearing to include the rest.

---

## 9. Evidence and arid-city framing

"Provide a citation with evidence of a meaningful health benefit" is the right
requirement and the one most likely to be quietly skipped, because finding a
systematic review is harder than running a buffer analysis. It therefore has
structure rather than good intentions:

- `rationale.evidence` requires, per entry: the specific claim, citation, DOI,
  evidence type, population, exposure, outcome, **effect size with
  uncertainty**, and any threshold the evidence supports.
- The validator **warns** when no entry is a systematic review, meta-analysis,
  cohort study or reputable guidance; when an effect size is missing; and when
  the cited work looks like the article the indicator was adapted from.
- `rationale.health_pathways` forces each indicator to name its mechanism.
  An indicator whose author cannot name a pathway should not be computed.
- Metadata still containing `TODO` placeholders is an **error**, so an
  indicator cannot be delivered with the evidence block unfilled.

`rationale.arid_context` captures how Mexicali's climate modifies the expected
relationship. Almost all built-environment and health literature comes from
temperate, high-income cities; in a city where summer maxima exceed 45 °C,
shade and time of day plausibly bind before distance does. **The walkability
indicators will be tailored to the arid context, mediated by the WP02 thermal
comfort outputs** — so WP02's results are an input to WP01, not just a
neighbour of it.

On thresholds: where evidence supports a threshold different from the source
article's, the evidence-based one is used and recorded in
`threshold_justification`. Where no threshold evidence exists,
`uli.vocab.DISTANCE_THRESHOLDS_M` (300, 500, 800, 1000, 1600 m) keeps the
unjustified cases at least mutually comparable.

---

## 10. Road density: out of scope

**#238 road density is excluded.** It is not clearly described in the source
article, and not clearly distinguishable from street connectivity (#362),
which the core GHSCI workflow already produces.

Excluded indicators are not deleted. They stay in the register flagged
`WP98_excluded`, with the reason and date recorded in
[`uli/work_packages.yml`](uli/work_packages.yml), so the decision stays
visible rather than looking like an oversight, and can be revisited. They get
no notebook scaffold, and the builder reports them on every run.

---

## 11. Documentation: plan and reasoning separated

The plan people need to follow and the reasoning behind it serve different
readers, so they are separate documents:

- [`DISTRIBUTED_CALCULATION_PLAN.md`](DISTRIBUTED_CALCULATION_PLAN.md) — the
  plan as it stands, for contributors and partners. No ledger, no history.
- `DECISIONS.md` (this file) — what was raised, what was decided, and the
  evidence. For anyone asking why.

---

## 12. Citation provenance: resolved by article number

The metadata stub originally built its `adapted_from` field by concatenating
three workbook columns: the `Article #`, the free-text `Citation(s)` text, and
the reported effect size. Those columns disagree, and joining them produced
provenance that read as authoritative and was frequently wrong — for #136
*Annual average nitrogen dioxide*, an attribution to article #13 sat beside a
citation naming Lowe et al., who are not its authors.

An audit of all 82 indicators found this is systemic, not incidental:

- **75 of 79** indicators with both fields have a free-text citation naming no
  author of the article they are attributed to. The column holds *secondary*
  citations — works cited **inside** the review articles (Lowe 2015,
  Saitluanga 2014, Ghasemi 2024, Yang 2021) — not the article itself.
- **1** indicator (#91, access to public green space) cites article #35, which
  does not exist in the article list.
- **1** indicator (#0, the index itself) has no article number.

Decided:

1. **The `Article #` is the authoritative link.** `adapted_from` is now
   resolved from the "Article list" sheet by number, formatted as
   `#13: Alderton (2021), 'title'`. Numbers absent from the list are reported
   as unresolved rather than silently dropped.
2. **The free-text `Citation(s)` column is not used** — not in the metadata,
   not in the notebook briefs. It is preserved in the workbook and surfaced in
   the audit, but nothing downstream depends on it.
3. **`Effect size` and `Methods sub-indices/measures` are omitted** from the
   briefs entirely. Both attach findings to a study the row may not correspond
   to, and neither is needed: analysts supply their own effect sizes from
   independent evidence.
4. **`citation_audit.csv` is regenerated on every build**, listing each
   indicator's resolved reference, the free-text citation, and whether the two
   agree — so the workbook can be corrected from it.
5. The article list has itself needed correction (authors of #12/#13 and
   #18/#19 were transposed; #15's author was recorded by given name). The guide
   therefore tells analysts to **verify the reference against the actual paper**
   before citing it.

The underlying lesson is narrower than "check citations": *do not synthesise a
single authoritative-looking string out of fields that have not been
reconciled.* Presenting the article number alone would have surfaced the
disagreement instead of hiding it.

---

## 13. How work is handed back

The question "do analysts commit results or email them?" had not been
answered, and the answer turns on file size.

A full delivery is about 37,000 rows: five reporting geographies, and one row
per unit of each. As plain CSV that is **5 MB per indicator, roughly 400 MB
across the indicator set** -- more than a git repository should carry.
Gzipped it is **0.3 MB per indicator, about 26 MB in total**, which is
unremarkable.

Decided:

1. **Results are gzipped** (`<code>_results.csv.gz`). `uli.write_indicator`
   does this by default; `pandas` reads and writes the compression from the
   file extension, so no other code changes.
2. **Deliverables are committed** on a branch, with a pull request -- which
   gives the work a review point and a record of what changed. Analysts who
   cannot use git send the output folder and notebook to the project lead.
3. **Raw source data is not committed.** It is often large, and licences
   frequently forbid redistribution. `data/raw/` is git-ignored except for
   its `.gitkeep`; the metadata records citation, URL, date retrieved and
   licence so the source can be fetched again.

---

## 14. Still open

1. **Leads for WP03-WP08.** Everything else is ready; the work packages are
   not.
2. **Which equity statistics** the index reports (section 6 settles who
   computes them, not which).
3. **How the composite index is calculated** — normalisation, weighting, and
   whether city-constant indicators are reported only as context (section 8).
4. **WP02 / WP01 interface** — how thermal comfort conditions the walkability
   index in practice, and on what schedule, given WP01 depends on WP02 output.
5. **Household size for the Condesa assumption** — confirm the Mexicali
   municipality mean against the INEGI 2020 tabulation rather than the
   constant currently in the code (section 4).
6. **Article list verification** — work through `citation_audit.csv` and
   confirm each article's author, year and title against the paper (section
   12). Some entries have already been corrected; the rest are unverified.
7. **Confirm the hand-back workflow** with the team (section 13) — in
   particular whether the repository is public, which would rule out
   committing anything licence-restricted.

---

## What was built

| | |
|---|---|
| Output schema | [`schema/ULI_output_schema.md`](schema/ULI_output_schema.md), plus JSON Schemas for results rows and metadata |
| Shared tooling | [`uli/`](uli/) — vocabularies, register, geographies, aggregation, validation, I/O |
| Reference geographies | 7 levels + full pairwise crosswalk, EPSG:6366, four population bases, covering Condesa |
| Exposure and index | [`uli/exposure.py`](uli/exposure.py) — population exposure shares, weighted distributions, provisional composite |
| Analyst guide | [`docs/analyst_guide.md`](docs/analyst_guide.md) |
| Notebooks | One overview with a worked end-to-end example, 8 work package notebooks and a synthesis notebook, generated from the workbook |
