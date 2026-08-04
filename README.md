# Mexicali Urban Liveability Index (ULI)

Shared schema, tooling and scaffolded notebooks for distributed calculation of
spatial liveability indicators for Mexicali, Baja California — and, from them, a
composite liveability index and layers for the **Reimagina Urbana** platform.

**80 indicators in scope** across 8 work packages, plus a synthesis step.
(The workbook narrowed the review to 81; one has since been excluded.)
Schema version **1.0.0**.

- [`DISTRIBUTED_CALCULATION_PLAN.md`](DISTRIBUTED_CALCULATION_PLAN.md) — the
  plan: how the work is divided and what each contributor delivers.
- [`DECISIONS.md`](DECISIONS.md) — why it is arranged that way, and what
  remains open.

---

## Start here

**New here? Two notebooks, about half an hour:**

1. [`notebooks/00_start_here.ipynb`](notebooks/00_start_here.ipynb) — what the
   project is, and a setup check.
2. [`notebooks/00b_cookbook.ipynb`](notebooks/00b_cookbook.ipynb) — **eight
   worked examples** covering every shape an indicator takes, running on demo
   data already in this repository. Run every cell.

Then open your work package notebook (`01_` to `08_`) and keep
[`docs/cheatsheet.md`](docs/cheatsheet.md) beside you.

| If you are… | Read |
|---|---|
| Starting a work package | the two notebooks above, then [`docs/analyst_guide.md`](docs/analyst_guide.md) §2 and §5 |
| Looking for a function name | [`docs/cheatsheet.md`](docs/cheatsheet.md) |
| Wondering what you were assigned | [`indicator_register.csv`](indicator_register.csv), or `uli.register.load()` |
| Writing code that produces results | [`schema/ULI_output_schema.md`](schema/ULI_output_schema.md) |
| Reviewing the approach | [`DISTRIBUTED_CALCULATION_PLAN.md`](DISTRIBUTED_CALCULATION_PLAN.md) |
| Wondering why something is the way it is | [`DECISIONS.md`](DECISIONS.md) |

---

## Layout

```
ULI_Tables by domain ... .xlsx   Source of truth for the indicator set
indicator_register.csv           Generated: flat indicator list + assignments
citation_audit.csv               Generated: Article # vs free-text citation

schema/         The output specification and JSON Schemas
docs/           Analyst guide and cheat sheet
uli/            Shared python package (see below)
build/          Notebook and demo-data generators
geography/      Reference geographies + aggregation crosswalk (generated)
notebooks/      Start page, cookbook, and one per work package (generated)
data/demo/      Small real layers so the cookbook runs after a clone
data/raw/       Raw source data, never edited in place
outputs/        Deliverables, one directory per indicator
```

## Work packages

| Code | Work package | Lead | Indicators |
|---|---|---|---|
| `WP00_composite_index` | Composite liveability index (synthesis, not an analyst task) | Carl Higgs | 1 |
| `WP01_ghsci_access_network` | Destination access and network measures (GHSCI) | Carl Higgs | 39 |
| `WP02_thermal_comfort_and_heat` | Thermal comfort and urban heat | Rossano Schifanella | 7 |
| `WP03_air_quality` | Air quality | TBC | 6 |
| `WP04_greenness_and_land_cover` | Greenness and land cover | TBC | 5 |
| `WP05_hazards_and_incidents` | Environmental hazards and safety incidents | TBC | 8 |
| `WP06_urban_form_and_land_use` | Urban form and land use | TBC | 7 |
| `WP07_street_infrastructure` | Street and active travel infrastructure | TBC | 4 |
| `WP08_housing_economy_and_services` | Housing, economy and public services | TBC | 4 |

One indicator (#238 road density) is out of scope; excluded indicators stay in
the register flagged `WP98_excluded` with the reason recorded, rather than
disappearing.

Assignments are defined in [`uli/work_packages.yml`](uli/work_packages.yml). Edit
that file — not the code — and re-run the notebook builder.

## The `uli` package

```python
import uli

uli.register.load()                    # the indicator register
uli.geography.load('manzana')           # shared reporting geographies
meta = uli.metadata_stub(91)            # documentation pre-filled from workbook

native = uli.count_features(points, 'grid_100m', per='sqkm')
results = uli.harmonise(native, 'grid_100m',
                        method='population_weighted_mean')
results = uli.label(results, meta, 'my_indicator__density_per_sqkm')

print(uli.check(results, meta))          # validate
uli.write_indicator(results, meta)       # deliver (refuses if invalid)

delivered, catalogue = uli.collect()     # ingest everything

# Reporting step: values-for-places become statements about people
uli.exposed_share(delivered, measure_id, threshold=500,
                  comparison='at_or_below',
                  population='population_scenario_2030')
uli.score(delivered, catalogue)           # provisional composite
```

| Module | Purpose |
|---|---|
| `uli.vocab` | Controlled vocabularies — the single definition of every valid term |
| `uli.register` | Reads the workbook into a tidy register with work package assignments |
| `uli.geography` | Reference geographies and the shared aggregation crosswalk |
| `uli.aggregate` | Move values between scales; builders for the common calculation shapes |
| `uli.templates` | Metadata stubs pre-filled from the workbook |
| `uli.validate` | Schema, consistency and project-requirement checks |
| `uli.io` | Read/write deliverables, collect them, export a geopackage |
| `uli.exposure` | Population exposure shares, weighted distributions, provisional composite |

## Rebuilding

The register, notebooks and reference geographies are all generated. When the
workbook or the work package assignments change:

```bash
python build/build_notebooks.py
```

Notebooks that have already been executed are skipped unless you pass
`--force`, so analysts' work is not clobbered.

To rebuild the reference geographies and crosswalk from source data (rarely
needed; takes a few minutes):

```bash
python -m uli.geography build
```

To rebuild the cookbook's demo data (needs the GHSCI outputs and GHS-POP
tiles, which are not in this repository):

```bash
python build/build_demo_data.py
```

## Requirements

`pandas`, `geopandas`, `shapely`, `pyyaml`, `jsonschema`, `pyarrow`,
`matplotlib`; `rasterio` for `zonal_statistic`. All are present in the GHSCI
container environment.

## Reference geographies

Built from the GHSCI Mexicali study region, INEGI 2020 AGEB and manzana
geometries, the Condesa new-development layers, and GHS-POP 2025. All in
**EPSG:6366**.

| Level | Units | Median area | GHS-POP 2025 | Scenario 2030 | Required |
|---|---|---|---|---|---|
| `city` | 1 | 210 km² | 823,260 | 890,079 | ✔ |
| `grid_1000m` | 302 | 1 km² | 840,122 | 907,543 | ✔ |
| `ageb` | 436 | 36 ha | 823,214 | 881,391 | ✔ |
| `condesa_fraccionamiento` | 40 | 7.9 ha | 372 | 48,032 | ✔ |
| `grid_100m` | 22,355 | 1 ha | 828,556 | 895,546 | preferred |
| `manzana` | 14,236 | 0.65 ha | 639,037 | 690,411 | ✔ |
| `condesa_lote` | 14,989 | 120 m² | 282 | 48,202 | optional |

Every unit carries four population bases — `population` (GHS-POP 2025),
`population_2030`, `population_planned` and `population_scenario_2030` — plus
`pop_census_2020` for reference. Manzana polygons do not cover the whole study
extent, which is why their totals are lower.

The study extent is the **union** of the GHSCI study region and the Condesa new
development, because about 20% of Condesa falls outside the former. Condesa
carries only 372 GHS-POP residents today (and 377 in the 2030 projection) — it
post-dates every available population product — so scenario reporting uses a
declared planned-occupancy denominator of 48,170. See
[`DECISIONS.md`](DECISIONS.md) §4–§5.
