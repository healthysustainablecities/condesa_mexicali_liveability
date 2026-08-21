// The wording, and where it can be edited.
//
// Every sentence the viewer composes about an indicator used to be a literal in
// showing.js or info.js, so revising a phrase for a workshop audience meant
// editing JavaScript. Now there are three layers, each overriding the one
// below it:
//
//   1. data/<slug>/text.json   hand-edited in the site repo. Edit, refresh.
//   2. indicators.json `text`  the exporter's defaults (DEFAULT_TEXT), so a
//                              region carries sensible wording without any
//                              text.json at all.
//   3. nothing                 a missing key renders as an empty string, and
//                              build/smoke.mjs fails rather than shipping it.
//
// Deliberately no fourth layer of literals in here: two copies of a sentence
// drift, and the one on screen is then whichever the reader did not edit.

import { applyOverrides, getLang } from './strings.js';

let DEFAULTS = {};
let OVERRIDES = {};

/**
 * Load the site's overrides, if it has any.
 *
 * A missing file is the normal case for a region that has not needed to revise
 * anything, so a 404 is not an error. `no-cache` because this file exists to be
 * edited and reloaded — a cached copy would make an edit look like it did
 * nothing.
 */
export async function loadText(slug, defaults) {
  DEFAULTS = defaults || {};
  OVERRIDES = {};
  try {
    const response = await fetch(`data/${slug}/text.json`, { cache: 'no-cache' });
    if (response.ok) OVERRIDES = await response.json();
  } catch (error) {
    OVERRIDES = {};
  }
  // UI chrome is overridden in place, since strings.js is what reads it
  if (OVERRIDES.strings) applyOverrides(OVERRIDES.strings);
  return OVERRIDES;
}

/** The {es, en} entry for a key, override first. */
function entry(group, key) {
  const over = OVERRIDES[group];
  const base = DEFAULTS[group];
  if (key === undefined) return over || base || null;
  return (over || {})[key] || (base || {})[key] || null;
}

/** The text for a key in the active language. */
export function template(group, key) {
  const found = entry(group, key);
  if (!found) return '';
  if (typeof found === 'string') return found;
  return found[getLang()] || found.en || found.es || '';
}

/**
 * Substitute {placeholders}.
 *
 * An unknown placeholder renders empty rather than leaving `{foo}` on screen:
 * a typo in an edited sentence should read as a gap, not as markup.
 */
export function fill(text, parts) {
  return String(text || '').replace(
    /\{(\w+)\}/g,
    (_, name) => (parts[name] === undefined || parts[name] === null
      ? '' : String(parts[name])),
  );
}

/** A sentence, looked up and filled in one step. */
export function say(group, key, parts) {
  return fill(template(group, key), parts || {});
}

/** The measure's name, as the dropdown and the legend title show it. */
export function measureLabel(resolved) {
  if (!resolved) return null;
  return (OVERRIDES.measures || {})[resolved.measureKey]
    || resolved.measure.label;
}

/** The measure's name by key, for the dropdown (which has no resolution yet). */
export function measureLabelFor(key, fallback) {
  return (OVERRIDES.measures || {})[key] || fallback;
}

/**
 * The network as a *sentence* names it.
 *
 * "using the pedestrian network", not "using the Walking network" — a dropdown
 * label and a phrase inside a sentence are different words for the same thing,
 * and writing one where the other belongs is what made the old sentences resort
 * to "red: caminando".
 */
export function networkPhrase(key, network) {
  const over = (OVERRIDES.networks || {})[key];
  const found = over || (network || {}).phrase || (network || {}).label;
  if (!found) return key || '';
  if (typeof found === 'string') return found;
  return found[getLang()] || found.en || found.es || key || '';
}

/** Every placeholder a sentence may use, for one resolved selection. */
export function partsFor(resolved, vocab) {
  if (!resolved) return {};
  const key = resolved.selection.network;
  const network = (vocab.networks || {})[key] || {};
  const distance = resolved.distance || resolved.selection.distance;
  return {
    network: networkPhrase(key, network),
    networkLabel: template('networkLabels', key)
      || labelOf(network.label, key),
    distance: distance ? `${distance} m` : '',
    bands: resolved.bands.length
      ? resolved.bands.map((b) => `${b} m`).join(' / ') : '',
    indicator: labelOf(resolved.family.label, resolved.family.id),
    description: resolved.description || '',
  };
}

function labelOf(value, fallback) {
  if (!value) return fallback;
  if (typeof value === 'string') return value;
  return value[getLang()] || value.en || value.es || fallback;
}
