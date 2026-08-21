// "How to read this indicator", composed from data rather than written out.
//
// The validation site's equivalent was seventy lines of literal HTML with a
// branch per display mode, which meant a new indicator family needed new prose
// in the viewer.  Here everything specific comes from the exporter — the data
// dictionary's description, the units and statistic, the destinations and
// distances the indicator used, what the network means, and the ULI crosswalk's
// relation and direction.  The per-measure narrative comes from the text layer
// (js/text.js), so it can be reworded for an audience without a code change.

import { label, t, term } from './strings.js';
import { measureLabel, partsFor, say, template } from './text.js';

/**
 * A description in the reader's language.
 *
 * The dictionary carries both; the panel used to render `.en` unconditionally,
 * so the whole of "how to read this indicator" came out in English while the
 * rest of the interface was in Spanish.
 */
function described(entry) {
  return label(entry, '');
}


function list(items) {
  return items.filter(Boolean).map((item) => `<li>${item}</li>`).join('');
}

/**
 * "Why it matters": what could move this indicator, and to what effect.
 *
 * Joined by theme rather than by core measure. The ULI crosswalk names its
 * measures in English and the workshop sheet in Spanish -- with several present
 * in only one of the two -- so matching on the name would be fragile. Every
 * family has exactly one theme, which makes theme the reliable key.
 */
function interventionsHTML(resolved, themes) {
  if (!themes || !resolved) return '';
  const theme = themes.forFamily(resolved.family.id);
  const entries = theme ? themes.interventionsFor(theme.id) : [];
  // Omitted entirely when the workshop catalogue records no impact for this
  // theme. It previously listed anything merely *tagged* to the theme, which
  // put "Ciclovía" under fresh food as the only entry.
  if (!entries.length) return '';
  const items = entries.map((entry) => {
    const impacts = (entry.themes || {})[theme.id] || [];
    if (!impacts.length) return '';
    return `<li>
      <div class="intervention-name">${entry.name}</div>
      ${entry.description ? `<div>${entry.description}</div>` : ''}
      ${impacts.map((i) =>
    `<div class="intervention-impact">${i}</div>`).join('')}
    </li>`;
  }).join('');
  if (!items) return '';
  return `<h3>${t('whyItMatters')}</h3>
    <p class="muted">${t('whatCouldChange')}</p>
    <ul class="interventions">${items}</ul>`;
}

/**
 * Where the numbers came from, for this indicator specifically.
 *
 * Built from the region's own configuration rather than written out: the SCIAN
 * codes, dataset, licence and citation are all recorded in
 * `points_of_interest`, and a Mexicali reader checking a result will want the
 * codes rather than a general statement about DENUE.
 */
function sourcesHTML(resolved, rules, manifest) {
  const family = resolved.family;
  const parts = [];
  for (const source of family.sources || []) {
    const bits = [
      source.codes && source.codes.length
        ? `<div><span class="muted">SCIAN:</span> <code>${
          source.codes.join(', ')}</code></div>` : '',
      source.source ? `<div>${source.source}${
        source.publication_date ? `, ${source.publication_date}` : ''}</div>` : '',
      source.licence ? `<div class="muted">${source.licence}</div>` : '',
      source.url
        ? `<div><a href="${source.url}" target="_blank" rel="noopener">${
          source.url}</a></div>` : '',
    ].filter(Boolean).join('');
    parts.push(`<li><div class="intervention-name">${source.name}</div>${bits}</li>`);
  }
  if (family.note) parts.push(`<li>${label(family.note, '')}</li>`);

  // the routing rules are properties of the analysis, not of one indicator
  const method = [];
  if (rules && rules.pedestrian_filter) {
    method.push(rules.retains_private_access
      ? t('networkRetainsPrivate') : t('networkStandard'));
  }
  const cycling = rules && rules.cycling;
  if (cycling && resolved.selection.network !== 'walk') {
    const adt = Object.entries(cycling.adt_by_group || {})
      .map(([k, v]) => `${k} ${v}`).join(', ');
    method.push(`${t('ltsThresholds')}${adt ? ` — ${adt}` : ''}`);
  }
  // the region's general dataset attribution, which used to sit behind a
  // second "i" on the map itself.  One panel now answers "where did this come
  // from", from the specific to the general.
  const base = attributionLines(manifest || {});
  if (!parts.length && !method.length && !base.length) return '';
  return `<h3>${t('sources')}</h3>
    ${parts.length ? `<ul class="interventions">${parts.join('')}</ul>` : ''}
    ${method.length
    ? `<p class="muted">${method.join('<br>')}</p>` : ''}
    ${base.length
    ? `<h3>${t('baseData')}</h3><ul class="sources muted">${
      base.map((line) => `<li>${line}</li>`).join('')}</ul>` : ''}`;
}

export function renderInfo(element, resolved, vocab, dataset, panes, themes, rules) {
  if (!resolved) {
    element.innerHTML = '';
    return;
  }
  const family = resolved.family;
  const network = vocab.networks[resolved.selection.network] || {};
  const definition = vocab.description(resolved.column) || {};

  const facts = [];
  // units and statistic often say the same word once translated ("percent" /
  // "percentage" are both "porcentaje"), and saying it twice reads as an error
  const units = resolved.units ? term(resolved.units) : '';
  const statistic = resolved.statistic ? term(resolved.statistic) : '';
  facts.push(
    `<strong>${t('measure')}:</strong> ${
      label(measureLabel(resolved), resolved.measureKey)}`
    + (units ? ` — ${units}` : '')
    + (statistic && statistic !== units ? ` · ${statistic}` : ''),
  );
  facts.push(
    `<strong>${t('network')}:</strong> ${label(network.label, resolved.selection.network)}` +
    (described(network.description)
      ? ` — ${described(network.description)}` : ''),
  );
  if (resolved.bands.length) {
    // the one the map is drawn from, marked among the ones measured
    facts.push(`<strong>${t('distance')}:</strong> ${
      resolved.bands.map((b) => (String(b) === String(resolved.distance)
        ? `<strong>${b} m</strong>` : `${b} m`)).join(' · ')}`);
  } else if (resolved.distance) {
    facts.push(`<strong>${t('distance')}:</strong> ${resolved.distance} m`);
  }
  if (resolved.overlay) {
    // the source's own full name where the region recorded one; the bare
    // dest_name is an internal key and reads like one
    const byKey = new Map(
      (family.sources || []).map((source) => [source.dest_name, source.name]),
    );
    const names = (resolved.overlay.dest_names || [])
      .map((key) => byKey.get(key) || key.replace(/_/g, ' '));
    facts.push(`<strong>${t('destinations')}:</strong> ${
      names.length ? names.join(', ')
        : resolved.overlay.layer.replace(/_/g, ' ')}`);
  }
  facts.push(`<strong>${t('scale')}:</strong> ${
    panes.map((pane) => label(
      (dataset.manifest.scales[pane.scale] || {}).label, pane.scale,
    )).join(' · ')}`);

  const uli = (resolved.uli || []).map((entry) =>
    `<li><strong>${entry.measure}. ${entry.core_measure}</strong> — ${
      t('relation')}: ${term(entry.relation)}${
      entry.direction ? ` · ${term(entry.direction)}` : ''}${
      entry.sub_variable ? `<br><span class="muted">${entry.sub_variable}</span>` : ''
    }</li>`).join('');

  const narrative = say(
    'notes', resolved.measureKey, partsFor(resolved, vocab),
  ) || say('notes', 'value', partsFor(resolved, vocab));
  const columns = resolved.columns.map((column) => {
    const d = vocab.description(column) || {};
    return `<li><code>${column}</code> — ${described(d)}</li>`;
  }).join('');

  element.innerHTML = `
    <h2>${label(family.label, family.id)}</h2>
    <p class="lead">${described(definition)}</p>
    <ul class="facts">${list(facts)}</ul>
    <p>${narrative}</p>
    <p class="muted">${template('scale_note')}</p>
    ${uli ? `<h3>${t('uliMeasure')}</h3><ul class="uli">${uli}</ul>` : ''}
    ${sourcesHTML(resolved, rules, dataset.manifest)}
    ${interventionsHTML(resolved, themes)}
    <h3>${t('variable')}</h3>
    <ul class="columns">${columns}</ul>
  `;
}

/** The attribution block, shared by the info panel and the image export. */
export function attributionLines(manifest) {
  return (manifest.sources || []).map((source) => {
    const parts = [source.source || source.name];
    if (source.publication_date) parts.push(source.publication_date);
    if (source.licence) parts.push(source.licence);
    return parts.filter(Boolean).join(', ');
  });
}
