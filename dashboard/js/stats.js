// The distribution chart: how much of the population sits in each map class.
//
// A map colours each area by its class; it cannot say how much of the
// population is in each one, and for a city where most people live in a few
// dense blocks those are very different questions. This answers the second.
//
// One bar per **map class**, always, so that the legend drawn underneath is
// literally this chart's axis: both are equal-width flex rows with the same
// number of cells, so a swatch stands under its bar without either measuring
// the other. That is why the class shares are computed by the exporter rather
// than re-binned here — a class edge falling inside a uniform histogram bin
// cannot be recovered afterwards.
//
// The shares are the exporter's population-weighted `class_shares` for the
// scale each pane is showing.
//
// An access measure judged at several distances is drawn differently: one bar
// per distance band, the share of each region's population with access within
// it.  How access grows with distance is what such a measure is about, and the
// class shares at one band showed only a slice of it -- mostly empty classes
// either side of a spike.  The legend beneath is then the map's key alone.

import { BEYOND, classOf } from './choropleth.js';
import { relationSymbol } from './legend.js';
import { state, update } from './state.js';
import { label, number, t } from './strings.js';

const PLOT_H = 56; // px, the drawing area's height
// Ceilings the y axis may round up to.  Finer than powers of ten so that a
// tallest bar of 77.9% gets an 80% axis rather than a 100% one that wastes half
// the chart, and always halvable into a legible midpoint.
const CEILINGS = [1, 2, 2.5, 5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 80, 100];

export function bandKey(resolved) {
  const s = resolved.selection;
  return `${s.family}|${s.measure}|${s.network}`;
}

function regionName(dataset, pane) {
  return label(
    (dataset.manifest.regions[pane.region] || {}).label, pane.region,
  );
}

/** The smallest legible ceiling above the tallest bar. */
function axisCeiling(peak) {
  return CEILINGS.find((c) => c >= peak - 1e-9) || 100;
}

/** A key naming which bar is which region, shown only when comparing. */
function regionKey(names) {
  if (names.length < 2) return '';
  return `<div class="histo-key">${names.map((name, i) =>
    `<span class="histo-key-item"><i style="opacity:${i ? 0.55 : 1}"></i>${name}</span>`,
  ).join('')}</div>`;
}

/**
 * The share of population meeting the column's target, stated once.
 *
 * Summed from the same class shares the bars are drawn from, so the sentence
 * and the picture cannot disagree.
 */
function targetNote(classification, perRegion, names) {
  const index = classification && classification.targetIndex;
  if (index === null || index === undefined) return '';
  const target = classification.target || {};
  const below = String(target.relationship || '>=').startsWith('<');
  const lines = perRegion.map((shares, i) => {
    if (!shares) return '';
    const met = below
      ? shares.slice(0, index + 1).reduce((a, b) => a + b, 0)
      : shares.slice(index).reduce((a, b) => a + b, 0);
    const prefix = names.length > 1 ? `${names[i]}: ` : '';
    return prefix + t('meetsTarget')
      .replace('{v}', number(met, 1))
      .replace('{t}', `${relationSymbol(target.relationship)} ${
        number(target.criteria, 0)}`);
  }).filter(Boolean);
  return lines.length
    ? `<div class="histo-target">${lines.join('<br>')}</div>` : '';
}

/**
 * The chart.
 *
 * `panes` are the pane configurations on screen, with `datasets` and
 * `statsEntries` in the same order. When two are given the bars are grouped:
 * one bar per region within each class, hovering naming the region.
 */
export function renderDistribution(
  element, resolved, classification, panes, datasets, statsEntries,
) {
  if (!resolved || !classification || !panes.length || !datasets[0]) {
    element.innerHTML = '';
    return;
  }
  if (resolved.bands.length > 1
      && ['access', 'beyond'].includes(resolved.measureKey)) {
    renderBands(element, resolved, classification, panes, datasets);
    return;
  }
  const names = panes.map((pane, i) => regionName(datasets[i], pane));
  const classes = classification.classes;

  // one row of shares per region, in class order, with -- for a censored
  // distance -- the share with nothing within the distance searched last
  const censored = classification.censored;
  const perRegion = panes.map((pane, i) => {
    const entry = statsEntries[i];
    const stats = entry && entry.columns
      ? entry.columns[classification.column] : null;
    if (!stats) return null;
    const shares = stats.class_shares
      || (censored && stats.beyond !== undefined
        ? classification.classes.map(() => 0) : null);
    if (!shares) return null;
    return censored ? [...shares, stats.beyond || 0] : shares;
  });
  if (perRegion.every((shares) => !shares)) {
    element.innerHTML = '';
    return;
  }

  // bars outside an isolated legend class are dimmed, so clicking the legend
  // reads as one action on the map and the chart together
  const isolated = state.isolated && state.isolated.kind === 'class'
    ? state.isolated.value : null;
  const peak = Math.max(
    0.1, ...perRegion.filter(Boolean).flatMap((s) => s),
  );
  const ceiling = axisCeiling(peak);
  const target = classification.targetIndex;

  const columns = censored
    ? [...classes, {
      color: BEYOND,
      beyond: t('censoredBeyond').replace('{d}', `${number(censored.distance, 0)} m`),
    }]
    : classes;
  const groups = columns.map((cls, i) => {
    const bars = perRegion.map((shares, r) => {
      const value = shares ? shares[i] : null;
      const height = Math.max(1, ((value || 0) / ceiling) * PLOT_H);
      const title = `${names[r] ? `${names[r]} · ` : ''}${
        cls.beyond ? `${cls.beyond} · ` : ''}${number(value, 1)}%`;
      return `<div class="histo-bar"
           style="height:${height.toFixed(1)}px;background:${cls.color};${
  r > 0 ? 'opacity:.55' : ''}"
           title="${title}"></div>`;
    }).join('');
    return `<div class="histo-group${
      isolated !== null && isolated !== i ? ' dim' : ''}${
      target !== null && i === target ? ' target-start' : ''}">${bars}</div>`;
  }).join('');

  const mid = ceiling / 2;
  element.innerHTML = `
    <div class="section-title">${t('byPopulation')}</div>
    <div class="histo">
      <div class="histo-y" style="height:${PLOT_H}px">
        <span>${number(ceiling, ceiling < 10 ? 1 : 0)}%</span>
        <span>${number(mid, mid < 10 ? 1 : 0)}%</span>
        <span>0%</span>
      </div>
      <div class="histo-plot" style="height:${PLOT_H}px">
        <div class="histo-bars">${groups}</div>
      </div>
    </div>
    ${regionKey(names)}
    ${targetNote(classification, perRegion, names)}`;
}

/**
 * The share of each region's population with access, band by band.
 *
 * The regions' own population-weighted figures, as the results table reports
 * them.  Bars take the colour the map gives that value, so a band reads the
 * same here as there; the band the map is drawn from is outlined, and clicking
 * another maps it instead.
 */
function renderBands(element, resolved, classification, panes, datasets) {
  const names = panes.map((pane, i) => regionName(datasets[i], pane));
  const perRegion = panes.map((pane, i) => {
    const values = (datasets[i].manifest.region_values || {})[pane.region] || {};
    return resolved.columns.map((column) => {
      const value = values[column];
      return value === undefined || value === null ? null : Number(value);
    });
  });
  if (perRegion.every((row) => row.every((v) => v === null))) {
    element.innerHTML = '';
    return;
  }
  const groups = resolved.bands.map((band, b) => {
    const bars = perRegion.map((row, r) => {
      const value = row[b];
      const cls = classOf(classification, value);
      const height = Math.max(1, ((value || 0) / 100) * PLOT_H);
      return `<div class="histo-bar"
           style="height:${height.toFixed(1)}px;background:${
  cls ? cls.color : '#c9c4bd'};${r > 0 ? 'opacity:.55' : ''}"
           title="${names[r]} · ${band} m · ${
  value === null ? '–' : `${number(value, 1)}%`}"></div>`;
    }).join('');
    const chosen = String(band) === String(resolved.distance);
    return `<div class="histo-group band${chosen ? ' chosen' : ''}"
      data-band="${band}" role="button" tabindex="0">${bars}</div>`;
  }).join('');
  const values = perRegion[0].map((v) => (v === null ? '–' : `${number(v, 0)}%`));
  element.innerHTML = `
    <div class="section-title" title="${t('bandChartHelp')}">${
  t('bandChartTitle')}</div>
    <div class="histo">
      <div class="histo-y" style="height:${PLOT_H}px">
        <span>100%</span><span>50%</span><span>0%</span>
      </div>
      <div class="histo-plot" style="height:${PLOT_H}px">
        <div class="histo-bars">${groups}</div>
      </div>
    </div>
    <div class="band-axis">${resolved.bands.map((band, b) =>
    `<span${String(band) === String(resolved.distance) ? ' class="chosen"' : ''}>${
      band} m<small>${values[b]}</small></span>`).join('')}</div>
    ${regionKey(names)}`;
  element.querySelectorAll('.histo-group.band').forEach((node) => {
    const pick = () => update((st) => {
      st.shared.distance = node.dataset.band;
      st.isolated = null;
    }, 'indicator');
    node.addEventListener('click', pick);
    node.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') pick();
    });
  });
}
