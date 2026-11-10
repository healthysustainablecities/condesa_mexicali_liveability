# Building the technical manual / Generar el manual técnico

```bash
python -m pip install -r build/manual/requirements.txt
python build/manual/manual.py                 # both languages, maps, PDFs
python build/manual/manual.py --lang en --no-pdf --no-maps   # quick text-only rebuild
```

Run from the root of this repository (`Mexicali Liveability`), inside a global-indicators checkout (or set `GHSCI_REPO` to one). The build reads only files that already exist and needs no database:

| Input | Path |
|---|---|
| Region configuration | `../MX_Mexicali_2025_ULI.yml` |
| Composite parameters | `process/data/_study_region_outputs/MX_Mexicali_2025_ULI/*_composite_uli{,_plain}_parameters.yml` |
| Dashboard export | `dashboard/data/mexicali/{indicators,manifest}.json` |
| Results | `outputs/mexicali_uli_ghsci_results.gpkg`, `outputs/mexicali_uli_ghsci_data_dictionary.csv` |
| Register and sheet | `indicator_register.csv`, `citation_audit.csv`, `../Update_on_ULI - 2026-09-22/excel_work_sheet_key.xlsx` |
| GHSCI code (for line references) | `process/subprocesses/*.py` of the checkout |

It writes `docs/manual/` (Markdown in `es/` and `en/`, maps in `figures/`, the configuration and parameters in `data/`, PDFs in `pdf/`).

**What to edit.**

| File | Holds |
|---|---|
| `content/<lang>/*.md` | hand-written prose: front matter, study design, runbook, recipes, glossary, pending list |
| `strings.yml` | headings, table labels, the method template for each kind of indicator, recalculation notes |
| `entries.yml` | per indicator: worksheet rows, register ids, kind, DENUE categories, inputs, caveats |
| `upstream.yml` | entries for inputs and sub-indicators |
| `rationale_es.yml` | draft Spanish translations of the register's rationale |

Labels, descriptions, readings and sources of indicators and domains are **not** here: they come from the region configuration, so correct them there and re-export the dashboard.

**Checks.** The build stops if a region value disagrees with the dashboard manifest, or a link or image does not resolve. It prints a gap report of fields no source records (marked *Pendiente / Pending* on the pages).

**Placeholders in content.** `{{code:file.py:function}}` links to the function's line on GitHub at the checkout's commit; `{{cfg:text}}` links to the first configuration line beginning with `text`; `{{fact:name}}` inserts a computed fact (see `render.Builder.compute_facts`).
