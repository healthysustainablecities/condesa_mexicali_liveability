// The composite index's settings panel.
//
// At the top, the walkability setting (attenuated by thermal comfort, the
// default, or not).  Beneath it, the profile of each region side by side:
// clicking an item of either -- the index, a domain or an indicator -- draws
// how the regions' areas are distributed on it, as overlaid smoothed
// histograms of the population grid's results.  Then importance weights of the
// reader's own.
//
// Settings are state (state.uli, and the hash), so they persist when the panel
// closes; see uli.js for what each setting does to the scores.

import {
  attenuationInfo, componentLabel, rawText, renderProfile, signed, walkabilityControl,
} from './profile.js';
import { state } from './state.js';
import { label, number, t, withUnits } from './strings.js';
import {
  activeIndex, hasCustomWeights, indicatorsOf, isActive, MAX_WEIGHT, referenceOf,
  roundWeight, variantFor,
} from './uli.js';

const attr = (text) => String(text === undefined || text === null ? '' : text)
  .replace(/&/g, '&amp;').replace(/\x22/g, '&quot;').replace(/</g, '&lt;');

// the regions' colours in the distributions: the index's own blue, and the
// comparison's pink
const REGION_COLOURS = ['#4E8EF7', '#d989d2', '#709e8b', '#e0a458'];

/** A weight slider, 0 (set aside) to MAX_WEIGHT, and its value. */
function slider(kind, key, value, text, swatch = '') {
  return `<label class="uli-weight">
    <span class="uli-weight-name">${swatch}${attr(text)}</span>
    <input type="range" min="0" max="${MAX_WEIGHT}" step="0.5" value="${value}"
      data-kind="${kind}" data-key="${attr(key)}" data-focus="${kind}-${attr(key)}"
      aria-label="${attr(text)}">
    <output>${value > 0 ? `×${number(value, 1)}` : attr(t('uliWeightExcluded'))}</output>
  </label>`;
}

/** Tick values for an axis between two values: about five, at a round step. */
function ticks(lo, hi) {
  const span = hi - lo;
  const raw = span / 5;
  const power = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * power).find((s) => s >= raw) || raw;
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) {
    out.push(Number(v.toFixed(6)));
  }
  return out;
}

/**
 * The regions' areas on one score, or on an indicator's own values, as
 * overlaid smoothed histograms with a legend, drawn from the export's
 * distributions.json.  `raw` ({axis, format}) draws an indicator's values in
 * their natural units, with the axis saying what they are.
 */
function distributionChart(dataset, column, title, reference, notes, raw = null) {
  const distributions = (dataset || {}).distributions;
  const range = distributions && distributions.x[column];
  if (!range) {
    return `<p class="note">${attr(t('uliDistributionMissing'))}</p>`;
  }
  const regions = Object.keys(dataset.manifest.regions || {})
    .filter((key) => (distributions.regions[key] || {})[column]);
  const W = 560;
  const H = raw ? 206 : 190;
  const m = { l: 12, r: 12, t: 12, b: raw ? 46 : 30 };
  const [lo, hi] = range.map(Number);
  const n = distributions.points || 64;
  const xs = Array.from({ length: n }, (_, i) => lo + ((hi - lo) * i) / (n - 1));
  const peak = Math.max(1e-12, ...regions.flatMap((key) =>
    distributions.regions[key][column].density));
  const px = (v) => m.l + ((v - lo) / (hi - lo)) * (W - m.l - m.r);
  const py = (d) => H - m.b - (d / peak) * (H - m.t - m.b);
  const areas = regions.map((key, i) => {
    const entry = distributions.regions[key][column];
    const colour = REGION_COLOURS[i % REGION_COLOURS.length];
    const line = xs.map((x, j) => `${px(x).toFixed(1)},${py(entry.density[j]).toFixed(1)}`);
    const fill = `M ${px(lo).toFixed(1)},${py(0).toFixed(1)} L ${line.join(' L ')} L ${
      px(hi).toFixed(1)},${py(0).toFixed(1)} Z`;
    const mean = Number(entry.mean);
    const meanMark = Number.isFinite(mean)
      ? `<line class="kde-mean" x1="${px(mean).toFixed(1)}" x2="${px(mean).toFixed(1)}"
          y1="${m.t}" y2="${H - m.b}" style="stroke:${colour}"></line>` : '';
    return `<path class="kde-area" d="${fill}" style="fill:${colour};stroke:${colour}"></path>
      ${meanMark}`;
  }).join('');
  const isScore = !raw && String(column).startsWith('index_');
  const tickText = (v) => {
    if (raw) return raw.format(v);
    return isScore ? signed(v - reference, 0) : number(v, 1);
  };
  const axis = (isScore
    ? ticks(lo - reference, hi - reference).map((v) => v + reference)
    : ticks(lo, hi))
    .filter((v) => v >= lo && v <= hi)
    .map((v) => `<line class="kde-tick" x1="${px(v).toFixed(1)}" x2="${px(v).toFixed(1)}"
        y1="${H - m.b}" y2="${H - m.b + 4}"></line>
      <text class="kde-label" x="${px(v).toFixed(1)}" y="${H - m.b + 14}"
        text-anchor="middle">${tickText(v)}</text>`).join('');
  const refLine = isScore && reference >= lo && reference <= hi
    ? `<line class="kde-ref" x1="${px(reference).toFixed(1)}" x2="${px(reference).toFixed(1)}"
        y1="${m.t - 4}" y2="${H - m.b}"></line>` : '';
  const legend = regions.map((key, i) => {
    const entry = distributions.regions[key][column];
    const colour = REGION_COLOURS[i % REGION_COLOURS.length];
    const mean = Number(entry.mean);
    return `<span class="kde-key"><i style="background:${colour};border-color:${colour}"></i>
      ${attr(label(dataset.manifest.regions[key].label, key))}
      <small>${attr(t('uliDistributionMean'))} ${Number.isFinite(mean)
    ? (raw ? raw.format(mean) : (isScore ? signed(mean - reference) : number(mean, 1)))
    : '–'} · ${
  attr(number(entry.n, 0))} ${attr(t('uliDistributionAreas'))}</small></span>`;
  }).join('');
  const scale = label((dataset.manifest.scales[distributions.scale] || {}).label,
    distributions.scale);
  return `<div class="kde">
    <div class="kde-title">${attr(title)}</div>
    <div class="kde-legend">${legend}</div>
    <svg class="kde-plot" viewBox="0 0 ${W} ${H}" role="img" aria-label="${attr(title)}">
      <line class="kde-axis" x1="${m.l}" x2="${W - m.r}" y1="${H - m.b}" y2="${H - m.b}"></line>
      ${areas}${refLine}${axis}
      ${raw ? `<text class="kde-axis-title" x="${(W / 2).toFixed(1)}" y="${H - 6}"
        text-anchor="middle">${attr(raw.axis)}</text>` : ''}
    </svg>
    <p class="note">${attr(t('uliDistributionNote').replace('{scale}', scale))}${
  isScore ? ` ${attr(t('uliDistributionPoints'))}` : ''}${notes ? ` ${attr(notes)}` : ''}</p>
  </div>`;
}

/** Render the panel into `element`. */
export function renderUliSettings(element, app, panes, datasets, statsEntries) {
  const base = app.uli ? app.uli.base : null;
  if (!base) {
    element.innerHTML = `<p class="note">${attr(t('reportNoIndex'))}</p>`;
    return;
  }
  // re-rendering replaces the controls; keep the one in use focused
  const focused = document.activeElement && element.contains(document.activeElement)
    ? document.activeElement.dataset.focus : null;
  const settings = state.uli;
  const variant = variantFor(base, settings);
  const custom = hasCustomWeights(base, settings);
  const shown = app.uli.structure;
  const reference = referenceOf(base);
  const dataset = datasets[0];
  const manifest = dataset.manifest;

  // the item whose distribution is drawn: the one last clicked, else the
  // index, in the columns of the walkability setting shown
  // (stored as the published column, so that it follows the walkability
  // setting to the same item)
  const pick = app.uliFocus || {};
  const column = pick.column ? app.uli.remap(pick.column) : shown.columns.index;
  // a score computed from custom weights has no exported distribution: the
  // published one of the same walkability setting (at equal weights) stands
  // in for it, and says so
  const substituted = String(column).startsWith('~');
  const exported = substituted
    ? activeIndex(base, { ...settings, domains: {}, indicators: {} })
      .remap(app.uli.inverse(column))
    : column;
  // an indicator is shown in its own units -- metres, per cent, degrees --
  // rather than as its score, where its values' distribution was exported
  const picked = indicatorsOf(shown).find((i) => i.column && i.column === column);
  const rawColumn = picked && picked.area_column;
  const described = rawColumn ? (app.vocab.descriptions || {})[rawColumn] || {} : {};
  const raw = rawColumn && ((dataset.distributions || {}).x || {})[rawColumn]
    ? {
      column: rawColumn,
      axis: withUnits(label(described.label, '') || label(described, '')
        || described.en || rawColumn, described.units),
      format: (v) => rawText(v, rawColumn, described),
    }
    : null;

  const domainSliders = base.domains
    .filter((d) => d.name && d.scored !== false && d.column).map((d) => {
    const colour = d.colour || {};
    const swatch = `<i class="uli-swatch" style="background:${
      attr(colour.fill || '#ccc')};border-color:${attr(colour.stroke || '#999')}"></i>`;
    const value = roundWeight(settings.domains[d.name] === undefined
      ? (Number(d.weight) || 1) : settings.domains[d.name]);
    return slider('domain', d.name, value, label(d.label, d.name), swatch);
  }).join('');
  // one slider per indicator, however many domains it counts towards (its
  // weight scales its share of each alike), grouped by the measure it reads
  let lastGroup = null;
  const indicatorSliders = indicatorsOf(base)
    .filter((i) => i.column && !i.dropped && isActive(i, variant)).map((i) => {
      const group = label(i.group, '');
      const title = group && group !== lastGroup
        ? `<div class="uli-group-title">${attr(group)}</div>` : '';
      lastGroup = group;
      const value = roundWeight(settings.indicators[i.id] === undefined
        ? (Number(i.weight) || 1) : settings.indicators[i.id]);
      return title + slider('indicator', i.id, value, label(i.label, i.id));
    }).join('');

  const status = custom
    ? `<span class="uli-badge exploratory" title="${attr(t('uliExploratoryHelp'))}">${
      attr(t('uliExploratory'))}</span>`
    : `<span class="uli-badge exact" title="${attr(t('uliExactHelp'))}">${
      attr(t('uliExact'))}</span>`;
  const regionKeys = Object.keys(manifest.regions || {});

  element.innerHTML = `
    <div class="uli-top">
      <p class="uli-status">${attr(t('uliShowing'))}: <b>${attr(
    label((variant || {}).label, label(base.label, base.name)))}</b> ${status}</p>
      ${walkabilityControl(base, settings, Boolean(app.walkInfoOpen))}
      ${app.walkInfoOpen ? `<div class="uli-info-box">${attenuationInfo(manifest)}</div>` : ''}
      ${custom ? `<p class="note">${attr(t('uliExploratoryHelp'))}</p>` : ''}
    </div>
    <section class="uli-section">
      <h3>${attr(t('uliRegionsTitle'))}</h3>
      <p class="note">${attr(t('uliRegionsIntro'))}</p>
      <div class="uli-regions">${regionKeys.map((key) =>
    `<div class="uli-profile" data-region="${attr(key)}"></div>`).join('')}</div>
      ${distributionChart(
    dataset,
    raw ? raw.column : exported,
    componentLabel(shown, column) || label(base.label, base.name),
    reference,
    substituted ? t('uliDistributionPublished') : '',
    raw,
  )}
    </section>
    <section class="uli-section">
      <h3>${attr(t('uliWeightsTitle'))}</h3>
      <p class="note">${attr(t('uliWeightsIntro'))}</p>
      ${domainSliders}
      <details class="uli-indicators"${custom && Object.keys(settings.indicators)
    .length ? ' open' : ''}>
        <summary>${attr(t('uliWeightsIndicators'))}</summary>
        ${indicatorSliders}
      </details>
      <button class="profile-chip" data-action="reset-weights">${
  attr(t('uliResetWeights'))}</button>
    </section>`;

  // each region's own profile, on one scale so the two can be compared
  const valuesOf = (key) => (manifest.region_values || {})[key] || {};
  const enrich = (app.uli && app.uli.values) || ((values) => values);
  const scaleWith = regionKeys.flatMap((key) => {
    const values = enrich(valuesOf(key));
    return shown.domains.flatMap((d) => [d.column, ...d.indicators
      .filter((i) => i.active !== false).map((i) => i.column)])
      .filter(Boolean).map((c) => (values[c] === undefined ? null : Number(values[c])));
  });
  regionKeys.forEach((key) => {
    renderProfile(
      element.querySelector(`.uli-profile[data-region="${key}"]`),
      app, panes, datasets, statsEntries,
      {
        inModal: true,
        compact: true,
        mode: 'distribution',
        focusColumn: column,
        scaleWith,
        subjects: {
          subject: {
            kind: 'region',
            pane: 0,
            name: label(manifest.regions[key].label, key),
            values: valuesOf(key),
          },
          references: [],
        },
        onItem: (item) => {
          app.uliFocus = item.column
            ? { ...item, column: app.uli.inverse(item.column) } : null;
          renderUliSettings(element, app, panes, datasets, statsEntries);
        },
      },
    );
  });

  const select = element.querySelector('.uli-top .uli-walk-select');
  if (select) {
    select.addEventListener('change', () => {
      app.setUliSettings((s) => { s.attenuation = select.value === '1'; });
    });
  }
  const info = element.querySelector('.uli-top [data-action="walk-info"]');
  if (info) info.addEventListener('click', () => app.toggleWalkInfo());
  element.querySelectorAll('input[type="range"]').forEach((input) => {
    const output = input.nextElementSibling;
    // the label follows the thumb; the index is recomputed on release, which
    // redraws the map once rather than for every step of a drag
    input.addEventListener('input', () => {
      const w = roundWeight(input.value);
      output.textContent = w > 0 ? `×${number(w, 1)}` : t('uliWeightExcluded');
    });
    input.addEventListener('change', () => {
      const w = roundWeight(input.value);
      app.setUliSettings((s) => {
        const map = input.dataset.kind === 'domain' ? s.domains : s.indicators;
        map[input.dataset.key] = w;
      });
    });
  });
  const reset = element.querySelector('[data-action="reset-weights"]');
  if (reset) reset.addEventListener('click', () => app.resetUliWeights());
  if (focused) {
    const again = element.querySelector(`[data-focus="${focused}"]`);
    if (again) again.focus();
  }
}
