// The featured composite index: a radial profile of its indicators, grouped by
// domain.
//
// An interactive descendant of the GHSCI access profile (Region.access_profile
// in ghsci.py), which draws a city's access to each destination as a circular
// bar plot, with the 25-city median as a dot and its interquartile range as a
// whisker.  Here each bar -- a petal -- is one indicator of the index, drawn on
// the scale the index is built on, as points above or below the reference (its
// mean over the study area's sample points): a petal grows outward from the dashed reference ring
// where an indicator does better than the reference, and inward where it does
// worse, so the variation within each domain, and between them, reads first.
//
// The styling follows the index's conceptual model (the Adapted Urban
// Liveability Framework, whose figure the Conceptual model button opens):
// petals are grouped into their domain's sector and filled in that domain's
// colour, each domain has a node on the rim like the figure's domain nodes,
// joined to its sector by a dashed connector, and the index sits in the centre
// as the figure's blue core.  A region whose index gives no colours falls back
// to the index's shared classes.
//
// The index is not the average of its domains, nor a domain the average of its
// indicators: each is the average less a penalty for imbalance (the
// Mazziotta-Pareto approach).  A domain's score is drawn as a dashed arc across
// its sector, and the strip beneath the chart spells out mean level − penalty =
// index.  Clicking a petal maps that indicator; clicking a domain node maps the
// domain and lists what it is made of; clicking the centre maps the index; and
// clicking an area on the map makes it the subject in place of the region.

import { classify, classOf, NO_DATA } from './choropleth.js';
import { state } from './state.js';
import { integer, label, number, t } from './strings.js';
import { modificationNote } from './uli.js';

const W = 470; // viewBox width: room for a domain label either side
const H = 340; // viewBox height
const CX = W / 2;
const CY = H / 2;
const R_INNER = 34; // the scale's floor, around the centre disc
const R_OUTER = 100; // the scale's ceiling
const R_RIM = 104; // the domain's arc around its sector
const R_NODE = 119; // the centre of a domain's node
const NODE_R = 12; // a domain node's radius
const R_LABEL = 136; // where a domain's label starts
const PETAL_GAP = 0.025; // radians between neighbouring petals
const DOMAIN_GAP = 0.12; // radians between neighbouring domains
const WRAP = 13; // characters per line of a domain label
const LINE = 10; // domain label line height
// the core's blue, where the index gives no colour of its own
const CORE = '#4E8EF7';
// the narrowest a petal is drawn, as a share of an ordinary one: an
// indicator weighted zero is set aside, and shown so rather than vanishing
const MIN_PETAL = 0.2;
// a cog, for the index's settings (24 x 24)
const COG = 'M19.4 13a7.5 7.5 0 0 0 0-2l2.1-1.6-2-3.5-2.5 1a7.6 7.6 0 0 0-1.7-1'
  + 'L15 3h-4l-.4 2.9a7.6 7.6 0 0 0-1.7 1l-2.5-1-2 3.5L6.6 11a7.5 7.5 0 0 0 0 2'
  + 'l-2.1 1.6 2 3.5 2.5-1a7.6 7.6 0 0 0 1.7 1L11 21h4l.4-2.9a7.6 7.6 0 0 0'
  + ' 1.7-1l2.5 1 2-3.5zM13 15.5a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7z';

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

/**
 * Text made safe for an attribute or an element body.
 *
 * The quote is matched as \x22 rather than written into the pattern: a bare
 * double quote inside a regular expression literal reads to build/check.py as
 * the start of a string, and hides every declaration after it.
 */
const attr = (text) => String(text === undefined || text === null ? '' : text)
  .replace(/&/g, '&amp;').replace(/\x22/g, '&quot;').replace(/</g, '&lt;');

/** A number, or null for anything missing. */
function numeric(value) {
  if (value === undefined || value === null || value === '') return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

// half-widths the radial scale may take, in points either side of the reference
const REACHES = [5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100];

/**
 * The profile's radial scale: symmetric about the reference, and just wide
 * enough for the petals and markers of every region or area on screen.
 *
 * It used to reach one class step beyond the index's shared classes, which are
 * sized for sample points: a scale of 65-135 on which whole regions, averaging
 * within a few points of the reference, barely moved.  Values beyond the scale
 * are clipped, and marked as such.
 *
 * The subject's own petals may widen the scale only so far beyond everything
 * else drawn: one indicator far from the rest -- a fringe cell with no
 * employment access, at −57 -- would otherwise shrink the others to slivers.
 * That one is clipped instead, with its value on the chevron and in the list.
 */
const OUTLIER_ALLOWANCE = 1.25;

function bounds(subjectValues, contextValues, reference) {
  const deviations = (values) => values
    .filter((v) => v !== null)
    .map((v) => Math.abs(v - reference))
    .sort((a, b) => b - a);
  const context = deviations(contextValues)[0] || 0;
  const [top = 0, next = 0] = deviations(subjectValues);
  const limit = Math.max(context, next) * OUTLIER_ALLOWANCE;
  const reach = Math.max(context, next, Math.min(top, limit));
  const half = REACHES.find((r) => r >= reach * 1.05) || REACHES[REACHES.length - 1];
  return [reference - half, reference + half];
}

/** A difference from the reference, signed: +3.9, −1.6, 0.0. */
function signed(value, digits = 1) {
  if (value === null) return '–';
  const size = Math.abs(value);
  const text = number(size, digits);
  if (Number(size.toFixed(digits)) === 0) return text;
  return `${value > 0 ? '+' : '−'}${text}`;
}

/** A score as points from the reference, with the score itself: +3.9 (103.9). */
function scoreText(value, reference) {
  if (value === null) return t('noData');
  return `${signed(value - reference)} (${number(value, 1)})`;
}

function xy(radius, angle) {
  return [CX + radius * Math.cos(angle), CY + radius * Math.sin(angle)];
}

function point(radius, angle) {
  const [x, y] = xy(radius, angle);
  return `${x.toFixed(2)} ${y.toFixed(2)}`;
}

/** An annular wedge between two radii and two angles. */
function wedge(r0, r1, a0, a1) {
  const inner = Math.min(r0, r1);
  // a value at the reference still gets a band, so the petal can be seen and
  // clicked
  const outer = Math.max(Math.max(r0, r1), inner + 2);
  const large = a1 - a0 > Math.PI ? 1 : 0;
  return `M ${point(outer, a0)} A ${outer} ${outer} 0 ${large} 1 ${point(outer, a1)}`
    + ` L ${point(inner, a1)} A ${inner} ${inner} 0 ${large} 0 ${point(inner, a0)} Z`;
}

/** An arc at one radius between two angles. */
function arc(radius, a0, a1) {
  const large = a1 - a0 > Math.PI ? 1 : 0;
  return `M ${point(radius, a0)} A ${radius} ${radius} 0 ${large} 1 ${point(radius, a1)}`;
}

/** A chevron at a clipped petal's end, pointing the way the value goes on. */
function chevron(radius, angle, outward) {
  const tip = radius + (outward ? 6 : -4);
  const across = angle + Math.PI / 2;
  const [bx, by] = xy(radius, angle);
  const [tx, ty] = xy(tip, angle);
  const dx = 3 * Math.cos(across);
  const dy = 3 * Math.sin(across);
  return `M ${(bx + dx).toFixed(2)} ${(by + dy).toFixed(2)} L ${tx.toFixed(2)} ${
    ty.toFixed(2)} L ${(bx - dx).toFixed(2)} ${(by - dy).toFixed(2)}`;
}

/** A domain label on at most two lines. */
function wrapLabel(text) {
  const lines = [''];
  for (const word of String(text).split(/\s+/)) {
    const current = lines[lines.length - 1];
    if (!current || `${current} ${word}`.length <= WRAP) {
      lines[lines.length - 1] = current ? `${current} ${word}` : word;
    } else if (lines.length < 2) {
      lines.push(word);
    } else {
      lines[1] = `${lines[1]}…`;
      break;
    }
  }
  return lines;
}

function distanceText(metres) {
  if (metres >= 1000) {
    return `${number(metres / 1000, metres % 1000 ? 1 : 0)} km`;
  }
  return `${integer(metres)} m`;
}

function regionName(dataset, pane) {
  return label(
    (dataset.manifest.regions[pane.region] || {}).label, pane.region,
  );
}

/** A colour the index gives, as {fill, stroke}, or null. */
function colourOf(given) {
  if (!given) return null;
  if (typeof given === 'string') return { fill: given, stroke: given };
  return { fill: given.fill || given.stroke, stroke: given.stroke || given.fill };
}

/**
 * The sectors: each domain with the indicators of it that were exported.
 *
 * A flat index is one sector.  An indicator left out as not varying stays in
 * its domain's list, marked, so its absence is explained rather than silent,
 * but has no petal.
 */
function sectorsOf(structure, available) {
  const has = (column) => Boolean(column) && available.has(column);
  return structure.domains
    .map((d) => ({
      key: d.name || structure.name,
      label: d.name ? d.label : structure.label,
      column: d.name && has(d.column) ? d.column : null,
      weight: d.weight === undefined || d.weight === null ? 1 : Number(d.weight),
      colour: colourOf(d.colour),
      indicators: d.indicators.filter((i) => has(i.column) || i.dropped),
    }))
    .map((d) => ({ ...d, petals: d.indicators.filter((i) => has(i.column)) }))
    .filter((d) => d.petals.length);
}

/**
 * What the profile describes, and what it is read against.
 *
 * The subject is the area selected on a map, where there is one, and otherwise
 * the first pane's region. Every other region on screen is a reference marker.
 */
function subjectsFor(panes, datasets) {
  const regions = panes.map((pane, i) => ({
    kind: 'region',
    pane: i,
    name: regionName(datasets[i], pane),
    values: (datasets[i].manifest.region_values || {})[pane.region] || {},
  }));
  const selected = state.selected;
  if (selected && datasets[selected.pane]) {
    const manifest = datasets[selected.pane].manifest;
    const scale = label(
      (manifest.scales[selected.scale] || {}).label, selected.scale,
    );
    return {
      subject: {
        kind: 'area',
        pane: selected.pane,
        name: `${scale} · ${selected.id}`,
        values: selected.props || {},
      },
      references: regions,
    };
  }
  return { subject: regions[0], references: regions.slice(1) };
}

/**
 * The subject and references a profile of these panes describes, with any
 * scores computed from custom weights added (used by the report).
 */
export function profileSubjects(app, panes, datasets) {
  const found = subjectsFor(panes, datasets);
  const enrich = (app.uli && app.uli.values) || ((values) => values);
  for (const who of [found.subject, ...found.references]) {
    who.values = enrich(who.values);
  }
  return found;
}

/** One row of the strip: mean level − penalty = index, drawn and stated. */
function stripRow(who, columns, scale, negative) {
  const values = who.values || {};
  const index = numeric(values[columns.index]);
  const mean = numeric(values[columns.mean]);
  const penalty = numeric(values[columns.penalty]);
  const name = `<span class="strip-name" title="${attr(who.name)}">${
    attr(who.name)}</span>`;
  if (index === null) {
    return `${name}<span class="strip-bar"></span><span class="strip-sum">–</span>`;
  }
  const at = (v) => ((clamp(v, scale.lo, scale.hi) - scale.lo)
    / (scale.hi - scale.lo)) * 100;
  const other = mean === null ? index : mean;
  const low = Math.min(index, other);
  const high = Math.max(index, other);
  // in points from the reference: the penalty is a difference already
  const ref = scale.reference;
  const sum = mean === null
    ? `<strong>${signed(index - ref)}</strong>`
    : `${signed(mean - ref)} ${negative ? '+' : '−'} ${
      number(penalty || 0, 1)} = <strong>${signed(index - ref)}</strong>`;
  return `${name}
    <span class="strip-bar">
      <span class="strip-fill" style="width:${at(low).toFixed(1)}%"></span>
      <span class="strip-penalty" style="left:${at(low).toFixed(1)}%;width:${
  (at(high) - at(low)).toFixed(1)}%"></span>
      <b style="left:${at(scale.reference).toFixed(1)}%"></b>
    </span>
    <span class="strip-sum" title="${attr(`${number(index, 1)}`)}">${sum}</span>`;
}

/** A lens chip, like the lens boxes of the conceptual model. */
function lensChip(lens, lenses) {
  if (!lens) return '';
  return `<span class="lens" title="${attr(t('profileLensHelp'))}">${
    attr(label((lenses || {})[lens], lens))}</span>`;
}

/**
 * The domains as a list beneath the chart: a header for each, and the focused
 * domain's indicators as bars about the reference, each with its subdomain and
 * lens.  `classes.colour` colours a value by the index's shared classes, for an
 * index that gives no domain colours.
 */
function domainList(sectors, focus, subject, references, scale, mapped, lenses, classes) {
  const at = (v) => ((clamp(v, scale.lo, scale.hi) - scale.lo)
    / (scale.hi - scale.lo)) * 100;
  const mid = at(scale.reference);
  const valueOf = (who, column) => numeric(((who || {}).values || {})[column]);
  const compare = (column) => [subject, ...references].map((who) =>
    `${who.name}: ${scoreText(valueOf(who, column), scale.reference)}`).join(' · ');
  return sectors.map((sector) => {
    const colour = sector.colour;
    const swatch = colour
      ? `style="background:${colour.fill};border-color:${colour.stroke}"` : '';
    const value = sector.column ? valueOf(subject, sector.column) : null;
    const open = focus && focus.key === sector.key;
    const head = `<li class="domain-head${open ? ' open' : ''}${
      sector.column && sector.column === mapped ? ' mapped' : ''}"
        data-key="${attr(sector.key)}" data-column="${attr(sector.column || '')}"
        title="${attr(sector.column ? compare(sector.column) : '')}">
      <span class="node" ${swatch}></span>
      <span class="domain-name">${attr(label(sector.label, sector.key))}
        <span class="comp-note">${sector.petals.length} ${
  attr(t(sector.petals.length === 1 ? 'profileIndicator' : 'profileIndicators'))}</span></span>
      <span class="comp-value">${value === null ? '' : signed(value - scale.reference)}</span>
    </li>`;
    if (!open) return head;
    const weights = sector.indicators.map((i) => Number(i.weight) || 1);
    const total = weights.reduce((a, b) => a + b, 0) || 1;
    const uneven = weights.some((w) => Math.abs(w - weights[0]) > 1e-9);
    const rows = sector.indicators.map((indicator, j) => {
      const v = valueOf(subject, indicator.column);
      const notes = [];
      if (indicator.subdomain) notes.push(label(indicator.subdomain, ''));
      if (indicator.soft_threshold) {
        notes.push(t('profileThreshold')
          .replace('{d}', distanceText(Number(indicator.soft_threshold))));
      }
      if (uneven) {
        notes.push(`${t('profileWeight')} ${number((weights[j] / total) * 100, 0)}%`);
      }
      if (indicator.dropped) notes.push(t('profileExcluded'));
      const clipped = v !== null && (v < scale.lo || v > scale.hi);
      const fill = colour ? colour.fill : classes.colour(v);
      const edge = colour ? colour.stroke : 'transparent';
      const bar = v === null ? ''
        : `<i class="${clipped ? 'clipped' : ''}" style="left:${
          Math.min(at(v), mid).toFixed(1)}%;width:${
          Math.abs(at(v) - mid).toFixed(1)}%;background:${fill};border-color:${edge}"></i>`;
      return `<li class="indicator${indicator.column && indicator.column === mapped
        ? ' mapped' : ''}" data-column="${attr(indicator.column || '')}"
          data-key="${attr(sector.key)}" title="${attr(compare(indicator.column))}">
        <span>${attr(label(indicator.label, indicator.id))} ${lensChip(indicator.lens, lenses)}${
  notes.length ? `<span class="comp-note">${attr(notes.join(' · '))}</span>` : ''}</span>
        <span class="comp-bar">${bar}<b style="left:${mid.toFixed(1)}%"></b></span>
        <span class="comp-value">${v === null ? '–' : signed(v - scale.reference)}</span>
      </li>`;
    }).join('');
    return head + rows;
  }).join('');
}

/**
 * Render the profile for the selection's composite index.
 *
 * `panes` are the pane configurations on screen, with `datasets` and
 * `statsEntries` in the same order, as for the other sidebar charts.
 */
export function renderProfile(
  element, app, panes, datasets, statsEntries, options = {},
) {
  const resolved = app.resolved;
  const structure = resolved && resolved.composite;
  if (!structure || !panes.length || !datasets[0]) {
    element.innerHTML = '';
    return;
  }
  const reference = Number(structure.reference_value) || 100;
  const columns = structure.columns;
  const negative = structure.phenomenon === 'negative';
  const core = (colourOf(structure.colour) || {}).fill || CORE;
  // the index's own classes: colours for a region whose index gives none
  const breaks = app.vocab.breaks[columns.index];
  const classification = breaks
    ? classify(
      { column: columns.index, direction: negative
        ? 'lower_is_better' : 'higher_is_better' },
      breaks,
      null,
    )
    : null;
  const classColour = (v) => {
    const cls = v === null || !classification ? null : classOf(classification, v);
    return cls ? cls.color : NO_DATA;
  };

  const available = new Set();
  for (const dataset of datasets) {
    for (const entry of Object.values(dataset.manifest.scales)) {
      for (const column of entry.columns || []) available.add(column);
    }
  }
  const sectors = sectorsOf(structure, available);
  if (!sectors.length) {
    element.innerHTML = '';
    return;
  }
  const { subject, references } = subjectsFor(panes, datasets);
  // scores computed from custom importance weights, beside the published ones
  const enrich = (app.uli && app.uli.values) || ((values) => values);
  for (const who of [subject, ...references]) who.values = enrich(who.values);
  const valueOf = (who, column) => numeric((who.values || {})[column]);
  const spread = ((statsEntries[subject.pane || 0] || {}).columns) || {};
  const focus = sectors.find((s) => s.key === state.focusDomain) || null;
  const mapped = resolved.column;

  // the scale reaches the petals and markers of what is compared; one far
  // outlying petal is clipped rather than obeyed.  The middle half of the
  // areas is drawn, but clipped at the scale rather than setting it: a single
  // indicator's areas spread much further than a region's average, and sized
  // to them (±40 for Mexicali's grid) the regions' own petals were slivers
  const own = [];
  const context = [];
  for (const sector of sectors) {
    for (const indicator of sector.petals) {
      own.push(valueOf(subject, indicator.column));
      for (const ref of references) context.push(valueOf(ref, indicator.column));
    }
    if (sector.column) own.push(valueOf(subject, sector.column));
  }
  const [lo, hi] = bounds(own, context, reference);
  const scale = { lo, hi, reference };
  // equal differences either side of the reference ring enclose equal areas:
  // on a linear radius an outward petal looks larger than an inward one
  const radius = (v) => Math.sqrt(R_INNER ** 2
    + ((clamp(v, lo, hi) - lo) / (hi - lo)) * (R_OUTER ** 2 - R_INNER ** 2));
  const beyond = (v) => v !== null && (v < lo || v > hi);

  // each indicator an equal share of the circle, with a wider gap between
  // domains; the first domain is centred at the top, as on the figure.  With
  // importance weights of the reader's own, each petal's share follows its
  // weight (its domain's times its own), so the chart shows what counts for
  // how much
  const weighted = Boolean(structure.custom);
  const petalWeight = (sector, indicator) => {
    if (!weighted) return 1;
    const w = sector.weight * (Number(indicator.weight) || 0);
    return Math.max(w, MIN_PETAL);
  };
  const totalWeight = sectors.reduce((n, sector) => n + sector.petals
    .reduce((m, i) => m + petalWeight(sector, i), 0), 0);
  const share = (2 * Math.PI - sectors.length * DOMAIN_GAP) / totalWeight;
  const spanOf = (sector) => sector.petals
    .reduce((m, i) => m + petalWeight(sector, i), 0) * share;
  const firstSpan = spanOf(sectors[0]);
  let angle = -Math.PI / 2 - firstSpan / 2;

  const svg = [];
  svg.push(`<circle class="grid limit" cx="${CX}" cy="${CY}" r="${R_OUTER}"></circle>`);
  svg.push(`<circle class="ring" cx="${CX}" cy="${CY}" r="${
    radius(reference).toFixed(2)}"></circle>`);
  const nodes = [];
  const labels = [];
  const firstStart = angle;

  sectors.forEach((sector) => {
    const s0 = angle;
    const s1 = angle + spanOf(sector);
    let at = s0;
    const middle = (s0 + s1) / 2;
    const colour = sector.colour;
    // colours go in style, where CSS variables work and the petal rule's
    // defaults are overridden
    const stroke = colour ? colour.stroke : '#7a7269';
    const focused = Boolean(focus && focus.key === sector.key);

    sector.petals.forEach((indicator) => {
      const span = petalWeight(sector, indicator) * share;
      const a0 = at + PETAL_GAP / 2;
      const a1 = at + span - PETAL_GAP / 2;
      at += span;
      const mid = (a0 + a1) / 2;
      const setAside = weighted
        && !(sector.weight * (Number(indicator.weight) || 0) > 0);
      const value = valueOf(subject, indicator.column);
      const name = label(indicator.label, indicator.id);
      const tip = [`${name}: ${scoreText(value, reference)}`]
        .concat(references.map((ref) =>
          `${ref.name}: ${scoreText(valueOf(ref, indicator.column), reference)}`))
        .join(' · ');
      const fill = colour ? colour.fill : classColour(value);
      svg.push(`<path class="petal${mapped === indicator.column ? ' focus' : ''}${
        value !== null && value < reference ? ' below' : ''}${
        setAside ? ' set-aside' : ''}" d="${wedge(
        radius(reference), radius(value === null ? reference : value), a0, a1,
      )}" style="fill:${fill};stroke:${stroke}" data-key="${attr(sector.key)}"
        data-column="${attr(indicator.column)}"><title>${attr(tip)}</title></path>`);
      if (beyond(value)) {
        svg.push(`<path class="clip" d="${chevron(radius(value), mid, value > hi)}"><title>${
          attr(tip)}</title></path>`);
      }

      // the middle half of the areas at the subject's scale
      const stats = spread[indicator.column];
      const p25 = stats ? numeric(stats.p25) : null;
      const p75 = stats ? numeric(stats.p75) : null;
      if (p25 !== null && p75 !== null) {
        const [x1, y1] = xy(radius(p25), mid);
        const [x2, y2] = xy(radius(p75), mid);
        svg.push(`<line class="whisker" x1="${x1.toFixed(2)}" y1="${
          y1.toFixed(2)}" x2="${x2.toFixed(2)}" y2="${y2.toFixed(2)}"></line>`);
      }

      // the regions on screen, beside each other where there are two
      references.forEach((ref) => {
        const v = valueOf(ref, indicator.column);
        if (v === null) return;
        const offset = references.length > 1
          ? (ref.pane ? span * 0.18 : -span * 0.18) : 0;
        const [x, y] = xy(radius(v), mid + offset);
        svg.push(`<circle class="marker${ref.pane ? ' compare' : ''}" cx="${
          x.toFixed(2)}" cy="${y.toFixed(2)}" r="2.8"><title>${
          attr(`${ref.name}: ${scoreText(v, reference)}`)}</title></circle>`);
      });
    });

    // the domain's score, after its penalty, as a dashed arc across its sector
    const domainValue = sector.column ? valueOf(subject, sector.column) : null;
    if (domainValue !== null && !beyond(domainValue)) {
      svg.push(`<path class="domain-score" d="${arc(radius(domainValue), s0, s1)}"
        stroke="${stroke}"><title>${attr(`${label(sector.label, sector.key)}: ${
        scoreText(domainValue, reference)}`)}</title></path>`);
    }
    // its arc on the rim, dashed connector and node, as on the figure
    svg.push(`<path class="domain-rim" d="${arc(R_RIM, s0 + PETAL_GAP, s1 - PETAL_GAP)}"
      stroke="${stroke}"></path>`);
    const [cx0, cy0] = xy(R_RIM, middle);
    const [cx1, cy1] = xy(R_NODE - NODE_R, middle);
    svg.push(`<line class="connector" x1="${cx0.toFixed(2)}" y1="${cy0.toFixed(2)}"
      x2="${cx1.toFixed(2)}" y2="${cy1.toFixed(2)}" stroke="${stroke}"></line>`);
    const [nx, ny] = xy(R_NODE, middle);
    nodes.push(`<g class="domain-node${focused ? ' focus' : ''}" data-key="${
      attr(sector.key)}" data-column="${attr(sector.column || '')}">
      <circle cx="${nx.toFixed(2)}" cy="${ny.toFixed(2)}" r="${NODE_R}"
        fill="${colour ? colour.fill : '#fff'}" stroke="${stroke}"></circle>
      <text x="${nx.toFixed(2)}" y="${(ny + 3).toFixed(2)}" text-anchor="middle">${
  domainValue === null ? '' : signed(domainValue - reference, 0)}</text>
      <title>${attr(`${label(sector.label, sector.key)}: ${
    scoreText(domainValue, reference)}`)}</title></g>`);

    const [lx, ly] = xy(R_LABEL, middle);
    const cos = Math.cos(middle);
    const sin = Math.sin(middle);
    const anchor = cos > 0.3 ? 'start' : (cos < -0.3 ? 'end' : 'middle');
    const lines = wrapLabel(label(sector.label, sector.key));
    const shift = sin < -0.3
      ? -(lines.length - 1) * LINE
      : (sin > 0.3 ? 7 : 3 - ((lines.length - 1) * LINE) / 2);
    labels.push(`<text class="axis-label${focused ? ' focus' : ''}" x="${
      lx.toFixed(1)}" y="${(ly + shift).toFixed(1)}" text-anchor="${anchor}"
      data-key="${attr(sector.key)}" data-column="${attr(sector.column || '')}">${
  lines.map((line, k) => `<tspan x="${lx.toFixed(1)}" dy="${k ? LINE : 0}">${
    attr(line)}</tspan>`).join('')}</text>`);
    angle = s1 + DOMAIN_GAP;
  });
  svg.push(...nodes, ...labels);

  // the scale, in points from the reference, in the gap before the first domain
  const tickAngle = firstStart - DOMAIN_GAP / 2;
  for (const [v, text] of [[reference, '0'], [hi, signed(hi - reference, 0)]]) {
    const [tx, ty] = xy(radius(v) + 1, tickAngle);
    svg.push(`<text class="tick" x="${tx.toFixed(1)}" y="${ty.toFixed(1)}"
      text-anchor="middle">${text}</text>`);
  }

  // the index itself, at the centre, as the figure's core; clicking it maps
  // the index again
  const indexValue = valueOf(subject, columns.index);
  svg.push(`<g class="centre${mapped === columns.index ? ' focus' : ''}" data-column="${
    attr(columns.index)}">
    <circle cx="${CX}" cy="${CY}" r="${R_INNER - 4}" fill="#F3F7FF"
      stroke="${core}" stroke-width="3"></circle>
    <text class="centre-value" x="${CX}" y="${CY + 4}" text-anchor="middle"
      fill="${core}">${indexValue === null ? '–' : signed(indexValue - reference)}</text>
    <text class="centre-label" x="${CX}" y="${CY + 14}" text-anchor="middle">${
  attr(t('profileIndex'))}</text>
    <title>${attr(`${t('profileAll')} · ${scoreText(indexValue, reference)}`)}</title></g>`);

  // a region read against its own average sits on the ring by construction
  const self = subject.kind === 'region' && !references.length
    && indexValue !== null && Math.abs(indexValue - reference) < 2;

  const clear = subject.kind === 'area'
    ? `<button class="profile-chip" data-action="clear">${
      attr(t('profileClear'))}</button>`
    : '';
  const model = app.hasConceptualModel()
    ? `<button class="profile-chip model" data-action="model">${
      attr(t('conceptualModel'))}</button>`
    : '';
  const who = subject.kind === 'area'
    ? `${t('profileArea')}: ${subject.name}` : subject.name;
  // the settings, from a cog in the corner; and, beneath the chart, what they
  // have changed, for as long as anything is
  const note = options.inModal ? ''
    : modificationNote(app.uli ? app.uli.base : structure, state.uli);
  const cog = options.inModal ? ''
    : `<button class="profile-cog" data-action="settings" title="${
      attr(t('uliSettingsHelp'))}" aria-label="${attr(t('uliSettings'))}">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="${COG}"></path></svg>
    </button>`;
  const modified = note ? `<div class="uli-note">
      <span><strong>${attr(t('uliModified'))}</strong> ${attr(note)}${
  structure.custom ? ` · <em>${attr(t('uliExploratory'))}</em>` : ''}</span>
      <button class="profile-chip" data-action="reset">${attr(t('uliReset'))}</button>
    </div>` : '';
  element.innerHTML = `
    <div class="section-title">${attr(label(structure.label, t('profileTitle')))}</div>
    <div class="profile-head">
      <span class="profile-subject">${attr(who)}</span>${clear}${model}
    </div>
    <svg class="profile-chart" viewBox="0 0 ${W} ${H}" role="img"
         aria-label="${attr(t('profileTitle'))}">${svg.join('')}</svg>
    ${self ? `<div class="profile-note profile-self">${attr(t('profileSelf'))}</div>` : ''}
    <div class="profile-note">${attr(t('profileReference'))} · ${
  attr(t('profileHint'))}</div>
    <div class="profile-note" title="${attr(t('profilePenaltyHelp'))}">${
  attr(t('profileMean'))} ${negative ? '+' : '−'} ${attr(t('profilePenalty'))} = ${
  attr(t('profileIndex'))}</div>
    <div class="profile-strip" title="${attr(t('profilePenaltyHelp'))}">${
  [subject, ...references].map((row) =>
    stripRow(row, columns, scale, negative)).join('')}</div>
    <div class="section-title">${attr(t('profileDomains'))}
      <span class="lens-key">${attr(t('profileLens'))}</span></div>
    <ul class="profile-list">${domainList(
    sectors, focus, subject, references, scale, mapped, structure.lenses,
    { colour: classColour },
  )}</ul>${modified}${cog}`;

  element.querySelectorAll('[data-column]').forEach((node) => {
    node.addEventListener('click', () => {
      const column = node.dataset.column;
      const key = node.dataset.key;
      if (node.classList.contains('centre')) {
        app.focusComponent(column, null);
        return;
      }
      const isDomain = node.classList.contains('domain-node')
        || node.classList.contains('domain-head')
        || node.classList.contains('axis-label');
      if (isDomain) {
        // a second click on the domain already open closes it, and returns the
        // map to the index
        if (state.focusDomain === key && (!column || resolved.column === column)) {
          app.focusComponent(columns.index, null);
        } else {
          app.focusComponent(column || resolved.column, key);
        }
        return;
      }
      if (column) app.focusComponent(column, key || state.focusDomain);
    });
  });
  const button = element.querySelector('[data-action="clear"]');
  if (button) button.addEventListener('click', () => app.clearSelection());
  const open = element.querySelector('[data-action="model"]');
  if (open) open.addEventListener('click', () => app.openConceptualModel());
  const settings = element.querySelector('[data-action="settings"]');
  if (settings) settings.addEventListener('click', () => app.openUliSettings());
  const reset = element.querySelector('[data-action="reset"]');
  if (reset) reset.addEventListener('click', () => app.resetUliSettings());
}
