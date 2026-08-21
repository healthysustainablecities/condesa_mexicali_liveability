// Colour classes and MapLibre paint expressions.
//
// The classes themselves are *not* decided here.  They come from the exporter,
// which knows each column's range across every scale, its declared units, and
// whatever the region configured for it — and which therefore also knows the
// exact share of population in each class.  That is what lets the legend sit
// directly under the histogram as its axis: a class edge falling inside a
// uniform histogram bin cannot be recovered afterwards, so both are computed
// from the data at once and read here as given.
//
// Two shapes of indicator, two shapes of map:
//
//   classes     a single value per area, cut at the exported edges.  Either end
//               may be open ("< -3", "≥ 3"), which is how a sum of z-scores or
//               an unbounded density gets a legible legend.
//   categories  an ordinal code (GUHVI class 1–5), matched exactly.  A code is
//               not a quantity and must not be cut into intervals.
//
// There used to be a third — an access map coloured by the closest distance
// band at which at least half an area's sample points reached the destination.
// It was replaced by the percentage at one chosen distance, which is the same
// data said plainly: the band rule took a paragraph to explain and left the
// distance selector inert.
//
// Missing values get their own visible class.  Coverage is genuinely partial at
// manzana and AGEB scale, and an area drawn transparent reads as "no access
// here" rather than "not measured here".

// batlow (Crameri), sampled at six stops: perceptually uniform and readable in
// greyscale, so an exported map still works when printed for a workshop.
export const BATLOW = [
  '#011959', '#12557C', '#3E7A5E', '#8C963F', '#DFA050', '#FACCFA',
];

function lerpHex(a, b, t) {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  return `#${pa.map((v, i) => Math.round(v + (pb[i] - v) * t)
    .toString(16).padStart(2, '0')).join('')}`;
}

/**
 * The ramp sampled continuously at `t` in [0, 1].
 *
 * Interpolated rather than nearest-stop because the configured break sets are
 * no longer all five classes wide: GUHVI is cut every ten units into ten, and
 * picking the nearest of six stops would hand two of them the same colour.
 */
export function batlowAt(t) {
  const x = Math.max(0, Math.min(1, t)) * (BATLOW.length - 1);
  const i = Math.min(Math.floor(x), BATLOW.length - 2);
  return lerpHex(BATLOW[i], BATLOW[i + 1], x - i);
}

export const NO_DATA = '#c9c4bd';
export const DIM = '#d9d5d0';
export const LTS_COLORS = { 1: '#1a9850', 2: '#a6d96a', 3: '#fdae61', 4: '#d73027' };

const SENTINEL = -999999;

function ramp(direction, n) {
  // one ramp, reversed where a low value is the good outcome, so the
  // favourable end of the scale is always the same colour
  const stops = Array.from(
    { length: n }, (_, i) => batlowAt(i / Math.max(1, n - 1)),
  );
  return direction === 'lower_is_better' ? stops.slice().reverse() : stops;
}

/**
 * Which class first meets the column's target, or null.
 *
 * The target is always one of the exported edges — a log2 ladder is hung off it
 * precisely so that it is — so this is an exact match rather than a search for
 * the nearest boundary.
 */
function targetClass(classes, target) {
  if (!target || target.criteria === undefined) return null;
  const near = (a, b) => a !== null && Math.abs(a - b) < 1e-9;
  const below = String(target.relationship || '>=').startsWith('<');
  for (let i = 0; i < classes.length; i += 1) {
    if (below && near(classes[i].max, target.criteria)) return i;
    if (!below && near(classes[i].min, target.criteria)) return i;
  }
  return null;
}

/**
 * Build the classification for a resolved selection.
 *
 * `breaks` is the exporter's definition for this column and `target` its
 * threshold, if it has one.  Passing the same pair whatever the panes are
 * showing is what makes one colour mean one thing on both sides.
 */
export function classify(resolved, breaks, target) {
  if (!breaks) return null;

  if (breaks.kind === 'categories') {
    const colors = ramp(resolved.direction, breaks.values.length);
    const classes = breaks.values.map((value, i) => ({
      color: colors[i], index: i, value, min: null, max: null,
    }));
    return {
      kind: 'categories', classes, column: resolved.column,
      target: target || null, targetIndex: null,
    };
  }

  // one entry per class: an open end contributes a bound of null, which is what
  // the legend reads as "< x" / "≥ x" and what the paint expression omits
  const edges = breaks.edges;
  const bounds = [];
  if (breaks.open_low) bounds.push([null, edges[0]]);
  for (let i = 0; i < edges.length - 1; i += 1) {
    bounds.push([edges[i], edges[i + 1]]);
  }
  if (breaks.open_high) bounds.push([edges[edges.length - 1], null]);
  const colors = ramp(resolved.direction, bounds.length);
  const classes = bounds.map(([min, max], i) => ({
    color: colors[i], min, max, index: i,
  }));
  return {
    kind: 'classes',
    classes,
    edges,
    scale: breaks.scale || null,
    column: resolved.column,
    target: target || null,
    targetIndex: targetClass(classes, target),
  };
}

/**
 * The value tests that put a feature in one class.
 *
 * The outermost classes deliberately drop their outer bound, so that a value
 * beyond the exported edges falls into the nearest class rather than into "no
 * data".  That matches the exporter's own clipping, which is what makes the
 * histogram's bars and the map's colours count the same areas.
 */
function classTests(classification, index, value) {
  const cls = classification.classes[index];
  const last = index === classification.classes.length - 1;
  const tests = [];
  if (cls.min !== null && cls.min !== undefined && index > 0) {
    tests.push(['>=', value, cls.min]);
  }
  if (cls.max !== null && cls.max !== undefined && !last) {
    tests.push(['<', value, cls.max]);
  }
  return tests;
}

function combine(tests) {
  if (!tests.length) return true;
  return tests.length === 1 ? tests[0] : ['all', ...tests];
}

/** Fill colour for the whole layer, before any legend isolation. */
export function fillExpression(classification) {
  const value = ['coalesce', ['get', classification.column], SENTINEL];
  const expression = ['case', ['==', value, SENTINEL], NO_DATA];
  if (classification.kind === 'categories') {
    classification.classes.forEach((cls) => {
      expression.push(['==', value, cls.value], cls.color);
    });
    expression.push(NO_DATA);
    return expression;
  }
  classification.classes.forEach((cls, i) => {
    expression.push(combine(classTests(classification, i, value)), cls.color);
  });
  expression.push(NO_DATA);
  return expression;
}

/** A predicate matching only the areas in one legend class. */
export function classFilter(classification, index) {
  const cls = classification.classes[index];
  if (!cls) return ['boolean', false];
  const value = ['coalesce', ['get', classification.column], SENTINEL];
  if (classification.kind === 'categories') {
    return ['==', value, cls.value];
  }
  return ['all',
    ['!=', value, SENTINEL],
    ...classTests(classification, index, value)];
}

/**
 * Paint properties for the choropleth, honouring a legend-class isolation.
 *
 * Isolating recolours everything else flat grey at low opacity rather than
 * hiding it, so the isolated class is read against the shape of the city
 * instead of floating in white space.
 */
export function choroplethPaint(classification, isolated) {
  if (isolated && isolated.kind === 'class') {
    const match = classFilter(classification, isolated.value);
    const cls = classification.classes[isolated.value];
    return {
      'fill-color': ['case', match, cls ? cls.color : DIM, DIM],
      'fill-opacity': ['case', match, 0.85, 0.15],
    };
  }
  return {
    'fill-color': fillExpression(classification),
    'fill-opacity': isolated ? 0.15 : 0.7,
  };
}

export function ltsPaint(isolated) {
  if (isolated && isolated.kind === 'lts') {
    const value = isolated.value;
    return {
      'line-color': ['match', ['get', 'lvl_traf_stress'], value,
        LTS_COLORS[value], DIM],
      'line-opacity': ['match', ['get', 'lvl_traf_stress'], value, 0.95, 0.15],
    };
  }
  return {
    'line-color': ['match', ['get', 'lvl_traf_stress'],
      1, LTS_COLORS[1], 2, LTS_COLORS[2], 3, LTS_COLORS[3], 4, LTS_COLORS[4],
      '#9a948c'],
    'line-opacity': isolated ? 0.2 : 0.85,
  };
}
