"""Read the ULI indicator workbook into a tidy indicator register.

The workbook ('ULI_Tables by domain ... .xlsx', sheet 'Indicators -
Classified') is the single source of truth for which indicators are in
scope.  This module turns it into a flat table that the notebook
builder, the metadata templates and the validator all share.

The classified sheet has a two-row header: row 1 carries the top-level
column names and merged group labels ('Domain', 'Lens / Enfoque'), row
2 carries the group members and per-column counts.  Data start at the
third row.  Columns are therefore read positionally against
``SOURCE_COLUMNS``.
"""

import os
import re
import unicodedata

import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
WORKBOOK_GLOB = 'ULI_Tables by domain*.xlsx'
SHEET = 'Indicators - Classified'

# Positional names for the 33 columns of the classified sheet.
#
# The August 2026 revision removed the 'Equity' lens column (equity is
# derived centrally from the distribution of the other lenses) and the
# two 'Composite? Abstract?' / 'Composite hierarchy' columns, whose
# draft classifications were superseded.  Composite construction is now
# handled explicitly: the walkability index, street connectivity,
# population density, access to daily living amenities and level of
# cycling traffic stress are produced by the core GHSCI workflow
# (WP01); nothing else in the register is treated as a composite.
SOURCE_COLUMNS = [
    'indicator_id',
    'indicator',
    'domain',
    'd_safety',
    'd_built_environment',
    'd_ambient_environment',
    'd_housing',
    'd_economic_development',
    'd_social_infrastructure',
    'd_sociodemographics',
    'd_mobility_transport',
    'subdomain',
    'category',
    'subject',
    'lens_text',
    'lens_proximity',
    'lens_accessibility',
    'lens_quantity',
    'lens_density',
    'lens_diversity',
    'lens_quality',
    'reason_draft',
    'source_citation',
    'source_effect_size',
    'can_calculate',
    'pragmatic_method',
    'article_numbers',
    'excluded',
    'methods_from_literature',
    'potential_data_sources',
    'notes',
    'doubts',
    '_spare',
]

DOMAIN_FLAG_COLUMNS = {
    'd_safety': 'Safety',
    'd_built_environment': 'Built Environment',
    'd_ambient_environment': 'Ambient Environment',
    'd_housing': 'Housing',
    'd_economic_development': 'Economic Development',
    'd_social_infrastructure': 'Social Infrastructure',
    'd_sociodemographics': 'Sociodemographics',
    'd_mobility_transport': 'Mobility & Transport',
}

LENS_FLAG_COLUMNS = {
    'lens_proximity': 'proximity',
    'lens_accessibility': 'accessibility',
    'lens_quantity': 'quantity',
    'lens_density': 'density',
    'lens_diversity': 'diversity',
    'lens_quality': 'quality',
}

UNASSIGNED = 'WP99_unassigned'
EXCLUDED = 'WP98_excluded'


def workbook_path(project_dir=None):
    """Return the path to the most recent indicator workbook."""
    import glob

    project_dir = project_dir or PROJECT_DIR
    matches = sorted(glob.glob(os.path.join(project_dir, WORKBOOK_GLOB)))
    if not matches:
        raise FileNotFoundError(
            f'No workbook matching {WORKBOOK_GLOB!r} in {project_dir}'
        )
    return matches[-1]


def slugify(text, max_words=8):
    """Return a stable snake_case slug for an indicator name."""
    text = unicodedata.normalize('NFKD', str(text))
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', ' ', text).strip()
    words = [w for w in text.split() if w]
    return '_'.join(words[:max_words]) or 'unnamed'


def _clean(value):
    """Collapse pandas nulls and blank strings to None."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text in ('', 'nan', 'NaN', 'None'):
        return None
    return text


def _flags(row, mapping):
    """Return the labels whose flag column is marked in this row."""
    return [
        label
        for column, label in mapping.items()
        if _clean(row.get(column)) is not None
    ]


def _definitions(path=None):
    path = path or os.path.join(HERE, 'work_packages.yml')
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_work_packages(path=None):
    """Load the work package definitions."""
    return _definitions(path)['work_packages']


def load_exclusions(path=None):
    """Return ``{indicator_id: reason}`` for out-of-scope indicators."""
    return {
        int(item['id']): ' '.join(str(item['reason']).split())
        for item in _definitions(path).get('excluded') or []
    }


def _assign(row, packages):
    """Return the work package code for an indicator row."""
    pragmatic = (row.get('pragmatic_method') or '').lower()
    category = row.get('category') or ''
    for package in packages:
        if row['indicator_id'] in (package.get('ids') or []):
            return package['code']
        needle = package.get('pragmatic_contains')
        if needle and needle.lower() in pragmatic:
            return package['code']
        if category in (package.get('category_in') or []):
            return package['code']
    return UNASSIGNED


def load(project_dir=None, path=None):
    """Return the indicator register as a ``pandas.DataFrame``.

    One row per indicator, with list-valued ``domains`` and ``lenses``
    columns, a stable ``indicator_code``, and the assigned
    ``work_package``.
    """
    path = path or workbook_path(project_dir)
    frame = pd.read_excel(path, SHEET, header=None, skiprows=2)
    if frame.shape[1] != len(SOURCE_COLUMNS):
        raise ValueError(
            f'Expected {len(SOURCE_COLUMNS)} columns in sheet {SHEET!r} '
            f'of {os.path.basename(path)}, found {frame.shape[1]}.  The '
            'workbook layout has changed; update SOURCE_COLUMNS.'
        )
    frame.columns = SOURCE_COLUMNS
    frame = frame.drop(columns=['_spare'])
    frame = frame[frame['indicator_id'].notna()].copy()
    frame['indicator_id'] = frame['indicator_id'].astype(int)

    packages = load_work_packages()
    exclusions = load_exclusions()
    records = []
    for _, row in frame.iterrows():
        record = {
            column: _clean(row[column])
            for column in frame.columns
            if column not in DOMAIN_FLAG_COLUMNS
            and column not in LENS_FLAG_COLUMNS
        }
        record['indicator_id'] = int(row['indicator_id'])
        record['domains'] = _flags(row, DOMAIN_FLAG_COLUMNS) or (
            [record['domain']] if record['domain'] else []
        )
        record['lenses'] = _flags(row, LENS_FLAG_COLUMNS)
        record['excluded_reason'] = exclusions.get(
            record['indicator_id']
        )
        record['work_package'] = (
            EXCLUDED
            if record['excluded_reason']
            else _assign(record, packages)
        )
        records.append(record)

    register = pd.DataFrame.from_records(records)
    register['indicator_code'] = _unique_codes(register)
    register = register.sort_values(
        ['work_package', 'category', 'indicator_id'],
        na_position='last',
    ).reset_index(drop=True)
    return register


def _unique_codes(register):
    """Slug each indicator name, disambiguating repeats with the id.

    Repeated names are common and meaningful -- the same construct was
    adapted from several source articles -- so the id suffix is a
    deliberate signal that those rows are candidates for consolidation.
    """
    slugs = register['indicator'].fillna('unnamed').map(slugify)
    counts = slugs.value_counts()
    return [
        f'{slug}_{indicator_id}' if counts[slug] > 1 else slug
        for slug, indicator_id in zip(slugs, register['indicator_id'])
    ]


def get(indicator_id, register=None):
    """Return a single indicator record as a dict."""
    register = load() if register is None else register
    matches = register[register['indicator_id'] == int(indicator_id)]
    if matches.empty:
        raise KeyError(f'No indicator with id {indicator_id}')
    return matches.iloc[0].to_dict()


def excluded(register=None):
    """Return the indicators dropped from scope, with reasons."""
    register = load() if register is None else register
    return register[register['work_package'] == EXCLUDED][
        ['indicator_id', 'indicator', 'category', 'excluded_reason']
    ]


def by_work_package(register=None):
    """Return ``{work_package_code: DataFrame}`` in definition order."""
    register = load() if register is None else register
    order = [package['code'] for package in load_work_packages()]
    order += [
        code
        for code in register['work_package'].unique()
        if code not in order
    ]
    return {
        code: register[register['work_package'] == code].copy()
        for code in order
        if (register['work_package'] == code).any()
    }


def save(path=None, register=None):
    """Write the register to CSV for review outside Python."""
    register = load() if register is None else register
    path = path or os.path.join(PROJECT_DIR, 'indicator_register.csv')
    flat = register.copy()
    for column in ('domains', 'lenses'):
        flat[column] = flat[column].map(lambda v: '; '.join(v))
    flat.to_csv(path, index=False, encoding='utf-8-sig')
    return path
