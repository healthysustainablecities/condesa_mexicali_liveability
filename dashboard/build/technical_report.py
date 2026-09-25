"""
The technical report on how the featured composite index is calculated.

Writes docs/<slug>_technical_report_<code>.pdf for each language, which the
conceptual model panel and the printed report link to.  Everything it says is
read from the dataset the dashboard itself reads: the prose from the
exporter's `methods` text (indicators.json `text.methods`, i.e.
_export_dashboard.DEFAULT_TEXT, which describes what _composite_index.py
does), and the domains, indicators, shares, goalposts and effective weights
from the index's structure (`family.composite`, from
_composite_index.index_structure).  Only the formulas, the headings and the
table layout are written here, as the viewer draws its own.  Re-run it after
every export:

    python build/technical_report.py [slug] [data folder]

The data folder defaults to data/<slug>; give an export folder to build the
report before that export is deployed.

The PDF is printed by headless Edge (or Chrome) from an HTML page written to
build/_work.
"""

import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
WORK = SITE / 'build' / '_work'
DOCS = SITE / 'docs'
BROWSERS = (
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'msedge',
    'google-chrome',
    'chromium',
)

HEADINGS = {
    'kicker': {'es': 'Documento técnico', 'en': 'Technical report'},
    'overview': {'es': 'Resumen', 'en': 'Overview'},
    'model': {'es': 'Modelo conceptual', 'en': 'Conceptual model'},
    'domains': {'es': 'Dominios', 'en': 'Domains'},
    'lenses': {'es': 'Enfoques', 'en': 'Lenses'},
    'measures': {
        'es': '1. De la medición al indicador',
        'en': '1. From measurement to indicator',
    },
    'normalise': {'es': '2. Normalización', 'en': '2. Normalisation'},
    'aggregate': {
        'es': '3. Agregación: dominios e índice',
        'en': '3. Aggregation: domains and index',
    },
    'areas': {
        'es': '4. De los puntos de muestra a las áreas',
        'en': '4. From sample points to areas',
    },
    'walk': {
        'es': '5. Caminabilidad y confort térmico',
        'en': '5. Walkability and thermal comfort',
    },
    'table': {
        'es': 'Anexo: indicadores, pesos y metas',
        'en': 'Appendix: indicators, weights and goalposts',
    },
    'table_note': {
        'es': (
            'Cada indicador se lista una vez, con la parte de su peso que '
            'cuenta en cada dominio y su peso efectivo en el nivel medio del '
            'índice. Las metas (Mín., Ref., Máx.) están en la escala que se '
            'puntúa: la puntuación de acceso suave (0 a 1) donde hay un '
            'umbral, la escala escalonada donde la hay, y si no el valor '
            'medido. Ref. es el promedio de la región de estudio y puntúa 0.'
        ),
        'en': (
            'Each indicator is listed once, with the share of its weight '
            'that counts in each domain and its effective weight in the '
            'index\'s mean level. Goalposts (Min, Ref, Max) are on the scale '
            'scored: the soft access score (0 to 1) where there is a '
            'threshold, the ladder where there is one, otherwise the value '
            'as measured. Ref is the study region average, and scores 0.'
        ),
    },
    'indicator': {'es': 'Indicador', 'en': 'Indicator'},
    'counts': {'es': 'Dominios (parte)', 'en': 'Domains (share)'},
    'scored': {'es': 'Se puntúa', 'en': 'Scored as'},
    'better': {'es': 'Mejor', 'en': 'Better'},
    'goalposts': {
        'es': 'Mín. · Ref. · Máx.',
        'en': 'Min · Ref · Max',
    },
    'effective': {'es': 'Peso efectivo', 'en': 'Effective weight'},
    'higher': {'es': 'mayor', 'en': 'higher'},
    'lower': {'es': 'menor', 'en': 'lower'},
    'soft': {'es': 'acceso suave, umbral {d}', 'en': 'soft access, {d} threshold'},
    'ladder': {'es': 'escala escalonada', 'en': 'ladder'},
    'as_is': {'es': 'tal cual', 'en': 'as measured'},
    'inactive': {
        'es': 'no se cuenta en el índice publicado',
        'en': 'not counted in the published index',
    },
    'unscored': {'es': 'aún sin indicadores', 'en': 'no indicators yet'},
    'n_indicators': {'es': '{n} indicadores', 'en': '{n} indicators'},
    'formulas': {'es': 'Fórmulas', 'en': 'Formulas'},
    'reference_run': {
        'es': (
            'Metas resueltas el {created} a partir de {units} puntos de '
            'muestra.'
        ),
        'en': 'Goalposts resolved on {created} from {units} sample points.',
    },
    'generated': {'es': 'Generado el', 'en': 'Generated'},
    'within': {'es': 'a', 'en': 'within'},
    'beyond': {'es': 'más allá', 'en': 'beyond'},
    'dashboard': {
        'es': 'Acompaña al tablero de entornos vivibles.',
        'en': 'Companion to the liveability dashboard.',
    },
}


def esc(text):
    return html.escape(str(text if text is not None else ''))


def label(value, fallback, lang):
    if isinstance(value, dict):
        return value.get(lang) or value.get('en') or value.get('es') or fallback
    return value or fallback


def number(value, digits, lang):
    text = f'{float(value):,.{digits}f}'
    if lang == 'es':
        text = text.replace(',', ' ').replace('.', ',').replace(' ', '\u2009')
    return text


def distance(metres, lang):
    metres = float(metres)
    if metres >= 1000:
        return f'{number(metres / 1000, 1 if metres % 1000 else 0, lang)} km'
    return f'{number(metres, 0, lang)} m'


def fill(text, parts):
    return re.sub(
        r'\{(\w+)\}',
        lambda m: str(parts.get(m.group(1), '')),
        text or '',
    )


def say(texts, key, parts, lang):
    return fill(label(texts.get(key), '', lang), parts)


def references(site):
    """The works the methods text cites, as the viewer lists them."""
    source = (site / 'js' / 'model.js').read_text(encoding='utf-8')
    block = source.split('const REFERENCES = [', 1)[1].split('\n];', 1)[0]
    out = []
    for entry in re.split(r'\n  \{', block):
        text = re.search(r'text:(.*?)(?:,\n\s+(?:doi|when):|,\n\s*\},?$)',
                         entry, re.S)
        if not text:
            continue
        joined = ''.join(re.findall(r"'((?:[^'\\]|\\.)*)'", text.group(1)))
        doi = re.search(r"doi: '([^']+)'", entry)
        out.append((joined.replace("\\'", "'"), doi.group(1) if doi else None,
                    'when:' in entry, entry))
    return out


def parts_for(structure, manifest, lang):
    """The methods text's placeholders, as model.js methodParts() fills them."""
    indicators = structure['indicators']
    active = [i for i in indicators if i.get('active') is not False]
    effective = [
        float(i['effective_weight']) * 100
        for i in active
        if i.get('effective_weight') is not None
    ]
    thresholds = sorted({
        float(i['soft_threshold'])
        for i in indicators
        if i.get('soft_threshold')
    })
    slopes = sorted({
        float(i.get('k') or 5) for i in indicators if i.get('soft_threshold')
    })
    steps = '; '.join(
        f"{label(i.get('label'), i['id'], lang)} ("
        + ', '.join(
            f"{number(score, 0, lang)} {HEADINGS['within'][lang]} "
            f'{distance(metres, lang)}'
            for metres, score in i['steps']
        )
        + f"; {number(i['beyond'], 0, lang)} {HEADINGS['beyond'][lang]})"
        for i in active
        if i.get('steps')
    )
    attenuation = (manifest or {}).get('attenuation') or {}
    heat = next(iter((attenuation.get('heat') or {}).values()), {})
    bounds = heat.get('bounds') or []
    observed = heat.get('observed') or []

    def degrees(v):
        if v is None:
            return '–'
        return f"{number(v, 0 if float(v).is_integer() else 1, lang)} °C"

    pct = lambda v: f'{number(v, 1, lang)}%'
    return {
        'index': label(structure.get('label'), structure['name'], lang),
        'domains': ', '.join(
            label(d.get('label'), d['name'], lang)
            for d in structure['domains']
            if d.get('name') and d.get('scored') is not False
            and d.get('indicators')
        ),
        'n': len(active),
        'thresholds': ', '.join(distance(t, lang) for t in thresholds),
        'k': ', '.join(number(k, 0 if k.is_integer() else 1, lang)
                       for k in slopes),
        'steps': steps,
        'effective_min': pct(min(effective)) if effective else '–',
        'effective_max': pct(max(effective)) if effective else '–',
        'attenuation': number(attenuation.get('lambda') or 0.5, 1, lang),
        'lowValue': degrees(bounds[0] if bounds else None),
        'highValue': degrees(bounds[1] if len(bounds) > 1 else None),
        'obsLow': degrees(observed[0] if observed else None),
        'obsHigh': degrees(observed[1] if len(observed) > 1 else None),
        'low': number((attenuation.get('percentiles') or [5])[0], 0, lang),
        'high': number((attenuation.get('percentiles') or [5, 95])[-1], 0,
                       lang),
        'observed': '',
    }


FORMULAS = {
    'soft': 's(d) = 1 / (1 + e<sup>k(d − t)/t</sup>)',
    'ampi': (
        'r = 100 ± 60 · (x − Ref) / (Max − Min), &nbsp; '
        '{default} Max − Min = max(x) − min(x) &nbsp; (± : + '
        '{higher}, − {lower})'
    ),
    'mpi': 'z = 100 ± 10 · (x − M<sub>x</sub>) / S<sub>x</sub>',
    'mean': (
        'M = Σ w<sub>i</sub> r<sub>i</sub>, &nbsp; '
        'S = √(Σ w<sub>i</sub> (r<sub>i</sub> − M)²), &nbsp; cv = S / M'
    ),
    'weights': (
        'w<sub>i</sub> ∝ weight<sub>i</sub> · share<sub>i,d</sub>, &nbsp; '
        'Σ w<sub>i</sub> = 1 &nbsp; (share = 1/k {shared})'
    ),
    'index': (
        'score = M − S · cv &nbsp; → &nbsp; {reported}'
    ),
}

FORMULA_WORDS = {
    'default': {'es': 'por defecto,', 'en': 'by default,'},
    'higher': {'es': 'si mayor es mejor', 'en': 'where higher is better'},
    'lower': {'es': 'si menor es mejor', 'en': 'where lower is better'},
    'shared': {
        'es': 'para un indicador en k dominios',
        'en': 'for an indicator in k domains',
    },
    'reported': {
        'es': 'se informa como score − 100 (0 = promedio de la región de '
        'estudio)',
        'en': 'reported as score − 100 (0 = study region average)',
    },
    'reported100': {
        'es': 'se informa con la referencia en 100',
        'en': 'reported with the reference at 100',
    },
}


def formula(key, lang, centred=True):
    words = {k: v[lang] for k, v in FORMULA_WORDS.items()}
    if not centred:
        words['reported'] = words['reported100']
    return f'<p class="formula">{FORMULAS[key].format(**words)}</p>'


def indicator_rows(structure, lang):
    domains = {d['name']: d for d in structure['domains'] if d.get('name')}
    order = structure.get('order') or [i['id'] for i in structure['indicators']]
    by_id = {i['id']: i for i in structure['indicators']}
    rows = []
    for key in order:
        i = by_id.get(key)
        if not i:
            continue
        shares = ', '.join(
            f"{esc(label(domains.get(d, {}).get('label'), d, lang))}"
            + ('' if abs(share - 1) < 1e-9
               else f' ({number(share * 100, 0, lang)}%)')
            for d, share in (i.get('domains') or {}).items()
        )
        if i.get('soft_threshold'):
            scored = HEADINGS['soft'][lang].format(
                d=distance(i['soft_threshold'], lang),
            )
        elif i.get('steps'):
            scored = HEADINGS['ladder'][lang]
        else:
            scored = HEADINGS['as_is'][lang]
        n = i.get('normalisation') or {}
        if n.get('min') is not None:
            span = abs(float(n['max']) - float(n['min']))
            digits = 0 if span >= 100 else (1 if span >= 10 else 3)
            goal = ' · '.join(
                number(n[k], digits, lang) for k in ('min', 'reference', 'max')
            )
        else:
            goal = '–'
        inactive = i.get('active') is False
        eff = i.get('effective_weight')
        rows.append(
            f"<tr{' class=\"inactive\"' if inactive else ''}>"
            f"<td>{esc(label(i.get('label'), i['id'], lang))}"
            + (f"<br><small>{esc(label(i.get('inactive_reason'), HEADINGS['inactive'][lang], lang))}</small>"
               if inactive else '')
            + f'</td><td>{shares}</td><td>{esc(scored)}</td>'
            f"<td>{HEADINGS['higher' if i.get('polarity') != 'negative' else 'lower'][lang]}</td>"
            f'<td class="num">{goal}</td>'
            f"<td class=\"num\">{'–' if inactive or eff is None else number(float(eff) * 100, 1, lang) + '%'}</td>"
            '</tr>',
        )
    return '\n'.join(rows)


CSS = """
@page { size: A4; margin: 18mm 17mm 18mm 17mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 9.6pt;
  line-height: 1.45; color: #2b2723; }
h1 { font-size: 20pt; margin: 0 0 4pt; color: #1f3a5f; font-weight: 600; }
h2 { font-size: 13pt; margin: 16pt 0 6pt; color: #1f3a5f;
  break-after: avoid; }
h3 { font-size: 10.5pt; margin: 10pt 0 4pt; break-after: avoid; }
.kicker { text-transform: uppercase; letter-spacing: .08em; font-size: 8pt;
  color: #7a7269; }
.meta { color: #7a7269; font-size: 8.5pt; margin-bottom: 10pt; }
p { margin: 0 0 6pt; text-align: left; }
.about { font-size: 10pt; }
.formula { font-family: 'Cambria Math', Cambria, serif; font-size: 10.5pt;
  background: #f5f1ea; border-radius: 4pt; padding: 5pt 9pt; margin: 4pt 0 8pt;
  break-inside: avoid; }
.provisional { border: 1px solid #e3c98f; background: #fdf6e6;
  padding: 5pt 8pt; border-radius: 4pt; font-size: 9pt; }
figure { margin: 6pt 0 10pt; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; max-height: 120mm; }
ul.domains { list-style: none; padding: 0; margin: 0; }
ul.domains li { margin: 0 0 5pt; break-inside: avoid; }
.swatch { display: inline-block; width: 9pt; height: 9pt; border-radius: 50%;
  border: 1.5px solid; vertical-align: -1pt; margin-right: 5pt; }
.muted { color: #7a7269; }
table { border-collapse: collapse; width: 100%; font-size: 8.2pt; }
th, td { border-bottom: 1px solid #ddd6cb; padding: 3pt 4pt; text-align: left;
  vertical-align: top; }
th { background: #f5f1ea; font-weight: 600; }
td.num, th.num { text-align: right; white-space: nowrap; }
tr { break-inside: avoid; }
tr.inactive td { color: #7a7269; font-style: italic; }
ol.refs { padding-left: 14pt; font-size: 8.8pt; }
ol.refs li { margin-bottom: 3pt; }
a { color: #1f5fa8; text-decoration: none; }
"""


def build(slug, lang, data=None):
    data = Path(data) if data else SITE / 'data' / slug
    indicators = json.loads((data / 'indicators.json').read_text('utf-8'))
    manifest = json.loads((data / 'manifest.json').read_text('utf-8'))
    featured = manifest.get('featured')
    families = [f for f in indicators['families'] if f.get('composite')]
    family = next(
        (f for f in families if featured in (f.get('key'), f['composite']['name'])),
        families[0],
    )
    structure = family['composite']
    texts = indicators['text']['methods']
    parts = parts_for(structure, manifest, lang)
    centred = float(structure.get('reference_value', 100)) == 0
    p = lambda key: (f'<p>{esc(say(texts, key, parts, lang))}</p>'
                     if say(texts, key, parts, lang) else '')
    title = label(structure.get('label'), structure['name'], lang)
    model = (manifest.get('conceptual_models') or {}).get(lang) or next(
        iter((manifest.get('conceptual_models') or {}).values()), None)
    figure = ''
    if model and model.get('type') != 'document':
        figure = (f'<figure><img src="{(data / model["file"]).as_uri()}" '
                  f'alt=""></figure>')
    domains = ''.join(
        f"<li><span class=\"swatch\" style=\"background:{esc((d.get('colour') or {}).get('fill', '#ddd'))};"
        f"border-color:{esc((d.get('colour') or {}).get('stroke', '#999'))}\"></span>"
        f"<b>{esc(label(d.get('label'), d['name'], lang))}</b> "
        f"<span class=\"muted\">· "
        + (HEADINGS['n_indicators'][lang].format(n=len(d['indicators']))
           if d.get('scored') is not False and d.get('indicators')
           else HEADINGS['unscored'][lang])
        + '</span>'
        + (f"<br>{esc(label(d.get('about'), '', lang))}" if d.get('about') else '')
        + '</li>'
        for d in structure['domains'] if d.get('name')
    )
    lenses = ', '.join(
        esc(label(v, k, lang)) for k, v in (structure.get('lenses') or {}).items()
    )
    params = structure.get('parameters') or {}
    run = ''
    if params.get('created'):
        run = (f"<p class=\"muted\">{esc(HEADINGS['reference_run'][lang].format(created=params['created'][:10], units=number(params.get('units', 0), 0, lang)))}</p>")
    has_variants = bool(structure.get('variants'))
    uses_utci = any('t' in (v.get('heat') or []) or v.get('attenuation')
                    is not None for v in structure.get('variants') or [])
    refs = ''.join(
        f'<li>{esc(text)}'
        + (f' <a href="https://doi.org/{esc(doi)}">doi:{esc(doi)}</a>' if doi else '')
        + '</li>'
        for text, doi, conditional, entry in references(SITE)
        # the viewer's `when` conditions: the method, the variants, and UTCI
        # wherever the thermal comfort caveat is shown
        if not conditional
        or ("method !== 'mpi'" in entry and structure.get('method') != 'mpi')
        or ('includes(' in entry and uses_utci)
        or ('includes(' not in entry and 'variants' in entry and has_variants)
    )
    method = 'normalise_mpi' if structure.get('method') == 'mpi' else 'normalise'
    body = f"""
<div class="kicker">{esc(HEADINGS['kicker'][lang])} · {esc(label(manifest.get('title'), '', lang))}</div>
<h1>{esc(title)}</h1>
<h2 style="margin-top:0;font-weight:400">{esc(say(texts, 'title', parts, lang))}</h2>
<div class="meta">{esc(HEADINGS['generated'][lang])} {esc(date.today().isoformat())} · {esc(HEADINGS['dashboard'][lang])}</div>
<p class="provisional">{esc(say(texts, 'provisional', parts, lang))}</p>

<h2>{esc(HEADINGS['overview'][lang])}</h2>
<p class="about"><b>{esc(label(structure.get('description'), '', lang))}</b></p>
<p class="about">{esc(label(structure.get('about'), '', lang))}</p>
{p('intro')}

<h2>{esc(HEADINGS['model'][lang])}</h2>
{figure}
<h3>{esc(HEADINGS['domains'][lang])}</h3>
<ul class="domains">{domains}</ul>
<p><b>{esc(HEADINGS['lenses'][lang])}:</b> {lenses}</p>

<h2>{esc(HEADINGS['measures'][lang])}</h2>
{p('threshold') if parts['thresholds'] else ''}
{formula('soft', lang) if parts['thresholds'] else ''}
{p('steps') if parts['steps'] else ''}

<h2>{esc(HEADINGS['normalise'][lang])}</h2>
{p(method)}
{formula('ampi' if method == 'normalise' else 'mpi', lang)}
{run}

<h2>{esc(HEADINGS['aggregate'][lang])}</h2>
{p('aggregate')}
{formula('mean', lang)}
{formula('weights', lang) if structure.get('shared') else ''}
{formula('index', lang, centred)}
{p('shared') if structure.get('shared') else ''}

<h2>{esc(HEADINGS['areas'][lang])}</h2>
{p('scale')}
{p('reading')}

{f'''<h2>{esc(HEADINGS['walk'][lang])}</h2>
{p('walkability')}
{p('variants')}
{p('utci') if uses_utci else ''}
{p('weights')}''' if has_variants else ''}

<h2>{esc(HEADINGS['table'][lang])}</h2>
<p class="muted">{esc(HEADINGS['table_note'][lang])}</p>
<table>
<thead><tr><th>{esc(HEADINGS['indicator'][lang])}</th><th>{esc(HEADINGS['counts'][lang])}</th>
<th>{esc(HEADINGS['scored'][lang])}</th><th>{esc(HEADINGS['better'][lang])}</th>
<th class="num">{esc(HEADINGS['goalposts'][lang])}</th><th class="num">{esc(HEADINGS['effective'][lang])}</th></tr></thead>
<tbody>{indicator_rows(structure, lang)}</tbody>
</table>

<h2>{esc(say(texts, 'further_reading', parts, lang))}</h2>
<ol class="refs">{refs}</ol>
"""
    page = (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<title>{esc(title)}</title><style>{CSS}</style></head>'
            f'<body>{body}</body></html>')
    WORK.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    source = WORK / f'{slug}_technical_report_{lang}.html'
    source.write_text(page, encoding='utf-8')
    target = DOCS / f'{slug}_technical_report_{lang}.pdf'
    print_pdf(source, target)
    return target


def print_pdf(source, target):
    browser = next(
        (b for b in BROWSERS if Path(b).exists() or shutil.which(b)), None,
    )
    if not browser:
        raise SystemExit('No Edge or Chrome found to print the PDF.')
    subprocess.run(
        [browser, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
         '--allow-file-access-from-files', f'--print-to-pdf={target}',
         source.as_uri()],
        check=True, capture_output=True, timeout=180,
    )
    if not target.exists() or target.stat().st_size < 1000:
        raise SystemExit(f'Printing {target.name} failed.')


def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else 'mexicali'
    data = sys.argv[2] if len(sys.argv) > 2 else None
    for lang in ('es', 'en'):
        print(build(slug, lang, data))


if __name__ == '__main__':
    main()
