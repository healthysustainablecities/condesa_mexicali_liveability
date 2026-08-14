"""Pre-fill indicator metadata from the ULI workbook.

An analyst should never start from a blank page, and should never
retype what the workbook already records.  :func:`metadata_stub` copies
across identity, classification, the draft rationale, the source
articles, the candidate data sources and the team's open questions,
then leaves clearly marked ``TODO`` slots for the parts that are
genuinely the analyst's job: the operational definition, the
independent health evidence, and the data source documentation.
"""

import textwrap

from . import register, vocab

TODO = 'TODO'

# The only composites constructed inside a work package: the GHSCI
# walkability index and its components, and the level of traffic
# stress cycling network.  Everything else is delivered as measured,
# and any further compositing happens centrally at the index step.
GHSCI_COMPOSITES = {
    3,  # access to activity centres (daily living amenities)
    62,  # level of cycling traffic stress
    74,  # walkability index
}

# Lens -> (unit, value_type, direction) starting points.  These are
# defaults to be corrected, not decisions.
LENS_DEFAULTS = {
    'proximity': ('m', 'continuous', 'lower_is_better'),
    'accessibility': ('percent', 'percentage', 'higher_is_better'),
    'quantity': ('count', 'count', 'higher_is_better'),
    'density': ('count per km2', 'rate', 'higher_is_better'),
    'diversity': ('dimensionless', 'index', 'higher_is_better'),
    'quality': ('dimensionless', 'index', 'higher_is_better'),
}


def _wrap(text, width=68):
    if not text:
        return None
    return textwrap.fill(' '.join(str(text).split()), width)


def metadata_stub(indicator_id, analyst=None, reg=None):
    """Return a metadata dict pre-filled from the workbook."""
    record = register.get(indicator_id, reg)
    code = record['indicator_code']
    lenses = [
        lens
        for lens in record['lenses']
        if lens in vocab.ANALYST_LENSES
    ] or ['quantity']

    measures = []
    for lens in lenses:
        unit, value_type, direction = LENS_DEFAULTS[lens]
        measures.append(
            {
                'id': f'{code}__{lens}',
                'lens': lens,
                'measure_family': None,
                'temporal_basis': None,
                'name_en': f'{record["indicator"]} ({lens})',
                'name_es': None,
                'description': (
                    f'{TODO}: one or two sentences saying exactly what '
                    'was computed, precisely enough for someone else '
                    'to reproduce it.'
                ),
                'unit': unit,
                'value_type': value_type,
                'direction': direction,
                'denominator_type': (
                    'population' if lens == 'accessibility' else 'none'
                ),
                'coverage_basis': 'population',
                'threshold': None,
                'threshold_justification': None,
                'parameters': {},
                'benchmark': None,
                'native_scale': f'{TODO}: e.g. manzana, grid_100m',
                'aggregation_method': (
                    f'{TODO}: how the native value was carried to '
                    'coarser units'
                ),
                'include_in_index': True,
                'index_notes': None,
            }
        )

    sources = []
    if record.get('potential_data_sources'):
        for line in str(record['potential_data_sources']).splitlines():
            line = line.strip()
            if not line:
                continue
            sources.append(
                {
                    'name': line[:120],
                    'custodian': None,
                    'citation': (
                        f'{TODO}: institution, year, dataset title, '
                        'version'
                    ),
                    'url': None,
                    'date_retrieved': f'{TODO}: YYYY-MM-DD',
                    'licence': 'Unknown - to be confirmed',
                    'licence_url': None,
                    'redistributable': None,
                    'spatial_resolution': None,
                    'temporal_coverage': None,
                    'condesa_coverage': 'unknown',
                    'notes': (
                        'Candidate source suggested in the ULI '
                        'workbook; confirm, replace or remove.'
                    ),
                }
            )
    if not sources:
        sources = [
            {
                'name': f'{TODO}: dataset name',
                'custodian': None,
                'citation': (
                    f'{TODO}: institution, year, dataset title, version'
                ),
                'url': None,
                'date_retrieved': f'{TODO}: YYYY-MM-DD',
                'licence': 'Unknown - to be confirmed',
                'licence_url': None,
                'redistributable': None,
                'spatial_resolution': None,
                'temporal_coverage': None,
                'condesa_coverage': 'unknown',
                'notes': None,
            }
        ]

    limitations = []
    for field, prefix in (
        ('doubts', 'Open question from the workbook'),
        ('notes', 'Note from the workbook'),
    ):
        if record.get(field):
            limitations.append(f'{prefix}: {_wrap(record[field])}')

    return {
        'schema_version': vocab.SCHEMA_VERSION,
        'indicator': {
            'id': int(record['indicator_id']),
            'code': code,
            'name_en': record['indicator'],
            'name_es': None,
            'domains': list(record['domains']),
            'subdomain': record.get('subdomain'),
            'category': record.get('category'),
            'subject': record.get('subject'),
            'role': (
                'composite'
                if int(record['indicator_id']) in GHSCI_COMPOSITES
                else 'leaf'
            ),
            'composite_parent': None,
            'work_package': record['work_package'],
            'status': 'not_started',
            'analyst': analyst
            or {
                'name': f'{TODO}: your name',
                'email': None,
                'institution': None,
            },
            'adapted_from': _adapted_from(record),
        },
        'rationale': {
            'statement': _wrap(record.get('reason_draft'))
            or f'{TODO}: why this matters for health and wellbeing.',
            'statement_es': None,
            'health_pathways': [
                f'{TODO}: one or more of '
                f'{sorted(vocab.HEALTH_PATHWAYS)}'
            ],
            'arid_context': (
                f'{TODO}: how Mexicali\'s arid, hot climate changes the '
                'expected relationship (optional but encouraged)'
            ),
            'evidence': [
                {
                    'claim': (
                        f'{TODO}: the specific health or wellbeing '
                        'benefit this reference supports'
                    ),
                    'citation': (
                        f'{TODO}: author(s), year, title, journal - '
                        'independent of the adapted_from article above'
                    ),
                    'doi': None,
                    'url': None,
                    'evidence_type': (
                        f'{TODO}: one of {sorted(vocab.EVIDENCE_TYPES)}'
                    ),
                    'population': None,
                    'exposure': None,
                    'outcome': None,
                    'effect': None,
                    'threshold_support': None,
                    'notes': None,
                }
            ],
        },
        'measures': measures,
        'data_sources': sources,
        'method': {
            'summary': (
                f'{TODO}: how the measure was computed, in enough '
                'detail for someone else to reproduce it from the '
                'documented sources.'
            ),
            'software': ['python', 'geopandas', 'uli'],
            'notebook': None,
            'parameters': {},
            'assumptions': [],
            'limitations': limitations,
            'condesa_treatment': (
                f'{TODO}: how coverage of the Condesa new development '
                'was achieved, or why it could not be'
            ),
        },
        'provenance': {
            'computed_by': None,
            'computed_on': None,
            'code_version': None,
        },
    }


def _adapted_from(record, articles=None):
    """Resolve provenance from the reviewed article list, by number.

    The workbook's free-text 'Citation(s)' column is deliberately not
    used here.  It holds secondary citations -- works cited *inside*
    the review articles -- and for 75 of 79 indicators it names no
    author of the article the indicator is attributed to, so combining
    the two produced confident-looking but wrong provenance.  The
    ``Article #`` is the reliable link; everything else is resolved
    from the article list.

    Verify the resolved reference before publication: the article list
    is the team's own record and has needed correction.
    """
    references, unknown = register.article_reference(
        record.get('article_numbers'), articles
    )
    parts = []
    if references:
        parts.append('Adapted from ULI review article ' + '; '.join(references))
    if unknown:
        parts.append(
            'Article number(s) '
            + ', '.join(str(n) for n in unknown)
            + ' are cited in the workbook but absent from the article '
            'list; provenance unresolved'
        )
    if not parts:
        parts.append(
            'No source article recorded in the workbook; provenance '
            'unknown'
        )
    return ' | '.join(parts)


def todos(metadata, path=()):
    """List the dotted paths in a metadata dict still marked TODO."""
    found = []
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            found += todos(value, path + (str(key),))
    elif isinstance(metadata, list):
        for index, value in enumerate(metadata):
            found += todos(value, path + (str(index),))
    elif isinstance(metadata, str) and TODO in metadata:
        found.append('.'.join(path))
    return found
