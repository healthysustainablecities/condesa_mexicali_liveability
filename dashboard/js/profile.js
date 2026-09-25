// The featured composite index: a radial profile laid out as its conceptual
// model is.
//
// An interactive descendant of the GHSCI access profile (Region.access_profile
// in ghsci.py), and of the Adapted Urban Liveability Framework's figure (the
// Conceptual model button).  From the centre outwards:
//
//   the core         the index, as points above or below the reference
//   domain labels    the framework's domains, around the core, each placed
//                    at the centre of the indicators it counts (spread apart
//                    where they would collide)
//   domain circles   each domain's score
//   domain tracks    one ring per domain, in the same order from the inside
//                    out, coloured beneath each indicator the domain counts:
//                    an indicator bearing on three domains has three coloured
//                    bands at three distances, and its petal is shared by them
//   variation        one petal per indicator, grouped by the measure it reads
//                    (its core measure) and alphabetically within it, growing
//                    outward from the dashed reference ring where the
//                    indicator does better than the reference and inward where
//                    it does worse, coloured by its score as the map is, with
//                    the middle half of the areas as a whisker
//
// Hovering a petal gives the indicator's own value too (metres, per cent,
// degrees): the population-weighted average over the region or area.
//
// Every score is shown as points from the reference (0), the study area's
// average of each indicator over its sample points.  A region's
// or area's values are population-weighted averages of its sample points'.
//
// Each indicator takes an equal share of the circle; with importance weights
// of the reader's own, its share follows its weight.  An indicator counting
// towards several domains counts a share of its weight in each (a third in each
// of three), which its tooltip gives with its effective weight in the index.
// An indicator the index lists but does not count under the settings shown --
// thermal comfort, where walkability is attenuated by it -- keeps its place,
// hatched, and says why on hover.  Hovering a domain picks out its track and
// its indicators; a domain opened in the list below stays picked out.
//
// The index is not the average of its domains, nor a domain the average of its
// indicators: each is the average less a penalty for imbalance (the
// Mazziotta-Pareto approach), which the strip beneath the chart spells out.
//
// A click does what the context asks of it (`options.mode`): in the sidebar it
// maps the item clicked ('select'); in the conceptual model it describes it
// ('describe'); in the settings it shows how the regions' areas are
// distributed on it ('distribution').

import { classify, classOf, NO_DATA } from './choropleth.js';
import { state } from './state.js';
import { integer, label, number, t } from './strings.js';
import { say } from './text.js';
import {
  indicatorsOf, isVariant, referenceOf, shareOf, shareText, variantFor,
  walkabilityOptions, weightsNote,
} from './uli.js';

const S = 440; // the viewBox is square
const C = S / 2;
const R_CORE = 24; // the core: the index
const R_LABEL = 50; // where the domain labels are centred
const R_NODE = 88; // the centre of a domain's circle
const NODE_R = 11; // a domain circle's radius
const R_TRACK = 104; // the innermost domain track
const TRACK_STEP = 5; // from one domain's track to the next
const TRACK_W = 3.2; // a track's coloured band
const TRACK_CLEAR = 5; // between the outermost track and the petals
const R_OUT = 210; // the variation band's ceiling
const PETAL_GAP = 0.018; // radians between neighbouring petals
const GROUP_GAP = 0.07; // ... between neighbouring groups of petals
const TOP_GAP = 0.2; // ... at the top, where the scale is written
const WRAP = 12; // characters per line of a domain label
const LABEL_WIDTH = 50; // the widest a domain label may be drawn
const LINE = 9; // domain label line height
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

// several profiles may be on the page at once (the sidebar, the settings,
// the conceptual model), and each needs its own hatch pattern
let drawn = 0;

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
export function signed(value, digits = 1) {
  if (value === null) return '–';
  const size = Math.abs(value);
  const text = number(size, digits);
  if (Number(size.toFixed(digits)) === 0) return text;
  return `${value > 0 ? '+' : '−'}${text}`;
}

/** A score as points from the reference: +3.9. */
function scoreText(value, reference) {
  if (value === null) return t('noData');
  return signed(value - reference);
}

/**
 * What an area's own values of an indicator mean, in words: its `reading`
 * template filled from the area columns it names ({value}: the indicator's
 * average, {access}: the share of the population within its threshold...),
 * each in its units.  Without a template, its average value alone.
 */
export function readingText(indicator, values, describe) {
  const columns = { ...(indicator.reading_columns || {}) };
  // the variant shown may measure it differently (walkability, attenuated or
  // not): its average is the variant's
  if (indicator.area_column) columns.value = indicator.area_column;
  const valueOf = (column) => numeric((values || {})[column]);
  const template = label(indicator.reading, '');
  if (!template) {
    return columns.value
      ? rawLong(valueOf(columns.value), columns.value, describe(columns.value)) : '';
  }
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    const column = columns[key];
    return column ? rawText(valueOf(column), column, describe(column)) : '–';
  });
}

function xy(radius, angle) {
  return [C + radius * Math.cos(angle), C + radius * Math.sin(angle)];
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

/**
 * An indicator's own value, compactly, in its units: 312 m, 78%, 44.1°, 0.62.
 *
 * `described` is the data dictionary entry of the column holding it.
 */
export function rawText(value, column, described) {
  if (value === null) return '–';
  const units = String((described || {}).units || '').toLowerCase();
  const name = String(column || '');
  if (units.includes('°c') || name.startsWith('utci')) {
    return `${number(value, 1)}°`;
  }
  if (units.startsWith('percent') || units === '%' || name.startsWith('pct_')) {
    return `${integer(value)}%`;
  }
  if (units.startsWith('metre') || units === 'm' || name.includes('_dist_')) {
    return value >= 1000 ? `${number(value / 1000, 1)} km` : `${integer(value)} m`;
  }
  const size = Math.abs(value);
  return number(value, size < 10 ? 2 : (size < 100 ? 1 : 0));
}

/** The same value with its units in full, for a tooltip. */
function rawLong(value, column, described) {
  if (value === null) return t('noData');
  const units = (described || {}).units;
  const text = rawText(value, column, described);
  return /[0-9]$/.test(text) && units ? `${text} (${units})` : text;
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
 * The domains, each with the indicators of it that were exported.
 *
 * A flat index is one domain.  An indicator left out as not varying stays in
 * its domain's list, marked, so its absence is explained rather than silent,
 * but has no petal; an inactive one keeps its petal, hatched.  A domain the
 * framework names but no indicator yet measures is listed, not scored.
 */
function domainsOf(structure, available) {
  const has = (column) => Boolean(column) && available.has(column);
  return structure.domains
    .map((d) => ({
      key: d.name || structure.name,
      label: d.name ? d.label : structure.label,
      column: d.name && has(d.column) ? d.column : null,
      weight: d.weight === undefined || d.weight === null ? 1 : Number(d.weight),
      colour: colourOf(d.colour),
      scored: d.scored !== false && (d.indicators || []).length > 0,
      indicators: (d.indicators || []).filter((i) => has(i.column) || i.dropped),
    }))
    .map((d) => ({ ...d, petals: d.indicators.filter((i) => has(i.column)) }))
    .filter((d) => d.petals.length || !d.scored);
}

/**
 * The petals: each exported indicator once, in the index's order, with the
 * domains it counts towards (`memberOf`, keys of the domains drawn).
 */
function petalsOf(structure, domains, available) {
  const has = (column) => Boolean(column) && available.has(column);
  const memberOf = new Map();
  for (const domain of domains) {
    for (const indicator of domain.petals) {
      if (!memberOf.has(indicator.id)) memberOf.set(indicator.id, []);
      memberOf.get(indicator.id).push({ key: domain.key, share: shareOf(indicator) });
    }
  }
  return indicatorsOf(structure)
    .filter((i) => has(i.column) && memberOf.has(i.id))
    .map((i) => ({ ...i, memberOf: memberOf.get(i.id) }));
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
function domainList(domains, focus, subject, references, scale, mapped, lenses, classes,
  describe) {
  const at = (v) => ((clamp(v, scale.lo, scale.hi) - scale.lo)
    / (scale.hi - scale.lo)) * 100;
  const mid = at(scale.reference);
  const valueOf = (who, column) => numeric(((who || {}).values || {})[column]);
  const compare = (column) => [subject, ...references].map((who) =>
    `${who.name}: ${scoreText(valueOf(who, column), scale.reference)}`).join(' · ');
  return domains.map((domain) => {
    const colour = domain.colour;
    const swatch = colour
      ? `style="background:${colour.fill};border-color:${colour.stroke}"` : '';
    const value = domain.column ? valueOf(subject, domain.column) : null;
    const open = focus && focus.key === domain.key;
    const counted = domain.petals.filter((i) => i.active !== false).length;
    const note = domain.scored
      ? `${counted} ${t(counted === 1 ? 'profileIndicator' : 'profileIndicators')}`
      : t('profileUnscored');
    const head = `<li class="domain-head${open ? ' open' : ''}${
      domain.column && domain.column === mapped ? ' mapped' : ''}${
      domain.scored ? '' : ' unscored'}"
        data-key="${attr(domain.key)}" data-column="${attr(domain.column || '')}"
        data-kind="domain" data-tip="${attr(domain.column ? compare(domain.column) : '')}">
      <span class="node" ${swatch}></span>
      <span class="domain-name">${attr(label(domain.label, domain.key))}
        <span class="comp-note">${attr(note)}</span></span>
      <span class="comp-value">${value === null ? '' : signed(value - scale.reference)}</span>
    </li>`;
    if (!open) return head;
    // each member's part of the domain: its weight times its share here
    const weights = domain.indicators.map((i) => (Number(i.weight) || 1) * shareOf(i));
    const total = weights.reduce((a, b) => a + b, 0) || 1;
    const uneven = weights.some((w) => Math.abs(w - weights[0]) > 1e-9);
    const rows = domain.indicators.map((indicator, j) => {
      const inactive = indicator.active === false;
      const v = inactive ? null : valueOf(subject, indicator.column);
      const notes = [];
      if (indicator.subdomain) notes.push(label(indicator.subdomain, ''));
      if (indicator.soft_threshold) {
        notes.push(t('profileThreshold')
          .replace('{d}', distanceText(Number(indicator.soft_threshold))));
      }
      if (shareOf(indicator) < 1) {
        notes.push(`${shareText(shareOf(indicator))} ${t('profileWeight')}`);
      }
      if (uneven && !inactive) {
        notes.push(`${number((weights[j] / total) * 100, 0)}%`);
      }
      if (indicator.dropped) notes.push(t('profileExcluded'));
      if (inactive) notes.push(t('profileInactive'));
      const clipped = v !== null && (v < scale.lo || v > scale.hi);
      const fill = classes.colour(v);
      const bar = v === null ? ''
        : `<i class="${clipped ? 'clipped' : ''}" style="left:${
          Math.min(at(v), mid).toFixed(1)}%;width:${
          Math.abs(at(v) - mid).toFixed(1)}%;background:${fill};border-color:${
          colour ? colour.stroke : 'transparent'}"></i>`;
      // hovering says what the indicator's own values are, in words, for
      // the subject and every region compared with it
      const readings = [subject, ...references].map((who, n) => {
        const text = readingText(indicator, who.values, describe);
        return text && (n || references.length) ? `${who.name}: ${text}` : text;
      }).filter(Boolean).join(' · ');
      const tip = [inactive
        ? label(indicator.inactive_reason, t('profileInactive')) : '', readings]
        .filter(Boolean).join(' · ');
      return `<li class="indicator${indicator.column && indicator.column === mapped
        ? ' mapped' : ''}${inactive ? ' inactive' : ''}" data-column="${
  attr(inactive ? '' : indicator.column || '')}" data-kind="indicator"
          data-id="${attr(indicator.id)}"
          data-key="${attr(domain.key)}" data-tip="${attr(tip)}">
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
 * The walkability setting: a select between walkability attenuated by thermal
 * comfort (the default) and walkability without that attenuation, the default
 * marked as such, and an information button explaining what attenuation does.
 * Returns '' for an index without variants.
 */
export function walkabilityControl(structure, settings, open = false) {
  const options = walkabilityOptions(structure);
  if (options.length < 2) return '';
  const variant = variantFor(structure, settings);
  const isDefault = !isVariant(structure, settings);
  return `<div class="uli-walk">
      ${isDefault ? `<span class="uli-default" title="${attr(t('uliDefaultHelp'))}">${
    attr(t('uliDefault'))}</span>` : ''}
      <select class="uli-walk-select" aria-label="${attr(t('uliWalkability'))}"
        title="${attr(t('uliWalkability'))}">
        ${options.map((o) => `<option value="${o.attenuation ? '1' : '0'}"${
    variant && variant.name === o.name ? ' selected' : ''}>${
    attr(label(o.label, o.name))}</option>`).join('')}
      </select>
      <button class="btn icon serif uli-info-btn${open ? ' on' : ''}" data-action="walk-info"
        title="${attr(t('uliAttenuationInfo'))}" aria-label="${attr(t('uliAttenuationInfo'))}"
        aria-expanded="${open ? 'true' : 'false'}">i</button>
    </div>`;
}

/**
 * How attenuation works, in words and as a plot: walkability's percentile
 * rank, for places of four levels of walkability, falling as daytime thermal
 * comfort (UTCI) rises between the bounds it is re-scaled between, with the
 * city's own range on the modelled day shaded.
 */
export function attenuationInfo(manifest) {
  const info = (manifest || {}).attenuation;
  const heat = info && info.heat ? Object.values(info.heat)[0] : null;
  const bounds = heat && heat.bounds;
  if (!info || !bounds || bounds.length !== 2) {
    return `<p>${attr(say('methods', 'walkability', { attenuation: '0.5' }))}</p>`;
  }
  const lambda = Number(info.lambda) || 0.5;
  const [lo, hi] = bounds.map(Number);
  const [pLo, pHi] = (info.percentiles || [5, 95]).map(Number);
  const observed = (heat.observed || bounds).map(Number);
  const fixed = heat.basis === 'range';
  const degrees = (v) => `${number(v, fixed && Number.isInteger(v) ? 0 : 1)} °C`;
  const observedText = say('methods', 'attenuation_observed', {
    obsLow: `${number(observed[0], 1)} °C`,
    obsHigh: `${number(observed[1], 1)} °C`,
    low: number(pLo, 0),
    high: number(pHi, 0),
  });
  const text = say('methods', 'attenuation', {
    attenuation: number(lambda, 1),
    lowValue: degrees(lo),
    highValue: degrees(hi),
    observed: observedText,
  });
  // the plot: a margin for the axes, the bounds dashed, the city's range shaded
  const W = 300;
  const H = 170;
  const m = { l: 34, r: 10, t: 20, b: 34 };
  const span = hi - lo;
  const x0 = lo - span * (fixed ? 0.1 : 0.6);
  const x1 = hi + span * (fixed ? 0.1 : 0.6);
  const px = (x) => m.l + ((x - x0) / (x1 - x0)) * (W - m.l - m.r);
  const py = (y) => H - m.b - y * (H - m.t - m.b);
  const factor = (x) => 1 - lambda * clamp((x - lo) / span, 0, 1);
  const ranks = [1, 0.75, 0.5, 0.25];
  const lines = ranks.map((r, i) => {
    const points = [x0, lo, hi, x1].map((x) =>
      `${px(x).toFixed(1)},${py(r * factor(x)).toFixed(1)}`).join(' ');
    const [lx, ly] = [px(x1) - 2, py(r * factor(x1)) - 3];
    return `<polyline class="att-line" points="${points}"
        style="opacity:${(1 - i * 0.2).toFixed(2)}"></polyline>
      <text class="att-rank" x="${lx.toFixed(1)}" y="${ly.toFixed(1)}"
        text-anchor="end">${number(r, 2)}</text>`;
  }).join('');
  // about six ticks, at a round step
  const rough = (x1 - x0) / 6;
  const power = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 5, 10].map((f) => f * power).find((v) => v >= rough);
  const ticksX = [];
  for (let x = Math.ceil(x0 / step) * step; x <= x1 + 1e-9; x += step) {
    ticksX.push(`<text class="att-tick" x="${px(x).toFixed(1)}" y="${
      (H - m.b + 12).toFixed(1)}" text-anchor="middle">${number(x, step < 1 ? 1 : 0)}</text>`);
  }
  const ticksY = [0, 0.25, 0.5, 0.75, 1].map((y) =>
    `<text class="att-tick" x="${(m.l - 4).toFixed(1)}" y="${(py(y) + 3).toFixed(1)}"
      text-anchor="end">${number(y, 2)}</text>
     <line class="att-grid" x1="${m.l}" x2="${W - m.r}" y1="${py(y).toFixed(1)}"
      y2="${py(y).toFixed(1)}"></line>`).join('');
  const boundLabel = (v, p) => (fixed ? degrees(v) : `P${number(p, 0)} · ${degrees(v)}`);
  const plot = `<svg class="att-plot" viewBox="0 0 ${W} ${H}" role="img"
      aria-label="${attr(t('uliAttenuationPlot'))}">
    <rect class="att-range" x="${px(observed[0]).toFixed(1)}" y="${m.t}" width="${
  Math.max(1, px(observed[1]) - px(observed[0])).toFixed(1)}" height="${H - m.t - m.b}">
      <title>${attr(observedText)}</title></rect>
    ${ticksY}
    <line class="att-bound" x1="${px(lo).toFixed(1)}" x2="${px(lo).toFixed(1)}"
      y1="${m.t}" y2="${H - m.b}"></line>
    <line class="att-bound" x1="${px(hi).toFixed(1)}" x2="${px(hi).toFixed(1)}"
      y1="${m.t}" y2="${H - m.b}"></line>
    <text class="att-note" x="${px(lo).toFixed(1)}" y="${(m.t - 6).toFixed(1)}"
      text-anchor="middle">${boundLabel(lo, pLo)}</text>
    <text class="att-note" x="${px(hi).toFixed(1)}" y="${(m.t - 6).toFixed(1)}"
      text-anchor="end">${boundLabel(hi, pHi)}</text>
    ${lines}
    ${ticksX.join('')}
    <text class="att-axis" x="${((W + m.l - m.r) / 2).toFixed(1)}" y="${H - 4}"
      text-anchor="middle">${attr(t('uliAttenuationX'))}</text>
    <text class="att-axis" transform="translate(10 ${((H - m.b + m.t) / 2).toFixed(1)}) rotate(-90)"
      text-anchor="middle">${attr(t('uliAttenuationY'))}</text>
  </svg>`;
  return `<p>${attr(text)}</p>${plot}
    <p class="muted">${attr(say('methods', 'attenuation_plot', {}))}</p>`;
}

/** Show a tooltip beside the pointer, for the chart's [data-tip] items. */
function wireTips(element) {
  const tip = document.getElementById('hoverTip');
  if (!tip) return;
  const hide = () => { tip.style.display = 'none'; };
  element.querySelectorAll('[data-tip]').forEach((node) => {
    const text = node.dataset.tip;
    if (!text) return;
    node.addEventListener('mousemove', (event) => {
      tip.textContent = text;
      tip.style.left = `${event.clientX + 14}px`;
      tip.style.top = `${event.clientY + 10}px`;
      tip.style.display = 'block';
    });
    node.addEventListener('mouseleave', hide);
  });
  // a re-render replaces the node under the pointer without a mouseleave
  hide();
}

/**
 * Where each domain's circle and label go: at the weighted centre of the
 * petals of the indicators it counts (by their spans and its share of each),
 * so that a domain sits beside what it is made of.  Circles closer than a
 * minimum are pushed apart, keeping their order around the core, so that
 * neither they nor their labels overlap.
 */
function domainAngles(domains, placed) {
  const n = domains.length;
  const angles = domains.map((domain) => {
    const shares = new Map(domain.petals.map((i) => [i.id, shareOf(i)]));
    let x = 0;
    let y = 0;
    for (const p of placed) {
      const share = shares.get(p.indicator.id);
      if (!share) continue;
      x += Math.cos(p.mid) * p.span * share;
      y += Math.sin(p.mid) * p.span * share;
    }
    return x || y ? Math.atan2(y, x) : -Math.PI / 2;
  });
  if (n < 2) return angles;
  const TAU = 2 * Math.PI;
  const minimum = Math.min(TAU / n, 0.9) * 0.9;
  const order = angles.map((a, k) => [((a % TAU) + TAU) % TAU, k])
    .sort((a, b) => a[0] - b[0]);
  const at = order.map(([a]) => a);
  for (let step = 0; step < 300; step += 1) {
    let moved = false;
    for (let i = 0; i < n; i += 1) {
      const j = (i + 1) % n;
      const gap = ((at[j] - at[i]) % TAU + TAU) % TAU;
      if (gap < minimum - 1e-6) {
        const push = (minimum - gap) / 2;
        at[i] -= push;
        at[j] += push;
        moved = true;
      }
    }
    if (!moved) break;
  }
  const out = new Array(n);
  order.forEach(([, k], i) => { out[k] = at[i]; });
  return out;
}

/**
 * Hovering a domain -- its circle, label or track -- picks out its track and
 * the indicators it counts, dimming the rest; leaving it returns to the domain
 * opened in the list, if any.
 */
function wireDomainHover(element, focusKey) {
  const chart = element.querySelector('.profile-chart');
  if (!chart) return;
  const pick = (key) => {
    chart.querySelectorAll('[data-domains]').forEach((node) => {
      const member = node.dataset.domains.split(' ').includes(key);
      node.classList.toggle('dim', Boolean(key) && !member);
    });
    chart.querySelectorAll('[data-track]').forEach((node) => {
      node.classList.toggle('dim', Boolean(key) && node.dataset.track !== key);
    });
  };
  chart.querySelectorAll('[data-track]').forEach((node) => {
    node.addEventListener('mouseenter', () => pick(node.dataset.track));
    node.addEventListener('mouseleave', () => pick(focusKey));
  });
}

/**
 * The label of the item a column holds: the index, a domain, or an
 * indicator -- without its domain, which the chart already shows.
 */
export function componentLabel(structure, column) {
  if (!structure || !column) return '';
  const columns = structure.columns || {};
  if (column === columns.index) return t('profileIndexWhole');
  if (column === columns.mean) return t('profileMean');
  if (column === columns.penalty) return t('profilePenalty');
  const domain = structure.domains.find((d) => d.column === column);
  if (domain) return label(domain.label, domain.name);
  const indicator = indicatorsOf(structure).find((i) => i.column === column);
  return indicator ? label(indicator.label, indicator.id) : '';
}

/**
 * Render the profile for the selection's composite index.
 *
 * `panes` are the pane configurations on screen, with `datasets` and
 * `statsEntries` in the same order, as for the other sidebar charts.
 * `options`:
 *   compact     the chart and its strip alone, for a panel
 *   inModal     no settings cog or walkability control
 *   subjects    {subject, references} in place of those on screen
 *   scaleWith   further values the radial scale must reach
 *   mode        'select' (map the item clicked), 'describe' or
 *               'distribution' (both call onItem instead)
 *   onItem      ({kind, key, column, id}) for the modes other than select
 *   focusColumn the item to outline, where it is not the one mapped
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
  const mode = options.mode || 'select';
  const reference = referenceOf(structure);
  const columns = structure.columns;
  const negative = structure.phenomenon === 'negative';
  const core = (colourOf(structure.colour) || {}).fill || CORE;
  drawn += 1;
  const hatch = `profile-hatch-${drawn}`;
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
  const domains = domainsOf(structure, available);
  const petals = petalsOf(structure, domains, available);
  if (!petals.length) {
    element.innerHTML = '';
    return;
  }
  // the domains scored, each with a track and a circle
  const scored = domains.filter((d) => d.scored && d.petals.length);
  const { subject, references } = options.subjects || subjectsFor(panes, datasets);
  // scores computed from custom importance weights, beside the published ones
  const enrich = (app.uli && app.uli.values) || ((values) => values);
  for (const who of [subject, ...references]) who.values = enrich(who.values);
  const valueOf = (who, column) => numeric((who.values || {})[column]);
  const spread = options.subjects
    ? {} : ((statsEntries[subject.pane || 0] || {}).columns) || {};
  const focus = domains.find((d) => d.key === state.focusDomain) || null;
  const mapped = options.focusColumn !== undefined
    ? options.focusColumn : resolved.column;
  const describe = (column) => (app.vocab.descriptions || {})[column] || null;

  // the scale reaches the petals and markers of what is compared; one far
  // outlying petal is clipped rather than obeyed
  const own = [];
  const context = [...(options.scaleWith || [])];
  for (const indicator of petals) {
    if (indicator.active === false) continue;
    own.push(valueOf(subject, indicator.column));
    for (const ref of references) context.push(valueOf(ref, indicator.column));
  }
  for (const domain of scored) {
    if (domain.column) own.push(valueOf(subject, domain.column));
  }
  const [lo, hi] = bounds(own, context, reference);
  const scale = { lo, hi, reference };
  // the tracks, one per domain scored, and the petals beyond them
  const trackRadius = (k) => R_TRACK + k * TRACK_STEP;
  const R_IN = trackRadius(Math.max(scored.length - 1, 0)) + TRACK_W / 2 + TRACK_CLEAR;
  // equal differences either side of the reference ring enclose equal areas:
  // on a linear radius an outward petal looks larger than an inward one
  const radius = (v) => Math.sqrt(R_IN ** 2
    + ((clamp(v, lo, hi) - lo) / (hi - lo)) * (R_OUT ** 2 - R_IN ** 2));
  const beyond = (v) => v !== null && (v < lo || v > hi);

  // each indicator an equal share of the circle (or its weight's share, with
  // weights of the reader's own), clockwise from the top, with a gap between
  // groups and a wider one at the top for the scale
  const weighted = Boolean(structure.custom);
  const domainWeight = new Map(domains.map((d) => [d.key, d.weight]));
  const setAsideDomain = (key) => weighted && !(domainWeight.get(key) > 0);
  const petalWeight = (indicator) => {
    if (!weighted || indicator.active === false) return 1;
    return Math.max(Number(indicator.weight) || 0, MIN_PETAL);
  };
  const groupOf = (indicator) => label(indicator.group, '') || indicator.id;
  const groups = petals.reduce((n, p, i) =>
    n + (i && groupOf(p) === groupOf(petals[i - 1]) ? 0 : 1), 0);
  const totalWeight = petals.reduce((n, p) => n + petalWeight(p), 0);
  const share = (2 * Math.PI - TOP_GAP - (groups - 1) * GROUP_GAP) / totalWeight;
  let angle = -Math.PI / 2 + TOP_GAP / 2;
  const placed = petals.map((indicator, i) => {
    if (i && groupOf(indicator) !== groupOf(petals[i - 1])) angle += GROUP_GAP;
    const span = petalWeight(indicator) * share;
    const at = { indicator, a0: angle + PETAL_GAP / 2, a1: angle + span - PETAL_GAP / 2 };
    angle += span;
    return { ...at, mid: (at.a0 + at.a1) / 2, span };
  });

  const svg = [`<defs><pattern id="${hatch}" width="4" height="4"
      patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="4" height="4" fill="#fff"></rect>
      <line x1="0" y1="0" x2="0" y2="4" stroke="#b6b0a7" stroke-width="1.6"></line>
    </pattern></defs>`];
  svg.push(`<circle class="grid limit" cx="${C}" cy="${C}" r="${R_OUT}"></circle>`);
  svg.push(`<circle class="grid" cx="${C}" cy="${C}" r="${R_IN.toFixed(2)}"></circle>`);
  svg.push(`<circle class="ring" cx="${C}" cy="${C}" r="${
    radius(reference).toFixed(2)}"></circle>`);
  const names = new Map(domains.map((d) => [d.key, label(d.label, d.key)]));

  // the petals
  placed.forEach(({ indicator, a0, a1, mid, span }) => {
    const inactive = indicator.active === false;
    const name = label(indicator.label, indicator.id);
    const reading = readingText(indicator, subject.values, describe);
    const rawTip = reading ? ` · ${reading}` : '';
    // the domains it counts towards, with its share of each, and what it counts
    // for in the index as a whole
    const towards = indicator.memberOf.map((m) =>
      `${names.get(m.key)}${m.share < 1 ? ` (${shareText(m.share)})` : ''}`).join(', ');
    const effective = indicator.effective_weight === null
      || indicator.effective_weight === undefined ? NaN : Number(indicator.effective_weight);
    const weightTip = ` · ${t('profileCountsTowards')}: ${towards}${
      !weighted && Number.isFinite(effective) && !inactive
        ? ` · ${t('profileEffective')} ${number(effective * 100, 1)}%` : ''}`;
    const member = indicator.memberOf.map((m) => m.key).join(' ');
    const common = `data-key="${attr(indicator.memberOf[0].key)}" data-kind="indicator"
      data-id="${attr(indicator.id)}" data-column="${attr(indicator.column)}"
      data-domains="${attr(member)}"`;
    const focusClass = focus && !indicator.memberOf.some((m) => m.key === focus.key)
      ? ' dim' : '';
    if (inactive) {
      const reason = label(indicator.inactive_reason, t('profileInactive'));
      const tip = `${name}${rawTip} · ${reason}`;
      svg.push(`<path class="petal inactive${focusClass}" d="${wedge(
        radius(reference) - 5, radius(reference) + 5, a0, a1,
      )}" style="fill:url(#${hatch})" ${common}
        data-tip="${attr(tip)}"></path>`);
      return;
    }
    const setAside = weighted && (!((Number(indicator.weight) || 0) > 0)
      || indicator.memberOf.every((m) => setAsideDomain(m.key)));
    const value = valueOf(subject, indicator.column);
    const tip = [`${name}: ${scoreText(value, reference)}${rawTip}`]
      .concat(references.map((ref) =>
        `${ref.name}: ${scoreText(valueOf(ref, indicator.column), reference)}`))
      .join(' · ') + weightTip;
    svg.push(`<path class="petal${mapped === indicator.column ? ' focus' : ''}${
      value !== null && value < reference ? ' below' : ''}${
      setAside ? ' set-aside' : ''}${focusClass}" d="${wedge(
      radius(reference), radius(value === null ? reference : value), a0, a1,
    )}" style="fill:${classColour(value)}" ${common}
      data-tip="${attr(tip)}"></path>`);
    if (beyond(value)) {
      svg.push(`<path class="clip${focusClass}" d="${chevron(radius(value), mid, value > hi)}"
        ${common} data-tip="${attr(tip)}"></path>`);
    }

    // the middle half of the areas at the subject's scale
    const stats = spread[indicator.column];
    const p25 = stats ? numeric(stats.p25) : null;
    const p75 = stats ? numeric(stats.p75) : null;
    if (p25 !== null && p75 !== null) {
      const [x1, y1] = xy(radius(p25), mid);
      const [x2, y2] = xy(radius(p75), mid);
      svg.push(`<line class="whisker${focusClass}" x1="${x1.toFixed(2)}" y1="${
        y1.toFixed(2)}" x2="${x2.toFixed(2)}" y2="${y2.toFixed(2)}"
        data-domains="${attr(member)}"></line>`);
    }

    // the regions on screen, beside each other where there are two
    references.forEach((ref) => {
      const v = valueOf(ref, indicator.column);
      if (v === null) return;
      const offset = references.length > 1
        ? (ref.pane ? span * 0.18 : -span * 0.18) : 0;
      const [x, y] = xy(radius(v), mid + offset);
      svg.push(`<circle class="marker${ref.pane ? ' compare' : ''}${focusClass}" cx="${
        x.toFixed(2)}" cy="${y.toFixed(2)}" r="2.8" data-domains="${attr(member)}"
        data-tip="${attr(`${ref.name}: ${scoreText(v, reference)}`)}"></circle>`);
    });
  });

  // the tracks: each domain's ring, coloured beneath the indicators it counts,
  // and its circle and label around the core, joined to its ring
  const nodes = [];
  const labels = [];
  const middles = domainAngles(scored, placed);
  scored.forEach((domain, k) => {
    const r = trackRadius(k);
    const colour = domain.colour;
    const stroke = colour ? colour.stroke : '#7a7269';
    const faint = colour ? colour.fill : '#e4e0da';
    const focused = Boolean(focus && focus.key === domain.key);
    const dim = focus && !focused ? ' dim' : '';
    const aside = setAsideDomain(domain.key) ? ' set-aside' : '';
    const domainValue = domain.column ? valueOf(subject, domain.column) : null;
    const domainTip = `${label(domain.label, domain.key)}: ${
      scoreText(domainValue, reference)}`;
    const domainAttrs = `data-key="${attr(domain.key)}" data-kind="domain"
      data-column="${attr(domain.column || '')}"`;
    const members = new Set(domain.petals.map((i) => i.id));
    const arcs = placed.filter((p) => members.has(p.indicator.id))
      .map((p) => arc(r, p.a0, p.a1)).join(' ');
    svg.push(`<g class="track${dim}${aside}${focused ? ' focus' : ''}"
      data-track="${attr(domain.key)}" ${domainAttrs} data-tip="${attr(domainTip)}">
      <circle class="track-base" cx="${C}" cy="${C}" r="${r}" stroke="${faint}"></circle>
      <path class="track-arcs" d="${arcs}" stroke="${stroke}"
        stroke-width="${TRACK_W}"></path></g>`);
    // circle and label at the centre of the indicators it counts
    const middle = middles[k];
    const [cx0, cy0] = xy(R_NODE + NODE_R, middle);
    const [cx1, cy1] = xy(r, middle);
    svg.push(`<line class="connector${dim}" x1="${cx0.toFixed(2)}" y1="${cy0.toFixed(2)}"
      x2="${cx1.toFixed(2)}" y2="${cy1.toFixed(2)}" stroke="${stroke}"
      data-track="${attr(domain.key)}"></line>`);
    const [nx, ny] = xy(R_NODE, middle);
    nodes.push(`<g class="domain-node${focused ? ' focus' : ''}${
      mapped && domain.column === mapped ? ' mapped' : ''}${dim}" ${domainAttrs}
      data-track="${attr(domain.key)}" data-tip="${attr(domainTip)}">
      <circle cx="${nx.toFixed(2)}" cy="${ny.toFixed(2)}" r="${NODE_R}"
        fill="${colour ? colour.fill : '#fff'}" stroke="${stroke}"></circle>
      <text x="${nx.toFixed(2)}" y="${(ny + 3).toFixed(2)}" text-anchor="middle">${
  domainValue === null ? '' : signed(domainValue - reference, 0)}</text></g>`);

    // the label, between the core and the domain's circle, shrunk to fit
    const lines = wrapLabel(label(domain.label, domain.key));
    const longest = Math.max(...lines.map((line) => line.length));
    // shrunk to fit, but never below legibility: one long word
    // ('medioambiental') would otherwise set it at 6 px
    const font = Math.max(7, Math.min(8, LABEL_WIDTH / (longest * 0.56)));
    const [lx, ly] = xy(R_LABEL, middle);
    const top = ly - ((lines.length - 1) * LINE) / 2 + font * 0.35;
    labels.push(`<text class="axis-label${focused ? ' focus' : ''}${dim}" x="${
      lx.toFixed(1)}" y="${top.toFixed(1)}" text-anchor="middle"
      style="font-size:${font.toFixed(1)}px" ${domainAttrs}
      data-track="${attr(domain.key)}" data-tip="${attr(domainTip)}">${
  lines.map((line, j) => `<tspan x="${lx.toFixed(1)}" dy="${j ? LINE : 0}">${
    attr(line)}</tspan>`).join('')}</text>`);
  });
  svg.push(...nodes, ...labels);

  // the scale, in points from the reference, in the gap at the top
  for (const [v, text] of [[reference, '0'], [hi, signed(hi - reference, 0)]]) {
    const [tx, ty] = xy(radius(v) + 1, -Math.PI / 2);
    svg.push(`<text class="tick" x="${tx.toFixed(1)}" y="${ty.toFixed(1)}"
      text-anchor="middle">${text}</text>`);
  }

  // the index itself, at the centre, as the figure's core; clicking it maps
  // the index again
  const indexValue = valueOf(subject, columns.index);
  svg.push(`<g class="centre${mapped === columns.index ? ' focus' : ''}"
    data-kind="index" data-column="${attr(columns.index)}"
    data-tip="${attr(`${t('profileAll')} · ${scoreText(indexValue, reference)}`)}">
    <circle cx="${C}" cy="${C}" r="${R_CORE - 2}" fill="#F3F7FF"
      stroke="${core}" stroke-width="3"></circle>
    <text class="centre-value" x="${C}" y="${C + 3}" text-anchor="middle"
      fill="${core}">${indexValue === null ? '–' : signed(indexValue - reference)}</text>
    <text class="centre-label" x="${C}" y="${C + 12}" text-anchor="middle">${
  attr(t('profileIndex'))}</text></g>`);

  const chart = `<svg class="profile-chart" viewBox="0 0 ${S} ${S}" role="img"
      aria-label="${attr(t('profileTitle'))}">${svg.join('')}</svg>`;
  const strip = `<div class="profile-strip" title="${attr(t('profilePenaltyHelp'))}">${
    [subject, ...references].map((row) =>
      stripRow(row, columns, scale, negative)).join('')}</div>`;

  if (options.compact) {
    element.innerHTML = `
      <div class="profile-head">
        <span class="profile-subject">${attr(subject.name)}</span>
      </div>
      ${chart}${strip}`;
  } else {
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
    const base = app.uli ? app.uli.base : structure;
    // what is mapped, beneath the index's name: the item alone, as its
    // domain is plain from the chart
    const shown = componentLabel(structure, resolved.column);
    // the settings, from a cog in the corner; the walkability setting, and
    // what custom weights have changed, beneath the list
    const walk = options.inModal ? ''
      : walkabilityControl(base, state.uli, Boolean(app.walkInfoOpen));
    const info = walk && app.walkInfoOpen
      ? `<div class="uli-info-box">${attenuationInfo(datasets[0].manifest)}</div>` : '';
    const weights = options.inModal ? '' : weightsNote(base, state.uli);
    const note = weights ? `<div class="uli-note">
        <span>${attr(weights)} · <em>${attr(t('uliExploratory'))}</em></span>
        <button class="profile-chip" data-action="reset-weights">${
  attr(t('uliResetWeights'))}</button>
      </div>` : '';
    const cog = options.inModal ? ''
      : `<button class="profile-cog" data-action="settings" title="${
        attr(t('uliSettingsHelp'))}" aria-label="${attr(t('uliSettings'))}">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="${COG}"></path></svg>
      </button>`;
    element.innerHTML = `
      <div class="section-title">${attr(label(structure.label, t('profileTitle')))}</div>
      ${shown ? `<div class="profile-mapped">${attr(shown)}</div>` : ''}
      <div class="profile-legend legend"></div>
      <div class="profile-head">
        <span class="profile-subject">${attr(who)}</span>${clear}${model}
      </div>
      <div class="profile-chart-wrap">${chart}${cog}</div>
      ${self ? `<div class="profile-note profile-self">${attr(t('profileSelf'))}</div>` : ''}
      <div class="profile-note">${attr(t('profileReference'))} · ${
  attr(t('profileHint'))}</div>
      <div class="profile-note" title="${attr(t('profilePenaltyHelp'))}">${
  attr(t('profileMean'))} ${negative ? '+' : '−'} ${attr(t('profilePenalty'))} = ${
  attr(t('profileIndex'))}</div>
      ${strip}
      <div class="section-title">${attr(t('profileByDomain'))}</div>
      <ul class="profile-list">${domainList(
    domains, focus, subject, references, scale, mapped, structure.lenses,
    { colour: classColour }, describe,
  )}</ul>${structure.shared
    ? `<div class="profile-note">${attr(t('profileShare'))}</div>` : ''}${
  walk}${info}${note}`;
  }

  wireTips(element);
  wireDomainHover(element, focus ? focus.key : null);
  element.querySelectorAll('[data-kind]').forEach((node) => {
    node.addEventListener('click', () => {
      const { kind, key, id } = node.dataset;
      const column = node.dataset.column || null;
      if (mode !== 'select') {
        if (options.onItem) options.onItem({ kind, key, id, column });
        return;
      }
      if (kind === 'index') {
        app.focusComponent(column, null);
        return;
      }
      if (kind === 'domain') {
        // a second click on the domain already open closes it, and returns the
        // map to the index
        if (state.focusDomain === key && (!column || resolved.column === column)) {
          app.focusComponent(columns.index, null);
        } else {
          app.focusComponent(column || resolved.column, key);
        }
        return;
      }
      // an inactive indicator has nothing to map: its tooltip says why
      if (column) app.focusComponent(column, key || state.focusDomain);
    });
  });
  const on = (action, fn) => {
    const button = element.querySelector(`[data-action="${action}"]`);
    if (button) button.addEventListener('click', fn);
  };
  on('clear', () => app.clearSelection());
  on('model', () => app.openConceptualModel());
  on('settings', () => app.openUliSettings());
  on('reset-weights', () => app.resetUliWeights());
  on('walk-info', () => app.toggleWalkInfo());
  const select = element.querySelector('.uli-walk-select');
  if (select) {
    select.addEventListener('change', () => {
      app.setUliSettings((s) => { s.attenuation = select.value === '1'; });
    });
  }
}
