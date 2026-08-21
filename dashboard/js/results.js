// The region results table, and the difference between regions.
//
// This replaces the per-pane percentile strip, which reported p25/p50/p75 for
// percentages — where a percentile means nothing — and led with a single band
// as though it were "the" answer.
//
// The table's shape follows the measure:
//
//   access      one column per distance, holding the share of population with
//               access within it. These are the region's own
//               population-weighted figures, straight from the manifest. The
//               column the map is drawn from is outlined, so the map and the
//               table say which distance they are talking about -- the other
//               two are what make the first one mean something.
//   otherwise   mean, median and interquartile range -- the middle and the
//               spread, which is what a reader wants of a distribution. Three
//               quartiles named p25/p50/p75 stated the same thing in the
//               vocabulary of whoever computed them.
//
// Laid out as a table because that is how the workshop's own printed cards
// present the same comparison.

import { integer, label, number, t } from './strings.js';

/** The region-wide value of one column, or null. */
function regionValue(manifest, region, column) {
  const values = (manifest.region_values || {})[region];
  if (!values) return null;
  const value = values[column];
  return value === undefined ? null : value;
}

/** True where the region's own per-distance figures are the right summary. */
function isBanded(resolved) {
  return resolved.bands.length > 1
    && ['access', 'beyond'].includes(resolved.measureKey);
}

function formatValue(value, resolved, spread) {
  if (value === null || value === undefined) return '–';
  const units = (resolved.units || '').toLowerCase();
  // a width between two percentages is percentage points, not per cent: "0.7%"
  // for an interquartile range invites the reader to divide by something
  if (units.includes('percent')) {
    return spread ? `${number(value, 1)} pp` : `${number(value, 1)}%`;
  }
  if (units.includes('metre')) return `${integer(value)} m`;
  if (units.includes('index')) return number(value, 2);
  return number(value, 1);
}

/** True for the column holding a spread rather than a position. */
function isSpread(resolved, index) {
  return !isBanded(resolved) && index === 2;
}

/** The row of numbers for one region. */
function rowFor(resolved, dataset, pane, statsEntry) {
  if (isBanded(resolved)) {
    return resolved.columns.map(
      (column) => regionValue(dataset.manifest, pane.region, column),
    );
  }
  const stats = statsEntry && statsEntry.columns
    ? statsEntry.columns[resolved.column] : null;
  if (!stats) return [null, null, null];
  // the interquartile range is a width, not a position: it is the distance
  // between the quartiles, which is why it is computed rather than read
  const spread = stats.p75 === null || stats.p25 === null
    ? null : stats.p75 - stats.p25;
  return [stats.mean, stats.p50, spread];
}

function headings(resolved) {
  if (isBanded(resolved)) {
    return resolved.bands.map((band) => ({
      text: `${band} m`,
      help: '',
      // the distance the map is currently drawn from
      selected: String(band) === String(resolved.distance),
    }));
  }
  return [
    { text: t('mean'), help: t('meanHelp') },
    { text: t('median'), help: t('medianHelp') },
    { text: t('iqr'), help: t('iqrHelp') },
  ];
}

/**
 * Render the table.
 *
 * `panes` are the pane configurations on screen, `datasets` and `statsEntries`
 * their corresponding data, in the same order.
 */
export function renderResults(
  element, resolved, panes, datasets, statsEntries,
) {
  if (!resolved || !panes.length || !datasets[0]) {
    element.innerHTML = '';
    return;
  }
  const columns = headings(resolved);
  const rows = panes.map((pane, i) => ({
    name: label(
      (datasets[i].manifest.regions[pane.region] || {}).label, pane.region,
    ),
    scale: label(
      (datasets[i].manifest.scales[pane.scale] || {}).label, pane.scale,
    ),
    values: rowFor(resolved, datasets[i], pane, statsEntries[i]),
    // only the grid and region layers tile the whole study area, so a summary
    // over any other scale describes the areas shown and says so
    partial: !(pane.scale === 'grid' || pane.scale.startsWith('region')),
  }));

  const body = rows.map((row) => `
    <tr>
      <th scope="row">
        ${row.name}
        <span class="results-scale">${row.scale}</span>
      </th>
      ${row.values.map((v, i) =>
    `<td${columns[i].selected ? ' class="selected"' : ''}>${
      formatValue(v, resolved, isSpread(resolved, i))}</td>`).join('')}
    </tr>`).join('');

  // the difference belongs in the table, not floating over the maps: it is one
  // more row of the same comparison
  let difference = '';
  if (rows.length > 1) {
    const units = (resolved.units || '').toLowerCase();
    // a difference of two percentages is percentage points, not per cent
    const suffix = units.includes('percent') ? ' pp'
      : units.includes('metre') ? ' m' : '';
    const cells = columns.map((_, i) => {
      const a = rows[0].values[i];
      const b = rows[1].values[i];
      if (a === null || b === null || a === undefined || b === undefined) {
        return '<td>–</td>';
      }
      const delta = a - b;
      const better = resolved.direction === 'lower_is_better' ? -1 : 1;
      const tone = delta === 0 ? '' : (delta * better > 0 ? 'up' : 'down');
      const text = units.includes('metre')
        ? integer(delta) : number(delta, 1);
      return `<td class="${tone}${
        columns[i].selected ? ' selected' : ''}">${
        delta > 0 ? '+' : ''}${text}${suffix}</td>`;
    }).join('');
    difference = `<tr class="results-diff">
      <th scope="row">${t('difference')}</th>${cells}</tr>`;
  }

  const caption = isBanded(resolved)
    ? t('shareWithAccess')
    : t('acrossAreasShown');

  element.innerHTML = `
    <div class="section-title">${t('results')}</div>
    <table class="results-table">
      <caption>${caption}</caption>
      <thead><tr><th></th>${columns.map((c) =>
    `<th${c.selected ? ' class="selected"' : ''}${
      c.help ? ` title="${c.help.replace(/"/g, '&quot;')}"` : ''}>${
      c.text}</th>`).join('')}</tr></thead>
      <tbody>${body}${difference}</tbody>
    </table>
    ${rows.some((r) => r.partial)
    ? `<div class="results-note">${t('onlyShownAreas')}</div>` : ''}`;
}
