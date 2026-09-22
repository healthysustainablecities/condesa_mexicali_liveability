// Application state, and its serialisation to the URL hash.
//
// The validation site had no state object: control values were read straight
// off the DOM in some thirty places, which works for one map and cannot carry
// two.  Here state is explicit and one-way — controls write to it, everything
// else reads from it — and the hash is its serialisation, so any view a
// workshop presenter reaches can be linked to and reproduced exactly.

import { DEFAULT_LANG, setLang } from './strings.js';

export const OVERLAYS = [
  'choropleth', 'destinations', 'network', 'population', 'boundaries',
];

export const state = {
  lang: DEFAULT_LANG,
  // opens on one region: two panes at once is a comparison the reader has not
  // asked for yet, and the tour is what introduces it
  compare: false,
  linkViews: false,
  // one basemap for both panes: it is a property of how the reader wants to
  // see the ground, not of either region
  basemap: 'streets',
  // 0 full, 1 indicator controls hidden, 2 header only.  The panel floats over
  // the map, so collapsing it is how the map gets the screen -- which is what a
  // narrow window needs, and what a media query was doing badly.
  panel: 0,
  isolated: null, // {kind: 'band'|'class'|'lts', value: index}
  // The area a composite index profile describes in place of its region, from
  // a clicked map feature: {pane, scale, id, props}. Not written to the hash:
  // its values come from the feature itself, which a reload has not drawn yet.
  selected: null,
  // the domain of a composite index whose components the profile lists
  focusDomain: null,
  // one indicator, shared by both panes: the comparison is only meaningful
  // when both sides show the same quantity on the same colour scale
  shared: {
    family: null,
    measure: 'access',
    network: 'walk',
    distance: null,
    variable: null,
    group: null,
  },
  // destinations are on by default: the first question anyone asks of an
  // access map is "access to what?", and the points answer it
  panes: [
    { dataset: null, region: null, scale: null,
      overlays: { choropleth: true, destinations: true, network: false,
        population: false, boundaries: true },
      view: null },
    { dataset: null, region: null, scale: null,
      overlays: { choropleth: true, destinations: true, network: false,
        population: false, boundaries: true },
      view: null },
  ],
};

const listeners = [];
let suspended = false;

export function subscribe(fn) {
  listeners.push(fn);
}

/**
 * Mutate state, then republish it.  `reason` lets listeners skip work they do
 * not need to redo — rebuilding a MapLibre style for a language change would
 * throw away the user's map position for nothing.
 */
export function update(mutator, reason = 'change') {
  mutator(state);
  if (suspended) return;
  writeHash();
  for (const fn of listeners) fn(state, reason);
}

/**
 * Record a change without repainting.
 *
 * Camera position and which pane has focus are state — they belong in the hash
 * so a view can be linked to — but nothing on screen depends on them, and
 * repainting on them is worse than pointless: `render()` resizes the maps,
 * resizing fires `moveend`, and handling `moveend` with a normal update would
 * feed straight back into `render()` and never settle.
 */
export function updateSilent(mutator) {
  mutator(state);
  if (!suspended) writeHash();
}

/** Apply several changes as one update (one repaint, one hash write). */
export function batch(mutator, reason = 'change') {
  suspended = true;
  try {
    mutator(state);
  } finally {
    suspended = false;
  }
  writeHash();
  for (const fn of listeners) fn(state, reason);
}

function encodePane(pane) {
  // encoded by position, not by initial letter: 'choropleth' and 'context'
  // would collide, and a silent collision here would turn the wrong layer on
  const flags = OVERLAYS.map((o) => (pane.overlays[o] ? '1' : '0')).join('');
  const view = pane.view
    ? `${pane.view.zoom.toFixed(2)}/${pane.view.lat.toFixed(5)}/${pane.view.lng.toFixed(5)}`
    : '';
  return [pane.dataset, pane.region, pane.scale, flags, view]
    .map((v) => v || '')
    .join('~');
}

function decodePane(value, pane) {
  const [dataset, region, scale, flags, view] = value.split('~');
  if (dataset) pane.dataset = dataset;
  if (region) pane.region = region;
  if (scale) pane.scale = scale;
  if (flags) {
    OVERLAYS.forEach((o, i) => { pane.overlays[o] = flags[i] === '1'; });
  }
  if (view) {
    const [zoom, lat, lng] = view.split('/').map(Number);
    if ([zoom, lat, lng].every(Number.isFinite)) pane.view = { zoom, lat, lng };
  }
}

export function writeHash() {
  const s = state.shared;
  const params = new URLSearchParams();
  params.set('l', state.lang);
  params.set('c', state.compare ? '1' : '0');
  params.set('b', state.basemap);
  if (state.panel) params.set('pn', String(state.panel));
  if (state.linkViews) params.set('lv', '1');
  if (state.focusDomain) params.set('fd', state.focusDomain);
  for (const [key, value] of Object.entries({
    f: s.family, m: s.measure, n: s.network,
    d: s.distance, v: s.variable, g: s.group,
  })) {
    if (value) params.set(key, value);
  }
  params.set('p0', encodePane(state.panes[0]));
  if (state.compare) params.set('p1', encodePane(state.panes[1]));
  const hash = `#${params.toString()}`;
  if (hash !== window.location.hash) {
    history.replaceState(null, '', hash);
  }
}

/** Read the hash into state.  Called once at boot, before anything renders. */
export function readHash() {
  const raw = window.location.hash.replace(/^#/, '');
  if (!raw) return;
  const params = new URLSearchParams(raw);
  if (params.has('l')) state.lang = setLang(params.get('l'));
  if (params.has('c')) state.compare = params.get('c') === '1';
  if (params.has('b')) state.basemap = params.get('b');
  if (params.has('pn')) state.panel = Number(params.get('pn')) || 0;
  state.linkViews = params.get('lv') === '1';
  if (params.has('fd')) state.focusDomain = params.get('fd');
  const s = state.shared;
  for (const [key, field] of Object.entries({
    f: 'family', m: 'measure', n: 'network',
    d: 'distance', v: 'variable', g: 'group',
  })) {
    if (params.has(key)) s[field] = params.get(key);
  }
  if (params.has('p0')) decodePane(params.get('p0'), state.panes[0]);
  if (params.has('p1')) decodePane(params.get('p1'), state.panes[1]);
}

/** The panes currently on screen. */
export function activePanes() {
  return state.compare ? state.panes : [state.panes[0]];
}
