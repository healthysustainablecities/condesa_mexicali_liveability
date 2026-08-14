# Archive

Material from the first, more elaborate coordination approach. Parked in
August 2026 when the project moved to a simpler footing: a single
[`OUTPUT_SPECIFICATION.md`](../OUTPUT_SPECIFICATION.md) handed to teams
alongside a separately prepared brief.

Nothing here is wrong, and none of it has been deleted — it is simply more
apparatus than the current approach needs. It is kept because parts of it may
be worth returning to.

## What is here

| | |
|---|---|
| `uli/` | Python package: controlled vocabularies, indicator register, reference geographies and crosswalk, scale aggregation, validation, deliverable I/O, population exposure statistics |
| `notebooks/` | Eleven generated notebooks — a start page, a cookbook of worked examples, one per work package, and a synthesis notebook |
| `schema/` | The long-format output schema, JSON Schemas for results rows and indicator metadata, and exported controlled vocabularies |
| `docs/` | The analyst guide and cheat sheet |
| `build/` | Generators for the notebooks, demo data and vocabularies, plus the notebook checker |
| `demo/` | Small real Mexicali layers used by the cookbook |
| `mexicali_uli_geographies.gpkg`, `mexicali_uli_crosswalk.parquet` | The earlier reference geographies and their aggregation crosswalk |

## Why it was set aside

The original design assumed each analyst would deliver **long-format** results
(one row per measure, geography and unit) with a structured metadata document
per indicator, including independent health evidence, effect sizes and licence
records, validated programmatically before delivery.

The current approach asks for **wide** tables instead — one row per area, one
column per indicator — with a plain data dictionary. That is a great deal
easier to produce and to explain, and it is what the receiving platform needs.

## What replaced the reference geographies

`mexicali_uli_geographies.gpkg` built its own 100 m grid aligned to EPSG:6366.
The replacement, `geography/mexicali_reference_areas.gpkg`, instead uses the
**GHS-POP 2025 population grid** transformed from Mollweide and vectorised by
GHSCI 4.15.0, which conserves population counts through sum resampling. It also
covers the union of the Mexicali urban area and the Condesa development, and
carries the two region rows the specification asks for.

## Still useful, possibly

- The **indicator register** and **citation audit** remain in the repository
  root; they are still the record of what is in scope and which source article
  each indicator came from.
- `uli/vocab.py` holds the controlled vocabularies — health pathways, evidence
  types, aggregation methods, temporal bases — which may be worth reusing if
  the evidence requirements are revived.
- The cookbook's worked examples show how to compute an indicator at a native
  scale and aggregate it consistently, which is still the underlying method
  even though the delivery format has changed.
