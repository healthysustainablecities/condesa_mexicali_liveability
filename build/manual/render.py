"""Render the manual's pages: Markdown for GitHub, then one HTML page and a
PDF per language.

Pages are written under ``docs/manual/<lang>/``; maps under
``docs/manual/figures/<lang>/``; the region configuration and composite
parameters the manual cites are copied to ``docs/manual/data/`` so that every
configuration reference resolves; PDFs go to ``docs/manual/pdf/``.
"""

import html
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path, PurePosixPath

import markdown as markdown_lib
import pyogrio
import yaml

import maps
from numbers_fmt import digits_for, fmt
from sources import (
    CODENAME, CONFIG, DOCS, GPKG, HERE, LANGS, OUTPUTS, SITE, WORK, label,
)
from stats import REGIONS, cross_check

ULI_REPO = 'https://github.com/healthysustainablecities/condesa_mexicali_liveability'
DATA_FILES = [
    CONFIG,
    OUTPUTS / f'{CODENAME}_composite_uli_parameters.yml',
    OUTPUTS / f'{CODENAME}_composite_uli_plain_parameters.yml',
]

KIND_RECIPES = {
    'soft_walk': ['R1', 'R2', 'R10'],
    'steps_walk': ['R1', 'R2', 'R10'],
    'beyond_walk': ['R1', 'R2', 'R3'],
    'banded_walk': ['R1', 'R2', 'R3'],
    'soft_euclid': ['R1', 'R5', 'R10'],
    'soft_cycle': ['R1', 'R6', 'R2', 'R10'],
    'diversity': ['R1', 'R4'],
    'linked': ['R1', 'R7'],
    'utci': ['R1', 'R7', 'R9'],
    'gee': ['R1', 'R8'],
    'lpugs': ['R1', 'R8', 'R2', 'R3'],
    'walkability': ['R1', 'R2', 'R3', 'R9'],
}
COMMON_RECIPES = ['R11', 'R12', 'R13', 'R14']
WALK = [('_accessibility_spec.py', '_banded_distances'),
        ('setup_sp.py', 'create_full_nodes')]
KIND_CODE = {
    'soft_walk': WALK + [('_composite_index.py', 'soft_threshold')],
    'steps_walk': WALK + [('_composite_index.py', 'stepped_score')],
    'beyond_walk': WALK + [('_accessibility_spec.py', 'sample_point_access')],
    'banded_walk': WALK + [('_accessibility_spec.py', 'sample_point_access')],
    'soft_euclid': [('_euclidean_accessibility.py', 'nearest_distances'),
                    ('_composite_index.py', 'soft_threshold')],
    'soft_cycle': [('_cycling_lts_network.py', 'assign_lts'),
                   ('_cycling_accessibility.py', 'cycling_poi_distance'),
                   ('_composite_index.py', 'soft_threshold')],
    'diversity': [('_accessibility_spec.py', '_banded_counts'),
                  ('_accessibility_spec.py', 'normalised_entropy')],
    'linked': [('_linkage_indicators.py', 'match_by_geometry'),
               ('_linkage_indicators.py', 'sample_point_values')],
    'utci': [('_linkage_indicators.py', 'apply_rules'),
             ('_linkage_indicators.py', 'sample_point_values')],
    'gee': [('_earth_engine_indicators.py', 'guhvi_analysis'),
            ('_earth_engine_indicators.py', 'normalise_band')],
    'lpugs': [('_earth_engine_indicators.py', 'lpugs_analysis'),
              ('_earth_engine_indicators.py', 'lpugs_indicators')],
    'walkability': [('_walkability_variants.py', 'compute_variants'),
                    ('_walkability_variants.py', 'percentile_rank')],
}
COMMON_CODE = [('_composite_index.py', 'normalise'),
               ('_composite_index.py', 'mpi_aggregate')]
RECALC = {
    'soft_walk': 'network', 'steps_walk': 'network', 'beyond_walk': 'network',
    'banded_walk': 'network', 'lpugs': 'network', 'soft_euclid': 'euclid',
    'soft_cycle': 'cycle', 'diversity': 'diversity', 'linked': 'linked',
    'utci': 'linked', 'gee': 'gee', 'walkability': 'walkability',
}
UNIT_SUFFIX = {'metres': ' m', 'm': ' m', 'percent': '%', '°C': ' °C',
               'm²': ' m²'}
LEGEND_UNIT = {'metres': 'm', 'm': 'm', 'percent': '%', '°C': '°C',
               'index 0-100': '0–100', 'index 0-1': '0–1', 'NDVI': 'NDVI',
               'm²': 'm²'}
FRONT = ['00_front.md', '01_design.md', '02_reproduce.md', '03_recipes.md']
APPENDICES = ['A_variables.md', 'B_general.md', 'C_goalposts.md',
              'D_datasets.md', 'E_glossary.md', 'F_references.md',
              'G_pending.md']


def cell(text):
    return str(text if text is not None else '').replace('\n', ' ').replace(
        '|', '\\|').strip()


def signed(value, digits=1, lang='en'):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return '–'
    text = fmt(value, digits, lang)
    return f'+{text}' if float(value) > 0 and text.strip('0.') else text


def rel(here, target):
    """Relative link from page ``here`` to ``target`` (both under a language
    folder, posix)."""
    start = PurePosixPath(here).parent
    return os.path.relpath(PurePosixPath(target), start).replace(os.sep, '/')


class Builder:
    def __init__(self, sources, results, make_maps=True, langs=LANGS):
        self.s = sources
        self.r = results
        self.make_maps = make_maps
        self.langs = langs
        self.st = sources.strings
        self.structure = sources.structure
        self.ind = {i['id']: i for i in self.structure['indicators']}
        self.order = self.structure.get('order') or list(self.ind)
        self.domains = {
            d['name']: d for d in self.structure['domains'] if d.get('name')
        }
        self.params = {
            'uli': sources.parameters('uli'),
            'uli_plain': sources.parameters('uli_plain'),
        }
        self.variants = {v['name']: v for v in self.structure.get('variants') or []}
        self.pages = {lang: {} for lang in langs}
        self.gaps = []
        self.variables = {}  # variable -> entry id
        self.facts = self.compute_facts()
        self.recipe_titles = {lang: self.read_recipe_titles(lang) for lang in langs}
        self.problems = cross_check(
            results, sources.manifest,
            [c for c in results.regions.columns if c.startswith('index_uli')],
        )

    # ------------------------------------------------------------- helpers
    def t(self, path, lang, **parts):
        node = self.st
        for key in path.split('.'):
            node = node[key]
        text = label(node, lang) if isinstance(node, dict) else str(node)
        return text.format(**parts) if parts else text

    def gap(self, lang, page, what):
        self.gaps.append((lang, page, what))

    def read_recipe_titles(self, lang):
        path = HERE / 'content' / lang / '03_recipes.md'
        if not path.exists():
            return {}
        return {
            m.group(1): m.group(2).strip()
            for m in re.finditer(r'^## (R\d+)\. (.+)$',
                                 path.read_text('utf-8'), re.M)
        }

    def compute_facts(self):
        run = yaml.safe_load((OUTPUTS / '_parameters.yml').read_text('utf-8'))
        commit = self.s.commit or ''
        regions = self.r.regions
        counts = {
            layer: pyogrio.read_info(GPKG, layer=layer)['features']
            for layer in ('grid_100m', 'agebs', 'manzanas', 'condesa_lotes',
                          'condesa_fraccionamientos')
        }
        heat = next(iter(
            ((self.s.manifest.get('attenuation') or {}).get('heat') or {}).values()
        ), {})
        observed = heat.get('observed') or [None, None]
        effective = list(self.params['uli']['effective_weights'].values())
        return {
            'software_version': run.get('software_version'),
            'software_environment': run.get('software_environment'),
            'run_date': str(run.get('date', ''))[:10],
            'commit_short': commit[:7],
            'commit_url': f'https://github.com/healthysustainablecities/global-indicators/tree/{commit}',
            'goalposts_created': str(self.params['uli']['created'])[:10],
            'sample_points': fmt(self.params['uli']['units'], 0),
            'built': date.today().isoformat(),
            'site_commit': self.s.site_commit or '–',
            'config_name': CONFIG.name,
            'study_area_km2': fmt(regions.at['mexicali', 'area_sqm'] / 1e6, 1),
            'condesa_area_km2': fmt(regions.at['condesa', 'area_sqm'] / 1e6, 2),
            'n_grid': fmt(counts['grid_100m'], 0),
            'n_agebs': fmt(counts['agebs'], 0),
            'n_manzanas': fmt(counts['manzanas'], 0),
            'n_lots': fmt(counts['condesa_lotes'], 0),
            'n_fracc': fmt(counts['condesa_fraccionamientos'], 0),
            'utci_p5': fmt(observed[0], 1),
            'utci_p95': fmt(observed[1], 1),
            'eff_min': f'{fmt(min(effective) * 100, 1)}%',
            'eff_max': f'{fmt(max(effective) * 100, 1)}%',
        }

    def entry_label(self, eid, lang):
        if eid in self.ind:
            return label(self.ind[eid]['label'], lang) or eid
        if eid.startswith('domain_'):
            return label(self.domains[eid[7:]]['label'], lang)
        if eid == 'uli':
            return label(self.structure['label'], lang)
        if eid == 'uli_plain':
            return (f"{label(self.structure['label'], lang)}: "
                    f"{label(self.variants['uli_plain']['label'], lang)}")
        return label(self.s.upstream[eid]['label'], lang)

    def link(self, eid, lang, here):
        return f'[{self.entry_label(eid, lang)}]({rel(here, f"entries/{eid}.md")})'

    def recipe_link(self, rid, lang, here):
        title = self.recipe_titles[lang].get(rid, '')
        return f'[{rid}. {title}]({rel(here, "03_recipes.md")}#{rid.lower()})'

    def code(self, file, name):
        text, url = self.s.code_link(file, name)
        return f'[`{text}`]({url}) `{name}()`'

    def cfg(self, needle, here):
        line = self.s.config_line(needle)
        path = rel(here, f'../data/{CONFIG.name}')
        return f'[`{CONFIG.name}:{line}`]({path}#L{line})'

    def resolve(self, text, lang, here):
        def sub(m):
            kind, _, arg = m.group(1).partition(':')
            if kind == 'title':
                return self.t('title', lang)
            if kind == 'subtitle':
                return self.t('subtitle', lang)
            if kind == 'fact':
                return str(self.facts[arg])
            if kind == 'code':
                file, _, name = arg.partition(':')
                return self.code(file, name)
            if kind == 'cfg':
                return self.cfg(arg, here)
            if kind == 'entry':
                return self.link(arg, lang, here)
            if kind == 'recipe':
                return self.recipe_link(arg, lang, here)
            raise KeyError(m.group(0))
        return re.sub(r'\{\{([^}]+)\}\}', sub, text)

    def units(self, column):
        return (self.s.describe(column) or {}).get('units')

    def digits(self, column):
        units = self.units(column)
        if units in ('metres', 'm', 'm²', 'persons'):
            return 0
        if units in ('percent', '°C', 'index 0-100'):
            return 1
        return 2

    def value(self, column, value, lang):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return '–'
        known = ('metres', 'm', 'm²', 'persons', 'percent', '°C', 'index 0-100',
                 'index 0-1', 'NDVI')
        digits = (self.digits(column) if self.units(column) in known
                  else digits_for([value]))
        return fmt(value, digits, lang) + UNIT_SUFFIX.get(
            self.units(column), '')

    def legend_unit(self, column, lang):
        units = self.units(column)
        if units and str(units).startswith('points'):
            return self.t('map.score_unit', lang)
        return LEGEND_UNIT.get(units, units or '')

    # ------------------------------------------------------------- results
    def results_table(self, lang, raw=None, scores=(), here=''):
        """Results section lines for a raw column and score columns."""
        t = lambda k: self.t(f'table.{k}', lang)
        rows = []
        raw_s = self.r.summary(raw, self.s.censored(raw)) if raw else None
        score_s = [(name, self.r.summary(col)) for name, col in scores]

        def region(summary, fn):
            return [fn(summary['region'].get(r)) for r in REGIONS]

        if raw_s and raw_s['region']:
            rows.append([t('region_value')] + region(
                raw_s, lambda v: self.value(raw, v, lang)))
        for name, s in score_s:
            if s['region']:
                # a penalty is not centred on the average, so takes no sign
                show = ((lambda v: fmt(v, 2, lang)) if name.endswith('_penalty')
                        else (lambda v: signed(v, 1, lang)))
                rows.append([f"{t('region_score')} (`{name}`)"] + region(s, show))
        primary = raw_s or (score_s[0][1] if score_s else None)
        column = raw if raw_s else (scores[0][1] if scores else None)
        if primary:
            m, l = primary.get('manzanas') or {}, primary.get('lots') or {}

            def areas(s, word):
                return (f"{fmt(s.get('n'), 0)} {t('of')} "
                        f"{fmt(s.get('areas'), 0)} {t(word)}") if s else '–'

            def iqr(s, fn):
                if s.get('p50') is None:
                    return '–'
                return f"{fn(s['p50'])} ({fn(s['p25'])} – {fn(s['p75'])})"

            def span(s, fn):
                if s.get('min') is None:
                    return '–'
                return f"{fn(s['min'])} – {fn(s['max'])}"

            fn = ((lambda v: self.value(column, v, lang)) if raw_s
                  else (lambda v: signed(v, 1, lang)))
            rows.append([t('areas_with_value'), areas(m, 'manzanas'),
                         areas(l, 'lots')])
            rows.append([t('median_iqr'), iqr(m, fn), iqr(l, fn)])
            rows.append([t('range'), span(m, fn), span(l, fn)])
            if raw_s and ('beyond' in m or 'beyond' in l):
                rows.append([t('beyond'),
                             f"{fmt(m.get('beyond', 0), 1)}%",
                             f"{fmt(l.get('beyond', 0), 1)}%" if l else '–'])
            if raw_s:
                for name, s in score_s:
                    sm, sl = s.get('manzanas') or {}, s.get('lots') or {}
                    fn2 = lambda v: signed(v, 1, lang)
                    rows.append([f"{t('score_median')} (`{name}`)",
                                 iqr(sm, fn2), iqr(sl, fn2)])
        lines = [f"| {t('measure')} | {t('study_region')} | {t('condesa')} |",
                 '|---|---|---|']
        lines += ['| ' + ' | '.join(cell(c) for c in row) + ' |' for row in rows]
        lines += ['', f"*{t('weighting_note')}*"]
        if raw and self.s.censored(raw):
            lines += ['', f"*{t('beyond_note')}*"]
        return lines, raw_s, score_s

    def map_figure(self, lang, here, name, column, direction, diverging,
                   caption_label):
        target = DOCS / 'figures' / lang / f'{name}.png'
        unit = self.legend_unit(column, lang)
        spec = {
            'column': column, 'breaks': self.s.breaks(column),
            'direction': direction, 'diverging': diverging, 'unit': unit,
            'title': caption_label, 'censored': self.s.censored(column),
        }
        if column not in self.r.layer('manzanas'):
            self.gap(lang, here, f'no manzana values for {column}')
            return []
        if self.make_maps or not target.exists():
            words = {k: self.t(f'map.{k}', lang) for k in
                     ('manzanas', 'lots', 'no_data', 'beyond', 'condesa')}
            maps.render(spec, self.r, target, lang, words)
        better = self.t('field.lower' if direction == 'lower_is_better'
                        else 'field.higher', lang)
        if diverging:
            caption = self.t('map.caption_score', lang, label=caption_label)
        else:
            caption = self.t('map.caption_raw', lang, label=caption_label,
                             unit=unit or '–', better=better)
        path = rel(here, f'../figures/{lang}/{name}.png')
        return [f'![{cell(caption_label)}]({path})', '', f'*{caption}*']

    # ------------------------------------------------------------- pieces
    def params_for(self, iid):
        for index in ('uli', 'uli_plain'):
            if iid in self.params[index]['indicators']:
                return index, self.params[index]['indicators'][iid]
        return None, None

    def score_columns(self, iid):
        i = self.ind[iid]
        out = []
        if i.get('active') is not False:
            out.append(('uli', i['column']))
        plain = self.variants.get('uli_plain') or {}
        column = (plain.get('indicators') or {}).get(iid)
        if column and column != i['column']:
            out.append(('uli_plain', column))
        elif iid in (plain.get('activates') or []):
            out.append(('uli_plain', f'index_uli_plain__{iid}'))
        return out

    def subdomain_text(self, i, lang):
        sub = i.get('subdomain')
        if not sub:
            return '–'
        if 'es' in sub or 'en' in sub:
            return label(sub, lang)
        return '; '.join(
            f"{label(self.domains[d]['label'], lang)}: {label(v, lang)}"
            for d, v in sub.items() if d in self.domains
        )

    def domain_shares(self, i, lang, here):
        return ', '.join(
            f"{self.link('domain_' + d, lang, here)}"
            + ('' if abs(share - 1) < 1e-9 else f' ({fmt(share * 100, 0)}%)')
            for d, share in (i.get('domains') or {}).items()
        )

    def register_lines(self, ids, lang, page):
        lines = []
        register = self.s.register
        audit = self.s.citation_audit
        for rid in ids:
            if rid not in register.index:
                self.gap(lang, page, f'register id {rid} not found')
                continue
            row = register.loc[rid]
            reason = row['reason_draft'] if isinstance(row['reason_draft'], str) else ''
            if lang == 'es':
                es = self.s.translations.get(rid)
                if es:
                    reason = f"{es} {self.t('field.draft_translation', lang)}"
                elif reason:
                    self.gap(lang, page, f'register {rid}: rationale not translated')
            if not reason:
                reason = self.t('words.not_recorded', lang)
            lines.append(f'> {reason}')
            lines.append('>')
            lines.append(f"> — *{self.t('field.register', lang)} #{rid}: "
                         f"{row['indicator']} ({row['domain']} / {row['subdomain']})*")
            cite = row['source_citation'] if isinstance(row['source_citation'], str) else ''
            if cite:
                lines.append('')
                lines.append(f"- {self.t('field.workbook_citation', lang)}: {cite}")
                if rid in audit.index:
                    a = audit.loc[rid]
                    listed = a['resolved_from_article_list']
                    if isinstance(listed, str) and listed:
                        lines.append(f"- {self.t('field.article_list', lang)}: {listed}")
                    if str(a['names_a_cited_author']).strip().lower() == 'false':
                        lines.append(f"- ⚠ {self.t('field.citation_mismatch', lang)}")
            lines.append('')
        return lines

    def sheet_lines(self, names, lang, page):
        if not names:
            return []
        try:
            rows = self.s.sheet_rows(names)
        except KeyError as e:
            self.gap(lang, page, str(e))
            return []
        lines = []
        note = ' (en inglés en la hoja)' if lang == 'es' else ''
        for _, row in rows.iterrows():
            uid = row['Unique ID']
            uid = '–' if not isinstance(uid, str) and (uid is None or math.isnan(float(uid))) else str(uid)
            lines.append(f"**{' '.join(str(row['Sub-variable']).split())}** "
                         f"({' '.join(str(row['Core measure']).split())}; ID {uid}){note}")
            for key, field in (('How to calculate', 'sheet_how'),
                               ('Notes', 'sheet_notes'),
                               ('Doubts', 'sheet_doubts')):
                value = row.get(key)
                if isinstance(value, str) and value.strip():
                    lines.append(f"- *{self.t('field.' + field, lang)}:* "
                                 f"{' '.join(value.split())}")
            lines.append('')
        return lines

    def poi_lines(self, pois, lang):
        config = self.s.config.get('points_of_interest') or {}
        lines = []
        for name in pois:
            spec = config.get(name)
            if not spec:
                continue
            data = spec.get('data', '')
            filt = data.split('-where', 1)[1].strip() if '-where' in data else ''
            path = data.split(' -where')[0]
            title = spec.get('dest_name_full') or name
            text = f"- `{name}` ({title}): `{path}`"
            if filt:
                text += f" — {self.t('field.destination_filter', lang)}: `{filt}`"
            lines.append(text)
        return lines

    @staticmethod
    def raw_direction(i):
        """Which way the measured (area) value is better: a distance scored
        through a transform is better when lower, whatever the score's
        polarity; otherwise the polarity says."""
        if i.get('soft_threshold') or i.get('steps'):
            return 'lower_is_better'
        return 'lower_is_better' if i.get('polarity') == 'negative' else 'higher_is_better'

    def configured_variable(self, iid):
        """The variable the region configuration gives an indicator now."""
        spec = self.s.config['composite_indices']['uli']['indicators']
        for item in spec:
            if item.get('name') == iid or item.get('variable') == self.ind[iid]['variable']:
                return item['variable']
        return self.ind[iid]['variable']

    def dest_name(self, variable):
        m = re.match(r'sp_walk_(?:nearest_node|beyond|access)_(.+?)(?:_\d+m)?$',
                     variable)
        return m.group(1) if m else None

    def theory(self, iid, cur, lang):
        i = self.ind[iid]
        kind = cur['kind']
        config = self.s.config
        parts = {'t': '', 'k': fmt(i.get('k') or 5, 0)}
        if i.get('soft_threshold'):
            parts['t'] = f"{fmt(i['soft_threshold'], 0)} m"
        if kind == 'steps_walk':
            within = 'a' if lang == 'es' else 'within'
            parts['steps'] = ', '.join(
                f"{fmt(score, 0)} {within} {fmt(metres, 0)} m"
                for metres, score in i['steps'])
            parts['beyond'] = fmt(i['beyond'], 0)
        if kind == 'soft_euclid':
            spec = next(d for d in config['accessibility']['euclidean']['destinations']
                        if d['name'] == cur['euclid'])
            limit = spec.get('max_distance') or max(spec['distances'])
            parts['max_distance'] = f"{fmt(limit / 1000, 0)} km"
        if kind in ('beyond_walk', 'banded_walk'):
            parts['d'] = fmt(int(re.search(r'_(\d+)m$', i['variable']).group(1)), 0)
        if kind == 'diversity':
            groups = config['accessibility']['pedestrian']['diversity'][cur['set']]['groups']
            parts.update(set=cur['set'], k_groups=len(groups),
                         groups=', '.join(f'`{g}`' for g in groups))
        if kind in ('linked', 'utci'):
            spec = config['linkage_indicators'][(cur.get('linkage') or {}).get('spec', 'utci')]
            match = spec.get('match')
            if lang == 'es':
                parts['match'] = ('por identificador' if match == 'id' else
                                  'por geometría contra las áreas de referencia')
            else:
                parts['match'] = ('by identifier' if match == 'id' else
                                  'by geometry against the reference areas')
            layers = []
            for s in spec.get('sample_points') or []:
                if isinstance(s, dict):
                    layer = s['layer']
                    layers.append(f"{layer} ({fmt(s['within'], 0)} m)" if s.get('within') else layer)
                else:
                    layers.append(str(s))
            parts['sample_points'] = ', '.join(f'`{x}`' for x in layers)
        if kind == 'walkability':
            wv = config['walkability_variants']
            low, high = wv['heat']['t']['range']
            parts.update(**{'lambda': fmt(wv['attenuation'], 1), 'low': fmt(low, 0),
                            'high': fmt(high, 0)})
        text = label(self.st['kinds'][kind]['theory'], lang)
        return text.format(**parts).rstrip().splitlines()

    def parameter_rows(self, iid, lang):
        t = lambda k: self.t(f'field.{k}', lang)
        rows = []
        for index in ('uli', 'uli_plain'):
            p = self.params[index]['indicators'].get(iid)
            if not p:
                continue
            transform = p.get('transform') or {}
            if 'soft_threshold' in transform:
                tr = self.t('scored_as.soft', lang,
                            t=f"{fmt(transform['soft_threshold'], 0)} m") + f", k = {fmt(transform.get('k', 5), 0)}"
            elif 'steps' in transform:
                tr = self.t('scored_as.steps', lang)
            else:
                tr = self.t('scored_as.as_is', lang)
            span = abs(p['max'] - p['min'])
            d = 0 if span >= 100 else (1 if span >= 10 else 3)
            goal = ' · '.join(fmt(p[k], d) for k in ('min', 'reference', 'max'))
            obs = f"{fmt(p['inf'], d)} – {fmt(p['sup'], d)}"
            dist = p.get('distribution') or {}
            flags = ', '.join(dist.get('flags') or []) or t('none')
            rows.append([f'`{index}`', p['variable'], tr, goal, obs,
                         f"{fmt(dist.get('skewness'), 2)} / {fmt(dist.get('kurtosis'), 2)} / {fmt((dist.get('tied_share') or 0) * 100, 1)}%",
                         flags])
        if not rows:
            return []
        head = ['', t('sample_point'), t('transform'), t('goalposts'),
                'inf – sup',
                'skew / kurt. / tied' if lang == 'en' else 'asim. / curt. / empates',
                t('flags')]
        lines = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
        lines += ['| ' + ' | '.join(cell(c) for c in r) + ' |' for r in rows]
        return lines

    def sentences(self, lang, i, raw_s, score_s, raw):
        out = []
        reading = label(i.get('reading'), lang) if i else ''
        cols = (i or {}).get('reading_columns') or {}
        if reading and raw_s:
            for region, key in (('mexicali', 'reading_mx'), ('condesa', 'reading_cd')):
                parts = {}
                for name, column in cols.items():
                    v = self.r.region_values(column).get(region)
                    parts[name] = self.value(column, v, lang)
                if 'value' not in parts:
                    parts['value'] = self.value(raw, raw_s['region'].get(region), lang)
                text = re.sub(r'\{(\w+)\}', lambda m: parts.get(m.group(1), '–'), reading)
                out.append(self.t(f'summary.{key}', lang, text=text))
        if score_s:
            name, s = score_s[0]
            mxs, cds = s['region'].get('mexicali'), s['region'].get('condesa')
            if cds is not None and raw_s:
                direction = self.t('words.points_above' if cds >= 0 else 'words.points_below', lang)
                out.append(self.t(
                    'summary.mexicali_vs_condesa', lang,
                    mx=self.value(raw, raw_s['region'].get('mexicali'), lang),
                    cd=self.value(raw, raw_s['region'].get('condesa'), lang),
                    gap=fmt(abs(cds), 1), direction=direction,
                    mxs=signed(mxs, 1, lang)))
        return out

    # ------------------------------------------------------------- pages
    def indicator_page(self, iid, lang):
        here = f'entries/{iid}.md'
        i = self.ind[iid]
        cur = self.s.curation['indicators'].get(iid)
        if not cur:
            raise KeyError(f'{iid} has no entry in entries.yml')
        f = lambda k: self.t(f'field.{k}', lang)
        e = lambda k: self.t(f'entry.{k}', lang)
        title = self.entry_label(iid, lang)
        if not label(i.get('label'), lang):
            self.gap(lang, here, 'label')
        lines = [f'# {title}', '', f"[← {e('back')}](../README.md)", '']
        about = label(i.get('about'), lang)
        if about:
            lines += [f'> {about}', '']
        else:
            self.gap(lang, here, 'about')
        # identity
        score_cols = self.score_columns(iid)
        sheet_ids = []
        try:
            raw_ids = self.s.sheet_rows(cur.get('sheet') or [])['Unique ID'].dropna()
            for value in raw_ids:
                for part in re.split(r'[,;]', str(value)):
                    part = part.strip()
                    if part and part not in sheet_ids:
                        sheet_ids.append(part)
        except KeyError:
            pass
        eff_plain = (self.variants.get('uli_plain') or {}).get('effective_weights', {}).get(iid)
        eff = i.get('effective_weight') if i.get('active') is not False else None
        weight = ' · '.join(x for x in [
            f"`uli` {fmt(eff * 100, 1)}%" if eff else '',
            f"`uli_plain` {fmt(eff_plain * 100, 1)}%" if eff_plain else '',
        ] if x) or '–'
        better = f('higher') if i.get('polarity') != 'negative' else f('lower')
        raw_better = f('lower') if self.raw_direction(i) == 'lower_is_better' else f('higher')
        if i.get('soft_threshold') or i.get('steps'):
            better_text = (f"valor medido {raw_better} (puntuación transformada {better})" if lang == 'es'
                           else f"measured value {raw_better} (transformed score {better})")
        else:
            better_text = raw_better
        status = f('active') if i.get('active') is not False else (
            f"{f('inactive')}: {label(i.get('inactive_reason'), lang)}")
        rows = [
            (f('id'), f'`{iid}`'),
            (f('core_measure'), label(i.get('group'), lang) or '–'),
            (f('sheet_ids'), ' · '.join(x for x in [
                ', '.join(sheet_ids),
                ', '.join(f'#{r}' for r in cur.get('register') or []),
            ] if x) or '–'),
            (f('sample_point'), f"`{i['variable']}`"),
            (f('area'), f"`{i.get('area_column')}`" + (f" ({self.legend_unit(i['area_column'], lang)})" if i.get('area_column') else '')),
        ]
        for name, column in score_cols:
            rows.append((f('score') if name == 'uli' else f('score_plain'), f'`{column}`'))
        rows += [
            (f('domains'), self.domain_shares(i, lang, here)),
            (f('subdomain'), self.subdomain_text(i, lang)),
            (f('lens'), label(self.st['lens'].get(i.get('lens')), lang) or '–'),
            (f('polarity'), better_text),
            (f('weight'), weight),
            (f('status'), status),
        ]
        lines += [f"## {e('identity')}", '', '| | |', '|---|---|']
        lines += [f'| {a} | {cell(b)} |' for a, b in rows]
        lines.append('')
        for v in [i['variable'], i.get('area_column')] + [c for _, c in score_cols]:
            if v:
                self.variables.setdefault(v, iid)
        # rationale
        lines += [f"## {e('rationale')}", '']
        reg = self.register_lines(cur.get('register') or [], lang, here)
        if reg:
            lines += reg
        else:
            lines += [f"*{self.t('words.pending', lang)}: {self.t('words.not_recorded', lang)}*", '']
            self.gap(lang, here, 'no register rationale')
        reading = label(i.get('reading'), lang)
        if reading:
            text = reading.replace('{value}', '…').replace('{access}', '…')
            # a reading that already says which way is better needs no gloss
            gloss = '' if '(' in text else (
                f" ({raw_better} {'es mejor' if lang == 'es' else 'is better'})")
            lines += [f"**{f('reading')}.** {text}{gloss}.", '']
        lines += self.sheet_lines(cur.get('sheet') or [], lang, here)
        # data sources
        lines += [f"## {e('sources')}", '']
        srcs = i.get('sources') or []
        if srcs:
            lines += [f"**{f('config_sources')}:**", ''] + [f'- {s}' for s in srcs] + ['']
        dd = self.s.dictionary
        area = i.get('area_column')
        if area in dd.index and isinstance(dd.at[area, 'source'], str):
            lines += [f"**{f('dictionary_source')}** (`{area}`):", '',
                      f"- {dd.at[area, 'source']}", '']
        elif area:
            self.gap(lang, here, f'no dictionary source for {area}')
        pois = self.poi_lines(cur.get('pois') or [], lang)
        if pois:
            lines += [f"**{f('destination_filter')}:**", ''] + pois + ['']
        if cur.get('upstream'):
            lines += [f"**{e('upstream')}:** " + ', '.join(
                self.link(u, lang, here) for u in cur['upstream']), '']
        # theory
        lines += [f"## {e('theory')}", ''] + self.theory(iid, cur, lang) + ['']
        if i.get('active') is False:
            lines += [f"*{self.t('words.inactive_note', lang)}*", '']
        # practice
        recipes = KIND_RECIPES[cur['kind']] + COMMON_RECIPES
        lines += [f"## {e('practice')}", '',
                  f"**{f('recipes')}:** " + ', '.join(self.recipe_link(r, lang, here) for r in recipes), '']
        configured = self.configured_variable(iid)
        block, line = self.s.config_block(f"- variable: {configured}")
        lines += [f"**{f('config')}** ({self.cfg('- variable: ' + configured, here)}):", '',
                  '```yaml', block, '```', '']
        if configured != i['variable']:
            self.gap(lang, here, f"configuration now names {configured}; results use {i['variable']}")
            lines += [('*La configuración actual nombra esta variable `{c}`; los resultados publicados se produjeron con `{v}`, antes de que se acortara el nombre para respetar el límite de 63 caracteres de PostgreSQL. Volver a ejecutar el análisis adopta el nombre nuevo.*'
                       if lang == 'es' else
                       "*The current configuration names this variable `{c}`; the published results were produced with `{v}`, before the name was shortened to respect PostgreSQL's 63-character identifier limit. Re-running the analysis adopts the new name.*").format(
                c=configured, v=i['variable']), '']
        dest = self.dest_name(i['variable'])
        if dest:
            try:
                spec_line = self.s.config_line('{name: ' + dest + ',')
                text = self.s.config_text.splitlines()[spec_line - 1].strip()
                lines += [f"{self.cfg('{name: ' + dest + ',', here)}:", '', '```yaml', text, '```', '']
            except KeyError:
                pass
        code = KIND_CODE[cur['kind']] + COMMON_CODE
        lines += [f"**{f('code')}:**", ''] + [f'- {self.code(a, b)}' for a, b in code] + ['']
        lines += self.parameter_rows(iid, lang) + ['']
        # recalculation
        lines += [f"## {e('recalculation')}", '',
                  self.t(f"recalculation.{RECALC[cur['kind']]}", lang), '',
                  self.t('recalculation.common', lang), '']
        # results
        lines += [f"## {e('results')}", '']
        table, raw_s, score_s = self.results_table(lang, area, score_cols, here)
        lines += table + ['']
        lines += [f'- {s}' for s in self.sentences(lang, i, raw_s, score_s, area)] + ['']
        # map
        if area:
            lines += [f"## {e('map')}", '']
            lines += self.map_figure(lang, here, iid, area, self.raw_direction(i),
                                     False, title) + ['']
        # caveats
        caveats = [label(c, lang) for c in cur.get('caveats') or []]
        if caveats:
            lines += [f"## {e('caveats')}", ''] + [f'- {c}' for c in caveats] + ['']
        return here, '\n'.join(lines)

    def domain_page(self, name, lang):
        here = f'entries/domain_{name}.md'
        d = self.domains[name]
        e = lambda k: self.t(f'entry.{k}', lang)
        t = lambda k: self.t(f'table.{k}', lang)
        lines = [f"# {label(d['label'], lang)}", '', f"[← {e('back')}](../README.md)", '']
        if d.get('about'):
            lines += [f"> {label(d['about'], lang)}", '']
        subs = d.get('subdomains') or {}
        if subs:
            lines += [f"## {e('subdomains')}", '']
            lines += [f"- **{label(s['label'], lang)}.** {label(s.get('about'), lang)}" for s in subs.values()]
            lines.append('')
        members = [i for i in self.structure['indicators'] if name in (i.get('domains') or {})]
        if d.get('scored') is False or not members:
            note = ('Este dominio aún no tiene indicadores: se describe pero no se puntúa, de modo que el índice es el compuesto de seis dominios (Anexo G).'
                    if lang == 'es' else
                    'This domain has no indicator yet: it is described but not scored, so the index is the composite of six domains (Appendix G).')
            lines += [f'*{note}*', '', f"[{self.t('sections.pending', lang)}](../G_pending.md)", '']
            return here, '\n'.join(lines)
        lines += [f"## {e('members')}", '',
                  f"| {t('indicator')} | {self.t('field.subdomain', lang)} | {t('share')} | {t('effective')} | {self.t('field.polarity', lang)} |",
                  '|---|---|---|---|---|']
        for iid in self.order:
            i = self.ind.get(iid)
            if not i or name not in (i.get('domains') or {}):
                continue
            share = i['domains'][name]
            eff = i.get('effective_weight') if i.get('active') is not False else None
            sub = i.get('subdomain') or {}
            sub = label(sub.get(name, sub) if name in sub else sub, lang) if sub else '–'
            mark = '' if i.get('active') is not False else ' *(inactivo en `uli`)*' if lang == 'es' else ' *(inactive in `uli`)*'
            lines.append(
                f"| {self.link(iid, lang, here)}{mark} | {cell(sub)} | {fmt(share * 100, 0)}% | "
                f"{fmt(eff * 100, 1) + '%' if eff else '–'} | "
                f"{self.t('field.higher' if i.get('polarity') != 'negative' else 'field.lower', lang)} |")
        lines.append('')
        theory = (
            'La puntuación del dominio es el compuesto ponderado de Mazziotta–Pareto de las puntuaciones normalizadas de sus indicadores (R12): cada indicador pesa `weight × parte`, normalizado sobre los indicadores con valor; `M` es su media ponderada, `S` su desviación ponderada y la puntuación es `M − S·(S/M)`, menos 100. En la variante `uli_plain` la caminabilidad no se atenúa y, en el entorno medioambiental, se activa el confort térmico.'
            if lang == 'es' else
            "The domain score is the weighted Mazziotta–Pareto composite of its indicators' normalised scores (R12): each indicator weighs `weight × share`, normalised over the indicators with a value; `M` is their weighted mean, `S` their weighted deviation, and the score is `M − S·(S/M)`, less 100. In the `uli_plain` variant walkability is not attenuated and, in the ambient environment, thermal comfort is activated.")
        lines += [f"## {e('theory')}", '', theory, '',
                  f"**{self.t('field.recipes', lang)}:** " + ', '.join(self.recipe_link(r, lang, here) for r in ('R11', 'R12', 'R13', 'R14')),
                  '', f"**{self.t('field.code', lang)}:** {self.code('_composite_index.py', 'score')}, {self.code('_composite_index.py', 'mpi_aggregate')}", '']
        cols = [('uli', d['column'])]
        plain = (self.variants.get('uli_plain') or {}).get('domains', {}).get(name)
        if plain:
            cols.append(('uli_plain', plain))
        for _, c in cols:
            self.variables.setdefault(c, f'domain_{name}')
        lines += [f"## {e('results')}", '']
        table, _, score_s = self.results_table(lang, None, cols, here)
        lines += table + ['']
        s = score_s[0][1]['region']
        if s.get('condesa') is not None:
            word = self.t('words.points_above' if s['condesa'] >= 0 else 'words.points_below', lang)
            lines += [('- La región de estudio puntúa {mx}; Condesa queda {gap} {dir} del promedio de la región de estudio.'
                       if lang == 'es' else
                       '- The study region scores {mx}; Condesa lies {gap} {dir} the study region average.').format(
                mx=signed(s.get('mexicali'), 1, lang), gap=fmt(abs(s['condesa']), 1), dir=word), '']
        lines += [f"## {e('map')}", '']
        lines += self.map_figure(lang, here, f'domain_{name}', d['column'], 'higher_is_better', True,
                                 label(d['label'], lang)) + ['']
        return here, '\n'.join(lines)

    def index_page(self, name, lang):
        here = f'entries/{name}.md'
        e = lambda k: self.t(f'entry.{k}', lang)
        st = self.structure
        variant = self.variants.get(name) or {}
        columns = variant.get('columns') or st['columns']
        title = self.entry_label(name, lang)
        lines = [f'# {title}', '', f"[← {e('back')}](../README.md)", '']
        lines += [f"> {label(st.get('description'), lang)}", '', label(st.get('about'), lang), '']
        if name == 'uli_plain':
            text = ('Variante del índice en la que la caminabilidad no se atenúa por confort térmico (`sp_walk_idx_300`) y el confort térmico diurno (`sp_utci_day_mean`) se puntúa como indicador del entorno medioambiental, de modo que el confort térmico cuenta exactamente una vez. Se puntúa contra sus propias metas.'
                    if lang == 'es' else
                    'A variant of the index in which walkability is not attenuated by thermal comfort (`sp_walk_idx_300`) and daytime thermal comfort (`sp_utci_day_mean`) is scored as an ambient environment indicator instead, so that thermal comfort counts exactly once. It is scored against its own goalposts.')
            lines += [text, '']
        else:
            text = ('Índice publicado: la caminabilidad entra atenuada por el confort térmico diurno (`sp_walk_idx_300_tm`), y el confort térmico no se puntúa por separado. Véase también la variante ' if lang == 'es'
                    else 'The published index: walkability enters attenuated by daytime thermal comfort (`sp_walk_idx_300_tm`), and thermal comfort is not scored separately. See also the variant ')
            lines += [text + self.link('uli_plain', lang, here) + '.', '']
        # structure table
        t = lambda k: self.t(f'table.{k}', lang)
        lines += [f"## {self.t('sections.domains', lang)[3:]}", '',
                  f"| {self.t('sections.domains', lang)[3:]} | n | {t('region_score')}: {t('study_region')} | {t('condesa')} |",
                  '|---|---|---|---|']
        dom_cols = variant.get('domains') or {d: self.domains[d]['column'] for d in self.domains}
        for dname, dd in self.domains.items():
            members = [i for i in self.structure['indicators'] if dname in (i.get('domains') or {})
                       and (i.get('active') is not False or name == 'uli_plain')]
            col = dom_cols.get(dname)
            vals = self.r.region_values(col) if col else {}
            lines.append(f"| {self.link('domain_' + dname, lang, here)} | {len(members) if col else '–'} | "
                         f"{signed(vals.get('mexicali'), 1, lang) if col else '–'} | {signed(vals.get('condesa'), 1, lang) if col else '–'} |")
        lines.append('')
        formula = ('```text\n'
                   'r_i      = 100 ± 60 · (x_i − Ref_i) / (Max_i − Min_i)                 (R11)\n'
                   'domain_d = M_d − S_d · (S_d / M_d),  w_i ∝ weight_i · share_{i,d}       (R12)\n'
                   'index    = M − S · (S / M)  over the six scored domains, equal weights\n'
                   'reported = index − 100   (0 = study region average)\n'
                   '```')
        lines += [f"## {e('theory')}", '', formula, '',
                  f"**{self.t('field.recipes', lang)}:** " + ', '.join(self.recipe_link(f'R{n}', lang, here) for n in range(10, 15)), '']
        lines += [f"## {e('practice')}", '',
                  f"**{self.t('field.config', lang)}:** {self.cfg('composite_indices:', here)}; "
                  f"[`{CODENAME}_composite_{name}_parameters.yml`]({rel(here, f'../data/{CODENAME}_composite_{name}_parameters.yml')})", '',
                  f"**{self.t('field.code', lang)}:** " + ', '.join(self.code('_composite_index.py', f) for f in ('resolve_parameters', 'score', 'mpi_aggregate', 'propagate')), '']
        lines += [f"## {e('recalculation')}", '', self.t('recalculation.common', lang), '',
                  self.recipe_link('R14', lang, here), '']
        cols = [(name, columns['index']), (f'{name}_mean', columns['mean']),
                (f'{name}_penalty', columns['penalty'])]
        for _, c in cols:
            self.variables.setdefault(c, name)
        lines += [f"## {e('results')}", '']
        table, _, score_s = self.results_table(lang, None, cols, here)
        lines += table + ['']
        s = score_s[0][1]['region']
        word = self.t('words.points_above' if (s.get('condesa') or 0) >= 0 else 'words.points_below', lang)
        lines += [('- La región de estudio (Mexicali con Condesa) puntúa {mx}, y Condesa {cd}: {gap} {dir} del promedio de la región de estudio. La penalización mide el desequilibrio entre dominios (`_penalty`, sin centrar).'
                   if lang == 'es' else
                   '- The study region (Mexicali with Condesa) scores {mx}, and Condesa {cd}: {gap} {dir} the study region average. The penalty measures imbalance between domains (`_penalty`, not centred).').format(
            mx=signed(s.get('mexicali'), 1, lang), cd=signed(s.get('condesa'), 1, lang),
            gap=fmt(abs(s.get('condesa') or 0), 1), dir=word), '']
        lines += [f"## {e('map')}", '']
        lines += self.map_figure(lang, here, name, columns['index'], 'higher_is_better', True, title) + ['']
        provisional = label((self.s.indicators_json['text']['methods'] or {}).get('provisional'), lang)
        if name == 'uli' and st.get('sources'):
            lines += [f"## {self.t('field.config_sources', lang)}", ''] + [f'- {x}' for x in st['sources']] + ['']
        if provisional:
            lines += [f"## {e('caveats')}", '', f'- {provisional}', '']
        return here, '\n'.join(lines)

    def upstream_page(self, uid, lang):
        here = f'entries/{uid}.md'
        u = self.s.upstream[uid]
        e = lambda k: self.t(f'entry.{k}', lang)
        t = lambda k: self.t(f'table.{k}', lang)
        lines = [f"# {label(u['label'], lang)}", '', f"[← {e('back')}](../README.md)", '',
                 label(u['about'], lang).rstrip(), '']
        if u.get('variables'):
            lines += [f"| {self.t('field.sample_point', lang)} | {self.t('field.area', lang)} | {t('description')} | {t('study_region')} | {t('condesa')} |",
                      '|---|---|---|---|---|']
            for sp, area in u['variables']:
                desc = self.s.describe(area)
                text = label(desc, lang) if desc else ''
                vals = self.r.region_values(area)
                lines.append(f"| `{sp}` | `{area}` | {cell(text)} | {self.value(area, vals.get('mexicali'), lang)} | {self.value(area, vals.get('condesa'), lang)} |")
                self.variables.setdefault(sp, uid)
                self.variables.setdefault(area, uid)
            lines.append('')
        if u.get('table'):
            lines += getattr(self, f"table_{u['table']}")(lang, here) + ['']
        lines += [f"## {e('practice')}", '',
                  f"**{self.t('field.recipes', lang)}:** " + ', '.join(self.recipe_link(r, lang, here) for r in u.get('recipes') or []), '']
        for needle in u.get('config') or []:
            block, _ = self.s.config_block(needle)
            if block.count('\n') > 80:
                block = '\n'.join(block.splitlines()[:80]) + '\n# …'
            lines += [f"**{self.t('field.config', lang)}** ({self.cfg(needle, here)}):", '', '```yaml', block, '```', '']
        if u.get('code'):
            lines += [f"**{self.t('field.code', lang)}:**", ''] + [f'- {self.code(a, b)}' for a, b in u['code']] + ['']
        users = [iid for iid in self.order
                 if uid in ((self.s.curation['indicators'].get(iid) or {}).get('upstream') or [])]
        if users:
            lines += [f"## {e('used_by')}", '', ', '.join(self.link(x, lang, here) for x in users), '']
        if u.get('map'):
            m = u['map']
            lines += [f"## {e('results')}", '']
            table, _, _ = self.results_table(lang, m['column'], (), here)
            lines += table + ['', f"## {e('map')}", '']
            lines += self.map_figure(lang, here, uid, m['column'], m['direction'], False,
                                     label(u['label'], lang)) + ['']
        return here, '\n'.join(lines)

    # ------------------------------------------------------------- tables
    def table_denue(self, lang, here):
        pois = self.s.config.get('points_of_interest') or {}
        users = {}
        for iid, cur in self.s.curation['indicators'].items():
            for p in cur.get('pois') or []:
                users.setdefault(p, []).append(iid)
        head = (['Destino', 'Nombre', 'Filtro SCIAN (OGR)', 'Lo usan'] if lang == 'es'
                else ['Destination', 'Name', 'SCIAN filter (OGR)', 'Used by'])
        lines = ['| ' + ' | '.join(head) + ' |', '|---|---|---|---|']
        for name, spec in pois.items():
            if not name.startswith('denue_'):
                continue
            data = spec.get('data', '')
            filt = data.split('-where', 1)[1].strip() if '-where' in data else ('(todos)' if lang == 'es' else '(all)')
            lines.append(f"| `{name}` | {cell(spec.get('dest_name_full'))} | `{cell(filt)}` | "
                         + ', '.join(self.link(x, lang, here) for x in users.get(name, [])) + ' |')
        return lines

    def table_diversity(self, lang, here):
        sets = self.s.config['accessibility']['pedestrian']['diversity']
        head = (['Conjunto', 'Subtipo', 'Filtro (SQL)'] if lang == 'es' else ['Set', 'Sub-type', 'Filter (SQL)'])
        lines = ['| ' + ' | '.join(head) + ' |', '|---|---|---|']
        for name, spec in sets.items():
            for g, where in spec['groups'].items():
                lines.append(f"| `{name}` (k = {len(spec['groups'])}) | `{g}` | `{cell(where)}` |")
        return lines

    def table_guhvi(self, lang, here):
        regions = self.r.regions
        cols = [c for c in regions.columns if c.startswith('urban_heat_')]
        head = (['Variable', 'Descripción', 'Región de estudio', 'Condesa'] if lang == 'es'
                else ['Variable', 'Description', 'Study region', 'Condesa'])
        lines = ['| ' + ' | '.join(head) + ' |', '|---|---|---|---|']
        for c in cols:
            vals = self.r.region_values(c)
            lines.append(f"| `{c}` | {cell(label(self.s.describe(c), lang))} | {self.value(c, vals.get('mexicali'), lang)} | {self.value(c, vals.get('condesa'), lang)} |")
        return lines

    def _linkage_table(self, spec_name, lang):
        spec = self.s.config['linkage_indicators'][spec_name]
        head = (['Columna', 'Nombre', 'Unidades', 'Dirección'] if lang == 'es'
                else ['Column', 'Name', 'Units', 'Direction'])
        lines = ['| ' + ' | '.join(head) + ' |', '|---|---|---|---|']
        for c, cs in (spec.get('columns') or {}).items():
            lines.append(f"| `{spec.get('prefix', '')}{c}` | {cell(label(cs.get('label'), lang))} | {cell(cs.get('units'))} | {cell(cs.get('direction', '–'))} |")
        extra = []
        for key in ('data', 'match', 'id', 'reference', 'mask', 'null_as', 'source', 'licence', 'notes'):
            if spec.get(key) is not None:
                extra.append(f"- `{key}`: {cell(spec[key])}")
        return lines + [''] + extra

    def table_linkage_utci(self, lang, here):
        return self._linkage_table('utci', lang)

    def table_linkage_external(self, lang, here):
        return self._linkage_table('external', lang)

    def table_euclid(self, lang, here):
        specs = self.s.config['accessibility']['euclidean']['destinations']
        lines = []
        for spec in specs:
            lines.append(f"- **`{spec['name']}`** ({spec.get('dest_name_full')}): `{spec['data']}`; "
                         + ('distancias' if lang == 'es' else 'distances') + f" {spec.get('distances')}"
                         + (f", max_distance {spec['max_distance']}" if spec.get('max_distance') else '')
                         + f". {spec.get('notes', '')} ({spec.get('source')}; {spec.get('licence')})")
        return lines

    # ------------------------------------------------------------- appendices
    def appendix_variables(self, lang):
        here = 'A_variables.md'
        t = lambda k: self.t(f'table.{k}', lang)
        for c in self.s.indicators_json['descriptions']:
            if c.startswith('index_uli') and c not in self.variables:
                self.gap(lang, here, f'{c} has no entry')
        lines = [f"# {self.t('sections.variables', lang)}", '',
                 f"| {t('variable')} | {t('entry')} |", '|---|---|']
        for v in sorted(self.variables):
            lines.append(f'| `{v}` | {self.link(self.variables[v], lang, here)} |')
        return here, '\n'.join(lines)

    def appendix_general(self, lang):
        here = 'B_general.md'
        dd = self.s.dictionary
        intro = ('Todas las variables del tablero general y del GeoPackage de resultados, del diccionario de datos (`outputs/mexicali_uli_ghsci_data_dictionary.csv`), agrupadas por categoría. Las variables del ULI tienen su propia entrada (Anexo A).'
                 if lang == 'es' else
                 'Every variable of the general dashboard and the results GeoPackage, from the data dictionary (`outputs/mexicali_uli_ghsci_data_dictionary.csv`), grouped by category. ULI variables have their own entries (Appendix A).')
        lines = [f"# {self.t('sections.general', lang)}", '', intro, '']
        desc_col = 'description_es' if lang == 'es' else 'description'
        for category, group in dd.groupby('category', sort=False):
            lines += [f'## {category}', '', f"| {self.t('table.variable', lang)} | {self.t('table.description', lang)} | {self.t('field.units', lang)} |", '|---|---|---|']
            for _, row in group.iterrows():
                lines.append(f"| `{row['variable']}` | {cell(row[desc_col] if isinstance(row[desc_col], str) else row['description'])} | {cell(row['units'] if isinstance(row['units'], str) else '')} |")
            lines.append('')
        return here, '\n'.join(lines)

    def appendix_goalposts(self, lang):
        here = 'C_goalposts.md'
        t = lambda k: self.t(f'table.{k}', lang)
        intro = ('Metas y pesos efectivos de cada índice, tal como los escribió el análisis (`data/`). Las metas están en la escala que se puntúa: la puntuación de acceso suave (0 a 1) donde hay umbral, la escala escalonada donde la hay, y si no el valor medido. Ref. es el promedio de la región de estudio y puntúa 0.'
                 if lang == 'es' else
                 'Goalposts and effective weights of each index, as the analysis wrote them (`data/`). Goalposts are on the scale scored: the soft access score (0 to 1) where there is a threshold, the ladder where there is one, otherwise the value as measured. Ref is the study region average, and scores 0.')
        lines = [f"# {self.t('sections.goalposts', lang)}", '', intro, '']
        for index in ('uli', 'uli_plain'):
            p = self.params[index]
            lines += [f'## `{index}`', '',
                      ('Metas resueltas el {c} a partir de {n} puntos de muestra; método `{m}`, centro {z}.' if lang == 'es'
                       else 'Goalposts resolved on {c} from {n} sample points; method `{m}`, centre {z}.').format(
                          c=str(p['created'])[:10], n=fmt(p['units'], 0), m=p['method'], z=fmt(p['centre'], 0)), '',
                      f"| {t('indicator')} | {t('variable')} | {self.t('field.domains', lang)} | {t('scored_as')} | {t('min_ref_max')} | {t('effective')} |",
                      '|---|---|---|---|---|---|']
            for iid, spec in p['indicators'].items():
                transform = spec.get('transform') or {}
                if 'soft_threshold' in transform:
                    scored = self.t('scored_as.soft', lang, t=f"{fmt(transform['soft_threshold'], 0)} m")
                elif 'steps' in transform:
                    scored = self.t('scored_as.steps', lang)
                else:
                    scored = self.t('scored_as.as_is', lang)
                span = abs(spec['max'] - spec['min'])
                d = 0 if span >= 100 else (1 if span >= 10 else 3)
                shares = ', '.join(f"{label(self.domains[k]['label'], lang)}{'' if abs(v - 1) < 1e-9 else f' ({fmt(v * 100, 0)}%)'}"
                                   for k, v in spec['domains'].items())
                lines.append(f"| {self.link(iid, lang, here)} | `{spec['variable']}` | {cell(shares)} | {cell(scored)} | "
                             f"{' · '.join(fmt(spec[k], d) for k in ('min', 'reference', 'max'))} | "
                             f"{fmt(p['effective_weights'].get(iid, 0) * 100, 1)}% |")
            lines.append('')
        return here, '\n'.join(lines)

    def appendix_datasets(self, lang):
        here = 'D_datasets.md'
        c = self.s.config
        intro = ('Registros de los conjuntos de datos tal como están en la configuración de la región, sin modificar. Cada conjunto conserva su propia licencia.'
                 if lang == 'es' else
                 "Dataset records as they stand in the region configuration, unaltered. Each dataset keeps its own licence.")
        lines = [f"# {self.t('sections.datasets', lang)}", '', intro, '']
        keys = ('name', 'data', 'data_dir', 'source', 'publication_date', 'year_published',
                'url', 'source_url', 'licence', 'citation', 'notes', 'note')

        def record(title, spec, needle=None):
            out = [f'## {title}', '']
            if needle:
                out += [self.cfg(needle, here), '']
            for k in keys:
                if spec.get(k) not in (None, ''):
                    out.append(f"- `{k}`: {cell(spec[k])}")
            return out + ['']

        lines += record('Study region boundary' if lang == 'en' else 'Límite de la región de estudio', c['study_region_boundary'], 'study_region_boundary:')
        lines += record('Exclusion region' if lang == 'en' else 'Región de exclusión', c['exclusion_region'], 'exclusion_region:')
        lines += record('Population' if lang == 'en' else 'Población', c['population'], 'population:')
        lines += record('OpenStreetMap', c['OpenStreetMap'], 'OpenStreetMap:')
        pois = c.get('points_of_interest') or {}
        lines += record('IMIP: public transport stops (pt_any)' if lang == 'en' else 'IMIP: paradas de transporte público (pt_any)', pois['pt_any'], '  pt_any:')
        lines += record('INEGI DENUE (May 2026)' if lang == 'en' else 'INEGI DENUE (mayo de 2026)', pois['denue_fresh_food'], 'denue_fresh_food: &denue')
        for spec in c['accessibility']['euclidean']['destinations']:
            lines += record(f"{spec.get('dest_name_full')} (`{spec['name']}`)", spec)
        for name, spec in c['linkage_indicators'].items():
            lines += record(f"{label(spec.get('label'), lang)} (`{name}`)", spec, f'  {name}:')
        lines += [('## Agregaciones personalizadas' if lang == 'es' else '## Custom aggregations'), '']
        for name, spec in c['custom_aggregations'].items():
            lines.append(f"- **`{name}`**: `{spec.get('data')}` — {cell(spec.get('notes', ''))}")
        lines.append('')
        gee = ('## Google Earth Engine\n\nLos indicadores GUHVI y de grandes espacios verdes públicos se calculan en Google Earth Engine (`gee: true`) a partir de colecciones de Landsat 8, MODIS y Sentinel-2; la configuración de la región no declara un registro de datos para ellos. Las fuentes que GHSCI registra están en el diccionario de datos.'
               if lang == 'es' else
               '## Google Earth Engine\n\nThe GUHVI and large public green space indicators are computed in Google Earth Engine (`gee: true`) from Landsat 8, MODIS and Sentinel-2 collections; the region configuration declares no dataset record for them. The sources GHSCI records are in the data dictionary.')
        lines += [gee, '']
        return here, '\n'.join(lines)

    def appendix_references(self, lang):
        here = 'F_references.md'
        sys.path.insert(0, str(SITE / 'dashboard' / 'build'))
        import technical_report  # noqa: E402
        lines = [f"# {self.t('sections.references', lang)}", '']
        lines += [('## Métodos' if lang == 'es' else '## Methods'), '']
        seen = set()
        for x in self.structure.get('sources') or []:
            lines.append(f'- {x}')
            seen.add(x)
        for text, doi, _, _ in technical_report.references(SITE / 'dashboard'):
            if text in seen:
                continue
            seen.add(text)
            lines.append(f'- {text}' + (f' doi:[{doi}](https://doi.org/{doi})' if doi else ''))
        lines += ['', ('*Los DOI provienen de `dashboard/js/model.js` y no se han verificado de forma independiente.*' if lang == 'es'
                       else '*DOIs are as recorded in `dashboard/js/model.js` and have not been independently verified.*'), '']
        lines += [('## Fuentes de los indicadores' if lang == 'es' else '## Indicator sources'), '']
        for iid in self.order:
            for x in self.ind[iid].get('sources') or []:
                if x not in seen:
                    seen.add(x)
                    lines.append(f'- {x}')
        lines += ['', ('## Literatura citada en el registro de indicadores' if lang == 'es'
                       else '## Literature cited in the indicator register'), '']
        cites = set()
        for cur in self.s.curation['indicators'].values():
            for rid in cur.get('register') or []:
                if rid in self.s.register.index:
                    c = self.s.register.at[rid, 'source_citation']
                    if isinstance(c, str):
                        for part in c.split('; '):
                            if part.strip() and not part.startswith(('Not reported', 'No external')):
                                cites.add(part.strip())
        lines += [f'- {c}' for c in sorted(cites)]
        lines += ['', ('*Citas del libro de trabajo del proyecto; varias no coinciden con la lista de artículos (citation_audit.csv) y deben verificarse antes de citarlas.*' if lang == 'es'
                       else "*Citations as given in the project workbook; several do not match the article list (citation_audit.csv) and should be verified before being cited.*"), '']
        return here, '\n'.join(lines)

    def content_page(self, name, lang):
        path = HERE / 'content' / lang / name
        if not path.exists():
            self.gap(lang, name, 'content fragment missing')
            path = HERE / 'content' / 'en' / name
        return name, self.resolve(path.read_text('utf-8'), lang, name)

    def readme(self, lang, entries):
        here = 'README.md'
        lines = [f"# {self.t('title', lang)}", '', f"**{self.t('subtitle', lang)}**", '',
                 self.t('other_language', lang), '',
                 f"PDF: [`mexicali_uli_manual_{lang}.pdf`](../pdf/mexicali_uli_manual_{lang}.pdf)", '',
                 f"## {self.t('contents', lang)}", '']
        for key, file in (('front', '00_front.md'), ('design', '01_design.md'),
                          ('reproduce', '02_reproduce.md'), ('recipes', '03_recipes.md')):
            lines.append(f"- [{self.t('sections.' + key, lang)}]({file})")
            if key == 'recipes':
                for rid, title in self.recipe_titles[lang].items():
                    lines.append(f'  - [{rid}. {title}](03_recipes.md#{rid.lower()})')
        lines.append(f"- **{self.t('sections.index', lang)}**")
        lines += [f"  - {self.link(x, lang, here)}" for x in entries['index']]
        lines.append(f"- **{self.t('sections.domains', lang)}**")
        lines += [f"  - {self.link(x, lang, here)}" for x in entries['domains']]
        lines.append(f"- **{self.t('sections.indicators', lang)}**")
        for x in entries['indicators']:
            i = self.ind[x]
            doms = ', '.join(label(self.domains[d]['label'], lang) for d in i.get('domains') or {})
            lines.append(f"  - {self.link(x, lang, here)} — *{doms}*")
        lines.append(f"- **{self.t('sections.upstream', lang)}**")
        lines += [f"  - {self.link(x, lang, here)}" for x in entries['upstream']]
        lines.append(f"- **{self.t('sections.appendices', lang)}**")
        for key, file in zip(('variables', 'general', 'goalposts', 'datasets', 'glossary',
                              'references', 'pending'), APPENDICES):
            lines.append(f"  - [{self.t('sections.' + key, lang)}]({file})")
        return here, '\n'.join(lines)

    # ------------------------------------------------------------- build
    def build(self):
        entries = {
            'index': ['uli', 'uli_plain'],
            'domains': [f'domain_{d}' for d in self.domains],
            'indicators': [i for i in self.order if i in self.ind],
            'upstream': list(self.s.upstream),
        }
        for lang in self.langs:
            self.variables = {}
            pages = self.pages[lang]
            sequence = []
            for name in FRONT:
                path, text = self.content_page(name, lang)
                pages[path] = text
                sequence.append(path)
            for x in entries['index']:
                path, text = self.index_page(x, lang)
                pages[path] = text
                sequence.append(path)
            for x in entries['domains']:
                path, text = self.domain_page(x[7:], lang)
                pages[path] = text
                sequence.append(path)
            for x in entries['indicators']:
                path, text = self.indicator_page(x, lang)
                pages[path] = text
                sequence.append(path)
            for x in entries['upstream']:
                path, text = self.upstream_page(x, lang)
                pages[path] = text
                sequence.append(path)
            for fn in (self.appendix_variables, self.appendix_general,
                       self.appendix_goalposts, self.appendix_datasets):
                path, text = fn(lang)
                pages[path] = text
                sequence.append(path)
            path, text = self.content_page('E_glossary.md', lang)
            pages[path] = text
            sequence.append(path)
            path, text = self.appendix_references(lang)
            pages[path] = text
            sequence.append(path)
            path, text = self.content_page('G_pending.md', lang)
            pages[path] = text
            sequence.append(path)
            path, text = self.readme(lang, entries)
            pages[path] = text
            self.write(lang, pages)
            self.sequence = getattr(self, 'sequence', {})
            self.sequence[lang] = ['README.md'] + sequence
        self.write_landing()
        self.copy_data()

    def write(self, lang, pages):
        root = DOCS / lang
        for path, text in pages.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text.rstrip() + '\n', encoding='utf-8')

    def write_landing(self):
        text = f"""# {self.t('title', 'es')} · {self.t('title', 'en')}

**{self.t('subtitle', 'es')}** · *{self.t('subtitle', 'en')}*

| Español | English |
|---|---|
| [Manual en español](es/README.md) · [PDF](pdf/mexicali_uli_manual_es.pdf) | [Manual in English](en/README.md) · [PDF](pdf/mexicali_uli_manual_en.pdf) |

Carl Higgs, Eugen Resendiz, Juan Ernesto Díaz Noguez y el equipo del Tecnológico de Monterrey / and the team from Tecnológico de Monterrey. Financiado por / funded by Tecnológico de Monterrey, 2026.

- `es/`, `en/`: el manual por idioma / the manual in each language
- `figures/`: mapas / maps
- `data/`: configuración de la región y parámetros del índice / region configuration and index parameters
- `pdf/`: PDF por idioma / PDF in each language

Licencia / licence: el manual, [CC BY 4.0](LICENSE.md); el código, MIT. Los datos de insumo conservan sus propias licencias. / The manual, [CC BY 4.0](LICENSE.md); the code, MIT. Input data keep their own licences.

Generado con / built with `build/manual/manual.py` ({self.facts['built']}).
"""
        (DOCS / 'README.md').write_text(text, encoding='utf-8')

    def copy_data(self):
        target = DOCS / 'data'
        target.mkdir(parents=True, exist_ok=True)
        for path in DATA_FILES:
            shutil.copy2(path, target / path.name)

    # ------------------------------------------------------------- checks
    def check_links(self):
        problems = []
        for lang in self.langs:
            root = DOCS / lang
            for path, text in self.pages[lang].items():
                base = (root / path).parent
                for href in re.findall(r'\]\(([^)\s]+)\)', text):
                    if href.startswith(('http://', 'https://', '#', 'mailto:')):
                        continue
                    # the other edition and the PDFs, when this build skips them
                    other = [x for x in LANGS if x not in self.langs]
                    if any(f'../{x}/' in href for x in other) or (
                            '/pdf/' in href):
                        continue
                    file, _, anchor = href.partition('#')
                    target = (base / file).resolve()
                    if not target.exists():
                        problems.append((lang, path, href))
                    elif anchor and target.suffix == '.md' and anchor.startswith('r'):
                        if f'<a id="{anchor}"></a>' not in target.read_text('utf-8'):
                            problems.append((lang, path, href))
        return problems


# ----------------------------------------------------------------- HTML / PDF
CSS = """
@page { size: A4; margin: 16mm 15mm 18mm 15mm;
  @bottom-center { content: counter(page); font-size: 8pt; color: #7a7269; } }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 9.4pt;
  line-height: 1.45; color: #2b2723; }
h1 { font-size: 17pt; margin: 0 0 6pt; color: #1f3a5f; font-weight: 600; }
h2 { font-size: 12pt; margin: 14pt 0 5pt; color: #1f3a5f; break-after: avoid; }
h3 { font-size: 10.5pt; margin: 10pt 0 4pt; break-after: avoid; }
section.page { break-before: page; }
section.page:first-of-type { break-before: auto; }
p, li { margin: 0 0 5pt; }
blockquote { margin: 4pt 0 8pt; padding: 4pt 10pt; border-left: 3px solid #709e8b;
  background: #f5f1ea; color: #4a443c; }
blockquote p { margin: 0 0 3pt; }
code { font-family: Consolas, 'Cascadia Mono', monospace; font-size: 8.3pt;
  background: #f2efe9; padding: 0 2px; border-radius: 2px; word-break: break-word; }
pre { background: #f5f1ea; border-radius: 4pt; padding: 6pt 8pt; font-size: 7.8pt;
  white-space: pre-wrap; word-break: break-word; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 7.8pt; }
table { border-collapse: collapse; width: 100%; font-size: 8pt; margin: 4pt 0 8pt; }
th, td { border-bottom: 1px solid #ddd6cb; padding: 2.5pt 4pt; text-align: left;
  vertical-align: top; }
th { background: #f5f1ea; font-weight: 600; }
tr { break-inside: avoid; }
img { max-width: 100%; max-height: 190mm; display: block; margin: 4pt auto; break-inside: avoid; }
a { color: #1f5fa8; text-decoration: none; }
em { color: #5b554d; }
"""


def page_slug(path):
    return 'p-' + re.sub(r'[^a-z0-9]+', '-', path.lower().removesuffix('.md'))


def to_pdf(builder, lang):
    root = DOCS / lang
    parts = []
    for path in builder.sequence[lang]:
        text = builder.pages[lang][path]
        body = markdown_lib.markdown(text, extensions=['tables', 'fenced_code'])
        base = PurePosixPath(path).parent

        def href(m):
            attr, value = m.group(1), m.group(2)
            if value.startswith(('http://', 'https://', '#', 'mailto:')):
                return m.group(0)
            file, _, anchor = value.partition('#')
            resolved = os.path.normpath(str(base / file)).replace(os.sep, '/')
            if attr == 'src':
                return f'src="{(root / resolved).resolve().as_uri()}"'
            if resolved.endswith('.md') and not resolved.startswith('../'):
                target = f'#{anchor}' if anchor else f'#{page_slug(resolved)}'
                return f'href="{target}"'
            if resolved.startswith('../'):
                tail = resolved[3:]
                ref = f'{ULI_REPO}/blob/main/docs/manual/{tail}'
                return f'href="{ref}' + (f'#{anchor}' if anchor else '') + '"'
            return m.group(0)

        body = re.sub(r'(href|src)="([^"]+)"', href, body)
        parts.append(f'<section class="page" id="{page_slug(path)}">{body}</section>')
    page = (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f"<title>{html.escape(builder.t('title', lang))}</title><style>{CSS}</style></head>"
            f"<body>{''.join(parts)}</body></html>")
    WORK.mkdir(parents=True, exist_ok=True)
    source = WORK / f'manual_{lang}.html'
    source.write_text(page, encoding='utf-8')
    target = DOCS / 'pdf' / f'mexicali_uli_manual_{lang}.pdf'
    target.parent.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(SITE / 'dashboard' / 'build'))
    from technical_report import BROWSERS  # noqa: E402
    browser = next((b for b in BROWSERS if Path(b).exists() or shutil.which(b)), None)
    if not browser:
        raise SystemExit('No Edge or Chrome found to print the PDF.')
    # A profile of its own: without one, headless Edge hands the job to an
    # Edge already open on the desktop and exits without printing anything.
    # Kept in the system temp folder, outside OneDrive.
    profile = Path(tempfile.gettempdir()) / 'uli-manual-edge-profile'
    if target.exists():
        target.unlink()
    subprocess.run(
        [browser, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
         '--allow-file-access-from-files', f'--user-data-dir={profile}',
         f'--print-to-pdf={target}', source.as_uri()],
        check=True, capture_output=True, timeout=900,
    )
    # The launcher may return before the headless browser has finished
    # printing a long document: wait until the file exists and stops growing.
    deadline, last, steady = time.time() + 900, -1, 0
    while time.time() < deadline and steady < 3:
        time.sleep(2)
        size = target.stat().st_size if target.exists() else -1
        steady = steady + 1 if size == last and size > 1000 else 0
        last = size
    if not target.exists() or target.stat().st_size < 1000:
        raise SystemExit(f'Printing {target.name} failed.')
    return target
