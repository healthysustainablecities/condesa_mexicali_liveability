# 2. Reproducing the analysis

This section is the runbook used for Mexicali and Condesa, from prepared inputs to the published dashboard and this manual. Commands run either in the GHSCI Earth Engine container (`ghsci-ee`, image `globalhealthyliveablecities/global-indicators:v{{fact:software_environment}}.ee`, working directory `/home/ghsci/process`) or on the host, as marked.

## Overview

```text
inputs (INEGI, DENUE, IMIP, OSM, GHS-POP, CFC, work packages)
  │  preparation scripts (CFC, reference areas)
  ▼
region configuration  MX_Mexicali_2025_ULI.yml
  │  analysis (_00 … _12)  ─────────────►  PostGIS database mx_mexicali_2025_uli
  │     _07 sample points, _11 walking access, euclidean catchments,
  │     cycling LTS, Earth Engine (GUHVI, LPUGS), _12 aggregation →
  │     linked indicators → walkability variants → composite indices
  ▼
generate  ─────►  GeoPackage, CSVs, data dictionary, metadata, reports
export_dashboard ─►  manifest / indicators / stats / distributions + layers
  │  build_tiles.sh (tippecanoe) → deploy.sh
  ▼
dashboard (static site)    build_results_geopackage.py → results GeoPackage
technical_report.py → PDFs   build/manual/manual.py → this manual
```

## 1. Prepare inputs (host or container)

| Step | Script | Produces |
|---|---|---|
| Study region and region layers | `process/data/MX/CFC/build_uli_boundaries.py` | the dissolved study region (`INEGI-02l-NOMGEO-Mexicali-Condesa-Fraccionamientos.geojson`) and `mexicali_uli_boundaries.gpkg` (`region_mexicali`, `region_condesa`) |
| Manzanas | `process/data/MX/CFC/build_manzanas.py` | `mexicali_manzanas.gpkg`: INEGI 2020 blocks with CFC geometries, synthetic `S` keys for 16 unkeyed Condesa blocks |
| Condesa lot sample points | `process/data/MX/CFC/build_condesa_sample_points.py` | `condesa_lot_sample_points.gpkg`: one point per lot, for snapping to the network |
| Reference areas | `Mexicali Liveability/build/build_reference_areas.py` | `geography/mexicali_reference_areas.gpkg`: the six reference layers the work packages and linkage use |

DENUE (May 2026), the IMIP facilities layer, the GHS-POP 2025 tile, the Geofabrik extract, the UTCI GeoPackage (work package 2) and `final_indicators.gpkg` (work packages) are used as delivered; their paths are in the configuration ([Appendix D](D_datasets.md)).

## 2. Run the analysis (container)

The region configuration lives beside its data, at `process/data/MX/MX_Mexicali_2025_ULI.yml`. In the container, pass its path rather than the codename, since a loose configuration file in `data/MX` is not discovered by codename:

```bash
python analysis.py data/MX/MX_Mexicali_2025_ULI.yml
```

or, in Python:

```python
import ghsci
r = ghsci.Region('data/MX/MX_Mexicali_2025_ULI.yml')
r.analysis()
```

The pipeline runs `_00` to `_12` in sequence ({{code:analysis.py:analysis}}). For this region, it adds:

- **Sample points** in unpopulated areas and one per Condesa lot ([R1](03_recipes.md#r1)).
- **Walking access** to every configured destination at 300, 500, 1,000 and 1,500 m, the diversity sets and activity centres ([R2](03_recipes.md#r2)–[R4](03_recipes.md#r4)).
- **Straight-line catchments** to police and fire stations ([R5](03_recipes.md#r5)).
- **Cycling level of traffic stress** ([R6](03_recipes.md#r6)).
- **Earth Engine:** GUHVI and large public green space ([R8](03_recipes.md#r8)), which need the `.ee` container and an authenticated Earth Engine account.
- **In `_12`, after aggregation:**
  - linked indicators: UTCI and the work-package indicators ([R7](03_recipes.md#r7));
  - walkability variants ([R9](03_recipes.md#r9));
  - the composite indices `uli` and `uli_plain` ([R10](03_recipes.md#r10)–[R13](03_recipes.md#r13)).

A full run takes several hours. Progress is logged to `process/data/_study_region_outputs/MX_Mexicali_2025_ULI/__Mexicali__MX_Mexicali_2025_ULI_processing_log.txt`.

The composite index can be re-scored without re-running the pipeline, for example against frozen goalposts ([R14](03_recipes.md#r14)):

```python
r.composite_index(goalposts='…/MX_Mexicali_2025_ULI_composite_uli_parameters.yml')
```

## 3. Generate outputs (container)

```python
r.generate()
```

writes the GeoPackage, per-scale CSVs, data dictionary, ISO 19115 metadata, maps and the standard GHSCI reports to the region's output folder.

## 4. Export the dashboard (container, then host)

```bash
# container: layers, manifest, stats, vocabulary (combined and general dashboards)
/env/bin/python subprocesses/_export_dashboard.py "data/MX/MX_Mexicali_2025_ULI.yml"
/env/bin/python subprocesses/_export_dashboard.py "data/MX/MX_Mexicali_2025_ULI.yml" --type=general
# host, in Mexicali Liveability/dashboard: PMTiles archives and deployment
docker build -t tippecanoe:local build/
bash build/build_tiles.sh mexicali mexicali_general
bash build/deploy.sh mexicali mexicali_general
```

Large intermediates stay outside OneDrive (`/tmp/ghsci-dashboard`). Label, theme, class or text changes need only `--no-layers`. All on-screen wording is editable in `dashboard/data/mexicali/text.json`.

## 5. Results GeoPackage and reports

```bash
# container: full-precision values per reference scale, with a bilingual dictionary
python "data/MX/Mexicali Liveability/build/build_results_geopackage.py" /export/mexicali
# host: the dashboard's technical report (headless Edge)
python dashboard/build/technical_report.py
# host: this manual
python build/manual/manual.py
```

## 6. Back up and restore the database

```python
r.dump(path='E:/backups')                # custom-format dump with a .dump.yml sidecar
ghsci.restore('…/mx_mexicali_2025_uli_YYYYMMDD.dump')
```

The 26 September 2026 analysis database is backed up as `mx_mexicali_2025_uli_20260926.dump` (231 MB; restore steps in the `.dump.txt` beside it).

## Pitfalls met in this project

- **Network date.** Until 26 September 2026 the Overpass query was pinned to the start of the extract's publication date, which missed Condesa streets mapped that morning (26 streets; about 1,200 lots without estimates). `_03` now uses the extract's replication timestamp.
- **Region path.** In the container, `ghsci.Region('MX_Mexicali_2025_ULI')` does not resolve the loose file in `data/MX`; pass its path.
- **Parameters file.** If the output folder is not writable by the container user, the composite parameters are still recorded as the comment of the `sample_points_composite` table.
- **OneDrive.** Keep tile scratch and database dumps outside the synced folder.
- **Identifier length.** PostgreSQL truncates identifiers beyond 63 characters, so derived names (for example of diversity sets) are kept short: `community_culture_rec`.
