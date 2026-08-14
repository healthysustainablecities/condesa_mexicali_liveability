# Mexicali Liveability Index

Spatial liveability indicators for Mexicali, Baja California — including the
Condesa development in the south-east — feeding a composite liveability index
and the **Reimagina Urbana** platform.

Calculation is shared across several teams. This repository holds what they
need in order to deliver results that fit together.

## Start here

| | |
|---|---|
| **[`OUTPUT_SPECIFICATION.md`](OUTPUT_SPECIFICATION.md)** | **The format results must be delivered in.** One page. Hand this to teams with the brief. |
| `geography/mexicali_reference_areas.gpkg` | Reference geometries for every reporting scale, EPSG:6366. Use as supplied. |

What to calculate is covered in a separate brief, not here.

## Reference geometries

`mexicali_reference_areas.gpkg`, EPSG:6366 (Mexico ITRF2008 / UTM zone 11N).
Every layer carries `area_id`, `area_sqm` and `pop_2025`.

| Layer | What it is |
|---|---|
| `region` | Two rows: the Mexicali urban area, and the Condesa development |
| `grid_100m` | GHS-POP 2025 population grid, vectorised into EPSG:6366 |
| `agebs` | INEGI 2020 AGEBs, keyed by `CVEGEO` |
| `manzanas` | INEGI 2020 census blocks, keyed by `CVEGEO` |
| `condesa_fraccionamientos` | Condesa subdivisions |
| `condesa_lotes` | Individual Condesa lots |

The extent is the **union** of the Mexicali urban area and the Condesa
development: about 18% of Condesa falls outside the mapped urban area, so the
administrative boundary alone would omit part of the development.

The 100 m grid comes from a GHSCI 4.15.0 analysis
(`process/data/MX/MX_Mexicali_2025_ULI.yml`), which reprojects GHS-POP from
Mollweide using sum resampling so that population counts are conserved, then
vectorises the result. Cells are exactly 100 m × 100 m in EPSG:6366, and the
grid population total matches the source raster to within 0.03%.

## Also in this repository

| | |
|---|---|
| `ULI_Tables by domain … .xlsx` | The indicator workbook — the source of truth for what is in scope |
| `indicator_register.csv` | Flat list of indicators with work package assignments |
| `citation_audit.csv` | Each indicator's source article, checked against the article list |
| `DISTRIBUTED_CALCULATION_PLAN.md` | How the work is divided across teams |
| `DECISIONS.md` | Why things are arranged as they are, and what remains open |
| `archive/` | The earlier, more elaborate coordination approach — see [`archive/README.md`](archive/README.md) |

## Rebuilding the reference geometries

Requires the GHSCI containers and the source data under `process/data/MX`:

```bash
python build/build_reference_areas.py
```

The boundaries it depends on are built by
`process/data/MX/CFC/build_uli_boundaries.py`.
