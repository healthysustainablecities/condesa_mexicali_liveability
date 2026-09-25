// The legend, and the class isolation it drives.
//
// It is a row, not a list: equal cells under the distribution chart's equal
// bars, so the legend reads as that chart's axis. Labels sit at each cell's
// left boundary for a cut indicator, which is where the value actually applies.
//
// Clicking a swatch isolates that class on every pane at once: the point of a
// side-by-side view is to ask "where is this class on each side", and isolating
// one pane at a time would answer half the question.  Clicking the same swatch
// again clears it.

import { BEYOND, LTS_COLORS, NO_DATA } from './choropleth.js';
import { state, update } from './state.js';
import { label, number, t, withUnits } from './strings.js';
import { measureLabel } from './text.js';

// Rough cycling and walking times, as the validation site showed them: a
// distance means more to a workshop audience once it is also a duration. Now
// shown against the DISTANCE options, where the distance is chosen, rather than
// taking a column of the legend.
const WALK_MINUTES = (metres) => Math.round(metres / 80); // ~4.8 km/h
const CYCLE_MINUTES = (metres) => Math.round(metres / 200); // ~12 km/h

/**
 * Minutes to cover a distance on the selected network.
 *
 * Shared with the distribution chart, which reads quartile distances out as
 * durations: the same distance is a very different journey walked or ridden,
 * so the estimate has to follow the network the indicator was measured over.
 */
export function travelMinutes(metres, network) {
  return network === 'walk' ? WALK_MINUTES(metres) : CYCLE_MINUTES(metres);
}

function timeLabel(metres, network) {
  const minutes = travelMinutes(metres, network);
  if (!minutes) return '';
  return `~${minutes} min`;
}

function swatch(color, primary, secondary, attrs = '') {
  return `<div class="leg-item ${attrs}">
    <span class="patch" style="background:${color}"></span>
    <span class="leg-label">${primary}</span>
    <span class="leg-note">${secondary || ''}</span>
  </div>`;
}

/**
 * What the legend is a legend *of* — the measure, in the reader's language.
 *
 * The swatches used to be distance bands, which meant the title could not be
 * the measure's own name: "Access (%)" over a proximity ramp, marked "higher is
 * better", read as though further away were better. Now that the map is the
 * percentage itself, the measure names it and its own direction is correct.
 */
export function legendTitle(resolved) {
  return {
    text: label(measureLabel(resolved), resolved.measureKey),
    help: resolved.description || '',
  };
}

/** The direction note, which follows the swatches rather than the measure. */
export function legendDirection(resolved) {
  if (resolved.direction === 'lower_is_better') return t('lowerBetter');
  if (resolved.direction === 'higher_is_better') return t('higherBetter');
  return '';
}

/**
 * A break value as a legend reads it.
 *
 * Trailing zeros are trimmed: a walkability class boundary is "-3", not
 * "-3.0", and a log2 ladder wants "12.5" beside "200".
 */
export function formatBreak(value) {
  if (value === null || value === undefined) return '';
  if (Number.isInteger(value)) return number(value, 0);
  if (Math.abs(value) >= 100) return number(value, 0);
  if (Math.abs(value) >= 1) return number(value, 1);
  return number(value, 2);
}

/** The label for one class: "0 – 20", "< -3", "≥ 3", or an ordinal code. */
export function classLabel(classification, index) {
  const cls = classification.classes[index];
  if (classification.kind === 'categories') return formatBreak(cls.value);
  const low = cls.min === null || cls.min === undefined;
  const high = cls.max === null || cls.max === undefined;
  if (low && high) return '';
  if (low) return `< ${formatBreak(cls.max)}`;
  if (high) return `≥ ${formatBreak(cls.min)}`;
  return `${formatBreak(cls.min)} – ${formatBreak(cls.max)}`;
}

/**
 * The cells of the legend row.
 *
 * One cell per class, in the same order and the same count as the distribution
 * chart's bars — the two are equal-width flex rows, so the swatches land under
 * their bars without either measuring the other.  "No data" is deliberately not
 * here: it has no bar, and including it would offset everything after it.
 *
 * A cut indicator's labels sit at each cell's **left boundary**, so the row
 * reads as an axis: `| −3 | −2 | −1 | 0 |`, with the value written where the
 * class actually begins.  Centring the full range under each cell instead needs
 * "-3 – -2" in about six characters of width, which wraps and reads badly; and
 * a boundary is what a reader is actually looking for.  Bands and ordinal codes
 * are not cuts — each names its whole cell — so those stay centred.
 */
function legendCells(resolved, classification) {
  const isolated = state.isolated;
  const target = classification.targetIndex;
  const cuts = classification.kind === 'classes';
  return classification.classes.map((cls, i) => {
    const selected =
      isolated && isolated.kind === 'class' && isolated.value === i;
    // blank where the class has no lower boundary: the cell below the first
    // edge begins at negative infinity, and the edge above it is the next
    // cell's label
    const primary = cuts
      ? (cls.min === null || cls.min === undefined ? '' : formatBreak(cls.min))
      : classLabel(classification, i);
    return `<div class="leg-item clickable ${selected ? 'selected' : ''}${
      target !== null && i === target ? ' target-start' : ''}"
          data-class="${i}"
          title="${classLabel(classification, i).replace(/"/g, '&quot;')}">
      <span class="patch" style="background:${cls.color}"></span>
      <span class="leg-label">${primary}</span>
    </div>`;
  }).join('');
}

/**
 * A last cell for the areas with nothing within the distance searched, where
 * the measure is a censored distance: it has a bar of its own in the chart,
 * so it takes a cell here, labelled at its left boundary like the others.
 */
function beyondCell(classification) {
  const censored = classification.censored;
  if (!censored) return '';
  const text = t('censoredBeyond').replace('{d}', `${formatBreak(censored.distance)} m`);
  return `<div class="leg-item beyond" title="${text.replace(/"/g, '&quot;')}">
      <span class="patch" style="background:${BEYOND}"></span>
      <span class="leg-label">${formatBreak(censored.distance)}</span>
    </div>`;
}

/** The value the row ends at, where the topmost class is not open-ended. */
function legendEnd(classification) {
  if (classification.kind !== 'classes') return '';
  // the cell for what lies beyond carries that boundary instead
  if (classification.censored) return '';
  const last = classification.classes[classification.classes.length - 1];
  if (last.max === null || last.max === undefined) return '';
  return `<div class="leg-end">${formatBreak(last.max)}</div>`;
}

// a relationship is configured as an SQL-ish operator; a legend says it in
// mathematics, not in SQL
const RELATIONS = { '>=': '≥', '<=': '≤', '>': '>', '<': '<' };

export function relationSymbol(relationship) {
  return RELATIONS[String(relationship || '>=').trim()] || '≥';
}

/** "≥ 5700", the target stated in the terms the legend uses. */
export function targetText(classification) {
  const target = classification && classification.target;
  if (!target || classification.targetIndex === null) return '';
  return `${relationSymbol(target.relationship)} ${formatBreak(target.criteria)}`;
}

export function renderLegend(element, resolved, classification) {
  if (!resolved || !classification) {
    element.innerHTML = '';
    return;
  }
  const direction = legendDirection(resolved);
  const heading = legendTitle(resolved);
  // units belong to the measure, not to the bands; a banded legend's swatches
  // are metres whatever the measure's own unit is
  const units = resolved.units;
  const censored = classification.censored;
  const notes = [
    `<span class="leg-swatch" style="background:${NO_DATA}"></span>${t('noData')}`,
    censored ? `<span class="leg-swatch" style="background:${BEYOND}"></span>${
      t('censoredNote').replace(/\{d\}/g, `${formatBreak(censored.distance)} m`)}` : '',
    classification.scale === 'log2' ? t('log2Scale') : '',
  ].filter(Boolean);
  element.innerHTML = `
    <div class="leg-title" title="${heading.help.replace(/"/g, '&quot;')}">
      ${[withUnits(heading.text, units), direction].filter(Boolean).join(' · ')}
    </div>
    <div class="leg-row${
  classification.kind === 'classes' ? ' cuts' : ''}">${
  legendCells(resolved, classification)}${beyondCell(classification)}${
  legendEnd(classification)}</div>
    <div class="leg-foot">${notes.join(' · ')}</div>
  `;

  element.querySelectorAll('.leg-item.clickable').forEach((node) => {
    node.addEventListener('click', () => {
      const value = Number(node.dataset.class);
      update((s) => {
        s.isolated =
          s.isolated && s.isolated.kind === 'class' && s.isolated.value === value
            ? null
            : { kind: 'class', value };
      }, 'isolate');
    });
  });
}

// Matches the population layer's paint stops in pane.js.  Kept beside the
// legend rather than derived from the layer, because a legend that reads its
// own colours out of the map is harder to follow than one that states them.
const POPULATION_STOPS = [
  ['#f3e6d8', '1 – 25'],
  ['#dba368', '25 – 100'],
  ['#a1591f', '100 +'],
];

/**
 * The population grid's own legend.
 *
 * Shown only while that overlay is on: an unlabelled brown wash under the
 * choropleth is not context, it is confusion.
 */
export function renderPopulationLegend(element, visible) {
  if (!visible) {
    element.innerHTML = '';
    element.hidden = true;
    return;
  }
  element.hidden = false;
  element.innerHTML = `
    <div class="leg-title">${t('overlayPopulation')}</div>
    <div class="leg-row">${POPULATION_STOPS.map(([color, text]) =>
    swatch(color, text, '', 'static')).join('')}</div>
    <div class="leg-direction">${t('peoplePerCell')}</div>`;
}

/** The traffic-stress legend, shown only while the network overlay is on. */
export function renderLtsLegend(element, visible) {
  if (!visible) {
    element.innerHTML = '';
    element.hidden = true;
    return;
  }
  element.hidden = false;
  const isolated = state.isolated;
  const rows = [1, 2, 3, 4].map((level) => {
    const selected =
      isolated && isolated.kind === 'lts' && isolated.value === level;
    return `<div class="leg-item clickable ${selected ? 'selected' : ''}"
                 data-lts="${level}">
      <span class="patch" style="background:${LTS_COLORS[level]}"></span>
      <span class="leg-label">LTS ${level}</span>
      <span class="leg-note"></span>
    </div>`;
  });
  element.innerHTML = `
    <div class="leg-title">${t('networkLayer')} — LTS</div>
    <div class="leg-row">${rows.join('')}</div>`;
  element.querySelectorAll('.leg-item.clickable').forEach((node) => {
    node.addEventListener('click', () => {
      const value = Number(node.dataset.lts);
      update((s) => {
        s.isolated =
          s.isolated && s.isolated.kind === 'lts' && s.isolated.value === value
            ? null
            : { kind: 'lts', value };
      }, 'isolate');
    });
  });
}
