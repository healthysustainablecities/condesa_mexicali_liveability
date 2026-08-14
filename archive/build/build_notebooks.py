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
def _dedent(text):
    """Strip the template's own indentation from a cell body.

    ``textwrap.dedent`` removes only the whitespace *common to every
    line*, which is the wrong rule here: these templates interpolate
    multi-line values (a table of work packages, a list of indicators)
    that are built at zero indent.  One such line drops the common
    prefix to nothing, dedent becomes a no-op, and every other line
    keeps its twelve spaces -- which Markdown then renders as a code
    block.

    So take the indent of the first non-blank line as the template's
    own, and strip exactly that from the lines that carry it. Lines
    already at zero indent are left alone, and lines indented further
    (nested lists, continuations) keep the difference.
    """
    lines = text.split('\n')
    first = next((line for line in lines if line.strip()), '')
    prefix = first[: len(first) - len(first.lstrip())]
    if not prefix:
        return text
    return '\n'.join(
        line[len(prefix):] if line.startswith(prefix) else line
        for line in lines
    )


def markdown(text):
    return {
        'cell_type': 'markdown',
        'metadata': {},
        'source': _lines(_dedent(text).strip('\n')),
    }


def code(text):
    return {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': _lines(_dedent(text).strip('\n')),
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

    Work in this order. Steps 1 and 2 shape everything after
    them, so they are worth doing before opening any data.

    | | Step | Where to look |
    |---|---|---|
    | 1 | Write the causal pathway: *X changes a mechanism, which changes a behaviour or exposure, which affects health* | [guide §2.1](../docs/analyst_guide.md) |
    | 2 | Find **independent health evidence** for that pathway, with an effect size | [guide §2.2](../docs/analyst_guide.md) |
    | 3 | Find the data. Record citation, URL, date retrieved, licence | [guide §3](../docs/analyst_guide.md) |
    | 4 | Compute it — pick the matching recipe | [cookbook](00b_cookbook.ipynb) |
    | 5 | `harmonise` → `label` → `check` → `write_indicator` | [cookbook §9](00b_cookbook.ipynb) |
    | 6 | Look at a map of your result before calling it done | [guide §6](../docs/analyst_guide.md) |

    Three things worth knowing now:

    - **The evidence matters as much as the calculation.** The
      article an indicator was adapted from shows it has been *used*,
      not that it affects health. Supplying that link is a substantive
      part of the work.
    - **Deliver natural units.** No normalising, no reverse-coding —
      set `direction` instead. The index does that once, centrally.
    - **Cover Condesa.** Compute on `grid_100m` where your data allow
      it: that reaches all 40 fraccionamientos of the development,
      where `manzana` reaches only 33. The validator treats poor
      Condesa coverage as an error.

    New to this? Part 1 of [`00b_cookbook.ipynb`](00b_cookbook.ipynb)
    works one indicator through the whole process, on data already in
    the repository.
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
    # Row 0 is the composite index itself rather than an indicator,
    # and excluded indicators are out of scope.
    in_scope = (
        len(reg)
        - int((reg['indicator_id'] == 0).sum())
        - int(counts.get(register.EXCLUDED, 0))
    )
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
            **{in_scope}** that are plausibly relevant to health in
            Mexicali and feasible with available data. Calculation is
            split across work packages:

            | | Work package | Lead | Indicators |
            |---|---|---|---|
            {rows}

            ---

            ## Getting started

            1. **Run the setup check below.** It reports whether the
               reference geographies and the indicator register are
               readable.
            2. **Work through Part 1 of
               [`00b_cookbook.ipynb`](00b_cookbook.ipynb)**, which
               takes one indicator from the workbook to a finished
               deliverable using data already in this repository.
            3. **Open your work package notebook** (`01_` to `08_`)
               and read the brief for your first indicator.
            4. **Read [the analyst guide](../docs/analyst_guide.md)**
               sections 2 and 5. The rest is reference.

            The schema, the plan and the decisions record are there
            when you need them; you do not need them to start.

            ---

            ## What you deliver

            Two files per indicator, written for you by one function
            call:

            ```
            outputs/<work_package>/<indicator_code>/
                <indicator_code>_results.csv     # the numbers
                <indicator_code>_metadata.yml    # why, from what, how
            ```

            The metadata is used, not filed. The index needs
            `direction` to know whether high is good or bad, and
            Reimagina Urbana needs the licence to know whether a layer
            can be published.
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

    # Normally your own details; this notebook is a demonstration.
    ANALYST_DETAILS = {
        'name': 'Cookbook demo',
        'email': None,
        'institution': None,
    }

    print('uli', uli.SCHEMA_VERSION)
    print('reference geographies:', uli.geography.available())
"""


def _recipe(number, title, when, used_by, cell, note=None):
    """One recipe: what it is for, the code, the catch."""
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
    """One indicator worked end to end, then the recipes."""
    cells = [
        markdown(
            f"""
            # Cookbook

            Part 1 takes a single indicator from a row in the workbook
            to a finished, validated deliverable — including the
            evidence, the data licensing, the map you use to check it,
            and how you hand it back.

            Part 2 is a set of recipes for the other shapes your data
            might take. Once you have been through Part 1, a recipe is
            just a replacement for one step.

            Everything runs on the demo data in `data/demo/`, so you
            can execute this notebook now, before you have data of your
            own.

            | | |
            |---|---|
            | **Part 1** | One indicator, start to finish |
            | **Part 2** | Recipes: points, polygons, lines, rasters, tables |
            | **Part 3** | Reference: aggregation methods, error messages |

            Schema version {vocab.SCHEMA_VERSION}.
            """
        ),
        markdown(
            """
            ## The demo data

            Real Mexicali layers, cut down so they are quick and small
            enough to commit — see
            [`data/demo/README.md`](../data/demo/README.md) for what
            each one is and where it came from. They are here to
            demonstrate the tooling; they are not a basis for indicator
            values, and one column (`has_sidewalk_FABRICATED`) is
            invented.
            """
        ),
        code(DEMO),
        code(
            """
            import pyogrio
            for name, kind in pyogrio.list_layers(GPKG):
                layer = gpd.read_file(GPKG, layer=name)
                print(f'{name:18s} {len(layer):>6,} {kind:12s} '
                      f'{[c for c in layer.columns if c != "geometry"]}')
            """
        ),
    ]

    cells += _part_one()
    cells += _part_two()
    cells += _part_three()
    return notebook(cells, 'ULI cookbook')


def _part_one():
    """The full process, on one real indicator."""
    return [
        markdown(
            """
            ---
            ---
            # Part 1 — One indicator, start to finish

            The indicator: **#187, access to public open space**,
            measured as the share of each area that is public open
            space.

            Eleven steps. Steps 1–4 are desk work and take longer than
            the code.
            """
        ),
        markdown(
            """
            ## 1. Read what the team already recorded

            Your work package notebook has a brief for each indicator,
            and `uli.metadata_stub()` pre-fills a metadata document
            from the same source. Start there rather than from a blank
            page.
            """
        ),
        code(
            """
            meta = uli.metadata_stub(187, analyst=ANALYST_DETAILS)

            print('indicator :', meta['indicator']['name_en'])
            print('domain    :', meta['indicator']['domains'])
            print('lenses    :', [m['lens'] for m in meta['measures']])
            print()
            print('adapted from:')
            print(' ', meta['indicator']['adapted_from'][:140])
            print()
            print('draft rationale from the workbook:')
            print(' ', meta['rationale']['statement'][:200])
            """
        ),
        markdown(
            """
            The `adapted_from` reference is **provenance, not
            evidence**: it records where the indicator idea came from,
            not that it affects health. Supplying that link is step 2,
            and it is the part of the job only you can do.

            ## 2. Write the causal pathway

            Before searching for anything, finish this sentence:

            > *[what I measure]* changes *[a mechanism]*, which changes
            > *[a behaviour or exposure]*, which affects *[a health
            > outcome]*.

            For this indicator:

            > **Public open space near where people live** provides
            > somewhere to walk, exercise and meet others, and offers
            > shade and cooler surfaces, which increases recreational
            > physical activity and social contact and reduces heat
            > exposure, which is associated with better mental health,
            > lower cardiovascular risk and lower heat-related illness.

            That sentence determines everything downstream: which
            evidence is relevant, which threshold to use, and whether
            the measure you are about to compute is the right one. If
            it is hard to write, that usually means the indicator needs
            discussion with the group rather than more GIS.

            The mechanisms are recorded as `health_pathways`, using the
            controlled list:
            """
        ),
        code(
            """
            for key, description in uli.vocab.HEALTH_PATHWAYS.items():
                print(f'{key:32s} {description}')
            """
        ),
        markdown(
            """
            ## 3. Find evidence for that pathway

            You need at least one citation, **independent of the
            article the indicator was adapted from**, showing a
            meaningful health or wellbeing benefit.

            Where to look: PubMed, Scopus, Google Scholar, WHO
            publications, *Environment International*, *Health &
            Place*, *Journal of Transport & Health*. Prefer
            meta-analyses and systematic reviews, then reputable
            guidance, then cohort studies.

            Search the **exposure and the outcome**, not the indicator
            name — for example
            `"green space" AND (mortality OR "mental health") AND
            (review OR meta-analysis)`.

            Record what the source actually says, including the effect
            size and its uncertainty where one is given. Some sources,
            including narrative reviews and guidance documents, do not
            report a pooled estimate; say so rather than inventing one.

            > The reference below is real and is used to show the
            > shape of the record. **Read your own sources and record
            > what they say** — do not copy this one across.
            """
        ),
        code(
            """
            meta['rationale']['statement'] = (
                'Public open space within walking distance gives '
                'residents somewhere to walk, exercise and meet '
                'others, and provides shade and cooler surfaces in a '
                'city where summer heat limits time outdoors. Access '
                'is associated with higher recreational physical '
                'activity, more social contact and better mental '
                'health. In Mexicali the benefit is likely '
                'conditional on shade and water provision, and on the '
                'time of day the space can be used; households '
                'without air conditioning or a car are least able to '
                'substitute other options.'
            )

            meta['rationale']['health_pathways'] = [
                'physical_activity_recreation',
                'social_interaction',
                'heat_exposure',
                'restoration_and_mental_health',
            ]

            meta['rationale']['arid_context'] = (
                'Most green space and health evidence comes from '
                'temperate cities. In Mexicali, summer maxima above '
                '45 C plausibly make shade, water and opening hours '
                'more binding than distance. Read alongside the WP02 '
                'thermal comfort outputs; unshaded open space may '
                'deliver much less benefit than the same area of '
                'shaded space.'
            )

            meta['rationale']['evidence'] = [
                {
                    'claim': (
                        'Access to urban green space is associated '
                        'with improved mental health and wellbeing, '
                        'reduced cardiovascular morbidity and '
                        'increased levels of physical activity.'
                    ),
                    'citation': (
                        'World Health Organization Regional Office '
                        'for Europe (2016). Urban green spaces and '
                        'health: a review of evidence. Copenhagen: '
                        'WHO Regional Office for Europe.'
                    ),
                    'doi': None,
                    'url': ('https://www.who.int/europe/publications/'
                            'i/item/WHO-EURO-2016-3352-43111-60341'),
                    'evidence_type': 'expert_guidance',
                    'population': (
                        'General urban populations, predominantly '
                        'European studies.'
                    ),
                    'exposure': 'Access to urban green space',
                    'outcome': (
                        'Mental health, cardiovascular morbidity, '
                        'physical activity'
                    ),
                    'effect': (
                        'Narrative review; consistent direction of '
                        'association reported across studies, no '
                        'pooled effect estimate given.'
                    ),
                    'threshold_support': (
                        'The review discusses accessibility within '
                        'walking distance rather than endorsing a '
                        'single distance; the project default of 500 '
                        'm is used here and should be revisited '
                        'against Mexicali-specific evidence.'
                    ),
                    'notes': (
                        'Used to demonstrate the record. Supplement '
                        'with a quantitative review before '
                        'publication.'
                    ),
                },
            ]

            print(len(meta['rationale']['evidence']), 'evidence entry')
            """
        ),
        markdown(
            """
            ## 4. Find the data, and record it as you go

            Record the source **when you download it**, not months
            later when you have forgotten the version and the date.

            Five things are required, and the validator will ask for
            them: citation, URL, date retrieved, licence, and whether
            the source covers Condesa. `redistributable` matters
            because Reimagina Urbana cannot publish a layer whose
            licence forbids it.

            Put the raw file in `data/raw/<your_work_package>/` and do
            not edit it by hand — every change should happen in code,
            so it can be repeated. Raw data is **not** committed: it
            can be large, and licences often do not allow
            redistribution.

            Likely sources for this project: INEGI (censo, ENIGH,
            ENVI, DENUE, marco geoestadístico), the IMIP Mexicali
            geovisor, municipal open data, SEMARNAT and the Mexicali
            air quality network, CONAGUA, OpenStreetMap, Sentinel-2
            and Landsat, GHSL, WorldPop.
            """
        ),
        code(
            """
            meta['data_sources'] = [
                {
                    'name': 'Public open space, Mexicali',
                    'custodian': 'OpenStreetMap contributors',
                    'citation': (
                        'OpenStreetMap contributors (2026). Geofabrik '
                        'Mexico extract, 10 April 2026. Public open '
                        'space derived using the GHSCI open space '
                        'method.'
                    ),
                    'url': 'https://download.geofabrik.de/',
                    'date_retrieved': '2026-04-10',
                    'licence': 'ODbL-1.0',
                    'licence_url': ('https://opendatacommons.org/'
                                    'licenses/odbl/'),
                    'redistributable': True,
                    'spatial_resolution': 'vector polygons',
                    'temporal_coverage': '2026',
                    'condesa_coverage': 'full',
                    'notes': (
                        'Volunteered data. Completeness varies and is '
                        'likely lower in recently developed areas, '
                        'which matters for Condesa.'
                    ),
                },
            ]

            # What is still outstanding at this point?
            for path in uli.todos(meta):
                print(path)
            """
        ),
        markdown(
            """
            ## 5. Compute the indicator

            One call. The helper is chosen by the shape of the data —
            polygons whose coverage you want, so `areal_share` (Part 2,
            Recipe 3).

            Compute at the finest scale your data genuinely support.
            Here that is the 100 m grid, which also means the result
            reaches all 40 Condesa fraccionamientos rather than the 33
            a manzana-based calculation would reach.
            """
        ),
        code(
            """
            open_space = gpd.read_file(GPKG, layer='open_space')
            print(f'{len(open_space)} open space polygons, '
                  f'{open_space.geometry.area.sum() / 1e6:.1f} km2 total')

            native = uli.areal_share(open_space, 'grid_100m',
                                     as_percentage=True)
            print()
            print(native.head())
            print()
            print(native['value'].describe().round(2))
            """
        ),
        markdown(
            """
            `native` is the whole output of the calculation: one row
            per 100 m cell, `geo_id` and `value`. Everything from here
            is bookkeeping.

            ## 6. Record how you did it

            The method summary should let someone else reproduce the
            number from the sources you documented. Write it now, while
            you remember the details.
            """
        ),
        code(
            """
            meta['method']['summary'] = (
                'Public open space polygons were dissolved to remove '
                'overlaps, intersected with each 100 m grid cell, and '
                'the intersecting area divided by the cell area to '
                'give the percentage of each cell that is public open '
                'space. Cell values were aggregated to coarser '
                'reporting geographies as an area-weighted mean, '
                'since open space coverage is a property of land '
                'rather than of people.'
            )
            meta['method']['software'] = ['python', 'geopandas', 'uli']
            meta['method']['notebook'] = 'notebooks/00b_cookbook.ipynb'
            meta['method']['assumptions'] = [
                'All mapped public open space is publicly accessible '
                'in practice, which OpenStreetMap does not verify.',
            ]
            meta['method']['limitations'] = [
                'Area of open space says nothing about its quality, '
                'shade, water provision or opening hours, which in an '
                'arid city plausibly matter more than area.',
            ]
            meta['method']['condesa_treatment'] = (
                'Computed natively on the 100 m grid, which covers '
                'the full Condesa extent. OpenStreetMap coverage of '
                'the new development is likely incomplete, so a low '
                'value there may reflect mapping rather than absence.'
            )
            meta['indicator']['status'] = 'draft'
            print('recorded')
            """
        ),
        markdown(
            """
            ## 7. Fill in the other geographies

            You computed at one scale; the project reports at five.
            `harmonise` produces them all from your single
            calculation, using the shared crosswalk, and records how
            each value got there.

            `method` describes what the value *is*, which determines
            how it should be combined:

            | Your measure is… | Use |
            |---|---|
            | something people experience (access, exposure, comfort) | `population_weighted_mean` |
            | a property of land (cover, temperature, land use) | `area_weighted_mean` |
            | a property of streets | `length_weighted_mean` |
            | a count of things | `sum` |
            """
        ),
        code(
            """
            results = uli.harmonise(
                native,
                native_scale='grid_100m',
                method='area_weighted_mean',
            )

            results.groupby(['geo_level', 'aggregation_method']).agg(
                units=('value', 'size'),
                with_value=('value', 'count'),
                median=('value', 'median'),
            ).round(2)
            """
        ),
        markdown(
            """
            Note `manzana` is marked `replicated`: manzanas are
            smaller than 100 m cells, so those values carry no
            variation at that scale. That is recorded honestly rather
            than hidden, and the index step knows to discount it.

            ## 8. Describe the measure and label the rows

            A **measure** is one specific way of measuring the
            indicator. This indicator could be measured several ways —
            distance to the nearest open space, count within 500 m,
            percentage cover. Here there is one, so the stub's other
            lenses are dropped.
            """
        ),
        code(
            """
            measure = meta['measures'][0]
            measure.update(
                id='access_to_public_open_space__density_percent_cover',
                lens='density',
                name_en='Public open space, percentage of area',
                name_es='Espacio público abierto, porcentaje del área',
                description=(
                    'Percentage of the unit covered by public open '
                    'space polygons.'),
                unit='percent',
                value_type='percentage',
                direction='higher_is_better',
                denominator_type='area_sqkm',
                coverage_basis='area',
                temporal_basis='point_in_time',
                native_scale='grid_100m',
                aggregation_method='area_weighted_mean',
                include_in_index=True,
                index_notes=(
                    'Highly skewed: most units have no open space at '
                    'all. Consider a transform or a threshold form.'),
            )
            meta['measures'] = [measure]

            results = uli.label(results, meta, measure['id'])
            results.head(3)
            """
        ),
        markdown(
            """
            Those twelve columns are the delivery format, and they are
            the same for every indicator in the project. `coverage`,
            `quality_flag` and `native_scale` are what let someone
            else judge how much to trust a given row.

            ## 9. Map it before you believe it

            The fastest check on a spatial indicator is to look at it.
            """
        ),
        code(
            """
            grid = uli.geography.load('grid_100m').merge(
                results.query("geo_level == 'grid_100m'"),
                on='geo_id', how='left')

            fig, axes = plt.subplots(1, 2, figsize=(15, 5))

            grid.plot(column='value', ax=axes[0], legend=True,
                      vmax=grid['value'].quantile(0.99),
                      missing_kwds={'color': 'lightgrey'})
            uli.geography.load('condesa_fraccionamiento').boundary.plot(
                ax=axes[0], color='crimson', linewidth=0.8)
            axes[0].set_title('% public open space, 100 m grid '
                              '(Condesa outlined)')
            axes[0].set_axis_off()

            ageb = uli.geography.load('ageb').merge(
                results.query("geo_level == 'ageb'"),
                on='geo_id', how='left')
            ageb.plot(column='value', ax=axes[1], legend=True,
                      missing_kwds={'color': 'lightgrey'})
            axes[1].set_title('the same values aggregated to AGEB')
            axes[1].set_axis_off()
            """
        ),
        markdown(
            """
            Questions worth asking of that map:

            - Are the high values where you would expect parks to be?
            - Is anywhere suspiciously blank — and is that a real
              absence, or missing data?
            - Does Condesa look plausible? Here it is largely empty,
              which is consistent with a new development, but could
              equally be incomplete OpenStreetMap coverage. That
              ambiguity belongs in `method.condesa_treatment`, which is
              why step 6 said it.
            - Do the two panels tell the same story? If aggregating
              changes the pattern, check the method.

            ## 10. Validate

            `uli.check()` runs the schema, consistency and
            project-requirement checks together.
            """
        ),
        code(
            """
            report = uli.check(results, meta)
            print(report)
            """
        ),
        markdown(
            """
            `[ERROR]` lines block delivery; `[WARN]` lines are worth
            reading but will not stop you. The replication warning here
            is expected and correct.

            ## 11. Deliver, and hand it back

            `write_indicator` writes three files and refuses to write
            at all if validation failed. While you are still working,
            `allow_failure=True` saves a draft anyway.
            """
        ),
        code(
            """
            # This demonstration writes to a temporary folder so it
            # does not leave a stray deliverable in outputs/.  Your own
            # work omits output_dir, and the files land under
            #   outputs/<work_package>/<indicator_code>/
            import tempfile
            demo_output = tempfile.mkdtemp()

            written = uli.write_indicator(results, meta,
                                          output_dir=demo_output)

            print()
            print('would normally be written to:')
            print('  outputs/' + meta['indicator']['work_package']
                  + '/' + meta['indicator']['code'] + '/')
            print()
            for key in ('results', 'metadata', 'validation'):
                path = written[key]
                print(f'{key:11s} {os.path.basename(path):55s} '
                      f'{os.path.getsize(path) / 1024:>8,.0f} KB')
            """
        ),
        code(
            """
            # What the metadata document looks like on disk:
            with open(written['metadata'], encoding='utf-8') as f:
                print(''.join(f.readlines()[:28]))
            """
        ),
        markdown(
            """
            (This indicator belongs to WP01, so the demo reports that
            path. Yours will name your own work package.)

            ### Handing it back

            Results are gzipped, so one delivery is about 0.3 MB
            rather than 5 MB, and the whole indicator set is around
            26 MB — small enough to live in the repository:

            ```bash
            git checkout -b wp04-open-space          # your package
            git add outputs/WP04_greenness_and_land_cover/
            git add notebooks/04_greenness_and_land_cover.ipynb
            git commit -m "WP04: public open space coverage"
            git push -u origin wp04-open-space
            ```

            Then open a pull request. That gives the work a review
            point and a record of what changed, which email does not.

            **Commit:** the three files in `outputs/`, and your
            notebook with its cells run.

            **Do not commit:** anything in `data/raw/`. Source data is
            often large and frequently cannot be redistributed; the
            metadata records where it came from so someone else can
            fetch it.

            If you cannot use git, send the `outputs/<indicator>/`
            folder and your notebook to the project lead, who will
            commit them.

            ---

            That is the whole process. Part 2 replaces step 5 —
            everything before and after it is the same every time.
            """
        ),
    ]


def _part_two():
    """Recipes for the other data shapes."""
    cells = [
        markdown(
            """
            ---
            ---
            # Part 2 — Recipes

            Eight ways of getting from source data to `native`, the
            two-column table that step 5 produced. Find the one that
            matches your data.

            | Your data looks like | Recipe |
            |---|---|
            | Points (shops, clinics, bus stops) | 1 how many · 2 how far |
            | Polygons (parks, flood zones, land use) | 3 how much cover · 4 which class |
            | Lines (streets, cycle lanes) | 5 |
            | A raster (NDVI, temperature, pollution) | 6 |
            | A table of values per AGEB or manzana | 7 |
            | One number for the whole city | 8 |

            **Each helper returns a table of `geo_id` and `value`** —
            one measure, one column of numbers. An indicator with
            several measures (a distance *and* a count, say) means
            several calls: compute each, `uli.label()` each with its
            own `measure_id`, and combine them at the end with
            `uli.assemble()`. Recipe 1 shows that.
            """
        ),
    ]

    cells += _recipe(
        1,
        'Points → how many, or how dense',
        'you have point locations and want a count, a count per km², '
        'or a count per 1,000 people.',
        'access to shops, clinics, bus stops; destination counts; '
        'incident counts.',
        """
        destinations = gpd.read_file(GPKG, layer='destinations')
        shops = destinations[destinations['category'] == 'convenience']

        count = uli.count_features(shops, 'ageb')
        print(count.head(3))
        """,
        None,
    )

    cells += [
        markdown(
            """
            The `per` argument changes what is measured, so each is a
            **separate measure** with its own `measure_id`, unit and
            direction — not extra columns on one table.
            """
        ),
        code(
            """
            density = uli.count_features(shops, 'ageb', per='sqkm')
            per_capita = uli.count_features(shops, 'ageb',
                                            per='1000_persons')

            # Three separate two-column tables:
            for name, table in [('count', count), ('per_sqkm', density),
                                ('per_1000_persons', per_capita)]:
                print(f'{name:18s} {list(table.columns)}  '
                      f'median={table["value"].median():.2f}')

            # Deliver several measures for one indicator like this:
            #   a = uli.label(uli.harmonise(count, 'ageb'), meta,
            #                 'my_code__quantity')
            #   b = uli.label(uli.harmonise(density, 'ageb'), meta,
            #                 'my_code__density_per_sqkm')
            #   results = uli.assemble([a, b])
            """
        ),
        markdown(
            '**Watch out:** a count per 1,000 people is empty where '
            'nobody lives. That is deliberate — dividing by zero '
            'population would give infinity, which the schema does not '
            'allow.'
        ),
    ]

    cells += _recipe(
        2,
        'Points → how far away',
        'you want the distance to the closest one.',
        'the `proximity` lens on any "access to X" indicator.',
        """
        markets = destinations[
            destinations['category'] == 'fresh_food_market']

        native = uli.distance_to_nearest(markets, 'grid_100m', cap=3000)
        print(native['value'].describe().round(0))
        """,
        'this is **straight-line** distance, not distance along '
        'streets. Walking distance is longer, and the difference '
        'varies with the street layout. Say which you used in the '
        'measure description. WP01 uses network distance from the '
        'GHSCI pipeline.',
    )

    cells += _recipe(
        3,
        'Polygons → how much of the unit they cover',
        'you want a percentage of area: tree canopy, flood extent, '
        'park cover, built-up land.',
        'vegetation percent, flooding, residential area, public open '
        'space.',
        """
        open_space = gpd.read_file(GPKG, layer='open_space')

        native = uli.areal_share(open_space, 'ageb', as_percentage=True)
        print(native['value'].describe().round(1))
        """,
        'overlapping polygons are dissolved first, so a park mapped '
        'twice in your source is not counted twice.',
    )

    cells += _recipe(
        4,
        'Polygons → which class dominates',
        'your polygons carry a category rather than a quantity.',
        'land use type, climate zone, hazard category.',
        """
        land = gpd.read_file(GPKG, layer='land_classes')
        print(land['land_class'].tolist())
        print()

        native = uli.dominant_class(land, 'condesa_fraccionamiento',
                                    'land_class')
        print(native['value'].value_counts(dropna=False))
        """,
        'the result is a **label**, not a number, so it cannot enter '
        'the index directly — deliver it as an `ordinal` measure with '
        'a documented encoding, or use Recipe 3 on one filtered class '
        'to get "percent residential", which is usually more useful. '
        'Note that 7 of the 40 fraccionamientos come back empty here: '
        'the census layer does not cover them.',
    )

    cells += _recipe(
        5,
        'Lines → how much of the network has something',
        'your data is an attribute of street segments and you want '
        'the share of street length that has it.',
        'sidewalk availability, street lighting, cycling '
        'infrastructure, traffic stress.',
        """
        streets = gpd.read_file(GPKG, layer='streets_condesa')
        print(streets['highway'].value_counts().head())
        print()

        # has_sidewalk_FABRICATED is invented demo data, not a finding.
        native = uli.network_share(
            streets, 'condesa_fraccionamiento',
            attribute='has_sidewalk_FABRICATED')
        print(native['value'].describe().round(2))
        """,
        'segments are cut at unit boundaries, so a road crossing three '
        'units is shared between them by length. Units with no streets '
        'return an empty value rather than zero.',
    )

    cells += _recipe(
        6,
        'A raster → summarise it within each unit',
        'you have a continuous surface from satellite imagery or a '
        'model.',
        'NDVI, land surface temperature, pollutant concentrations, '
        'urban heat.',
        """
        RASTER = os.path.join(DEMO, 'demo_population_100m.tif')

        native = uli.zonal_statistic(RASTER, 'ageb', 'mean')
        print(native['value'].describe().round(1))
        """,
        'this reads the raster once per unit, so it is slow over the '
        '22,355 cells of `grid_100m` — test on `ageb` first. Check '
        'the nodata value is being honoured, too: a nodata of -9999 '
        'averaged into a mean is easy to miss and hard to spot later.',
    )

    cells += _recipe(
        7,
        'A table you already have per unit',
        'your values already exist for AGEBs or manzanas — from the '
        'census, or a spreadsheet from a colleague.',
        'census variables, housing costs, employment, administrative '
        'data.',
        """
        census = pd.read_csv(
            os.path.join(DEMO, 'demo_ageb_census.csv'),
            dtype={'CVEGEO': str})

        # Your key must match geo_id exactly.  For ageb and manzana,
        # geo_id is the INEGI CVEGEO.
        native = census.rename(
            columns={'CVEGEO': 'geo_id', 'pct_65_plus': 'value'}
        )[['geo_id', 'value']]

        known = set(uli.geography.units('ageb')['geo_id'])
        print(f'{native["geo_id"].isin(known).sum()} of {len(native)} '
              'rows matched a reference AGEB')
        """,
        'if few rows match, it is usually the key being read as a '
        'number — CVEGEO has leading zeros, so read it as text with '
        '`dtype={"CVEGEO": str}`.',
    )

    cells += _recipe(
        8,
        'One number for the whole city',
        'your source only supports a single city-wide figure — a '
        'household survey, one monitoring station.',
        'housing affordability from ENIGH/ENVI, city-level survey '
        'measures.',
        """
        native = pd.DataFrame({
            'geo_id': ['MX_Mexicali_2025'],
            'value': [42.0],
        })

        example = uli.harmonise(native, native_scale='city')
        print(example.groupby(['geo_level', 'aggregation_method']).size())
        """,
        'every finer unit gets the same value, flagged `replicated`. '
        'That is the honest representation, and the composite index '
        'excludes such measures at fine scales because a constant '
        'cannot distinguish one part of the city from another.',
    )
    return cells


def _part_three():
    """Reference material."""
    return [
        markdown(
            """
            ---
            ---
            # Part 3 — Reference

            ## The steps that never change

            Whichever recipe produced `native`:

            ```python
            results = uli.harmonise(native, native_scale='grid_100m',
                                    method='area_weighted_mean')
            results = uli.label(results, meta, 'my_code__lens')
            print(uli.check(results, meta))
            uli.write_indicator(results, meta)
            ```

            ## When something goes wrong

            | Message | What it means | What to do |
            |---|---|---|
            | `FileNotFoundError: Reference geographies not found` | `geography/` missing, or the notebook is running from another folder | run from `notebooks/`; check `uli.geography.available()` |
            | `'x' is not a reporting geography` | a typo in a level name | one of `city`, `ageb`, `grid_1000m`, `condesa_fraccionamiento`, `grid_100m`, `manzana`, `condesa_lote` |
            | `... is finer than ...; use method='replicated'` | you asked to aggregate *down* | let `harmonise` decide; it replicates and flags |
            | `measure id ... must start with ...` | `measure_id` does not match `indicator_code` | use `<indicator_code>__<lens>` |
            | `N metadata fields still contain a TODO` | the stub is not filled in | `uli.todos(meta)` lists which |
            | `only N of 40 Condesa fraccionamientos have a value` | your native scale does not reach Condesa | compute on `grid_100m` if the data support it |
            | Values all empty after a merge | join keys do not match | check `dtype={'CVEGEO': str}`, compare a few ids directly |
            | Everything zero or absurd | often a CRS mismatch | project data is EPSG:6366; the helpers reproject inputs, so check the input file's own CRS |

            If none of that fits, bring the error message and the cell
            that produced it to the group.

            ## Where else to look

            | | |
            |---|---|
            | Function names and arguments | [`docs/cheatsheet.md`](../docs/cheatsheet.md) |
            | The reasoning behind the requirements | [`docs/analyst_guide.md`](../docs/analyst_guide.md) |
            | Exact output specification | [`schema/ULI_output_schema.md`](../schema/ULI_output_schema.md) |
            """
        ),
    ]

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
