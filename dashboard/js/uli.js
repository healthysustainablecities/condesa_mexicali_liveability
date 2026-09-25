// The composite index's settings: which variant of it is shown, and any
// importance weights a reader chooses to impose.
//
// The index is scored by the exporter's analysis at every sample point, once for
// each variant -- by default with walkability attenuated by daytime thermal
// comfort, and otherwise with walkability as it is and thermal comfort scored as
// an ambient environment indicator instead -- and those scores are exact.
// Choosing a variant only changes which exported columns are read, so nothing is
// computed here.  An indicator a variant activates is listed by the index as
// inactive (`active: false`), and is shown, but not counted, where it is not.
//
// Weights are different.  The index rewards a balanced profile by design; a
// reader may nonetheless want to say "parks matter more to me than schools".
// That cannot be scored at sample points in the browser, so the index is
// re-aggregated from each area's average indicator scores instead, with the same
// weighted Mazziotta-Pareto formula (Mazziotta & Pareto 2022) the analysis uses:
//
//   M = sum(w r);  S = sqrt(sum(w (r - M)^2));  score = M - S^2 / M
//
// That is the index of an area's averages, not the average of its points'
// indices, so even at equal weights it differs a little from the published
// scores.  It is always labelled exploratory, and the published scores return
// the moment the weights are reset.
//
// An indicator may count towards several domains, with a share of its weight
// in each (`share`, a third in each of three); a reader's weight for it scales
// every share alike, so it is set once, not once per domain.
//
// Nothing here constructs a column name the exporter did not emit, except the
// computed ones, which begin with CUSTOM and so can never collide with one.

import { SENTINEL } from './choropleth.js';
import { label, number, t } from './strings.js';

const CUSTOM = '~custom';
const WEIGHT_STEP = 0.5;
export const MAX_WEIGHT = 3;

/**
 * Settings as nothing has been changed: the index as published, with
 * walkability attenuated by thermal comfort where the index offers that.
 */
export function defaultSettings() {
  return { attenuation: true, domains: {}, indicators: {} };
}

/** True where an indicator is scored under a variant. */
export function isActive(indicator, variant) {
  if (!indicator) return false;
  if (indicator.active !== false) return true;
  return Boolean(variant && (variant.activates || []).includes(indicator.id));
}

/**
 * The variant a structure is scored as under these settings: the one whose
 * walkability is (or is not) attenuated as they ask, else the index itself.
 */
export function variantFor(structure, settings) {
  const variants = (structure && structure.variants) || [];
  if (!variants.length) return null;
  const wanted = (settings || {}).attenuation !== false;
  return variants.find((v) => (v.attenuation !== false) === wanted) || variants[0];
}

/** The walkability options a structure's variants offer, base first. */
export function walkabilityOptions(structure) {
  return ((structure && structure.variants) || []).map((v) => ({
    attenuation: v.attenuation !== false,
    label: v.label,
    name: v.name,
    base: v.key === null || v.key === undefined,
  }));
}

function weightOf(map, key, fallback) {
  const w = Number((map || {})[key]);
  return Number.isFinite(w) && w >= 0 ? w : fallback;
}

/**
 * The index's indicators, each once, in the order they are presented: the
 * structure's own list where the export gives one, else gathered from its
 * domains (an index whose indicators each belong to one domain).
 */
export function indicatorsOf(structure) {
  if (!structure) return [];
  if (Array.isArray(structure.indicators)) return structure.indicators;
  const seen = new Map();
  for (const domain of structure.domains || []) {
    for (const indicator of domain.indicators || []) {
      if (!seen.has(indicator.id)) {
        seen.set(indicator.id, {
          ...indicator,
          domains: domain.name ? { [domain.name]: 1 } : {},
        });
      }
    }
  }
  return [...seen.values()];
}

// the score the reference receives in the index's own calculation
const REFERENCE_SCORE = 100;

/**
 * The value scores are reported about: 100, or 0 for an index reporting them
 * as differences from the reference (`centre: 0`).
 */
export function referenceOf(structure) {
  const value = Number((structure || {}).reference_value);
  return Number.isFinite(value) ? value : REFERENCE_SCORE;
}

/** The share of an indicator's weight it carries in a domain (1 if alone). */
export function shareOf(indicator) {
  const share = Number((indicator || {}).share);
  return Number.isFinite(share) && share > 0 ? share : 1;
}

/** A share as a fraction where it is a simple one: ½, ⅓, ⅔, ¼, else 40%. */
export function shareText(share) {
  const fractions = [[1 / 2, '½'], [1 / 3, '⅓'], [2 / 3, '⅔'], [1 / 4, '¼'],
    [3 / 4, '¾'], [1 / 5, '⅕']];
  const found = fractions.find(([v]) => Math.abs(v - share) < 1e-6);
  return found ? found[1] : `${number(share * 100, 0)}%`;
}

/** True where the reader has imposed weights of their own. */
export function hasCustomWeights(structure, settings) {
  if (!structure) return false;
  const domains = structure.domains.some((d) =>
    weightOf(settings.domains, d.name, Number(d.weight) || 1)
      !== (Number(d.weight) || 1));
  return domains || indicatorsOf(structure).some((i) =>
    weightOf(settings.indicators, i.id, Number(i.weight) || 1)
      !== (Number(i.weight) || 1));
}

/** True where the variant shown is not the index as published. */
export function isVariant(structure, settings) {
  const variant = variantFor(structure, settings);
  const base = ((structure && structure.variants) || [])[0];
  return Boolean(variant && base && variant.name !== base.name);
}

/** True where anything differs from the index as published. */
export function isModified(structure, settings) {
  return isVariant(structure, settings) || hasCustomWeights(structure, settings);
}

/** Weighted Mazziotta-Pareto aggregation of scores, as in _composite_index. */
export function ampi(scores, weights, negative = false) {
  let total = 0;
  let mean = 0;
  for (let i = 0; i < scores.length; i += 1) {
    if (!(weights[i] > 0)) continue;
    if (scores[i] === null || !Number.isFinite(scores[i])) return null;
    total += weights[i];
    mean += weights[i] * scores[i];
  }
  if (!(total > 0)) return null;
  mean /= total;
  let variance = 0;
  for (let i = 0; i < scores.length; i += 1) {
    if (weights[i] > 0) variance += weights[i] * (scores[i] - mean) ** 2;
  }
  variance /= total;
  const penalty = mean ? variance / mean : 0;
  return { index: negative ? mean + penalty : mean - penalty, mean, penalty };
}

/** The same aggregation as a MapLibre expression over given expressions. */
function ampiExpression(parts, negative, prefix) {
  const used = parts.filter((p) => p.weight > 0);
  const total = used.reduce((a, p) => a + p.weight, 0);
  if (!used.length || !(total > 0)) return null;
  const bindings = [];
  used.forEach((p, i) => bindings.push(`${prefix}${i}`, p.expression));
  const v = (i) => ['var', `${prefix}${i}`];
  const mean = ['/', ['+', 0, ...used.map((p, i) => ['*', p.weight, v(i)])], total];
  const variance = ['/', ['+', 0, ...used.map((p, i) =>
    ['*', p.weight, ['^', ['-', v(i), ['var', `${prefix}m`]], 2]])], total];
  const penalty = ['/', variance, ['var', `${prefix}m`]];
  return ['let', ...bindings,
    ['let', `${prefix}m`, mean,
      [negative ? '+' : '-', ['var', `${prefix}m`], penalty]]];
}

/**
 * A feature property as a number.  Only read behind a guard that every input
 * is a number, since a MapLibre expression cannot carry a missing value
 * through arithmetic.
 */
function numberOf(column) {
  return ['to-number', ['get', column], 0];
}

/**
 * The index as these settings present it.
 *
 * Returns `{structure, variant, custom, remap, inverse, values, expression}`:
 * the structure with its columns swapped for the variant's (and, with custom
 * weights, for computed ones), maps between the published columns and those
 * shown, a function adding computed values to an area's values, and the paint
 * expression for a computed column.
 */
export function activeIndex(structure, settings) {
  const identity = {
    structure, base: structure, variant: null, custom: false,
    remap: (c) => c, inverse: (c) => c,
    values: (v) => v, expression: () => null,
  };
  if (!structure) return identity;
  const variant = variantFor(structure, settings);
  const swap = new Map();
  if (variant) {
    const cols = structure.columns;
    for (const key of ['index', 'mean', 'penalty']) {
      if (variant.columns[key]) swap.set(cols[key], variant.columns[key]);
    }
    for (const domain of structure.domains) {
      const column = (variant.domains || {})[domain.name];
      if (domain.column && column) swap.set(domain.column, column);
      for (const indicator of domain.indicators) {
        const own = (variant.indicators || {})[indicator.id];
        if (indicator.column && own && indicator.column !== own) {
          swap.set(indicator.column, own);
        }
      }
    }
  }
  const custom = hasCustomWeights(structure, settings);
  const negative = structure.phenomenon === 'negative';
  if (custom) {
    // the computed scores replace the index's and each domain's, whichever
    // variant they were read from
    swap.set(structure.columns.index, `${CUSTOM}_index`);
    swap.set(structure.columns.mean, `${CUSTOM}_mean`);
    swap.set(structure.columns.penalty, `${CUSTOM}_penalty`);
    for (const domain of structure.domains) {
      if (domain.column) swap.set(domain.column, `${CUSTOM}__${domain.name}`);
    }
  }
  const to = (column) => (swap.has(column) ? swap.get(column) : column);
  const back = new Map([...swap.entries()].map(([k, v]) => [v, k]));
  // the indicator a variant swaps is the variant's: its label, and not the
  // base index's goalposts, which the export records for that alone
  const swapped = (indicator) => Boolean(variant && variant.key !== null
    && variant.key !== undefined && indicator.id === structure.variant_replaces);
  const view = (indicator) => ({
    ...indicator,
    ...(swapped(indicator) ? { label: variant.label, normalisation: null } : {}),
    column: indicator.column ? to(indicator.column) : indicator.column,
    // the variant's own raw value (walkability as it is, or attenuated)
    area_column: ((variant || {}).area_columns || {})[indicator.id]
      || indicator.area_column,
    active: isActive(indicator, variant),
    weight: weightOf(settings.indicators, indicator.id,
      Number(indicator.weight) || 1),
    // what it counts for in the variant shown, which may score other
    // indicators than the index as published
    effective_weight: variant && variant.effective_weights
      ? (variant.effective_weights[indicator.id] ?? null)
      : indicator.effective_weight,
  });
  const shown = {
    ...structure,
    custom,
    columns: {
      ...structure.columns,
      index: to(structure.columns.index),
      mean: to(structure.columns.mean),
      penalty: to(structure.columns.penalty),
    },
    indicators: indicatorsOf(structure).map(view),
    domains: structure.domains.map((domain) => {
      const indicators = domain.indicators.map(view);
      // a domain whose every indicator is set aside is set aside with them,
      // rather than leaving the index with nothing to score it by
      const any = indicators.some((i) => i.column && i.active && !i.dropped
        && i.weight > 0);
      return {
        ...domain,
        column: domain.column ? to(domain.column) : domain.column,
        weight: any
          ? weightOf(settings.domains, domain.name, Number(domain.weight) || 1)
          : 0,
        indicators,
      };
    }),
  };
  if (variant) shown.label = structure.label;

  // the indicators a score is made of: exported, varying, and active
  const counted = (i) => i.column && i.active && !i.dropped;
  // scores reported relative to the reference are aggregated on the scale on
  // which it is 100, as the analysis does: the penalty divides by the mean
  const offset = REFERENCE_SCORE - referenceOf(structure);
  const values = (given) => {
    if (!custom || !given) return given;
    const out = { ...given };
    const scores = [];
    const weights = [];
    for (const domain of shown.domains) {
      const scored = domain.indicators.filter(counted);
      const result = ampi(
        scored.map((i) => {
          const v = Number(given[i.column]);
          return given[i.column] === null || given[i.column] === undefined
            || !Number.isFinite(v) ? null : v + offset;
        }),
        // a member shared with other domains counts its share here
        scored.map((i) => i.weight * shareOf(i)),
        negative,
      );
      const score = result ? result.index : null;
      if (domain.column) out[domain.column] = score === null ? null : score - offset;
      scores.push(score);
      weights.push(domain.weight);
    }
    const index = ampi(scores, weights, negative);
    out[shown.columns.index] = index ? index.index - offset : null;
    out[shown.columns.mean] = index ? index.mean - offset : null;
    out[shown.columns.penalty] = index ? index.penalty : null;
    return out;
  };

  const domainExpression = (domain, i) => ampiExpression(
    domain.indicators.filter(counted).map((x) => ({
      weight: x.weight * shareOf(x),
      expression: ['+', offset, numberOf(x.column)],
    })),
    negative,
    `d${i}_`,
  );
  const expression = (column) => {
    if (!custom || !String(column).startsWith(CUSTOM)) return null;
    const d = shown.domains.findIndex((x) => x.column === column);
    // a missing input makes the whole score missing -- drawn as no data -- as
    // in the analysis, where every indicator of a domain and every domain are
    // required
    const guard = (inputs, body) => ['case',
      ['all', ...inputs.map((c) =>
        ['==', ['typeof', ['get', c]], 'number'])], body, SENTINEL];
    if (d >= 0) {
      const domain = shown.domains[d];
      return guard(
        domain.indicators.filter((x) => counted(x) && x.weight > 0)
          .map((x) => x.column),
        ['-', domainExpression(domain, d), offset],
      );
    }
    if (column !== shown.columns.index) return null;
    const inputs = shown.domains.filter((x) => x.weight > 0).flatMap((x) =>
      x.indicators.filter((y) => counted(y) && y.weight > 0)
        .map((y) => y.column));
    return guard(inputs, ['-', ampiExpression(
      shown.domains.map((domain, i) => ({
        weight: domain.weight, expression: domainExpression(domain, i),
      })).filter((p) => p.expression),
      negative,
      'x_',
    ), offset]);
  };

  return {
    structure: shown,
    // the index as published, which the settings are read against
    base: structure,
    variant,
    custom,
    remap: to,
    inverse: (column) => (back.has(column) ? back.get(column) : column),
    values,
    expression,
  };
}

/** The weight a slider step rounds to. */
export function roundWeight(value) {
  const w = Math.round(Number(value) / WEIGHT_STEP) * WEIGHT_STEP;
  return Math.max(0, Math.min(MAX_WEIGHT, w));
}

/**
 * A sentence stating which custom weights the reader imposed, or '' where
 * there are none.  The walkability setting is shown by its own control.
 */
export function weightsNote(structure, settings) {
  if (!structure || !hasCustomWeights(structure, settings)) return '';
  const named = structure.domains
    .map((d) => [label(d.label, d.name),
      weightOf(settings.domains, d.name, Number(d.weight) || 1)])
    .filter(([, w]) => w !== 1)
    .map(([name, w]) => `${name} ×${number(w, 1)}`);
  return `${t('uliCustomWeights')}${named.length ? ` (${named.join(', ')})` : ''}`;
}

/**
 * A sentence stating how the index shown differs from the published one, or
 * '' where it does not (used by the report).
 */
export function modificationNote(structure, settings) {
  if (!structure || !isModified(structure, settings)) return '';
  const parts = [];
  const variant = variantFor(structure, settings);
  if (isVariant(structure, settings)) {
    parts.push(label(variant.label, variant.name));
  }
  const weights = weightsNote(structure, settings);
  if (weights) parts.push(weights);
  return parts.join(' · ');
}

/** Settings as the URL hash stores them. */
export function encodeSettings(settings) {
  const out = {};
  if (settings.attenuation === false) out.a = '0';
  const pairs = (map) => Object.entries(map || {})
    .filter(([, w]) => w !== undefined && w !== null && Number(w) !== 1)
    .map(([k, w]) => `${k}:${w}`).join(',');
  if (pairs(settings.domains)) out.uw = pairs(settings.domains);
  if (pairs(settings.indicators)) out.ui = pairs(settings.indicators);
  return out;
}

/** Settings read back from the URL hash's parameters. */
export function decodeSettings(params) {
  const settings = defaultSettings();
  settings.attenuation = params.get('a') !== '0';
  const read = (value) => Object.fromEntries(String(value || '').split(',')
    .map((pair) => pair.split(':'))
    .filter(([k, w]) => k && Number.isFinite(Number(w)))
    .map(([k, w]) => [k, roundWeight(w)]));
  if (params.has('uw')) settings.domains = read(params.get('uw'));
  if (params.has('ui')) settings.indicators = read(params.get('ui'));
  return settings;
}
