// The conceptual model, and how the featured composite index is calculated.
//
// A region may configure, for each report language, a figure of the
// conceptual model its indicators are organised by (reporting.languages.
// <Language>.conceptual_model); the exporter copies it into the dataset as
// conceptual_model_<code>.<ext> and lists it in the manifest.  The panel shows
// the index's profile, laid out as that model is, above the figure for the
// current language; clicking the core, a domain or an indicator of the
// profile describes how it is measured and from what data.  Beside them, a
// summary of the index's method: the prose from the exporter's `methods` text
// (editable in text.json), and the formulas, which are the same in every
// language, drawn here.

import { renderProfile } from './profile.js';
import { activePanes } from './state.js';
import { getLang, label, number, t } from './strings.js';
import { say } from './text.js';
import {
  indicatorsOf, referenceOf, shareOf, shareText,
} from './uli.js';

const attr = (text) => String(text === undefined || text === null ? '' : text)
  .replace(/&/g, '&amp;').replace(/\x22/g, '&quot;').replace(/</g, '&lt;');

/** The configured figure for a language, falling back to any language. */
export function modelFor(dataset, lang) {
  const models = ((dataset || {}).manifest || {}).conceptual_models || {};
  const code = lang || getLang();
  return models[code] || models.en || Object.values(models)[0] || null;
}

function distanceText(metres) {
  if (metres >= 1000) return `${number(metres / 1000, metres % 1000 ? 1 : 0)} km`;
  return `${number(metres, 0)} m`;
}

/**
 * Placeholders for the methods text, from the index's structure, and from
 * the dataset's manifest the bounds walkability's heat was re-scaled between.
 */
export function methodParts(structure, manifest = null) {
  const heat = (((manifest || {}).attenuation || {}).heat) || {};
  const bounds = (Object.values(heat)[0] || {}).bounds || [];
  const degrees = (v) => (v === undefined ? '–'
    : `${number(Number(v), Number.isInteger(Number(v)) ? 0 : 1)} °C`);
  const indicators = indicatorsOf(structure);
  // what the indicators scored count for in the index as a whole
  const effective = indicators
    .filter((i) => i.active !== false && i.effective_weight !== null
      && Number.isFinite(Number(i.effective_weight)))
    .map((i) => Number(i.effective_weight) * 100);
  const percent = (v) => `${number(v, 1)}%`;
  const thresholds = [...new Set(indicators
    .map((i) => Number(i.soft_threshold))
    .filter((d) => d > 0))]
    .sort((a, b) => a - b)
    .map(distanceText);
  const slopes = [...new Set(indicators
    .filter((i) => Number(i.soft_threshold) > 0)
    .map((i) => Number(i.k) || 5))];
  // each indicator scored by a ladder of distances, with its ladder
  const steps = indicators
    .filter((i) => i.active !== false && (i.steps || []).length)
    .map((i) => `${label(i.label, i.id)} (${i.steps.map(([metres, score]) =>
      `${number(score, 0)} ${t('describeWithin')} ${distanceText(Number(metres))}`)
      .join(', ')}; ${number(Number(i.beyond), 0)} ${t('describeBeyond')})`)
    .join('; ');
  return {
    steps,
    index: label(structure.label, structure.name),
    domains: structure.domains
      .filter((d) => d.name && d.scored !== false && (d.indicators || []).length)
      .map((d) => label(d.label, d.name))
      .join(', '),
    effective_min: effective.length ? percent(Math.min(...effective)) : '–',
    effective_max: effective.length ? percent(Math.max(...effective)) : '–',
    // the indicators the index scores: one listed but inactive is not
    n: indicators.filter((i) => i.active !== false).length,
    thresholds: thresholds.join(', '),
    k: slopes.map((k) => number(k, k % 1 ? 1 : 0)).join(', '),
    attenuation: number(Number(structure.attenuation)
      || Number(((manifest || {}).attenuation || {}).lambda) || 0.5, 1),
    lowValue: degrees(bounds[0]),
    highValue: degrees(bounds[1]),
  };
}

/**
 * Walkability, its heat variants and the settings, for an index with
 * variants; its thermal comfort caveats where any variant uses UTCI.
 */
export function variantParagraphs(structure, parts) {
  const variants = structure.variants || [];
  if (!variants.length) return [];
  const paragraphs = [
    say('methods', 'walkability', parts),
    say('methods', 'variants', parts),
    say('methods', 'weights', parts),
  ];
  if (variants.some((v) => v.attenuation !== undefined
      || (v.heat || []).includes('t'))) {
    paragraphs.push(say('methods', 'utci', parts));
  }
  return paragraphs.filter(Boolean);
}

/** How an indicator is scored, in a sentence or two, from its structure. */
function methodSentences(indicator, structure) {
  const out = [];
  const threshold = Number(indicator.soft_threshold);
  if (threshold > 0) {
    out.push(t('describeSoft').replace(/\{d\}/g, distanceText(threshold)));
  }
  if (indicator.steps && indicator.steps.length) {
    const steps = indicator.steps.map(([metres, score]) =>
      `${number(score, 0)} ${t('describeWithin')} ${distanceText(Number(metres))}`)
      .join(', ');
    out.push(t('describeSteps').replace('{steps}', steps)
      .replace('{beyond}', number(Number(indicator.beyond), 0)));
  }
  out.push(t(indicator.polarity === 'negative' ? 'describeLower' : 'describeHigher'));
  const n = indicator.normalisation || {};
  if (n.min !== undefined && n.max !== undefined) {
    const digits = Math.abs(Number(n.max) - Number(n.min)) < 10 ? 2 : 0;
    out.push(t('describeGoalposts')
      .replace('{min}', number(Number(n.min), digits))
      .replace('{max}', number(Number(n.max), digits))
      .replace('{ref}', n.reference === undefined ? '–'
        : number(Number(n.reference), digits))
      .replace('{centre}', number(referenceOf(structure), 0)));
  }
  if (indicator.id === structure.variant_replaces
      && (structure.variants || []).length > 1) {
    out.push(t('describeWalkVariant'));
  }
  return out;
}

/** A domain's subdomains, each with its definition. */
function subdomainList(subdomains) {
  const items = Object.entries(subdomains || {}).map(([key, sub]) =>
    `<li><b>${attr(label((sub || {}).label, key))}</b>${(sub || {}).about
      ? ` ${attr(label(sub.about, ''))}` : ''}</li>`).join('');
  return items ? `<ul class="describe-subdomains">${items}</ul>` : '';
}

function sourceList(sources) {
  const items = (sources || []).map((source) => label(source, ''))
    .filter(Boolean);
  if (!items.length) return '';
  return `<h4>${attr(t('reportSources'))}</h4><ul class="describe-sources">${
    items.map((item) => `<li>${attr(item)}</li>`).join('')}</ul>`;
}

/**
 * What the item clicked on the profile is, and how it is measured: the index,
 * a domain or an indicator (`item` as the profile reports a click).
 */
export function describeItem(structure, item) {
  if (!structure) return '';
  if (!item || item.kind === 'index') {
    return `<h3>${attr(label(structure.label, structure.name))}</h3>
      ${structure.description ? `<p>${attr(label(structure.description, ''))}</p>` : ''}
      ${structure.about ? `<p>${attr(label(structure.about, ''))}</p>` : ''}
      ${sourceList(structure.sources)}
      <p class="muted">${attr(t('describeHint'))}</p>`;
  }
  const domain = structure.domains.find((d) => (d.name || structure.name) === item.key);
  if (!domain) return '';
  if (item.kind === 'domain') {
    const members = domain.indicators.map((i) => {
      const notes = [];
      if (shareOf(i) < 1) notes.push(`${shareText(shareOf(i))} ${t('profileWeight')}`);
      if (i.active === false) notes.push(t('profileInactive'));
      return `<li${i.active === false ? ' class="inactive"' : ''}>${
        attr(label(i.label, i.id))}${notes.length
        ? ` <span class="comp-note">${attr(notes.join(' · '))}</span>` : ''}</li>`;
    }).join('');
    return `<h3>${attr(label(domain.label, domain.name))}</h3>
      ${domain.about ? `<p>${attr(label(domain.about, ''))}</p>` : ''}
      ${subdomainList(domain.subdomains)}
      <h4>${attr(t('profileIndicators'))}</h4>${members
    ? `<ul>${members}</ul>` : `<p class="muted">${attr(t('profileUnscored'))}</p>`}
      ${sourceList(domain.sources)}`;
  }
  const indicator = domain.indicators.find((i) => i.id === item.id);
  if (!indicator) return '';
  const lens = indicator.lens
    ? label((structure.lenses || {})[indicator.lens], indicator.lens) : '';
  // every domain it counts towards, with its share of each and the part of
  // the domain it answers to there
  const towards = structure.domains
    .map((d) => [d, (d.indicators || []).find((i) => i.id === indicator.id)])
    .filter(([, i]) => i)
    .map(([d, i]) => [label(d.label, d.name),
      shareOf(i) < 1 ? `(${shareText(shareOf(i))})` : '',
      i.subdomain ? `· ${label(i.subdomain, '')}` : ''].filter(Boolean).join(' '));
  const effective = indicator.effective_weight === null
    || indicator.effective_weight === undefined ? NaN : Number(indicator.effective_weight);
  const facts = [...towards, lens,
    Number.isFinite(effective) && indicator.active !== false
      ? `${t('profileEffective')} ${number(effective * 100, 1)}%` : '',
  ].filter(Boolean).join(' · ');
  return `<h3>${attr(label(indicator.label, indicator.id))}</h3>
    <p class="muted">${attr(facts)}</p>
    ${indicator.active === false ? `<p class="describe-inactive">${
    attr(label(indicator.inactive_reason, t('profileInactive')))}</p>` : ''}
    ${indicator.about ? `<p>${attr(label(indicator.about, ''))}</p>` : ''}
    <h4>${attr(t('describeMethod'))}</h4>
    <p>${methodSentences(indicator, structure).map(attr).join(' ')}</p>
    ${sourceList(indicator.sources)}`;
}

// The works the methods text cites, in full: bibliographic entries read the
// same in every language.  `when` limits an entry to the indices it describes.
const REFERENCES = [
  {
    text: 'De Muro P, Mazziotta M, Pareto A (2011). Composite indices of '
      + 'development and poverty: an application to MDGs. Social Indicators '
      + 'Research 104(1): 1–18.',
    doi: '10.1007/s11205-010-9727-z',
  },
  {
    text: 'Higgs C, Badland H, Simons K, Knibbs LD, Giles-Corti B (2019). The '
      + 'Urban Liveability Index: developing a policy-relevant urban '
      + 'liveability composite measure and evaluating associations with '
      + 'transport mode choice. International Journal of Health Geographics '
      + '18: 14.',
    doi: '10.1186/s12942-019-0178-8',
  },
  {
    text: 'Mazziotta M, Pareto A (2016). On a generalized non-compensatory '
      + 'composite index for measuring socio-economic phenomena. Social '
      + 'Indicators Research 127(3): 983–1003.',
    doi: '10.1007/s11205-015-0998-2',
  },
  {
    text: 'Mazziotta M, Pareto A (2018). Measuring well-being over time: the '
      + 'Adjusted Mazziotta–Pareto Index versus other non-compensatory '
      + 'indices. Social Indicators Research 136(3): 967–976.',
    doi: '10.1007/s11205-017-1577-5',
    when: (structure) => structure.method !== 'mpi',
  },
  {
    text: 'Mazziotta M, Pareto A (2022). Weighting in composite indices '
      + 'construction: the case of the Mazziotta-Pareto Index. Rivista '
      + 'Italiana di Economia Demografia e Statistica 76(4): 17–26.',
  },
  {
    text: 'Frank LD, Sallis JF, Saelens BE, Leary L, Cain K, Conway TL, Hess PM '
      + '(2010). The development of a walkability index: application to the '
      + 'Neighborhood Quality of Life Study. British Journal of Sports '
      + 'Medicine 44(13): 924–933.',
    doi: '10.1136/bjsm.2009.058701',
    when: (structure) => Boolean((structure.variants || []).length),
  },
  {
    text: 'Wang Y, He B-J, Kang C, et al. (2022). Assessment of walkability '
      + 'and walkable routes of a 15-min city for heat adaptation: '
      + 'development of a dynamic attenuation model of heat stress. Frontiers '
      + 'in Public Health 10: 1011391.',
    doi: '10.3389/fpubh.2022.1011391',
    when: (structure) => Boolean((structure.variants || []).length),
  },
  {
    text: 'Bröde P, Fiala D, Błażejczyk K, et al. (2012). Deriving the '
      + 'operational procedure for the Universal Thermal Climate Index (UTCI). '
      + 'International Journal of Biometeorology 56(3): 481–494.',
    doi: '10.1007/s00484-011-0454-1',
    when: (structure) => (structure.variants || [])
      .some((v) => (v.heat || []).includes('t')),
  },
  {
    text: 'OECD, JRC (2008). Handbook on Constructing Composite Indicators: '
      + 'Methodology and User Guide. Paris: OECD Publishing.',
    doi: '10.1787/9789264043466-en',
  },
];

/**
 * The companion technical report on how the index is calculated, in the
 * current language (docs/<slug>_technical_report_<code>.pdf, built by
 * build/technical_report.py from the dataset's own structure and text).
 */
export function technicalReportPath(dataset, lang) {
  return `docs/${dataset.slug}_technical_report_${lang || getLang()}.pdf`;
}

function technicalLink(dataset) {
  return `<p class="model-technical"><a href="${attr(technicalReportPath(dataset))}"
    target="_blank" rel="noopener">${attr(t('technicalReport'))}</a></p>`;
}

export function references(structure) {
  const items = REFERENCES
    .filter((r) => !r.when || r.when(structure))
    .map((r) => `<li>${attr(r.text)}${r.doi ? ` <a href="https://doi.org/${
      attr(r.doi)}" target="_blank" rel="noopener">doi:${attr(r.doi)}</a>`
      : ''}</li>`)
    .join('');
  return `<h3>${attr(say('methods', 'further_reading'))}</h3>
    <ul class="model-references">${items}</ul>`;
}

/** The domains and lenses of the index, as the figure's nodes and boxes. */
function vocabulary(structure) {
  const domains = structure.domains.filter((d) => d.name).map((d) => {
    const colour = d.colour || {};
    const style = colour.fill
      ? `style="background:${colour.fill};border-color:${colour.stroke || colour.fill}"` : '';
    const count = (d.indicators || []).length;
    return `<li><span class="node" ${style}></span>${attr(label(d.label, d.name))}
      <span class="comp-note">${count || attr(t('profileUnscored'))}</span>${
  d.about ? `<p class="muted model-definition">${attr(label(d.about, ''))}</p>` : ''}</li>`;
  }).join('');
  const lenses = Object.entries(structure.lenses || {}).map(([key, names]) =>
    `<span class="lens">${attr(label(names, key))}</span>`).join(' ');
  return `${domains ? `<h3>${attr(t('profileDomains'))}</h3>
    <ul class="model-domains">${domains}</ul>` : ''}
    ${lenses ? `<h3>${attr(t('lenses'))}</h3><p class="model-lenses">${lenses}</p>
    <p class="muted">${attr(t('profileLensHelp'))}</p>` : ''}`;
}

/**
 * Fill the panel for a dataset, in the current language.
 *
 * `structure` is the featured composite index's structure, where there is one:
 * without it the panel shows the figure alone.
 */
export function renderModel(element, dataset, structure, app = null) {
  const model = modelFor(dataset);
  const src = model ? `data/${dataset.slug}/${model.file}` : null;
  const alt = model ? (model.alt || t('conceptualModel')) : '';
  let figure = '';
  if (model && model.type === 'document') {
    figure = `<iframe class="model-figure" src="${attr(src)}"
      title="${attr(alt)}"></iframe>`;
  } else if (model) {
    figure = `<div class="model-figure zoomable" tabindex="0"
        title="${attr(t('modelZoom'))}">
      <img src="${attr(src)}" alt="${attr(alt)}"></div>`;
  }
  const caption = model && model.caption
    ? `<p class="muted">${attr(model.caption)}</p>` : '';
  // the panel, in two columns: the figure, and beneath it the domains, with
  // the framework's definitions, and the lenses; the interactive profile,
  // describing what is clicked, and beneath it the link to the technical
  // report, which sets out how the index is calculated in detail, and
  // further reading.
  const shown = app && app.resolved && app.resolved.composite;
  element.innerHTML = `
    <div class="model-layout">
      <div class="model-col">
        <h2 id="modelTitle">${attr(t('conceptualModel'))}</h2>
        ${figure}
        ${caption}
        ${src ? `<a class="model-open" href="${attr(src)}" target="_blank"
          rel="noopener">${attr(t('modelOpen'))}</a>` : ''}
        <div class="model-vocabulary">${structure ? vocabulary(structure) : ''}</div>
      </div>
      <div class="model-col">
        ${shown ? `<div class="model-profile"></div>
          <div class="model-describe">${describeItem(shown, app.modelFocus)}</div>` : ''}
        <div class="model-reading">${structure ? `${technicalLink(dataset)}
          ${references(structure)}` : ''}</div>
      </div>
    </div>`;
  if (shown) {
    const panes = activePanes();
    const datasets = panes.map((pane) => app.datasets.get(pane.dataset));
    const statsEntries = panes.map((pane, i) =>
      (datasets[i] ? datasets[i].stats[pane.scale] : null));
    const focus = app.modelFocus || {};
    renderProfile(
      element.querySelector('.model-profile'), app, panes, datasets,
      statsEntries,
      {
        inModal: true,
        compact: true,
        mode: 'describe',
        focusColumn: focus.column || (focus.kind === 'index'
          ? shown.columns.index : null),
        onItem: (item) => {
          app.modelFocus = item;
          renderModel(element, dataset, structure, app);
        },
      },
    );
  }
  const zoomable = element.querySelector('.zoomable');
  if (zoomable) {
    const toggle = () => zoomable.classList.toggle('zoomed');
    zoomable.addEventListener('click', toggle);
    zoomable.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        toggle();
      }
    });
  }
}
