"""Validate indicator results and metadata against the ULI schema.

The point of validating locally is that nobody discovers a problem six
weeks later while assembling the composite index.  Run
:func:`check` at the end of every calculation; it returns a
:class:`Report` that prints as a readable checklist and is falsy if
anything failed.

Checks fall into three groups:

* **schema** -- structural conformance to ``schema/*.schema.json``
* **consistency** -- results and metadata agree with each other, ids
  exist in the reference geographies, values respect their declared
  type and direction
* **project requirements** -- required geographies delivered, Condesa
  new development covered, evidence and data source documentation
  present
"""

import json
import os

import numpy as np
import pandas as pd

from . import geography, vocab

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
SCHEMA_DIR = os.path.join(PROJECT_DIR, 'schema')

# A measure must reach at least this share of the Condesa
# fraccionamientos to satisfy the project's focus-area requirement.
CONDESA_MIN_SHARE = 0.8


class Report:
    """Collected validation messages for one indicator."""

    def __init__(self, label):
        self.label = label
        self.errors = []
        self.warnings = []
        self.passed = []

    def error(self, message):
        self.errors.append(message)

    def warn(self, message):
        self.warnings.append(message)

    def ok(self, message):
        self.passed.append(message)

    def __bool__(self):
        return not self.errors

    def __repr__(self):
        lines = [f'Validation report: {self.label}']
        for message in self.passed:
            lines.append(f'  [ok]    {message}')
        for message in self.warnings:
            lines.append(f'  [WARN]  {message}')
        for message in self.errors:
            lines.append(f'  [ERROR] {message}')
        verdict = 'PASSED' if self else 'FAILED'
        lines.append(
            f'  -> {verdict} '
            f'({len(self.errors)} errors, {len(self.warnings)} warnings)'
        )
        return '\n'.join(lines)

    def to_dict(self):
        return {
            'label': self.label,
            'passed': bool(self),
            'checks_passed': self.passed,
            'warnings': self.warnings,
            'errors': self.errors,
        }


def _schema(name):
    with open(os.path.join(SCHEMA_DIR, name), encoding='utf-8') as f:
        return json.load(f)


def validate_metadata(metadata, report=None):
    """Validate an indicator metadata dict."""
    import jsonschema

    label = metadata.get('indicator', {}).get('code', '<unknown>')
    report = report or Report(f'metadata: {label}')
    validator = jsonschema.Draft202012Validator(
        _schema('indicator_metadata.schema.json')
    )
    failures = sorted(
        validator.iter_errors(metadata), key=lambda e: list(e.path)
    )
    for failure in failures:
        path = '/'.join(str(p) for p in failure.path) or '<root>'
        report.error(f'metadata {path}: {failure.message}')
    if not failures:
        report.ok('metadata conforms to indicator_metadata.schema.json')

    _check_vocabularies(metadata, report)
    _check_documentation(metadata, report)
    return report


def _check_vocabularies(metadata, report):
    """Controlled terms are checked here rather than in JSON Schema.

    Keeping them in :mod:`uli.vocab` means one place to add a term,
    and a clearer message than a 47-item enum mismatch.
    """
    for measure in metadata.get('measures', []):
        where = measure.get('id', '<no id>')
        for field, allowed in (
            ('lens', vocab.ANALYST_LENSES),
            ('value_type', vocab.VALUE_TYPES),
            ('direction', vocab.DIRECTIONS),
            ('native_scale', vocab.GEO_LEVELS),
            ('aggregation_method', vocab.AGGREGATION_METHODS),
        ):
            value = measure.get(field)
            if value is not None and value not in allowed:
                report.error(
                    f'measure {where}: {field}={value!r} is not in the '
                    f'controlled vocabulary ({sorted(allowed)})'
                )
        denominator = measure.get('denominator_type')
        if denominator and denominator not in vocab.DENOMINATOR_TYPES:
            report.error(
                f'measure {where}: denominator_type='
                f'{denominator!r} is not recognised'
            )
        basis = measure.get('temporal_basis')
        if basis and basis not in vocab.TEMPORAL_BASES:
            report.error(
                f'measure {where}: temporal_basis={basis!r} is not '
                f'recognised; expected one of '
                f'{sorted(vocab.TEMPORAL_BASES)}'
            )
        code = metadata['indicator']['code']
        if not str(where).startswith(f'{code}__'):
            report.error(
                f'measure id {where!r} must start with '
                f'{code + "__"!r} so results can be traced to their '
                'indicator'
            )
    for pathway in metadata.get('rationale', {}).get(
        'health_pathways', []
    ):
        if pathway not in vocab.HEALTH_PATHWAYS:
            report.error(
                f'health pathway {pathway!r} is not recognised; '
                f'expected one of {sorted(vocab.HEALTH_PATHWAYS)}'
            )
    for item in metadata.get('rationale', {}).get('evidence', []):
        kind = item.get('evidence_type')
        if kind and kind not in vocab.EVIDENCE_TYPES:
            report.error(
                f'evidence_type {kind!r} is not recognised; expected '
                f'one of {sorted(vocab.EVIDENCE_TYPES)}'
            )


def _outstanding(value, path=()):
    """Dotted paths still holding a literal TODO placeholder."""
    if isinstance(value, dict):
        return [
            item
            for key, child in value.items()
            for item in _outstanding(child, path + (str(key),))
        ]
    if isinstance(value, list):
        return [
            item
            for index, child in enumerate(value)
            for item in _outstanding(child, path + (str(index),))
        ]
    if isinstance(value, str) and 'TODO' in value:
        return ['.'.join(path)]
    return []


def _check_documentation(metadata, report):
    """Project requirements that go beyond structural validity."""
    outstanding = _outstanding(metadata)
    if outstanding:
        shown = ', '.join(outstanding[:6])
        more = (
            f' (and {len(outstanding) - 6} more)'
            if len(outstanding) > 6
            else ''
        )
        report.error(
            f'{len(outstanding)} metadata fields still contain a TODO '
            f'placeholder: {shown}{more}'
        )
    else:
        report.ok('no outstanding TODO placeholders in the metadata')

    rationale = metadata.get('rationale', {})
    evidence = rationale.get('evidence', [])
    adapted = (metadata.get('indicator', {}).get('adapted_from') or '')

    if not evidence:
        report.error(
            'no health evidence supplied; every indicator needs at '
            'least one citation demonstrating a meaningful health or '
            'wellbeing benefit'
        )
    strong = {
        'meta_analysis',
        'systematic_review',
        'expert_guidance',
        'cohort',
        'natural_experiment',
    }
    if evidence and not any(
        item.get('evidence_type') in strong for item in evidence
    ):
        report.warn(
            'no systematic review, meta-analysis, cohort study or '
            'reputable guidance among the evidence; aim for at least '
            'one of these'
        )
    for item in evidence:
        citation = (item.get('citation') or '').lower()
        if adapted and citation and citation[:25] in adapted.lower():
            report.warn(
                f'evidence citation {item.get("citation")[:60]!r} looks '
                'like the article the indicator was adapted from; the '
                'health evidence must be independent of it'
            )
        if not item.get('effect'):
            report.warn(
                f'evidence {item.get("citation", "")[:50]!r} reports no '
                'effect size or uncertainty'
            )

    for source in metadata.get('data_sources', []):
        if source.get('licence') in (None, '', 'Unknown - to be confirmed'):
            report.warn(
                f'data source {source.get("name")!r} has no confirmed '
                'licence; Reimagina Urbana ingestion may not be '
                'possible without one'
            )
        if source.get('condesa_coverage') in (None, 'unknown'):
            report.warn(
                f'data source {source.get("name")!r} does not state '
                'whether it covers the Condesa new development'
            )
        elif source.get('condesa_coverage') == 'none':
            report.warn(
                f'data source {source.get("name")!r} does not cover '
                'Condesa; explain the treatment in '
                'method.condesa_treatment'
            )

    for measure in metadata.get('measures', []):
        if measure.get('threshold') is not None and not measure.get(
            'threshold_justification'
        ):
            report.warn(
                f'measure {measure.get("id")}: a threshold is applied '
                'but not justified against the evidence'
            )
        if measure.get('direction') == 'non_monotonic' and not measure.get(
            'index_notes'
        ):
            report.warn(
                f'measure {measure.get("id")}: non-monotonic direction '
                'needs index_notes explaining the target range'
            )


def validate_results(results, metadata=None, report=None, strict_ids=True):
    """Validate a long results table."""
    label = (
        metadata['indicator']['code']
        if metadata
        else '<results without metadata>'
    )
    report = report or Report(f'results: {label}')

    missing = [
        column
        for column in vocab.RESULT_COLUMNS
        if column not in results.columns
    ]
    if missing:
        report.error(f'missing required columns: {missing}')
        return report
    extra = [
        column
        for column in results.columns
        if column not in vocab.RESULT_COLUMNS
    ]
    if extra:
        report.error(
            f'unexpected columns {extra}; the results table must have '
            f'exactly the columns {list(vocab.RESULT_COLUMNS)}'
        )
    if results.empty:
        report.error('results table is empty')
        return report
    report.ok(f'{len(results):,} result rows with the expected columns')

    _check_enumerations(results, report)
    _check_values(results, report)
    _check_duplicates(results, report)
    if strict_ids:
        _check_geo_ids(results, report)
    _check_required_levels(results, report)
    _check_condesa(results, report)
    if metadata is not None:
        _check_against_metadata(results, metadata, report)
    return report


def _check_enumerations(results, report):
    for column, allowed in (
        ('geo_level', vocab.GEO_LEVELS),
        ('native_scale', vocab.GEO_LEVELS),
        ('aggregation_method', vocab.AGGREGATION_METHODS),
        ('quality_flag', vocab.QUALITY_FLAGS),
    ):
        bad = sorted(set(results[column].dropna()) - set(allowed))
        if bad:
            report.error(f'{column}: unrecognised values {bad}')


def _check_values(results, report):
    flags = results['quality_flag']
    empty_expected = flags.isin(vocab.EMPTY_VALUE_FLAGS)
    wrong = results[empty_expected & results['value'].notna()]
    if len(wrong):
        report.error(
            f'{len(wrong)} rows carry a value despite a quality_flag of '
            f'{sorted(set(wrong["quality_flag"]))}; the value must be '
            'empty'
        )
    missing = results[~empty_expected & results['value'].isna()]
    if len(missing):
        report.error(
            f'{len(missing)} rows have no value but a quality_flag of '
            f'{sorted(set(missing["quality_flag"]))}; use no_data, '
            'suppressed or not_applicable'
        )
    coverage = pd.to_numeric(results['coverage'], errors='coerce')
    if ((coverage < 0) | (coverage > 1)).any():
        report.error('coverage must be between 0 and 1')
    if not np.isfinite(
        pd.to_numeric(results['value'], errors='coerce').dropna()
    ).all():
        report.error('value contains infinities; use an empty value')

    replicated = results[results['aggregation_method'] == 'replicated']
    if len(replicated):
        share = len(replicated) / len(results)
        report.warn(
            f'{len(replicated):,} rows ({share:.0%}) are replicated '
            'from a coarser scale and carry no variation there; they '
            'should not be treated as fine-grained evidence'
        )
    low = results[results['quality_flag'] == 'low_coverage']
    if len(low):
        report.warn(
            f'{len(low):,} rows flagged low_coverage (under the '
            'minimum share of valid input data)'
        )


def _check_duplicates(results, report):
    keys = ['measure_id', 'geo_level', 'geo_id']
    duplicated = results.duplicated(subset=keys, keep=False)
    if duplicated.any():
        examples = (
            results.loc[duplicated, keys].head(5).to_dict('records')
        )
        report.error(
            f'{duplicated.sum()} duplicated rows for the same '
            f'measure/geography/unit, e.g. {examples}'
        )
    else:
        report.ok('one row per measure, geography and unit')


def _check_geo_ids(results, report):
    if not geography.available():
        report.warn(
            'reference geographies not available; geo_id membership '
            'not checked'
        )
        return
    for level, group in results.groupby('geo_level'):
        known = set(geography.units(level)['geo_id'].astype(str))
        supplied = set(group['geo_id'].astype(str))
        unknown = supplied - known
        if unknown:
            report.error(
                f'{level}: {len(unknown)} geo_id values are not in the '
                f'reference geopackage, e.g. {sorted(unknown)[:3]}'
            )
        absent = known - supplied
        if absent:
            share = len(absent) / max(len(known), 1)
            message = (
                f'{level}: {len(absent):,} of {len(known):,} units '
                f'({share:.0%}) have no row'
            )
            (report.error if share > 0.5 else report.warn)(message)


def _check_required_levels(results, report):
    for measure_id, group in results.groupby('measure_id'):
        delivered = set(group['geo_level'])
        missing = [
            level
            for level in vocab.REQUIRED_GEO_LEVELS
            if level not in delivered
        ]
        if missing:
            report.error(
                f'measure {measure_id}: required reporting geographies '
                f'not delivered: {missing}'
            )
        else:
            report.ok(
                f'measure {measure_id}: all required reporting '
                'geographies delivered'
            )
        if 'grid_100m' not in delivered:
            report.warn(
                f'measure {measure_id}: no 100 m grid output (optional, '
                'but preferred where the data support it)'
            )


def _check_condesa(results, report):
    """The Condesa new development is a project focus area.

    An indicator that is silently empty there is not usable for this
    project, so this is an error rather than a warning.
    """
    subset = results[
        results['geo_level'] == 'condesa_fraccionamiento'
    ]
    if subset.empty:
        report.error(
            'no results for condesa_fraccionamiento; the Condesa new '
            'development in south-east Mexicali must be covered'
        )
        return
    if not geography.available():
        report.warn(
            'reference geographies not available; Condesa coverage '
            'checked only against the rows supplied'
        )
        total = subset['geo_id'].nunique()
    else:
        total = len(geography.condesa_ids('condesa_fraccionamiento'))
    for measure_id, group in subset.groupby('measure_id'):
        valued = group['value'].notna().sum()
        share = valued / max(total, 1)
        if share < CONDESA_MIN_SHARE:
            report.error(
                f'measure {measure_id}: only {valued} of {total} '
                f'Condesa fraccionamientos ({share:.0%}) have a value; '
                f'at least {CONDESA_MIN_SHARE:.0%} is required'
            )
        else:
            report.ok(
                f'measure {measure_id}: Condesa covered '
                f'({valued}/{total} fraccionamientos)'
            )


def _check_against_metadata(results, metadata, report):
    declared = {m['id']: m for m in metadata.get('measures', [])}
    supplied = set(results['measure_id'])
    undocumented = sorted(supplied - set(declared))
    if undocumented:
        report.error(
            f'results contain measures with no metadata entry: '
            f'{undocumented}'
        )
    undelivered = sorted(set(declared) - supplied)
    if undelivered:
        report.warn(
            f'metadata declares measures with no results: {undelivered}'
        )
    code = metadata['indicator']['code']
    if set(results['indicator_code']) - {code}:
        report.error(
            f'results contain indicator_code values other than {code!r}'
        )
    if set(results['indicator_id']) - {metadata['indicator']['id']}:
        report.error(
            'results contain indicator_id values other than '
            f'{metadata["indicator"]["id"]}'
        )
    for measure_id, measure in declared.items():
        group = results[results['measure_id'] == measure_id]
        if group.empty:
            continue
        values = pd.to_numeric(group['value'], errors='coerce').dropna()
        value_type = measure.get('value_type')
        if value_type == 'proportion' and (
            (values < 0).any() or (values > 1).any()
        ):
            report.error(
                f'measure {measure_id}: declared as a proportion but '
                f'values range {values.min():.3g} to {values.max():.3g}'
            )
        if value_type == 'percentage' and (
            (values < 0).any() or (values > 100).any()
        ):
            report.error(
                f'measure {measure_id}: declared as a percentage but '
                f'values range {values.min():.3g} to {values.max():.3g}'
            )
        if value_type == 'count' and (values < 0).any():
            report.error(
                f'measure {measure_id}: declared as a count but has '
                'negative values'
            )
        native = set(group['native_scale'])
        if native != {measure.get('native_scale')}:
            report.warn(
                f'measure {measure_id}: metadata declares native_scale '
                f'{measure.get("native_scale")!r} but results contain '
                f'{sorted(native)}'
            )


def check(results, metadata, label=None):
    """Validate metadata and results together; returns one Report."""
    label = label or metadata.get('indicator', {}).get('code', 'indicator')
    report = Report(label)
    validate_metadata(metadata, report)
    validate_results(results, metadata, report)
    return report
