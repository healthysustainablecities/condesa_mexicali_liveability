"""Everything the manual reads, resolved once.

The manual says nothing it cannot trace: labels, descriptions, readings,
transforms and sources come from the region configuration; goalposts and
weights from the composite parameters the analysis wrote; structure, classes
and units from the dashboard export; values from the results GeoPackage; and
rationale from the project's indicator register.  This module only finds and
loads those files.  Paths resolve from this file's place in the ULI repository
(``build/manual``), which sits at ``process/data/MX/Mexicali Liveability`` in a
global-indicators checkout; set ``GHSCI_REPO`` to point elsewhere.
"""

import functools
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
SITE = HERE.parents[1]  # the ULI repository root
REPO = Path(os.environ.get('GHSCI_REPO') or SITE.parents[3])
DATA_DIR = REPO / 'process' / 'data'
CODE_DIR = REPO / 'process' / 'subprocesses'
CODENAME = 'MX_Mexicali_2025_ULI'
CONFIG = DATA_DIR / 'MX' / f'{CODENAME}.yml'
OUTPUTS = DATA_DIR / '_study_region_outputs' / CODENAME
DASHBOARD = SITE / 'dashboard' / 'data' / 'mexicali'
GPKG = SITE / 'outputs' / 'mexicali_uli_ghsci_results.gpkg'
DICTIONARY = SITE / 'outputs' / 'mexicali_uli_ghsci_data_dictionary.csv'
REGISTER = SITE / 'indicator_register.csv'
CITATIONS = SITE / 'citation_audit.csv'
WORKSHEET = (
    DATA_DIR / 'MX' / 'Update_on_ULI - 2026-09-22' / 'excel_work_sheet_key.xlsx'
)
DOCS = SITE / 'docs' / 'manual'
WORK = HERE / '_work'
GITHUB = 'https://github.com/healthysustainablecities/global-indicators'
LANGS = ('es', 'en')


def read_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def label(value, lang, fallback=''):
    """The text for one language of a ``{es, en}`` value (or a plain one)."""
    if isinstance(value, dict):
        return value.get(lang) or ''
    if value is None:
        return fallback
    return str(value)


class Sources:
    """Lazy access to every input of the manual."""

    @functools.cached_property
    def config(self):
        return read_yaml(CONFIG)

    @functools.cached_property
    def config_text(self):
        return CONFIG.read_text(encoding='utf-8')

    def parameters(self, index='uli'):
        path = OUTPUTS / f'{CODENAME}_composite_{index}_parameters.yml'
        return read_yaml(path)

    @functools.cached_property
    def indicators_json(self):
        return json.loads((DASHBOARD / 'indicators.json').read_text('utf-8'))

    @functools.cached_property
    def manifest(self):
        return json.loads((DASHBOARD / 'manifest.json').read_text('utf-8'))

    @functools.cached_property
    def family(self):
        return next(
            f for f in self.indicators_json['families'] if f.get('composite')
        )

    @functools.cached_property
    def structure(self):
        """The index's structure, as _composite_index.index_structure gives it."""
        return self.family['composite']

    def describe(self, column):
        return self.indicators_json['descriptions'].get(column) or {}

    def breaks(self, column):
        return self.indicators_json['breaks'].get(column)

    def censored(self, column):
        return self.indicators_json['censored'].get(column)

    @functools.cached_property
    def register(self):
        frame = pd.read_csv(REGISTER, dtype={'indicator_id': str})
        return frame.set_index('indicator_id', drop=False)

    @functools.cached_property
    def citation_audit(self):
        frame = pd.read_csv(CITATIONS, dtype={'indicator_id': str})
        return frame.set_index('indicator_id', drop=False)

    @functools.cached_property
    def worksheet(self):
        """The variable sheet, read from a copy (it is often open in Excel)."""
        copy = Path(tempfile.mkdtemp()) / WORKSHEET.name
        shutil.copy(WORKSHEET, copy)
        sheet = pd.read_excel(copy, sheet_name='Current version of subvariable-')
        sheet.columns = ['mark'] + [str(c).strip() for c in sheet.columns[1:]]
        sheet['key'] = sheet['Sub-variable'].map(_squash)
        return sheet

    def sheet_rows(self, names):
        sheet = self.worksheet
        keys = [_squash(n) for n in names]
        rows = sheet[sheet['key'].isin(keys)]
        missing = set(keys) - set(rows['key'])
        if missing:
            raise KeyError(f'Sub-variables not in the sheet: {sorted(missing)}')
        return rows

    @functools.cached_property
    def dictionary(self):
        frame = pd.read_csv(DICTIONARY)
        return frame.set_index('variable', drop=False)

    @functools.cached_property
    def curation(self):
        return read_yaml(HERE / 'entries.yml')

    @functools.cached_property
    def upstream(self):
        return read_yaml(HERE / 'upstream.yml')

    @functools.cached_property
    def strings(self):
        return read_yaml(HERE / 'strings.yml')

    @functools.cached_property
    def translations(self):
        return read_yaml(HERE / 'rationale_es.yml')

    @functools.cached_property
    def commit(self):
        try:
            return subprocess.run(
                ['git', '-C', str(REPO), 'rev-parse', 'HEAD'],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    @functools.cached_property
    def site_commit(self):
        try:
            return subprocess.run(
                ['git', '-C', str(SITE), 'rev-parse', '--short', 'HEAD'],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    def committed_text(self, path):
        """A file's text at the linked commit, so that line numbers match
        the GitHub link even while the working tree holds uncommitted
        edits; the working copy is read only when git cannot supply it."""
        if self.commit:
            relative = path.relative_to(REPO).as_posix()
            try:
                return subprocess.run(
                    ['git', '-C', str(REPO), 'show',
                     f'{self.commit}:{relative}'],
                    capture_output=True, check=True,
                ).stdout.decode('utf-8')
            except (OSError, subprocess.CalledProcessError):
                pass
        return path.read_text(encoding='utf-8')

    @functools.lru_cache(maxsize=None)
    def code_line(self, file, name):
        """The line at which ``def name`` (or ``class name``) is defined."""
        path = CODE_DIR / file
        if not path.exists():
            path = REPO / 'process' / file
        text = self.committed_text(path)
        pattern = re.compile(rf'^[ \t]*(?:def|class)\s+{re.escape(name)}\b', re.M)
        match = pattern.search(text)
        if not match:
            raise KeyError(f'{name} is not defined in {file}')
        return text.count('\n', 0, match.start()) + 1, path

    def code_link(self, file, name):
        line, path = self.code_line(file, name)
        relative = path.relative_to(REPO).as_posix()
        ref = self.commit or 'mexicali'
        return f'{relative}:{line}', f'{GITHUB}/blob/{ref}/{relative}#L{line}'

    def config_line(self, needle):
        """The first line of the region configuration that begins with
        ``needle`` (ignoring indentation and a list item's dash)."""
        want = needle.strip()
        for number, line in enumerate(self.config_text.splitlines(), 1):
            text = line.strip()
            if text.startswith(want) or text.lstrip('- ').startswith(want):
                return number
        raise KeyError(f'{needle!r} is not in {CONFIG.name}')

    def config_block(self, needle):
        """The configuration text of the item beginning at ``needle``: that
        line and the more indented lines after it."""
        lines = self.config_text.splitlines()
        start = self.config_line(needle) - 1
        first = lines[start]
        indent = len(first) - len(first.lstrip())
        block = [first]
        for line in lines[start + 1:]:
            if line.strip() and len(line) - len(line.lstrip()) <= indent:
                break
            block.append(line)
        while block and not block[-1].strip():
            block.pop()
        width = min(len(b) - len(b.lstrip()) for b in block if b.strip())
        return '\n'.join(b[width:] for b in block), start + 1


def _squash(text):
    return re.sub(r'\s+', ' ', str(text)).strip().lower()
