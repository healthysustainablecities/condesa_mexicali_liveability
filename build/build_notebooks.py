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

BRIEFING = """
    ## Before you start

    **Your job, in one sentence:** for each indicator below, produce a
    number for every unit of geography, and the documentation that
    makes that number defensible.

    Work in this order. Steps 1 and 2 are the ones people skip and
    then have to redo.

    | | Step | Where to look |
    |---|---|---|
    | 1 | Write the causal pathway: *X changes a mechanism, which changes a behaviour or exposure, which affects health* | [guide §2.1](../docs/analyst_guide.md) |
    | 2 | Find **independent health evidence** for that pathway, with an effect size | [guide §2.2](../docs/analyst_guide.md) |
    | 3 | Find the data. Record citation, URL, date retrieved, licence | [guide §3](../docs/analyst_guide.md) |
    | 4 | Compute it — pick the matching recipe | [cookbook](00b_cookbook.ipynb) |
    | 5 | `harmonise` → `label` → `check` → `write_indicator` | [cookbook §9](00b_cookbook.ipynb) |
    | 6 | Look at a map of your result before calling it done | [guide §6](../docs/analyst_guide.md) |

    Three things worth knowing now:

    - **The evidence is the point.** The article an indicator was
      adapted from shows it has been *used*, not that it *matters*.
      Supplying that missing link is the substantive contribution
      asked of you.
    - **Deliver natural units.** No normalising, no reverse-coding —
      set `direction` instead. The index does that once, centrally.
    - **Cover Condesa.** Compute on `grid_100m` where your data allow
      it: that reaches all 40 fraccionamientos of the development,
      where `manzana` reaches only 33. The validator treats poor
      Condesa coverage as an error.

    New to this? Run [`00b_cookbook.ipynb`](00b_cookbook.ipynb) first
    — it is eight worked examples on data already in the repository,
    and takes about twenty minutes.
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
# Which cookbook recipe fits an indicator, guessed from its lens and
# category.  A guess in the right neighbourhood beats a blank cell:
# beginners stall hardest on the empty page, and a wrong suggestion is
# obvious and easy to replace.
RECIPE_BY_LENS = {
    'proximity': (
        2,
        "native = uli.distance_to_nearest(features, NATIVE_SCALE, "
        "cap=3000)",
    ),
    'accessibility': (
        2,
        "distance = uli.distance_to_nearest(features, NATIVE_SCALE)\n"
        "native = distance.assign(\n"
        "    value=(distance['value'] <= 500).astype(float) * 100)",
    ),
    'quantity': (1, "native = uli.count_features(features, NATIVE_SCALE)"),
    'density': (
        1,
        "native = uli.count_features(features, NATIVE_SCALE, per='sqkm')",
    ),
    'diversity': (
        3,
        "# Entropy over class shares; build the shares with\n"
        "# uli.areal_share() per class, then combine.",
    ),
    'quality': (
        6,
        "native = uli.zonal_statistic('your_raster.tif', NATIVE_SCALE,"
        " 'mean')",
    ),
}

RECIPE_BY_KEYWORD = [
    (
        ('vegetation', 'ndvi', 'canopy', 'green', 'land use', 'land',
         'flooding', 'residential area', 'heat', 'thermal'),
        (
            3,
            "native = uli.areal_share(polygons, NATIVE_SCALE, "
            "as_percentage=True)\n"
            "# or, for a continuous surface:\n"
            "# native = uli.zonal_statistic('raster.tif', NATIVE_SCALE,"
            " 'mean')",
        ),
    ),
    (
        ('sidewalk', 'street light', 'cycling', 'pedestrian '
         'infrastructure', 'road', 'traffic stress'),
        (
            5,
            "native = uli.network_share(edges, NATIVE_SCALE, "
            "attribute='has_sidewalk')",
        ),
    ),
    (
        ('housing', 'price', 'jobs', 'employment', 'density',
         'urbanization', 'demographic'),
        (
            7,
            "# Values probably already exist per AGEB or manzana:\n"
            "table = pd.read_csv('../data/raw/your_file.csv',\n"
            "                    dtype={'CVEGEO': str})\n"
            "native = table.rename(columns={'CVEGEO': 'geo_id',\n"
            "                               'your_column': 'value'}\n"
            "                      )[['geo_id', 'value']]",
        ),
    ),
]


def recipe_hint(record):
    """Return (recipe_number, starter_code) for an indicator."""
    haystack = ' '.join(
        str(record.get(field) or '').lower()
        for field in ('indicator', 'category', 'subject', 'subdomain')
    )
    for keywords, hint in RECIPE_BY_KEYWORD:
        if any(word in haystack for word in keywords):
            return hint
    for lens in record['lenses']:
        if lens in RECIPE_BY_LENS:
            return RECIPE_BY_LENS[lens]
    return (1, "native = uli.count_features(features, NATIVE_SCALE)")


def brief(record, articles=None):
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

    # Provenance is resolved from the reviewed article list by article
    # number.  The workbook's free-text 'Citation(s)' column is not
    # shown: it holds secondary citations -- works cited inside the
    # review articles -- and for 75 of 79 indicators it names no author
    # of the article the indicator is attributed to.  Nor are the
    # 'Effect size' and 'Methods sub-indices/measures' columns, both of
    # which risk misattributing findings to the wrong study.
    references, unknown = register.article_reference(
        record.get('article_numbers'), articles
    )
    provenance = '; '.join(references)
    if unknown:
        provenance += (
            (' — ' if provenance else '')
            + 'article number(s) '
            + ', '.join(str(n) for n in unknown)
            + ' cited in the workbook but absent from the article list'
        )

    bullets = [
        (
            'Lenses to deliver',
            ', '.join(record['lenses']) or 'none flagged in the workbook',
        ),
        ('Draft rationale (rewrite this)', record.get('reason_draft')),
        ('Adapted from', provenance or 'no source article recorded'),
        ('Pragmatic approach agreed', record.get('pragmatic_method')),
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


def indicator_cells(record, articles=None):
    """The three working cells for one indicator."""
    code_name = record['indicator_code']
    indicator_id = record['indicator_id']
    lenses = [
        lens for lens in record['lenses'] if lens in vocab.ANALYST_LENSES
    ] or ['quantity']
    first = f'{code_name}__{lenses[0]}'
    recipe_number, starter = recipe_hint(record)
    starter = starter.replace('\n', '\n            ')
    cookbook_link = '00b_cookbook.ipynb'
    method = (
        'area_weighted_mean'
        if recipe_number in (3, 4, 6)
        else 'length_weighted_mean'
        if recipe_number == 5
        else 'population_weighted_mean'
    )
    # Recipe 7 starts from an AGEB-keyed table, so suggesting a 100 m
    # native scale there would contradict its own example.
    native_scale = 'ageb' if recipe_number == 7 else 'grid_100m'
    # Commented out so the scaffold runs top to bottom without
    # erroring on names that do not exist yet.
    joiner = '\n' + ' ' * 12
    starter = joiner.join(
        line if not line or line.startswith('#') else '# ' + line
        for line in starter.split(joiner)
    )
    return [
        markdown(brief(record, articles)),
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
            # Produce a DataFrame with two columns: geo_id and value.
            #
            # Suggested starting point: cookbook Recipe {recipe_number}
            # ({cookbook_link}).  If it does not fit, the other recipes
            # are in the same notebook -- this is a guess from the
            # indicator's lens and category, not a decision.
            #
            # grid_100m reaches all 40 Condesa fraccionamientos;
            # manzana reaches only 33.
            NATIVE_SCALE = '{native_scale}'
            METHOD = '{method}'

            # Uncomment and adapt:
            # features = gpd.read_file('../data/raw/your_data.gpkg')
            {starter}

            native_{indicator_id} = None  # <- assign your result here
            """
        ),
        code(
            f"""
            # 3. Harmonise, validate, deliver ------------------------------
            harmonised_{indicator_id} = uli.harmonise(
                native_{indicator_id},
                native_scale=NATIVE_SCALE,
                method=METHOD,
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
    """A short orientation page.  Deliberately short."""
    counts = reg['work_package'].value_counts()
    rows = '\n'.join(
        f'| `{p["code"][:4]}` | {p["name"]} | {p["lead"]} | '
        f'{counts.get(p["code"], 0)} |'
        for p in packages
        if counts.get(p['code'], 0)
    )
    cells = [
        markdown(
            f"""
            # Mexicali Urban Liveability Index
            ## Start here

            A suite of spatial liveability indicators for Mexicali, an
            arid city in Baja California, and from them a composite
            liveability index. Outputs also feed the **Reimagina
            Urbana** platform.

            The local team reviewed the liveability literature,
            classified the candidate indicators, and narrowed them to
            **{len(reg) - 2}** that are plausibly relevant to health in
            Mexicali and feasible with available data. Calculation is
            split across work packages:

            | | Work package | Lead | Indicators |
            |---|---|---|---|
            {rows}

            ---

            ## Your first hour

            1. **Run the setup check below.** If it prints two ticks,
               you are ready.
            2. **Work through
               [`00b_cookbook.ipynb`](00b_cookbook.ipynb)** — eight
               worked examples on data already in this repository,
               about twenty minutes. This is the fastest way in.
            3. **Open your work package notebook** (`01_` to `08_`)
               and read the brief for your first indicator.
            4. **Skim [the analyst guide](../docs/analyst_guide.md)**
               — sections 2 and 5 especially. The rest is reference;
               come back to it when a question arises.

            You do not need to read the schema, the plan, or the
            decisions record to start. They are there for when you
            need them.

            ---

            ## What you deliver

            Two files per indicator, written for you by one function
            call:

            ```
            outputs/<work_package>/<indicator_code>/
                <indicator_code>_results.csv     # the numbers
                <indicator_code>_metadata.yml    # why, from what, how
            ```

            The metadata is not paperwork. The index cannot use a
            value without knowing whether high is good or bad, and the
            platform cannot publish a layer without knowing its
            licence.
            """
        ),
        markdown(
            """
            ---
            ## Setup check
            """
        ),
        code(SETUP),
        code(
            """
            ok_geography = uli.geography.available()
            ok_register = len(uli.register.load()) > 0
            print(f'{"[ok]" if ok_geography else "[!!]"} reference '
                  'geographies')
            print(f'{"[ok]" if ok_register else "[!!]"} indicator '
                  'register')
            if not ok_geography:
                print()
                print('Ask the project lead for the geography/ folder.')
            """
        ),
        markdown(
            """
            ---
            ## The geographies you report against

            Everyone uses the same units, from one geopackage, in
            EPSG:6366. Do not build your own grid — `uli.harmonise`
            fills in all of these from whichever one you compute on.
            """
        ),
        code(
            """
            pd.DataFrame([
                {
                    'geo_level': level,
                    'units': len(uli.geography.units(level)),
                    'median_area_ha': round(
                        uli.geography.units(level)['area_sqm'].median()
                        / 10000, 2),
                    'population_2025': round(
                        uli.geography.units(level)['population'].sum()),
                }
                for level in uli.vocab.GEO_RESOLUTION_ORDER
            ])
            """
        ),
        code(
            """
            # Mexicali, with the Condesa development in red.
            fig, ax = plt.subplots(figsize=(11, 6))
            uli.geography.load('manzana').plot(
                ax=ax, color='0.85', edgecolor='none')
            uli.geography.load('city').boundary.plot(
                ax=ax, color='0.6', linewidth=0.8)
            uli.geography.load('condesa_fraccionamiento').plot(
                ax=ax, color='crimson')
            ax.set_title('Study extent, with the Condesa new '
                         'development (red)')
            ax.set_axis_off()
            """
        ),
        markdown(
            """
            Condesa is the project focus area: platted and roaded, but
            barely built and almost unpopulated in every available
            dataset. Census geography covers only 44% of it. That is
            why the reporting geographies include Condesa-specific
            layers, and why the validator insists your indicator
            reaches them.

            ---

            ## Where everything is

            | | |
            |---|---|
            | Worked examples | [`00b_cookbook.ipynb`](00b_cookbook.ipynb) |
            | How to do the job well | [`docs/analyst_guide.md`](../docs/analyst_guide.md) |
            | What you were assigned | [`indicator_register.csv`](../indicator_register.csv) |
            | Exact output specification | [`schema/ULI_output_schema.md`](../schema/ULI_output_schema.md) |
            | How the work is divided | [`DISTRIBUTED_CALCULATION_PLAN.md`](../DISTRIBUTED_CALCULATION_PLAN.md) |
            | Why it is arranged that way | [`DECISIONS.md`](../DECISIONS.md) |
            """
        ),
    ]
    return notebook(cells, 'ULI start here')



DEMO = """
    import os
    import sys

    sys.path.insert(0, os.path.abspath('..'))

    import geopandas as gpd
    import matplotlib.pyplot as plt
    import pandas as pd

    import uli

    DEMO = os.path.join('..', 'data', 'demo')
    GPKG = os.path.join(DEMO, 'demo.gpkg')

    ANALYST_DETAILS = {'name': 'Cookbook demo', 'email': None,
                       'institution': None}

    print('uli', uli.SCHEMA_VERSION)
    print('reference geographies:', uli.geography.available())
"""


def _recipe(number, title, when, used_by, cell, note=None):
    """One cookbook entry: what it is for, the code, the catch."""
    cells = [
        markdown(
            f"""
            ---
            ## Recipe {number} — {title}

            **Use this when:** {when}

            **Indicators like:** {used_by}
            """
        ),
        code(cell),
    ]
    if note:
        cells.append(markdown(f'**Watch out:** {note}'))
    return cells


def cookbook_notebook():
    """Worked examples of every calculation shape, on real data."""
    cells = [
        markdown(
            f"""
            # Cookbook — worked examples

            Eight recipes covering the shapes almost every ULI
            indicator takes. Each one runs as-is on the small demo
            dataset in `data/demo/`, so you can execute this whole
            notebook now, before you have any data of your own.

            **You do not need to read this end to end.** Find the
            recipe that matches your data — points, polygons, lines,
            a raster, a table — copy it, and change the inputs.

            | Your data looks like | Recipe |
            |---|---|
            | Points (shops, clinics, bus stops) | 1 (how many), 2 (how far) |
            | Polygons (parks, flood zones, land use) | 3 (how much cover), 4 (which class) |
            | Lines (streets, cycle lanes) | 5 |
            | A raster (NDVI, temperature, pollution) | 6 |
            | A table of values per AGEB or manzana | 7 |
            | One number for the whole city | 8 |

            After the recipes, section 9 shows the four steps that are
            **the same for every indicator**, and section 10 walks one
            indicator all the way to a delivered file.

            Schema version {vocab.SCHEMA_VERSION}.
            """
        ),
        markdown(
            """
            ## The demo data

            Real Mexicali layers, cut down so they are quick and
            committed to the repository — see
            [`data/demo/README.md`](../data/demo/README.md) for
            provenance. **They are for learning the tooling, not for
            producing indicator values.** One column
            (`has_sidewalk_FABRICATED`) is invented outright.
            """
        ),
        code(DEMO),
        code(
            """
            # What is in the demo geopackage?
            import pyogrio
            for name, kind in pyogrio.list_layers(GPKG):
                layer = gpd.read_file(GPKG, layer=name)
                print(f'{name:18s} {len(layer):>6,} {kind:12s} '
                      f'{[c for c in layer.columns if c != "geometry"]}')
            """
        ),
        markdown(
            """
            ### The one thing to understand first

            Every recipe produces the **same simple thing**: a table
            with two columns, `geo_id` and `value` — one row per unit
            of whichever geography you computed on.

            ```
              geo_id              value
              CONDESA_F001        3.5
              CONDESA_F002        0.0
              ...
            ```

            That is all. Everything after that — the other
            geographies, the validation, the file layout — is done for
            you by three function calls (section 9).
            """
        ),
    ]

    cells += _recipe(
        1,
        'Points → how many, or how dense',
        'you have point locations and want a count, a count per km², '
        'or a count per 1,000 people.',
        'access to shops, clinics, bus stops, parks; destination '
        'counts; incident counts.',
        """
        destinations = gpd.read_file(GPKG, layer='destinations')
        shops = destinations[destinations['category'] == 'convenience']
        print(f'{len(shops)} convenience stores')

        # Three ways to count them.  Pick the one your measure needs.
        raw = uli.count_features(shops, 'ageb')
        density = uli.count_features(shops, 'ageb', per='sqkm')
        per_capita = uli.count_features(shops, 'ageb', per='1000_persons')

        pd.DataFrame({
            'geo_id': raw['geo_id'],
            'count': raw['value'],
            'per_sqkm': density['value'].round(2),
            'per_1000_people': per_capita['value'].round(2),
        }).sort_values('count', ascending=False).head()
        """,
        'a count per 1,000 people is `NaN` where nobody lives — that '
        'is deliberate, not a bug. Dividing by zero population would '
        'give infinity, and the schema forbids it.',
    )

    cells += _recipe(
        2,
        'Points → how far away',
        'you want the distance to the closest one.',
        'the `proximity` lens on any "access to X" indicator.',
        """
        markets = destinations[
            destinations['category'] == 'fresh_food_market']

        near = uli.distance_to_nearest(markets, 'grid_100m', cap=3000)
        near['value'].describe().round(0)
        """,
        'this is **straight-line** distance, not walking distance '
        'along streets. Real walking distance is longer, and the '
        'difference is not constant. Say which you used in the '
        'measure description. (WP01 uses network distance from the '
        'GHSCI pipeline.)',
    )

    cells += _recipe(
        3,
        'Polygons → how much of the unit they cover',
        'you want a percentage of area: tree canopy, flood extent, '
        'park cover, built-up land.',
        'vegetation percent, flooding, residential area, public open '
        'space coverage.',
        """
        open_space = gpd.read_file(GPKG, layer='open_space')

        cover = uli.areal_share(open_space, 'ageb', as_percentage=True)
        print(cover['value'].describe().round(1))

        # A map is the fastest way to see whether it is plausible.
        ax = uli.geography.load('ageb').merge(cover, on='geo_id').plot(
            column='value', legend=True, figsize=(9, 5),
            legend_kwds={'label': '% of AGEB area as public open space'})
        ax.set_axis_off()
        """,
        'overlapping polygons are dissolved first, so a park counted '
        'twice in your source will not be counted twice here.',
    )

    cells += _recipe(
        4,
        'Polygons → which class dominates',
        'your polygons carry a category rather than a quantity.',
        'land use type, climate zone, hazard category.',
        """
        land = gpd.read_file(GPKG, layer='land_classes')
        print(land['land_class'].tolist())

        classes = uli.dominant_class(land, 'condesa_fraccionamiento',
                                     'land_class')
        print(classes['value'].value_counts(dropna=False))
        """,
        'the result is a **label**, not a number, so it cannot go '
        'into the index as-is. Usually you want a share instead — '
        '"percent residential" — which is Recipe 3 applied to one '
        'filtered class. Note too that 7 of the 40 fraccionamientos '
        'come back empty: the census layer does not cover them.',
    )

    cells += _recipe(
        5,
        'Lines → how much of the network has something',
        'your data is an attribute of street segments and you want '
        'the share of street length that has it.',
        'sidewalk availability, street lighting, cycling '
        'infrastructure, level of traffic stress.',
        """
        streets = gpd.read_file(GPKG, layer='streets_condesa')
        print(streets['highway'].value_counts().head())

        # NOTE: has_sidewalk_FABRICATED is invented demo data.
        share = uli.network_share(
            streets, 'condesa_fraccionamiento',
            attribute='has_sidewalk_FABRICATED')
        share['value'].describe().round(2)
        """,
        'segments are cut at unit boundaries, so a long road passing '
        'through three units is shared between them by length. Units '
        'with no streets at all return `NaN`, not zero.',
    )

    cells += _recipe(
        6,
        'A raster → summarise it within each unit',
        'you have a continuous surface from satellite imagery or a '
        'model.',
        'NDVI, land surface temperature, air pollutant '
        'concentrations, urban heat.',
        """
        RASTER = os.path.join(DEMO, 'demo_population_100m.tif')

        mean_value = uli.zonal_statistic(RASTER, 'ageb', 'mean')
        max_value = uli.zonal_statistic(RASTER, 'ageb', 'max')

        pd.DataFrame({
            'geo_id': mean_value['geo_id'],
            'mean': mean_value['value'].round(1),
            'max': max_value['value'].round(1),
        }).head()
        """,
        'this reads the raster once per unit, so it is slow on the '
        '22,355 cells of `grid_100m`. Test on `ageb` first. Also '
        'check the raster nodata value is being honoured — a nodata '
        'of -9999 averaged into your mean is a silent disaster.',
    )

    cells += _recipe(
        7,
        'A table you already have per unit',
        'your values already exist for AGEBs or manzanas — from the '
        'census, or a spreadsheet a colleague sent.',
        'census variables, housing costs, employment, anything '
        'administrative.',
        """
        census = pd.read_csv(
            os.path.join(DEMO, 'demo_ageb_census.csv'),
            dtype={'CVEGEO': str})

        # The only trick: your key must match geo_id exactly.
        # For AGEB and manzana, geo_id IS the INEGI CVEGEO.
        native = census.rename(
            columns={'CVEGEO': 'geo_id', 'pct_65_plus': 'value'}
        )[['geo_id', 'value']]

        known = set(uli.geography.units('ageb')['geo_id'])
        print(f'{native["geo_id"].isin(known).sum()} of {len(native)} '
              'rows matched a reference AGEB')
        native.head()
        """,
        'if very few rows match, it is almost always a string/number '
        'problem — CVEGEO must be read as text or Excel eats the '
        'leading zero. That is why `dtype={"CVEGEO": str}` is there.',
    )

    cells += _recipe(
        8,
        'One number for the whole city',
        'your source only supports a single city-wide figure — a '
        'household survey, one air quality station.',
        'housing affordability from ENIGH/ENVI, city-level survey '
        'measures.',
        """
        native = pd.DataFrame({
            'geo_id': ['MX_Mexicali_2025'],
            'value': [42.0],
        })

        results = uli.harmonise(native, native_scale='city')
        results.groupby(['geo_level', 'aggregation_method']).size()
        """,
        'every finer unit gets the same value, flagged `replicated`. '
        'That is honest and it is fine — but the composite index will '
        'exclude it at fine scales, because a constant tells you '
        'nothing about where in the city is better. Do not try to '
        'make it look more detailed than it is.',
    )

    cells += [
        markdown(
            """
            ---
            # 9. The part that is always the same

            Whichever recipe you used, you now have `native` — a table
            of `geo_id` and `value`. Three calls finish the job.

            ### 9.1 `harmonise` — fill in the other geographies

            You computed at one scale. The project needs five. This
            does it, using the shared crosswalk, and records honestly
            how each value got there.

            ```python
            results = uli.harmonise(native, native_scale='ageb',
                                    method='population_weighted_mean')
            ```

            Which `method`?

            | Your measure is… | Use |
            |---|---|
            | something people experience (access, exposure, comfort) | `population_weighted_mean` |
            | a property of land (cover, temperature, land use) | `area_weighted_mean` |
            | a property of streets | `length_weighted_mean` |
            | a count of things | `sum` |

            ### 9.2 `label` — say which measure this is

            ```python
            results = uli.label(results, meta, 'my_code__quantity')
            ```

            ### 9.3 `check` and `write_indicator` — validate and deliver

            ```python
            print(uli.check(results, meta))
            uli.write_indicator(results, meta)
            ```

            `write_indicator` **refuses to write** if validation
            fails. While you are still working, add
            `allow_failure=True` to save a draft anyway.
            """
        ),
        markdown(
            """
            ---
            # 10. One indicator, all the way through

            Public open space coverage, from raw polygons to a
            validated deliverable. This is the whole job.
            """
        ),
        code(
            """
            # STEP 1 — documentation, pre-filled from the workbook.
            meta = uli.metadata_stub(187, analyst=ANALYST_DETAILS)

            print('indicator:', meta['indicator']['name_en'])
            print('adapted from:', meta['indicator']['adapted_from'][:90])
            print()
            print('still to fill in:')
            for path in uli.todos(meta)[:8]:
                print('  ', path)
            """
        ),
        code(
            """
            # STEP 2 — the calculation (Recipe 3).
            open_space = gpd.read_file(GPKG, layer='open_space')
            native = uli.areal_share(open_space, 'grid_100m',
                                     as_percentage=True)
            native['value'].describe().round(2)
            """
        ),
        code(
            """
            # STEP 3 — every reporting geography, from that one result.
            results = uli.harmonise(
                native,
                native_scale='grid_100m',
                method='area_weighted_mean',   # land cover, not people
            )
            results.groupby(['geo_level', 'aggregation_method']).agg(
                units=('value', 'size'), with_value=('value', 'count'))
            """
        ),
        code(
            """
            # STEP 4 — describe the measure, then label the rows.
            measure = meta['measures'][0]
            measure.update(
                id='access_to_public_open_space__density_percent_cover',
                name_en='Public open space, percent of area',
                description=(
                    'Share of each unit covered by public open space '
                    'polygons, as a percentage of unit area.'),
                unit='percent',
                value_type='percentage',
                direction='higher_is_better',
                denominator_type='area_sqkm',
                native_scale='grid_100m',
                aggregation_method='area_weighted_mean',
            )
            meta['measures'] = [measure]

            results = uli.label(results, meta, measure['id'])
            results.head(3)
            """
        ),
        code(
            """
            # STEP 5 — validate.  It will fail, and it should: the
            # health evidence is still a TODO, and that is the part
            # only you can do.
            print(uli.check(results, meta))
            """
        ),
        markdown(
            """
            Read that report from the bottom. The `[ERROR]` lines are
            what stops delivery; `[WARN]` lines are worth reading but
            will not block you.

            The outstanding errors here are the documentation the
            project asks of you — an independent health citation, a
            named pathway, documented data sources. Fill those in (see
            the [analyst guide](../docs/analyst_guide.md) §2) and the
            same call passes.
            """
        ),
        code(
            """
            # STEP 6 — deliver.  Uncomment once validation passes.
            # uli.write_indicator(results, meta)
            #
            # Writes three files under
            #   outputs/<work_package>/<indicator_code>/
            # and prints the validation report alongside them.
            """
        ),
        markdown(
            """
            ---
            # 11. When something goes wrong

            | Message | What it means | Fix |
            |---|---|---|
            | `FileNotFoundError: Reference geographies not found` | `geography/` is missing or you are running from the wrong folder | run the notebook from `notebooks/`; check `uli.geography.available()` |
            | `'x' is not a reporting geography` | a typo in a level name | one of `city`, `ageb`, `grid_1000m`, `condesa_fraccionamiento`, `grid_100m`, `manzana`, `condesa_lote` |
            | `... is finer than ...; use method='replicated'` | you asked to aggregate *down* | you cannot invent detail; let `harmonise` handle it |
            | `measure id ... must start with ...` | `measure_id` does not match `indicator_code` | use `<indicator_code>__<lens>` |
            | `N metadata fields still contain a TODO` | the stub is not filled in | `uli.todos(meta)` lists exactly which |
            | `only N of 40 Condesa fraccionamientos have a value` | your native scale does not reach Condesa | compute on `grid_100m` if you can |
            | Values all `NaN` after a merge | join keys do not match | check `dtype={'CVEGEO': str}` and compare a few ids by eye |
            | Everything is zero | usually a CRS mismatch | all project data is EPSG:6366; the helpers reproject for you, so check your **input** |

            Still stuck? Bring it to the group with the error message
            and the cell that produced it. A question asked early is
            cheaper than a week of quiet struggle.
            """
        ),
    ]
    return notebook(cells, 'ULI cookbook')

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

def package_notebook(package, records, reg, articles=None):
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
        markdown(BRIEFING),
        markdown(
            """
            ---
            ## Setup
            """
        ),
        # SETUP is indented four spaces in its own literal, so the
        # appended lines must match or textwrap.dedent leaves them
        # over-indented and the cell will not compile.
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
            cells += indicator_cells(record, articles)

    if package.get('measure_families'):
        cells.append(markdown(FAMILIES))
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
    articles = register.load_articles()
    packages = register.load_work_packages()
    grouped = register.by_work_package(reg)

    print('Building notebooks ...')
    write(
        os.path.join(NOTEBOOK_DIR, '00_start_here.ipynb'),
        overview_notebook(reg, packages),
        args.force,
    )
    write(
        os.path.join(NOTEBOOK_DIR, '00b_cookbook.ipynb'),
        cookbook_notebook(),
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
            package_notebook(package, records, reg, articles),
            args.force,
        )

    import subprocess

    check = subprocess.run(
        [sys.executable, os.path.join(HERE, 'check_notebooks.py')],
        capture_output=True,
        text=True,
    )
    print(check.stdout.strip().splitlines()[-1] if check.stdout else '')
    if check.returncode:
        print(check.stdout)

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
    audit = register.citation_audit(reg, articles)
    unresolved = audit['unknown_article_numbers'].notna().sum()
    disagree = (audit['names_a_cited_author'] == False).sum()  # noqa: E712
    audit_path = os.path.join(PROJECT_DIR, 'citation_audit.csv')
    try:
        audit.to_csv(audit_path, index=False, encoding='utf-8-sig')
        print(
            f'\nCitation audit written to {os.path.basename(audit_path)}: '
            f'{disagree} indicators whose free-text citation names no '
            f'author of the article they cite; {unresolved} citing an '
            'article number absent from the article list'
        )
    except PermissionError:
        print('\nCould not write citation_audit.csv (file locked).')

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
