// The conceptual model, and how the featured composite index is calculated.
//
// A region may configure, for each report language, a figure of the
// conceptual model its indicators are organised by (reporting.languages.
// <Language>.conceptual_model); the exporter copies it into the dataset as
// conceptual_model_<code>.<ext> and lists it in the manifest.  The panel shows
// the figure for the current language beside a summary of the index's method:
// the prose from the exporter's `methods` text (editable in text.json), and
// the formulas, which are the same in every language, drawn here.

import { getLang, label, number, t } from './strings.js';
import { say } from './text.js';

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

/** Placeholders for the methods text, from the index's structure. */
export function methodParts(structure) {
  const indicators = structure.domains.flatMap((d) => d.indicators);
  const thresholds = [...new Set(indicators
    .map((i) => Number(i.soft_threshold))
    .filter((d) => d > 0))]
    .sort((a, b) => a - b)
    .map(distanceText);
  const slopes = [...new Set(indicators
    .filter((i) => Number(i.soft_threshold) > 0)
    .map((i) => Number(i.k) || 5))];
  return {
    index: label(structure.label, structure.name),
    domains: structure.domains
      .filter((d) => d.name)
      .map((d) => label(d.label, d.name))
      .join(', '),
    n: indicators.length,
    thresholds: thresholds.join(', '),
    k: slopes.map((k) => number(k, k % 1 ? 1 : 0)).join(', '),
    attenuation: number(Number(structure.attenuation) || 0.5, 1),
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
  if (variants.some((v) => (v.heat || []).includes('t'))) {
    paragraphs.push(say('methods', 'utci', parts));
  }
  return paragraphs.filter(Boolean);
}

// The formulas, as HTML: identical in every language
const FORMULA_THRESHOLD = `<var>a</var> = 1 / (1 + <var>e</var><sup><var>k</var>
  (<var>d</var> − <var>t</var>) / <var>t</var></sup>)`;
const FORMULA_NORMALISE = `<var>r</var> = 100 ± 60 · (<var>x</var> −
  <var>Ref</var>) / (<var>Max</var> − <var>Min</var>)`;
// the classic MPI standardises instead
const FORMULA_STANDARDISE = `<var>z</var> = 100 ± 10 · (<var>x</var> −
  <var>M</var><sub><var>x</var></sub>) / <var>S</var><sub><var>x</var></sub>`;
// weights sum to 1; a 'negative' phenomenon (e.g. deprivation) adds the penalty
const formulaAggregate = (phenomenon) => `<var>M</var> = Σ
  <var>w</var><sub><var>i</var></sub> <var>r</var><sub><var>i</var></sub>,
  <var>S</var> = √(Σ <var>w</var><sub><var>i</var></sub>(<var>r</var><sub><var>i</var></sub>
  − <var>M</var>)²), Σ <var>w</var><sub><var>i</var></sub> = 1<br>
  ${t('methodsScore')} = <var>M</var> ${phenomenon === 'negative' ? '+' : '−'}
  <var>S</var> · <var>cv</var>, <var>cv</var> = <var>S</var> / <var>M</var>`;

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
    return `<li><span class="node" ${style}></span>${attr(label(d.label, d.name))}
      <span class="comp-note">${d.indicators.length}</span></li>`;
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
export function renderModel(element, dataset, structure) {
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
  const methods = structure ? (() => {
    const parts = methodParts(structure);
    const hasThreshold = structure.domains
      .some((d) => d.indicators.some((i) => i.soft_threshold));
    return `<h2>${attr(say('methods', 'title', parts))}</h2>
      <p>${attr(say('methods', 'intro', parts))}</p>
      <ol class="model-steps">
        ${hasThreshold ? `<li>${attr(say('methods', 'threshold', parts))}
          <div class="formula">${FORMULA_THRESHOLD}</div></li>` : ''}
        <li>${attr(say('methods', structure.method === 'mpi'
    ? 'normalise_mpi' : 'normalise', parts))}
          <div class="formula">${structure.method === 'mpi'
    ? FORMULA_STANDARDISE : FORMULA_NORMALISE}</div></li>
        <li>${attr(say('methods', 'aggregate', parts))}
          <div class="formula">${formulaAggregate(structure.phenomenon)}</div></li>
      </ol>
      <p>${attr(say('methods', 'scale', parts))}</p>
      ${variantParagraphs(structure, parts).map((p) => `<p>${attr(p)}</p>`).join('')}
      <p>${attr(say('methods', 'reading', parts))}</p>
      <p class="muted">${attr(say('methods', 'provisional', parts))}</p>
      ${vocabulary(structure)}
      ${references(structure)}`;
  })() : '';
  element.innerHTML = `
    <div class="model-layout">
      <div class="model-figure-col">
        <h2 id="modelTitle">${attr(t('conceptualModel'))}</h2>
        ${figure}
        ${caption}
        ${src ? `<a class="model-open" href="${attr(src)}" target="_blank"
          rel="noopener">${attr(t('modelOpen'))}</a>` : ''}
      </div>
      <div class="model-methods">${methods}</div>
    </div>`;
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
