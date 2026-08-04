# A guide for analysts

You have been assigned a small set of indicators from the Mexicali Urban
Liveability Index (ULI). This guide takes you from "here is a row in a
spreadsheet" to "here is a validated, documented, ingestible deliverable".

> ## Do this first
>
> **You do not need to read this document before starting.** Do this instead,
> in about half an hour:
>
> 1. Open [`notebooks/00_start_here.ipynb`](../notebooks/00_start_here.ipynb)
>    and run the setup check.
> 2. Work through
>    [`notebooks/00b_cookbook.ipynb`](../notebooks/00b_cookbook.ipynb) —
>    eight worked examples on data already in the repository. Run every cell.
>    This is the fastest way to understand what you are producing.
> 3. Open your work package notebook and read the brief for your first
>    indicator.
> 4. Keep [`cheatsheet.md`](cheatsheet.md) open beside you.
>
> Then come back here. **§2 and §5 are the two sections that matter most**;
> the rest is reference for when a question comes up.
>
> If you are new to Python: you will be copying and adapting recipes, not
> writing code from scratch. The cookbook is designed for that.

---

## Contents

| § | | Read it |
|---|---|---|
| 1 | What you are producing | once |
| **2** | **Start with the health evidence** | **carefully** |
| 3 | Finding and documenting data | when you get there |
| 4 | Computing at the right scale | when you get there |
| **5** | **Covering Condesa** | **carefully** |
| 6 | Validating and delivering | when you get there |
| 7 | Common pitfalls | skim now, revisit later |
| 8 | Where to ask | when stuck |

---

## 1. What you are actually producing

Not a map. Not a report. **A number for every unit of every reporting
geography, plus the documentation that makes that number defensible.**

For each indicator you deliver two files:

```
outputs/<work_package>/<indicator_code>/
    <indicator_code>_results.csv       # the numbers
    <indicator_code>_metadata.yml      # why, from what, how
```

The metadata is not paperwork. The composite index cannot use a value without
knowing its direction (is high good or bad?), and Reimagina Urbana cannot
publish a layer without knowing its licence. An undocumented number is
unusable, so it is worth exactly nothing.

---

## 2. Start with the health evidence, not the data

This is the most common mistake and the most expensive one. If you find the
data first, you will build the indicator the data happens to support, and only
then look for a justification. That produces indicators that measure something
real but irrelevant.

Work in this order:

### 2.1 Write the causal pathway in one sentence

Before searching for anything, complete this sentence:

> *[The thing I measure]* changes *[a mechanism]*, which changes
> *[a behaviour or exposure]*, which affects *[a health or wellbeing
> outcome]*.

Real examples:

> **Street lighting** improves night-time visibility and perceived safety,
> which increases evening walking for transport and recreation (especially for
> women and older adults), which increases physical activity and reduces social
> isolation.

> **Proximity to a petrol station** increases exposure to benzene and other
> volatile organic compounds at the residence, which increases risk of
> respiratory symptoms and haematological effects.

> **Tree canopy cover** reduces radiant heat load and surface temperature,
> which reduces heat stress and makes midday walking tolerable, which reduces
> heat-related morbidity and supports physical activity.

If you cannot write that sentence, you do not yet understand the indicator, and
no amount of GIS will fix it. Bring it to the group.

The mechanism must be one of `uli.vocab.HEALTH_PATHWAYS` — physical activity
(transport and recreation), social interaction, heat, air pollution, noise,
injury, crime and safety, food, healthcare, education, economic security,
housing conditions, hazard exposure, restoration and mental health. Most
built-environment indicators in this project act through **physical activity
for transport**, **physical activity for recreation**, **social interaction**
or **heat exposure**; if yours claims something else, be sure.

### 2.2 Find independent evidence for that pathway

Your brief names the article the indicator was *adapted from*. That is
**provenance, not evidence** — those articles mostly assert that an indicator
belongs in a liveability index, without demonstrating a health benefit. Your
job is to supply the missing link.

**Check the provenance before you rely on it.** The reference is resolved from
the workbook's "Article list" by article number, which is the reliable link.
The workbook also has a free-text "Citation(s)" column, but it holds *secondary*
citations — works cited **inside** the review articles — and for 75 of 79
indicators it names no author of the article the indicator is attributed to. It
is therefore not shown in your brief, and not carried into your metadata. The
article list itself is the team's own record and has already needed correction,
so verify the reference against the actual paper before you cite it. See
[`citation_audit.csv`](../citation_audit.csv).

Search for evidence that the **exposure** affects **health**, not that the
indicator appears in other indices.

- Prefer, in order: meta-analysis → systematic review → reputable guidance
  (WHO, UN-Habitat, PAHO, Secretaría de Salud) → cohort or natural experiment →
  cross-sectional.
- Search terms: the exposure in plain language, plus an outcome — e.g.
  `"street lighting" AND ("physical activity" OR walking OR "fear of crime")`,
  `"green space" AND (mortality OR "mental health") systematic review`,
  `"traffic noise" AND cardiovascular meta-analysis`.
- Where to look: PubMed, Scopus/Web of Science, Google Scholar, WHO
  publications, the Lancet series on urban design and health, *Environment
  International*, *Health & Place*, *Journal of Transport & Health*.
- Record the **effect size with its uncertainty**, not just "was associated
  with". `RR 0.92 (95% CI 0.88–0.96) per 10% increase in NDVI` is evidence;
  "greenness is beneficial" is an opinion.

**Watch for setting mismatch.** Most of this literature is from temperate,
high-income cities. Mexicali is arid, extremely hot in summer, low-to-middle
income, and heavily car-oriented. Say so in `rationale.arid_context` when the
transfer is questionable — for example, distance-based walkability thresholds
calibrated in European cities may overstate walking in a city where the summer
maximum routinely exceeds 45 °C and shade, not distance, is the binding
constraint. That observation is a scientific contribution, not an excuse.

### 2.3 Let the evidence set the threshold

If your indicator needs a cut-point (250 m from a petrol station, 500 m to a
park, 9 m² of green space per person), the evidence chooses it — not
convenience, and not the article the indicator was adapted from.

- If you find evidence supporting a **different** threshold, **use the
  evidence-based one** and record why in `threshold_justification`. This is
  explicitly what the project wants.
- If the evidence supports a dose-response rather than a threshold, deliver the
  continuous measure *and*, if useful, a thresholded one as a second measure.
- If you find no threshold evidence at all, use the project default set
  (`uli.vocab.DISTANCE_THRESHOLDS_M` = 300, 500, 800, 1000, 1600 m) so results
  stay comparable across the team, and say that is what you did.

### 2.4 Check whether your rows are really one indicator

The workbook was assembled article by article, so one construct sometimes
appears as several rows seen through different lenses or over different
periods. Air quality is the clear case: #292 is an index value, #8 is that
value against a standard, #293 is how often the standard is met across a year,
#173 is the same for PM2.5. That is one construct measured four ways, not four
indicators.

When you spot this, deliver them as a **measure family**: give the measures a
shared `measure_family` slug, one method and one set of data sources, and
distinguish them with `temporal_basis` (see `uli.vocab.TEMPORAL_BASES`) and
`threshold`. They keep their separate workbook ids — the family slug is what
tells the index step they belong together.

### 2.5 Rewrite the "reason this matters" text

The workbook has a draft. Most drafts are generic. Rewrite it so it: states the
pathway, names the population most affected, cites the evidence you found, and
says something specific to Mexicali. Four to six sentences. This text goes to
the platform and to the local partners, so write it for an intelligent
non-specialist.

---

## 3. Then find and document the data

Only now go looking for data.

For every dataset you use, record — **at the time you download it**, not three
months later:

- **Citation**: institution/author, year, dataset title, version
- **URL** it came from
- **Date retrieved** (YYYY-MM-DD)
- **Licence**, and whether it permits redistribution through Reimagina Urbana
- **Spatial resolution** and **temporal coverage**
- **Whether it covers Condesa** (see §5)

Save the raw file under `data/raw/<your_work_package>/` and never edit it in
place. All cleaning happens in code.

Candidate sources already identified by the team are pre-filled into your
metadata stub from the workbook — confirm, replace or delete them; do not
assume they are correct.

Likely sources for this project: INEGI (censo 2020, ENIGH, ENVI, DENUE, marco
geoestadístico), IMIP Mexicali geovisor, municipal open data, SEMARNAT and the
Mexicali air quality monitoring network, CONAGUA, OpenStreetMap, Sentinel-2 and
Landsat via Google Earth Engine, GHSL, WorldPop.

---

## 4. Compute at the scale your data actually support

**Compute once, at the finest scale your source genuinely supports.** That is
your `native_scale`. Then:

```python
results = uli.harmonise(native, native_scale='manzana',
                        method='population_weighted_mean')
```

`harmonise` produces every required reporting geography from your one
calculation, using the shared crosswalk, and labels each row with how it got
there.

Choosing `method`:

| Your measure is… | Use |
|---|---|
| experienced by people (access, exposure, comfort) | `population_weighted_mean` |
| a property of land (cover, temperature, land use) | `area_weighted_mean` |
| a property of streets (sidewalks, lighting, stress) | `length_weighted_mean` |
| per-dwelling | `dwelling_weighted_mean` |
| a count of things | `sum` |

Population weighting uses **GHS-POP 2025** by default, not the 2020 census,
because it is more current; other bases exist for the reporting step (§5).

**Never claim a finer scale than you measured.** If your data are city-level
(a household survey, a single air quality station), your native scale is
`city`, and `harmonise` will replicate the value downward and flag every one of
those rows as `replicated`. That is honest and it is fine — the composite index
will know not to treat it as spatial variation. What is *not* fine is silently
presenting a city constant as a 100 m grid.

Six helpers cover almost every calculation. Each has a worked example in
the [cookbook](../notebooks/00b_cookbook.ipynb):

```python
uli.count_features(points, 'manzana', per='1000_persons')   # recipe 1
uli.distance_to_nearest(points, 'grid_100m', cap=3000)      # recipe 2
uli.areal_share(polygons, 'grid_100m', as_percentage=True)  # recipe 3
uli.dominant_class(polygons, 'ageb', 'land_class')          # recipe 4
uli.network_share(edges, 'ageb', 'has_sidewalk')            # recipe 5
uli.zonal_statistic('ndvi.tif', 'grid_100m', 'mean')        # recipe 6
```

---

## 5. Cover Condesa

The Condesa new development in south-east Mexicali is a project focus area, and
it breaks the usual assumptions:

- Roughly **20% of it lies outside** the previously configured study region
  boundary.
- Only **44% of its area is covered by census manzana polygons**, so a
  manzana-native calculation reaches just **33 of the 40** fraccionamientos,
  while a `grid_100m`-native one reaches **all 40**.
- It is platted and roaded — 43 km of street network across 27 of the 40
  fraccionamientos in OpenStreetMap — but essentially unbuilt, with **zero
  destinations** and almost no population visible to satellite-derived
  products.

**One thing is your decision: the native scale.** If your data allow it,
compute on the 100 m grid. That is the difference between covering all of
Condesa and quietly missing a fifth of it.

**The population denominator is not your problem.** Which population basis to
weight by — observed 2025, the 2030 projection, or a planned-occupancy
scenario — is decided once at the reporting step (`uli.exposure`), not by each
analyst. Urban fabric and exposure measures are properties of *place*; who
lives there is applied afterwards. Compute the place.

Two things to record, though:

- `data_sources[].condesa_coverage` — whether your **source** reaches Condesa.
  Satellite imagery and OSM generally do; a 2020 census variable or a household
  survey generally does not.
- `method.condesa_treatment` — what you did about it. Where a source does not
  reach Condesa, mark those rows `no_data` rather than omitting them.

The validator treats poor Condesa coverage as an **error**.

---

## 6. Validate and deliver

```python
report = uli.check(results, meta)
print(report)

uli.write_indicator(results, meta)   # refuses to write if validation fails
```

Before you call it done:

- [ ] The causal pathway sentence is written and reflected in `rationale`
- [ ] At least one **independent** health citation, with an effect size
- [ ] Every threshold justified against evidence
- [ ] Every data source has citation, date retrieved and licence
- [ ] `native_scale` is honest
- [ ] `temporal_basis` set where the measure summarises over time
- [ ] `measure_family` shared where several rows are one construct (§2.5)
- [ ] `direction` is set, and values are **not** normalised or reverse-coded
- [ ] Condesa is covered, or its absence is explained
- [ ] `uli.todos(meta)` returns an empty list
- [ ] You have looked at a map of your result and it is not obviously wrong

That last one matters. Plot it:

```python
import uli
units = uli.geography.load('manzana').merge(
    results.query("geo_level == 'manzana'"), on='geo_id')
units.plot(column='value', legend=True, figsize=(10, 8))
```

Ask: are the extreme values where you would expect? Is the city centre
different from the periphery in the direction you would predict? Does Condesa
look plausible, or suspiciously empty? Most errors are visible in ten seconds
on a map and invisible in a table.

---

## 7. Common pitfalls

| Pitfall | What happens | Fix |
|---|---|---|
| Normalising to 0–1 before delivery | Double normalisation in the index; original units lost | Deliver natural units; set `direction` |
| Reverse-coding "bad" indicators | Sign errors nobody can detect later | Keep the natural sign; declare `lower_is_better` |
| Presenting a city-level survey value per manzana | False precision that dominates the index | `native_scale: city`, let it replicate |
| Counting features per capita in a zero-population unit | Infinities, or a spuriously huge value | `not_applicable` with an empty value |
| Using a threshold from the adapted article | Threshold has no evidential basis | Find threshold evidence, or use project defaults |
| Building your own grid | Results don't align with anyone else's | `uli.geography.load(level)` |
| Reprojecting to lat/long for area calculations | Areas wrong by a factor of ~10⁴ | Everything stays in EPSG:6366 |
| Silently dropping units with no data | Coverage looks perfect; Condesa vanishes | Emit rows flagged `no_data` |
| Downloading data without recording the date | Cannot be cited or reproduced | Record it at download time |

---

## 8. Where to ask

- How do I compute this? → [the cookbook](../notebooks/00b_cookbook.ipynb)
- What was that function called? → [`cheatsheet.md`](cheatsheet.md)
- An error I do not understand → cookbook §11 lists the common ones
- Schema questions → `schema/ULI_output_schema.md`
- What am I assigned → `indicator_register.csv`, or `uli.register.load()`
- Something in the workbook is ambiguous → raise it with the group **before**
  computing; ambiguity resolved differently by two analysts is worse than
  ambiguity resolved slowly
- Two indicators look like the same thing → they may well be; see
  `DISTRIBUTED_CALCULATION_PLAN.md` §2 and flag it
