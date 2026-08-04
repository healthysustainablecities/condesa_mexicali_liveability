"""Generate the scaffolded analyst notebooks from the ULI workbook.

The notebooks are *generated*, not hand-written, so that when the
workbook or the work package assignments change, one command brings
every notebook back into line::

    python build/build_notebooks.py

Existing notebooks are overwritten.  Analysts should therefore keep
their working copy under a different name once they start editing --
the generated file is a starting point, not a living document.  The
builder refuses to overwrite a notebook whose cells have been executed
unless ``--force`` is given.
"""

import argparse
import json
import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
NOTEBOOK_DIR = os.path.join(PROJECT_DIR, 'notebooks')
sys.path.insert(0, PROJECT_DIR)

from uli import register, templates, vocab  # noqa: E402

# Above this many indicators, per-indicator cells become unwieldy and
# the notebook switches to a batch-processing layout.
BATCH_THRESHOLD = 12


# --------------------------------------------------------------------
# Minimal nbformat v4 writer (avoids a dependency for a JSON file)
# --------------------------------------------------------------------
def markdown(text):
    return {
        'cell_type': 'markdown',
        'metadata': {},
        'source': _lines(textwrap.dedent(text).strip('\n')),
    }


def code(text):
    return {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': _lines(textwrap.dedent(text).strip('\n')),
    }


def _lines(text):
    lines = text.split('\n')
    return [line + '\n' for line in lines[:-1]] + [lines[-1]]


def notebook(cells, title):
    return {
        'cells': cells,
        'metadata': {
            'kernelspec': {
                'display_name': 'Python 3',
                'language': 'python',
                'name': 'python3',
            },
            'language_info': {'name': 'python'},
            'title': title,
        },
        'nbformat': 4,
        'nbformat_minor': 5,
    }


def write(path, content, force=False):
    if os.path.exists(path) and not force:
        with open(path, encoding='utf-8') as f:
            existing = json.load(f)
        if any(
            cell.get('execution_count')
            for cell in existing.get('cells', [])
        ):
            print(f'  SKIP {os.path.basename(path)} (has been run; '
                  'use --force to overwrite)')
            return False
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print(f'  wrote {os.path.basename(path)}')
    return True


# --------------------------------------------------------------------
# Shared cells
# --------------------------------------------------------------------
SETUP = """
    import os
    import sys

    sys.path.insert(0, os.path.abspath('..'))

    import geopandas as gpd
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    import uli

    # Identify yourself once; it is copied into every deliverable.
    ANALYST = {
        'name': 'TODO: your name',
        'email': None,
        'institution': None,
    }

    print(f'ULI schema version {uli.SCHEMA_VERSION}')
    print(f'Reference geographies available: {uli.geography.available()}')
"""

WORKFLOW = """
    ## How to work through this notebook

    For each indicator assigned to you, in this order:

    1. **Read the brief.** It reproduces everything the team already
       recorded in the workbook — the draft rationale, the article the
       indicator was adapted from, candidate data sources, and the open
       questions colleagues raised. Do not retype any of it; it is
       already in your metadata stub.
    2. **Write the causal pathway sentence** (guide §2.1) and find
       **independent health evidence** for it (§2.2). Do this *before*
       looking for data. Fill in `meta['rationale']`.
    3. **Find and document the data** (§3): citation, URL, date
       retrieved, licence, and whether it reaches Condesa.
    4. **Compute** at the finest scale your data genuinely support.
       Produce a `DataFrame` with `geo_id` and `value`.
    5. **Harmonise** with `uli.harmonise(...)`, label with
       `uli.label(...)`, and **deliver** with
       `uli.write_indicator(...)`.
    6. **Look at the map.** Most errors are obvious in ten seconds and
       invisible in a table.

    `uli.write_indicator` validates first and refuses to publish a
    failing deliverable. While you are still iterating, pass
    `allow_failure=True` to write a draft anyway.

    Full guidance: [`docs/analyst_guide.md`](../docs/analyst_guide.md).
    Schema: [`schema/ULI_output_schema.md`](../schema/ULI_output_schema.md).
"""

EVIDENCE = """
    ## Framing the indicator against health evidence

    Every indicator must be justified by evidence of a **meaningful
    health or wellbeing benefit**, independent of the liveability
    article it was adapted from. Those articles establish that an
    indicator is used; they rarely establish that it matters.

    Complete this sentence before you compute anything:

    > *[what I measure]* changes *[a mechanism]*, which changes *[a
    > behaviour or exposure]*, which affects *[a health outcome]*.

    For most indicators in this project the behaviour is **walking for
    transport**, **walking or recreation in public space**, or
    **social contact** — and the exposure is **heat**, **air
    pollution** or **injury risk**. Say which, using the vocabulary in
    `uli.vocab.HEALTH_PATHWAYS`.

    Prefer meta-analyses and systematic reviews, then reputable
    guidance (WHO, UN-Habitat, PAHO, Secretaría de Salud), then cohort
    studies and natural experiments. Record the **effect size with its
    uncertainty**.

    **If the evidence supports a different threshold from the one the
    workbook proposes, use the evidence-based threshold** and say so in
    `threshold_justification`. That is explicitly what the project
    wants.

    **Mexicali is arid and extremely hot.** Most of this literature
    comes from temperate cities. Where the transfer is doubtful — for
    example, distance-based walkability thresholds in a city where
    summer maxima exceed 45 °C and shade rather than distance is the
    binding constraint — record it in `rationale.arid_context`. That is
    a contribution, not a caveat.
"""

FAMILIES = """
    ## When several workbook rows are really one indicator

    The workbook harvested indicators article by article, so a single
    construct sometimes appears as several rows seen through different
    lenses or over different time periods. Air quality is the clearest
    case:

    | Row | What it is | Lens | Time basis |
    |---|---|---|---|
    | #292 Air quality | the index value itself | `quality` | `annual_mean` |
    | #8 Good air quality | that value against a standard | `quality` | `threshold_share` |
    | #293 Days with good air quality | how often the standard is met | `quantity` | `threshold_compliance_days` |
    | #173 Days PM2.5 over WHO | the same, for one pollutant | `quantity` | `threshold_exceedance_days` |

    These are not four indicators — they are one construct measured
    four ways, and computing them separately would mean four
    inconsistent methods and four sets of data documentation.

    Deliver them as a **measure family**: give every measure the same
    `measure_family` slug, and distinguish them with `temporal_basis`
    (see `uli.vocab.TEMPORAL_BASES`) and `threshold`. They can still
    live under separate workbook ids — the family slug is what tells
    the index step, and Reimagina Urbana, that they belong together.

    ```python
    for meta in (meta_292, meta_8, meta_293, meta_173):
        for measure in meta['measures']:
            measure['measure_family'] = 'air_quality'
        meta['data_sources'] = SHARED_SOURCES   # one method, one source
    ```

    The same pattern applies to mean summer temperature versus days
    above a comfort threshold (WP02), and to flood extent versus annual
    average days of flooding (WP05).
"""

CONDESA = """
    ## Condesa coverage is a requirement, not a nicety

    The Condesa new development in south-east Mexicali is a project
    focus area, and it defeats the usual assumptions:

    - about **20%** of it falls outside the previously configured
      study region boundary;
    - only **44%** of its area is covered by census manzana polygons,
      so a **manzana-native calculation reaches 33 of the 40
      fraccionamientos, while a `grid_100m`-native one reaches all
      40**;
    - it is platted and roaded (43 km of street network in OpenStreetMap
      across 27 of the 40 fraccionamientos) but essentially unbuilt —
      **zero destinations**, and satellite-derived population products
      see almost nobody there.

    **One thing is your decision: the native scale.** If your data
    allow it, compute on the 100 m grid. That is the difference between
    reaching all of Condesa and quietly missing a fifth of it.

    Everything else is handled downstream. Population denominators,
    the 2030 occupancy scenario and population-weighted exposure
    statistics are a reporting-step concern (`uli.exposure`), decided
    once for the whole project rather than by each analyst. Urban
    fabric and exposure measures — land cover, air quality, heat,
    hazards, street infrastructure — are properties of *place*, and
    should be computed as such; who lives there is applied later.

    Two things to record, though:

    - `data_sources[].condesa_coverage` — whether your **source**
      reaches Condesa. Satellite imagery and OSM generally do; a 2020
      census variable or a household survey generally does not.
    - `method.condesa_treatment` — what you did about it. Where a
      source does not reach Condesa, mark those rows `no_data` rather
      than omitting them.

    The validator treats poor Condesa coverage as an **error**.
"""

FINISH = """
    ---
    ## Check what this work package has delivered
"""

FINISH_CODE = """
    delivered, catalogue = uli.collect()
    if len(catalogue):
        display(catalogue)
        print(delivered.groupby(['indicator_code', 'geo_level']).size())
    else:
        print('Nothing delivered yet.')
"""

MAP_QA = """
    # Sanity-check a delivered measure on a map before you call it done.
    # MEASURE = 'your_indicator_code__quantity'
    # LEVEL = 'manzana'
    # units = uli.geography.load(LEVEL).merge(
    #     delivered.query('measure_id == @MEASURE and geo_level == @LEVEL'),
    #     on='geo_id', how='left')
    # ax = units.plot(column='value', legend=True, figsize=(11, 8),
    #                 missing_kwds={'color': 'lightgrey'})
    # condesa = uli.geography.load('condesa_fraccionamiento')
    # condesa.boundary.plot(ax=ax, color='red', linewidth=1)
    # ax.set_title(MEASURE)
    # ax.set_axis_off()
"""


# --------------------------------------------------------------------
# Indicator briefs
# --------------------------------------------------------------------
def brief(record):
    """Markdown brief reproducing everything the workbook records."""
    classification = ' · '.join(
        part
        for part in (
            '/'.join(record['domains']),
            record.get('subdomain'),
            record.get('category'),
            record.get('subject'),
        )
        if part
    )
    lines = [
        f'### {record["indicator_id"]} — {record["indicator"]}',
        '',
        f'`{record["indicator_code"]}` · *{classification}*',
        '',
    ]

    bullets = [
        (
            'Lenses to deliver',
            ', '.join(record['lenses']) or 'none flagged in the workbook',
        ),
        ('Draft rationale (rewrite this)', record.get('reason_draft')),
        ('Adapted from', record.get('source_citation')),
        ('Effect reported there', record.get('source_effect_size')),
        ('Pragmatic approach agreed', record.get('pragmatic_method')),
        (
            'Methods used in the literature',
            record.get('methods_from_literature'),
        ),
        ('Candidate data sources', record.get('potential_data_sources')),
        ('Team notes', record.get('notes')),
        ('Open questions raised', record.get('doubts')),
    ]
    feasibility = str(record.get('can_calculate') or '').split('.')[0]
    if feasibility:
        bullets.append(
            (
                'Feasibility flag',
                {
                    '1': 'yes, data believed available',
                    '2': 'to be determined',
                    '0': 'no',
                }.get(feasibility, feasibility),
            )
        )
    if record['indicator_id'] in templates.GHSCI_COMPOSITES:
        bullets.append(
            (
                'Composite',
                'built by the core GHSCI workflow from its component '
                'indicators rather than measured directly.',
            )
        )

    for label, value in bullets:
        if value:
            lines.append(f'- **{label}:** {" ".join(str(value).split())}')

    lines += [
        '',
        '> **Your first task is not GIS.** Write the causal pathway '
        'sentence, then find independent health evidence for it — see '
        'the framing section above.',
    ]
    return '\n'.join(lines)


def indicator_cells(record):
    """The three working cells for one indicator."""
    code_name = record['indicator_code']
    indicator_id = record['indicator_id']
    lenses = [
        lens for lens in record['lenses'] if lens in vocab.ANALYST_LENSES
    ] or ['quantity']
    first = f'{code_name}__{lenses[0]}'
    return [
        markdown(brief(record)),
        code(
            f"""
            # 1. Documentation --------------------------------------------
            # Pre-filled from the workbook; edit in place.  Run
            # uli.todos(meta_{indicator_id}) at any time to list what is
            # still outstanding.
            meta_{indicator_id} = uli.metadata_stub({indicator_id}, analyst=ANALYST)

            # meta_{indicator_id}['rationale']['statement'] = \"\"\"...\"\"\"
            # meta_{indicator_id}['rationale']['health_pathways'] = [
            #     'physical_activity_transport',
            # ]
            # meta_{indicator_id}['rationale']['arid_context'] = '...'
            # meta_{indicator_id}['rationale']['evidence'] = [
            #     {{
            #         'claim': '...',
            #         'citation': '...',
            #         'doi': '...',
            #         'evidence_type': 'systematic_review',
            #         'population': '...',
            #         'exposure': '...',
            #         'outcome': '...',
            #         'effect': 'RR 0.92 (95% CI 0.88-0.96) per ...',
            #         'threshold_support': '...',
            #     }},
            # ]
            # meta_{indicator_id}['data_sources'] = [
            #     {{
            #         'name': '...',
            #         'custodian': '...',
            #         'citation': '...',
            #         'url': '...',
            #         'date_retrieved': 'YYYY-MM-DD',
            #         'licence': '...',
            #         'redistributable': True,
            #         'spatial_resolution': '...',
            #         'temporal_coverage': '...',
            #         'condesa_coverage': 'full',
            #     }},
            # ]

            uli.todos(meta_{indicator_id})
            """
        ),
        code(
            f"""
            # 2. Calculation ----------------------------------------------
            # Compute at the finest scale your data genuinely support and
            # produce a DataFrame with columns: geo_id, value.
            #
            # Reaching all 40 Condesa fraccionamientos needs a native
            # scale of grid_100m (manzana reaches only 33).
            NATIVE_SCALE_{indicator_id} = 'grid_100m'
            METHOD_{indicator_id} = 'population_weighted_mean'

            native_{indicator_id} = None  # TODO: your calculation

            # Handy builders:
            #   uli.count_features(points, NATIVE_SCALE, per='1000_persons')
            #   uli.areal_share(polygons, NATIVE_SCALE, as_percentage=True)
            #   uli.network_share(edges, NATIVE_SCALE, 'has_sidewalk')
            #   uli.zonal_statistic('raster.tif', NATIVE_SCALE, 'mean')
            """
        ),
        code(
            f"""
            # 3. Harmonise, validate, deliver ------------------------------
            harmonised_{indicator_id} = uli.harmonise(
                native_{indicator_id},
                native_scale=NATIVE_SCALE_{indicator_id},
                method=METHOD_{indicator_id},
            )
            results_{indicator_id} = uli.label(
                harmonised_{indicator_id},
                meta_{indicator_id},
                measure_id='{first}',
            )
            # Several measures?  Label each and combine:
            #   results = uli.assemble([results_a, results_b])

            print(uli.check(results_{indicator_id}, meta_{indicator_id}))
            # uli.write_indicator(results_{indicator_id}, meta_{indicator_id})
            """
        ),
    ]


def batch_cells(package, records):
    """Layout for work packages with too many indicators to enumerate."""
    listing = '\n'.join(
        f'| {r["indicator_id"]} | {r["indicator"]} | '
        f'`{r["indicator_code"]}` | {", ".join(r["lenses"])} |'
        for r in records
    )
    return [
        markdown(
            f"""
            ## Assigned indicators ({len(records)})

            | # | Indicator | Code | Lenses |
            |---|---|---|---|
            {listing}

            This work package has too many indicators to give each its
            own cell, and they share a single method, so they are
            processed as a batch. The per-indicator briefs are still
            available from the register:

            ```python
            uli.register.get(91)
            ```
            """
        ),
        code(
            """
            assigned = uli.register.load()
            assigned = assigned[assigned['work_package'] == WORK_PACKAGE]
            assigned[['indicator_id', 'indicator', 'indicator_code',
                      'lenses', 'is_composite', 'pragmatic_method']]
            """
        ),
        markdown(
            """
            ### Batch processing

            Build one metadata stub per indicator, complete the shared
            documentation programmatically where it genuinely is
            shared (method, software, data sources), and the
            indicator-specific parts individually. Evidence is **not**
            shared: each destination type needs its own health
            citation, because the evidence for access to health
            services is not the evidence for access to a bakery.
            """
        ),
        code(
            """
            metas = {
                int(row.indicator_id): uli.metadata_stub(
                    int(row.indicator_id), analyst=ANALYST
                )
                for row in assigned.itertuples()
            }

            SHARED_SOURCES = [
                # {
                #     'name': 'OpenStreetMap',
                #     'custodian': 'OpenStreetMap contributors',
                #     'citation': 'OpenStreetMap contributors (2026). '
                #                 'Planet dump, Geofabrik extract Mexico.',
                #     'url': 'https://download.geofabrik.de/',
                #     'date_retrieved': '2026-04-10',
                #     'licence': 'ODbL-1.0',
                #     'redistributable': True,
                #     'spatial_resolution': 'vector',
                #     'temporal_coverage': '2026',
                #     'condesa_coverage': 'full',
                # },
            ]
            for meta in metas.values():
                if SHARED_SOURCES:
                    meta['data_sources'] = list(SHARED_SOURCES)
                meta['method']['software'] = ['GHSCI', 'OSMnx', 'pandana']
                meta['method']['notebook'] = NOTEBOOK

            len(metas)
            """
        ),
        code(
            """
            # Calculation ---------------------------------------------------
            # Produce, for each indicator, a native-scale DataFrame with
            # geo_id and value, then harmonise and label it.
            deliverables = {}

            # for indicator_id, meta in metas.items():
            #     native = ...
            #     harmonised = uli.harmonise(native, NATIVE_SCALE,
            #                                method=METHOD)
            #     deliverables[indicator_id] = uli.label(
            #         harmonised, meta,
            #         measure_id=meta['measures'][0]['id'])

            len(deliverables)
            """
        ),
        code(
            """
            # Validate and deliver ------------------------------------------
            for indicator_id, results in deliverables.items():
                uli.write_indicator(results, metas[indicator_id])
            """
        ),
    ]


# --------------------------------------------------------------------
# Notebook construction
# --------------------------------------------------------------------
def overview_notebook(reg, packages):
    counts = reg['work_package'].value_counts()
    rows = '\n'.join(
        f'| `{p["code"]}` | {p["name"]} | {p["lead"]} | '
        f'{counts.get(p["code"], 0)} |'
        for p in packages
    )
    lens_rows = '\n'.join(
        f'| `{key}` | {" ".join(value.split())} |'
        for key, value in vocab.LENSES.items()
    )
    geo_rows = '\n'.join(
        f'| `{key}` | {" ".join(value.split())} | '
        f'{"required" if key in vocab.REQUIRED_GEO_LEVELS else "optional"} |'
        for key, value in vocab.GEO_LEVELS.items()
    )
    cells = [
        markdown(
            f"""
            # Mexicali Urban Liveability Index
            ## Overview, output schema and a worked example

            **Read this notebook before starting your own work
            package.** It explains what is being built, what you are
            expected to deliver, and shows one indicator carried all
            the way from a row in the workbook to a validated,
            ingestible deliverable.

            Schema version **{vocab.SCHEMA_VERSION}**.

            ---

            ### What is being built

            A suite of spatial liveability indicators for Mexicali, an
            arid city in Baja California, and from them a composite
            liveability index. Outputs also feed the **Reimagina
            Urbana** platform.

            The local team identified a large set of candidate
            indicators from a review of the liveability literature,
            classified them by domain, subdomain, category and subject,
            and narrowed them to **{len(reg) - 1} indicators** that are
            both plausibly relevant to health and wellbeing in Mexicali
            and feasible with available data.

            Indicators are *adapted*, not copied, from the reviewed
            articles. That is precisely why each one needs independent
            health evidence: the source article establishes that the
            indicator has been used, not that it matters.

            ### Work packages

            | Code | Work package | Lead | Indicators |
            |---|---|---|---|
            {rows}

            ### Analytical lenses (*enfoques*)

            One indicator can be measured several ways. The team
            defined these lenses:

            | Lens | Meaning |
            |---|---|
            {lens_rows}

            ### Reporting geographies

            | Level | Description | Required |
            |---|---|---|
            {geo_rows}
            """
        ),
        markdown(WORKFLOW),
        markdown(EVIDENCE),
        markdown(FAMILIES),
        markdown(CONDESA),
        markdown(
            """
            ---
            ## Setup
            """
        ),
        code(SETUP),
        code(
            """
            register = uli.register.load()
            register.groupby('work_package').agg(
                indicators=('indicator_id', 'size'),
                composites=('is_composite', 'sum'),
            )
            """
        ),
        markdown(
            """
            ## The reference geographies

            Everyone reports against the same units, read from one
            geopackage in EPSG:6366. Do not build your own grid.
            """
        ),
        code(
            """
            summary = pd.DataFrame([
                {
                    'geo_level': level,
                    'units': len(uli.geography.units(level)),
                    'median_area_ha': round(
                        uli.geography.units(level)['area_sqm'].median()
                        / 10000, 2),
                    'population_ghs_pop_2025': round(
                        uli.geography.units(level)['population'].sum()),
                    'population_census_2020': round(
                        uli.geography.units(level)[
                            'pop_census_2020'].sum()),
                }
                for level in uli.vocab.GEO_RESOLUTION_ORDER
            ])
            summary
            """
        ),
        code(
            """
            # Where is Condesa?
            fig, ax = plt.subplots(figsize=(11, 6))
            uli.geography.load('city').boundary.plot(
                ax=ax, color='0.6', linewidth=0.8)
            uli.geography.load('manzana').plot(
                ax=ax, color='0.85', edgecolor='none')
            uli.geography.load('condesa_fraccionamiento').plot(
                ax=ax, color='crimson', edgecolor='crimson')
            ax.set_title('Mexicali ULI study extent, with the Condesa '
                         'new development in red')
            ax.set_axis_off()
            """
        ),
        markdown(
            """
            ---
            ## Worked example

            An indicator carried end to end, using data already in the
            repository: **access to convenience destinations**, from
            the GHSCI Mexicali destinations layer.

            The example is deliberately small. What matters is the
            shape: documentation first, then a native-scale
            calculation, then harmonisation, validation and delivery.
            """
        ),
        code(
            """
            GHSCI = os.path.join(
                '..', '..', '..', '_study_region_outputs',
                'MX_Mexicali_2025-MZA',
                'MX_Mexicali_2025-MZA_1600m_buffer.gpkg')

            destinations = gpd.read_file(GHSCI, layer='destinations')
            destinations['dest_name'].value_counts().head(10)
            """
        ),
        code(
            """
            # 1. Documentation.  Every field below is a real
            #    requirement, not an example of one.
            example = uli.metadata_stub(132, analyst=ANALYST)   # minimarts

            example['indicator']['status'] = 'draft'
            example['rationale']['statement'] = (
                'Small food retail within walking distance supports '
                'walking for transport and daily access to food '
                'without a car.  In Mexicali, where car ownership is '
                'high and summer heat suppresses discretionary '
                'walking, short trip distances to everyday '
                'destinations are a precondition for any walking at '
                'all, and the households least able to substitute a '
                'car trip are those on the lowest incomes.'
            )
            example['rationale']['health_pathways'] = [
                'physical_activity_transport',
                'food_environment',
            ]
            example['rationale']['arid_context'] = (
                'Distance thresholds calibrated in temperate cities '
                'likely overstate walking here: in summer, shade and '
                'time of day plausibly bind before distance does.  '
                'Results should be read alongside the thermal comfort '
                'indicators from WP02.'
            )
            example['rationale']['evidence'] = [
                {
                    'claim': 'Greater neighbourhood destination access '
                             'is associated with more walking for '
                             'transport and higher total physical '
                             'activity.',
                    'citation': 'TODO: replace with the systematic '
                                'review you select, e.g. a review of '
                                'built environment and walking for '
                                'transport',
                    'doi': None,
                    'url': None,
                    'evidence_type': 'systematic_review',
                    'population': 'TODO',
                    'exposure': 'Destination accessibility',
                    'outcome': 'Walking for transport',
                    'effect': 'TODO: effect size with 95% CI',
                    'threshold_support': 'TODO: what distance the '
                                         'evidence supports',
                },
            ]
            example['data_sources'] = [
                {
                    'name': 'OpenStreetMap (via GHSCI Mexicali study '
                            'region)',
                    'custodian': 'OpenStreetMap contributors',
                    'citation': 'OpenStreetMap contributors (2026). '
                                'Geofabrik Mexico extract, 10 April '
                                '2026.',
                    'url': 'https://download.geofabrik.de/'
                           'north-america/mexico.html',
                    'date_retrieved': '2026-04-10',
                    'licence': 'ODbL-1.0',
                    'licence_url': 'https://opendatacommons.org/'
                                   'licenses/odbl/',
                    'redistributable': True,
                    'spatial_resolution': 'vector points',
                    'temporal_coverage': '2026',
                    'condesa_coverage': 'full',
                    'notes': 'Volunteered data; completeness varies '
                             'and is likely lower in newly developed '
                             'areas.',
                },
            ]
            example['method']['summary'] = (
                'Convenience destination points were extracted from '
                'the GHSCI Mexicali destinations layer and counted '
                'within each 100 m grid cell, then expressed per '
                'square kilometre.  Cell values were aggregated to '
                'coarser reporting geographies as a population '
                'weighted mean, falling back to area weighting where '
                'no resident population is recorded.'
            )
            example['method']['notebook'] = (
                'notebooks/00_overview_and_schema.ipynb')
            example['method']['condesa_treatment'] = (
                'Computed natively on the 100 m grid, which covers '
                'the full Condesa extent; OpenStreetMap coverage of '
                'the new development is, however, likely incomplete.'
            )

            uli.todos(example)
            """
        ),
        code(
            """
            # 2. Calculation at the native scale.
            convenience = destinations[
                destinations['dest_name'] == 'convenience']

            native = uli.count_features(
                convenience, 'grid_100m', per='sqkm')
            native['value'].describe()
            """
        ),
        code(
            """
            # 3. Harmonise to every reporting geography, label, check.
            example['measures'] = [
                m for m in example['measures'] if m['lens'] == 'density'
            ]
            measure = example['measures'][0]
            measure['id'] = 'access_to_minimarts__density_per_sqkm'
            measure['name_en'] = 'Convenience destinations per km²'
            measure['description'] = (
                'Count of OpenStreetMap convenience destinations whose '
                'point falls within the unit, divided by unit area in '
                'km².')
            measure['unit'] = 'count per km2'
            measure['value_type'] = 'rate'
            measure['direction'] = 'higher_is_better'
            measure['denominator_type'] = 'area_sqkm'
            measure['native_scale'] = 'grid_100m'
            measure['aggregation_method'] = 'population_weighted_mean'

            harmonised = uli.harmonise(
                native, 'grid_100m', method='population_weighted_mean')
            results = uli.label(
                harmonised, example, measure['id'])
            results.head()
            """
        ),
        code(
            """
            print(uli.check(results, example))
            """
        ),
        markdown(
            """
            The report above will still fail: the `TODO` placeholders
            in the evidence block are exactly the work this project
            asks each analyst to do. That is the intended behaviour —
            an indicator without independent health evidence is not
            deliverable.

            Once the evidence is real, `uli.write_indicator(results,
            example)` writes the three deliverable files and the run is
            reproducible from this notebook alone.
            """
        ),
        code(
            """
            results.groupby(['geo_level', 'aggregation_method']).agg(
                units=('value', 'size'),
                with_value=('value', 'count'),
                median=('value', 'median'),
            )
            """
        ),
        markdown(
            """
            Note the `condesa_fraccionamiento` rows: because the
            calculation was native to the 100 m grid, all 40 units get
            a value. Had it been native to `manzana`, only 33 would —
            the seven fraccionamientos with no overlapping census block
            would have been silently absent. Note too the
            `area_weighted_mean` rows: those are units where the
            population weight was zero and the fallback took over.

            ---
            ## Ingestion

            The composite index and Reimagina Urbana both read
            deliverables through the same function you can run
            yourself:
            """
        ),
        code(
            """
            delivered, catalogue = uli.collect()
            print(f'{len(delivered):,} rows from '
                  f'{catalogue["indicator_code"].nunique() if len(catalogue) else 0} '
                  'indicators')
            catalogue.head(20) if len(catalogue) else 'Nothing delivered yet.'
            """
        ),
        code(
            """
            # Wide format for one geography, and a geopackage for QGIS
            # / the platform:
            # wide = uli.to_wide(delivered, 'manzana')
            # uli.to_geopackage(delivered, 'outputs/mexicali_uli.gpkg')
            """
        ),
    ]
    return notebook(cells, 'ULI overview and schema')



def synthesis_notebook(package):
    """Reporting-side notebook: exposure and the provisional index."""
    cells = [
        markdown(
            f"""
            # {package['name']}
            ## Mexicali ULI — `{package['code']}`

            **Lead:** {package['lead']}
            **Schema version:** {vocab.SCHEMA_VERSION}

            Not an analyst task. This notebook is the **reporting
            step**: it ingests validated work package deliverables and
            turns values-for-places into statements about *people* —
            what share of the population experiences what, and a
            population-weighted liveability score.

            Analysts do not need anything here. Choosing a population
            denominator is a decision made once, in one place, after
            delivery; urban fabric and exposure measures are properties
            of place and are computed as such.
            """
        ),
        markdown(
            """
            ## Population denominators

            Four denominators are carried on every reporting geography,
            because the right one depends on the question being asked.

            | Basis | What it is | Study extent | Condesa |
            |---|---|---|---|
            | `pop_census_2020` | INEGI census | 852,506 | 0 |
            | `population` | GHS-POP 2025 (observed today) | 823,260 | 372 |
            | `population_2030` | GHS-POP 2030 (projection as published) | 842,287 | 377 |
            | `population_planned` | Condesa at full occupancy | 48,170 | 48,032 |
            | `population_scenario_2030` | GHS-POP 2030 outside Condesa **+** planned occupancy inside | **890,079** | 48,032 |

            ### Why the scenario basis exists

            Condesa is platted and roaded — 43 km of street network
            across 27 of 40 fraccionamientos — but essentially unbuilt.
            No population product resolves it, and the 2030 projection
            does not either: it adds **19,760 people city-wide (+2.3%)
            and 5 to Condesa**, leaving its share of the city unchanged
            at 0.044%. GHS-POP allocates a projected total onto observed
            built-up surface, and the development has roads but few
            roofs.

            What population it does record is borrowed from next door:
            364 of the 372 persons sit in fraccionamientos within 100 m
            of an already-populated 2020 manzana, and none beyond 500 m.
            That is the signature of areal apportionment, not occupancy.

            So `population_planned` is a **declared assumption, not an
            estimate**: one household per residential lot (14,597 lots
            of 14,989 at ≤ 300 m²) at the assumed Mexicali mean
            household size of 3.3. Both parameters live in
            `uli.geography` and any result derived from them can be
            re-derived under different assumptions.

            Under that assumption Condesa becomes **48,170 residents —
            5.4% of Mexicali**, against the 377 the projection sees.
            That is the whole reason the scenario basis is worth having.

            > **Report scenario results as conditional.** They answer
            > "if Condesa is fully occupied by 2030, on top of the
            > projected city, what will people experience?" — not
            > "what do people experience?".
            """
        ),
        markdown(
            """
            ---
            ## Setup
            """
        ),
        code(SETUP),
        code(
            """
            denominators = [
                'pop_census_2020', 'population', 'population_2030',
                'population_planned', 'population_scenario_2030',
            ]
            pd.DataFrame([
                dict(
                    level=level,
                    units=len(uli.geography.units(level)),
                    **{
                        d: round(uli.geography.units(level)[d].sum())
                        for d in denominators
                    },
                )
                for level in uli.vocab.GEO_RESOLUTION_ORDER
            ])
            """
        ),
        markdown(
            """
            Note that AGEB and manzana capture only ~39,500 and ~37,200
            of the 48,170 planned residents: the 2020 census geographies
            do not extend over the whole development. **Report scenario
            statistics on the grids or the Condesa layers**, not on
            census geography.
            """
        ),
        markdown(
            """
            ---
            ## Ingest the delivered indicators
            """
        ),
        code(
            """
            delivered, catalogue = uli.collect()
            print(f'{len(delivered):,} rows, '
                  f'{catalogue["measure_id"].nunique() if len(catalogue) else 0} '
                  'measures')
            catalogue
            """
        ),
        markdown(
            """
            ---
            ## Population exposure

            "What share of the population has X?" — computed for the
            study area, for Condesa, and for the rest of the city, under
            whichever denominator the question calls for.

            Population with **no value** is reported separately rather
            than counted as unexposed: an indicator that does not reach
            an area is not evidence that the area is fine.
            """
        ),
        code(
            """
            MEASURE = catalogue['measure_id'].iloc[0]   # choose one
            THRESHOLD = 1.0

            for basis in ('population', 'population_scenario_2030'):
                out = uli.exposed_share(
                    delivered, MEASURE, threshold=THRESHOLD,
                    comparison='at_or_above', geo_level='grid_100m',
                    population=basis)
                out.insert(0, 'basis', basis)
                display(out[['basis', 'group', 'population_with_value',
                             'population_meeting', 'share_meeting']])
            """
        ),
        markdown(
            """
            The contrast between the two bases is the point of the
            exercise. Under the observed denominator Condesa is a few
            hundred people and its conditions are invisible in the city
            total; under the scenario it is 5.4% of Mexicali and pulls
            the city-wide figure with it.
            """
        ),
        code(
            """
            # Population-weighted distribution of a measure
            uli.weighted_summary(
                delivered, MEASURE, geo_level='grid_100m',
                population='population_scenario_2030')
            """
        ),
        markdown(
            """
            ---
            ## Provisional liveability score

            **How the composite index is actually calculated is a later
            decision.** What follows is deliberately simple — equal
            weights, min-max normalisation, mean of available measures —
            so that the plumbing can be exercised end to end now, and so
            that swapping in the real method is a one-argument change.

            Two rules are already enforced, because they are not
            matters of taste:

            - only measures flagged `include_in_index` are used;
            - measures that are **replicated** from a coarser scale are
              excluded at that scale, because a constant contributes
              nothing but noise to a within-city comparison.
            """
        ),
        code(
            """
            unit_scores, summary = uli.score(
                delivered, catalogue,
                geo_level='grid_100m',
                population='population_scenario_2030',
                # weights={'measure_id': 0.4, ...},   # later decision
                # normalise=my_normalisation,          # later decision
            )
            print('used:   ', summary.attrs['measures_used'])
            print('skipped:', summary.attrs['measures_skipped'])
            summary
            """
        ),
        code(
            """
            # Map it, with Condesa outlined
            grid = uli.geography.load('grid_100m').merge(
                unit_scores, on='geo_id', how='left')
            ax = grid.plot(column='score', legend=True, figsize=(12, 7),
                           missing_kwds={'color': 'lightgrey'})
            uli.geography.load('condesa_fraccionamiento').boundary.plot(
                ax=ax, color='crimson', linewidth=1)
            ax.set_title('Provisional liveability score, 100 m grid '
                         '(Condesa outlined)')
            ax.set_axis_off()
            """
        ),
        markdown(
            """
            ---
            ## Export

            One geopackage, one layer per reporting geography, wide
            format — the shape QGIS and Reimagina Urbana both want.
            """
        ),
        code(
            """
            # uli.to_geopackage(delivered, 'outputs/mexicali_uli.gpkg')
            # unit_scores.to_csv('outputs/provisional_score_grid_100m.csv',
            #                    index=False)
            """
        ),
    ]
    return notebook(cells, package['name'])

def package_notebook(package, records, reg):
    code_name = package['code']
    lens_note = ''
    if any('equity' in r['lenses'] for r in records):
        lens_note = (
            '\n\nSeveral of your indicators are flagged with the '
            '**equity** lens in the workbook. Do not compute it: '
            'distributional equity is derived centrally from the '
            'finest-scale results so that it means the same thing '
            'across every domain. Deliver the other lenses.'
        )
    cells = [
        markdown(
            f"""
            # {package['name']}
            ## Mexicali Urban Liveability Index — `{code_name}`

            **Lead:** {package['lead']}
            **Indicators assigned:** {len(records)}
            **Schema version:** {vocab.SCHEMA_VERSION}

            {' '.join(str(package.get('summary', '')).split())}

            {' '.join(str(package.get('method_notes', '')).split())}{lens_note}

            > New to this project? Work through
            > [`00_overview_and_schema.ipynb`](00_overview_and_schema.ipynb)
            > first — it carries one indicator end to end. Then read
            > [`docs/analyst_guide.md`](../docs/analyst_guide.md).
            """
        ),
        markdown(WORKFLOW),
        markdown(EVIDENCE),
        markdown(FAMILIES),
        markdown(CONDESA),
        markdown(
            """
            ---
            ## Setup
            """
        ),
        code(
            SETUP
            + f"""
            WORK_PACKAGE = '{code_name}'
            NOTEBOOK = 'notebooks/{_filename(package)}'
            """
        ),
    ]

    if len(records) > BATCH_THRESHOLD:
        cells += batch_cells(package, records)
    else:
        cells.append(
            markdown(
                f"""
                ---
                ## Your indicators ({len(records)})

                Each has a brief reproducing what the workbook records,
                then three working cells: documentation, calculation,
                delivery.
                """
            )
        )
        for record in records:
            cells += indicator_cells(record)

    cells += [markdown(FINISH), code(FINISH_CODE), code(MAP_QA)]
    return notebook(cells, package['name'])


def _filename(package):
    stem = package['code'][5:]
    # The synthesis notebook is the last step even though its work
    # package must be listed first (so that indicator 0 is claimed
    # before WP01's pragmatic-method rule sweeps it up).
    number = '09' if package.get('kind') == 'synthesis' else package['code'][2:4]
    return f'{number}_{stem}.ipynb'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--force',
        action='store_true',
        help='overwrite notebooks that have already been run',
    )
    args = parser.parse_args()

    os.makedirs(NOTEBOOK_DIR, exist_ok=True)
    reg = register.load()
    packages = register.load_work_packages()
    grouped = register.by_work_package(reg)

    print('Building notebooks ...')
    write(
        os.path.join(NOTEBOOK_DIR, '00_overview_and_schema.ipynb'),
        overview_notebook(reg, packages),
        args.force,
    )
    for package in packages:
        subset = grouped.get(package['code'])
        if subset is None or subset.empty:
            continue
        if package['code'] == register.EXCLUDED:
            continue
        if package.get('kind') == 'synthesis':
            write(
                os.path.join(NOTEBOOK_DIR, _filename(package)),
                synthesis_notebook(package),
                args.force,
            )
            continue
        records = subset.to_dict('records')
        write(
            os.path.join(NOTEBOOK_DIR, _filename(package)),
            package_notebook(package, records, reg),
            args.force,
        )

    dropped = register.excluded(reg)
    if len(dropped):
        print(
            f'\n{len(dropped)} indicator(s) excluded from scope, so '
            f'no notebook scaffold: {sorted(dropped["indicator_id"])}'
        )
    unassigned = reg[reg['work_package'] == register.UNASSIGNED]
    if len(unassigned):
        print(
            f'\nWARNING: {len(unassigned)} indicators are unassigned: '
            f'{sorted(unassigned["indicator_id"])}'
        )
    try:
        path = register.save(register=reg)
        print(f'\nRegister written to {os.path.basename(path)}')
    except PermissionError:
        # Most often the register is open in Excel.  The notebooks are
        # already written, so this should not fail the build.
        print(
            '\nCould not rewrite indicator_register.csv (file locked, '
            'probably open in Excel).  Close it and re-run to refresh '
            'the register; the notebooks above are up to date.'
        )


if __name__ == '__main__':
    main()
