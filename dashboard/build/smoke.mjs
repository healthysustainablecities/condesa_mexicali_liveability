// Headless checks of the parts that do not need a browser: the vocabulary's
// resolution of a selection to columns, the classification those columns get,
// and the agreement between the three exported JSON files.
//
//   node build/smoke.mjs [slug]
//
// This is what catches a naming drift between the exporter and the viewer --
// the failure mode the cycling validation site had, where the viewer rebuilt
// column names from its own copy of the conventions.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const slug = process.argv[2] || 'mexicali';
const read = (file) =>
  JSON.parse(fs.readFileSync(path.join(ROOT, 'data', slug, file), 'utf8'));

// a bare Windows path is not a valid ESM specifier; file:// URLs are
const module_ = (name) =>
  import(pathToFileURL(path.join(ROOT, 'js', name)).href);

const { Vocabulary } = await module_('vocab.js');
const {
  classify, fillExpression, classFilter,
} = await module_('choropleth.js');
const { classLabel } = await module_('legend.js');

const manifest = read('manifest.json');
const indicators = read('indicators.json');
const stats = read('stats.json');
const vocab = new Vocabulary(indicators);

// a composite index's own dashboard carries the index alone: no themes, no
// interventions, no destination layers
const composite = manifest.type === 'composite';
// a composite or combined dataset carries the index's own outputs
const indexed = ['composite', 'combined'].includes(manifest.type);

let failures = 0;
const check = (ok, message) => {
  if (!ok) {
    failures += 1;
    console.log(`  FAIL  ${message}`);
  }
};
const section = (name) => console.log(`\n${name}`);

// ---------------------------------------------------------------------------
section('manifest / stats agreement');
for (const [key, scale] of Object.entries(manifest.scales)) {
  const entry = stats[key];
  check(entry, `stats has an entry for scale ${key}`);
  if (!entry) continue;
  check(
    entry.areas === scale.features,
    `${key}: stats areas ${entry.areas} === layer features ${scale.features}`,
  );
  const missing = scale.columns.filter((c) => !entry.columns[c]);
  // a column may legitimately be all-null at a scale and so absent from stats
  console.log(
    `  ${key.padEnd(26)} ${String(scale.features).padStart(6)} areas, `
    + `${scale.columns.length} columns, ${missing.length} without stats`,
  );
}

// ---------------------------------------------------------------------------
section('every vocabulary column exists at some scale');
const everywhere = new Set(
  Object.values(manifest.scales).flatMap((s) => s.columns),
);
const orphans = [];
for (const family of indicators.families) {
  for (const column of family.columns) {
    if (!everywhere.has(column)) orphans.push(`${family.id}: ${column}`);
  }
}
check(orphans.length === 0, `orphan columns: ${orphans.slice(0, 5).join(', ')}`);
console.log(`  ${everywhere.size} distinct columns exported, ${orphans.length} orphans`);

// ---------------------------------------------------------------------------
section('selection resolution and classification');
const scaleColumns = (key) => new Set(manifest.scales[key].columns);
const cases = [
  { family: 'blue_space', measure: 'access', network: 'walk' },
  { family: 'denue_pharmacy', measure: 'distance', network: 'walk' },
  { family: 'denue_petrol_station', measure: 'beyond', network: 'walk' },
  { family: 'fresh_food_market', measure: 'access', network: 'low_stress' },
  { family: 'urban_heat', measure: 'value', variable: 'urban_heat_guhvi',
    network: 'walk' },
  { family: 'walkability', measure: 'value', variable: 'local_walkability',
    network: 'walk' },
  { family: 'diversity_fresh_food', measure: 'diversity', network: 'walk',
    distance: '1000' },
];
const available = scaleColumns('manzanas');
for (const raw of cases) {
  const selection = vocab.coerce(raw, available);
  const resolved = vocab.resolve(selection);
  check(resolved, `${raw.family}/${raw.measure} resolves`);
  if (!resolved) continue;
  const present = resolved.columns.every((c) => available.has(c));
  check(present, `${raw.family}/${raw.measure} columns exist at manzanas`);
  const classification = classify(
    resolved, vocab.breaksFor(resolved), vocab.targetFor(resolved),
  );
  const expression = fillExpression(classification);
  check(Array.isArray(expression), `${raw.family}: paint expression built`);
  check(
    classification.classes.length >= 2,
    `${raw.family}: at least two classes`,
  );
  const filter = classFilter(classification, 0);
  check(Array.isArray(filter), `${raw.family}: class filter built`);
  const range = classification.classes
    .map((_, i) => classLabel(classification, i)).join(' | ');
  console.log(
    `  ${resolved.title.slice(0, 62).padEnd(64)} ${classification.kind}  ${range}`,
  );
}

// ---------------------------------------------------------------------------
section('banded distributions are keyed as the viewer expects');
let bandsChecked = 0;
for (const family of indicators.families) {
  for (const [measure, spec] of Object.entries(family.measures)) {
    if (spec.kind !== 'banded') continue;
    for (const network of Object.keys(spec.networks || {})) {
      const key = `${family.id}|${measure}|${network}`;
      check(stats.manzanas.bands[key], `stats.manzanas.bands has ${key}`);
      bandsChecked += 1;
    }
  }
}
console.log(`  ${bandsChecked} banded family/network combinations, all keyed`);

// ---------------------------------------------------------------------------
section('coerce moves off a combination that is not available');
// every scale here happens to carry every column, so the reduced set is
// synthetic: it is the behaviour that matters, not that this data triggers it
if (!vocab.family('blue_space')) {
  console.log('  no blue_space family in this dataset');
} else {
  const family = vocab.family('blue_space');
  const blocked = new Set(
    [...everywhere].filter((c) => !family.columns.includes(c)),
  );
  const moved = vocab.coerce(
    { family: 'blue_space', measure: 'access', network: 'walk' }, blocked,
  );
  const columns = vocab.columnsFor(moved);
  check(columns.length > 0, 'coerce found some usable combination');
  check(
    columns.every((c) => blocked.has(c)),
    'coerce only chose columns that are available',
  );
  check(moved.family !== 'blue_space', 'coerce moved off the blocked family');
  console.log(`  blue_space blocked -> ${moved.family}/${moved.measure}/${moved.network}`);

  // and the opposite: an available combination is left exactly as it is
  const kept = vocab.coerce(
    { family: 'blue_space', measure: 'access', network: 'walk' },
    new Set(family.columns),
  );
  check(kept.family === 'blue_space' && kept.measure === 'access',
    'coerce leaves an available combination untouched');
  console.log(`  blue_space available -> ${kept.family}/${kept.measure}/${kept.network}`);
}

// ---------------------------------------------------------------------------
section('classes cover the data, and the chart lines up with the legend');
{
  // The check that would have caught GUHVI: it was declared "index 0-1" but
  // holds 3 to 56, so 0/0.2/../1 breaks put every area in the top class and
  // drew the map as one flat colour.  Classes that do not reach the data are a
  // map with no information in it.
  //
  // And the invariant the new figure rests on: the exporter counts a share per
  // class, so a legend row and the bars above it always have the same number of
  // cells.  If those ever disagree the swatches stop standing under their bars,
  // and the arrangement is a lie.
  let checked = 0;
  let sharesChecked = 0;
  const outOfRange = [];
  const misaligned = [];
  const unbalanced = [];
  const countOf = (breaks) => (breaks.kind === 'categories'
    ? breaks.values.length
    : breaks.edges.length - 1
      + (breaks.open_low ? 1 : 0) + (breaks.open_high ? 1 : 0));
  for (const [scaleKey, entry] of Object.entries(stats)) {
    for (const [column, st] of Object.entries(entry.columns || {})) {
      const breaks = indicators.breaks[column];
      if (!breaks) continue;
      checked += 1;
      // every area beyond a censored distance's search: nothing to range over
      if (breaks.kind === 'classes' && st.n) {
        const low = breaks.edges[0];
        const high = breaks.edges[breaks.edges.length - 1];
        const reaches = breaks.open_low || low <= st.min + 1e-9;
        // a censored distance is classed by the bands searched: the odd value
        // a little beyond (a point along a long edge from its node) is
        // clipped into the top class by design
        const censored = (indicators.censored || {})[column];
        const spans = breaks.open_high || Boolean(censored)
          || high >= st.max - 1e-9;
        if (!(reaches && spans)) {
          outOfRange.push(
            `${scaleKey}/${column}: data ${st.min}-${st.max} outside `
            + `${low}-${high}`,
          );
        }
      }
      if (!st.class_shares) continue;
      sharesChecked += 1;
      if (st.class_shares.length !== countOf(breaks)) {
        misaligned.push(
          `${scaleKey}/${column}: ${st.class_shares.length} shares for `
          + `${countOf(breaks)} classes`,
        );
      }
      // the population with nothing within a censored distance's search is
      // a share of its own, beside the classes
      const total = st.class_shares.reduce((a, b) => a + b, 0)
        + (st.unclassed || 0) + (st.beyond || 0);
      if (Math.abs(total - 100) > 1.5) {
        unbalanced.push(
          `${scaleKey}/${column}: shares sum to ${total.toFixed(1)}`,
        );
      }
    }
  }
  check(outOfRange.length === 0,
    `classes that do not reach their data: ${outOfRange.slice(0, 6).join(' | ')}`);
  check(misaligned.length === 0,
    `shares that do not match their classes: ${misaligned.slice(0, 6).join(' | ')}`);
  check(unbalanced.length === 0,
    `shares that do not sum to 100: ${unbalanced.slice(0, 6).join(' | ')}`);
  console.log(`  ${checked} column/scale classifications checked, `
    + `${sharesChecked} with class shares, ${outOfRange.length} out of range`);
}

// ---------------------------------------------------------------------------
section('configured breaks came through as configured');
if (composite) {
  console.log('  a composite index dashboard: none of the general indicators');
} else {
  const expected = {
    local_walkability: { open_low: true, open_high: true, n: 8 },
    local_daily_living: { open_low: false, open_high: false, n: 3 },
    urban_heat_guhvi: { open_low: false, open_high: false, n: 10 },
    urban_heat_guhvi_class: { kind: 'categories', n: 5 },
  };
  for (const [column, want] of Object.entries(expected)) {
    const breaks = indicators.breaks[column];
    check(breaks, `${column} has exported breaks`);
    if (!breaks) continue;
    if (want.kind) {
      check(breaks.kind === want.kind, `${column} is ${want.kind}`);
    } else {
      check(Boolean(breaks.open_low) === want.open_low,
        `${column} open_low is ${want.open_low}`);
      check(Boolean(breaks.open_high) === want.open_high,
        `${column} open_high is ${want.open_high}`);
    }
    const n = breaks.kind === 'categories'
      ? breaks.values.length
      : breaks.edges.length - 1
        + (breaks.open_low ? 1 : 0) + (breaks.open_high ? 1 : 0);
    check(n === want.n, `${column} has ${want.n} classes (got ${n})`);
  }
  // a log2 ladder is hung off its target precisely so that the target is an
  // edge, and so that the top class means exactly "meets it"
  let logged = 0;
  for (const [column, breaks] of Object.entries(indicators.breaks)) {
    if (breaks.scale !== 'log2') continue;
    logged += 1;
    const target = (indicators.targets || {})[column];
    check(target, `${column} is on a log2 scale and has a target`);
    if (!target) continue;
    check(
      breaks.edges.some((e) => Math.abs(e - target.criteria) < 1e-9),
      `${column}: target ${target.criteria} is one of its edges `
      + `(${breaks.edges.join(', ')})`,
    );
    // each edge doubles the one before it, give or take the rounding applied
    // so that a legend does not have to read "178.125"
    for (let i = 1; i < breaks.edges.length; i += 1) {
      const ratio = breaks.edges[i] / breaks.edges[i - 1];
      check(Math.abs(ratio - 2) < 0.02, `${column}: edges double (${ratio})`);
    }
  }
  console.log(`  ${Object.keys(indicators.breaks).length} classified columns, `
    + `${logged} on a log2 scale, `
    + `${Object.keys(indicators.targets || {}).length} with a target`);
}

// ---------------------------------------------------------------------------
section('the map paints the classes the chart counts');
{
  // MapLibre is not available here, so the expression is evaluated directly
  // over the handful of operators it uses. What this proves is the property
  // that matters: sweeping a column's whole domain returns each class colour
  // once, in order, with nothing falling through to "no data" -- the failure
  // that would put a populated area in the missing-data grey and make the map
  // disagree with the bars drawn above the legend.
  const evaluate = (node, feature) => {
    if (!Array.isArray(node)) return node;
    const [op, ...rest] = node;
    const value = (n) => evaluate(n, feature);
    switch (op) {
      case 'get': return feature[rest[0]];
      case 'coalesce': {
        for (const item of rest) {
          const v = value(item);
          if (v !== undefined && v !== null) return v;
        }
        return null;
      }
      case 'all': return rest.every((item) => value(item) === true);
      case 'boolean': return Boolean(rest[0]);
      case '>=': return value(rest[0]) >= value(rest[1]);
      case '<': return value(rest[0]) < value(rest[1]);
      case '>': return value(rest[0]) > value(rest[1]);
      case '==': return value(rest[0]) === value(rest[1]);
      case '!=': return value(rest[0]) !== value(rest[1]);
      case 'case': {
        for (let i = 0; i + 1 < rest.length; i += 2) {
          if (value(rest[i]) === true) return value(rest[i + 1]);
        }
        return value(rest[rest.length - 1]);
      }
      default: throw new Error(`unhandled operator ${op}`);
    }
  };

  let swept = 0;
  const wrong = [];
  for (const family of indicators.families) {
    for (const [measure, spec] of Object.entries(family.measures)) {
      const variables = spec.variables ? Object.keys(spec.variables) : [null];
      for (const variable of variables) {
        const selection = vocab.coerce(
          { family: family.id, measure, network: 'walk', variable },
          everywhere,
        );
        const resolved = vocab.resolve(selection);
        if (!resolved) continue;
        const breaks = vocab.breaksFor(resolved);
        if (!breaks) continue;
        const classification = classify(
          resolved, breaks, vocab.targetFor(resolved),
        );
        const paint = fillExpression(classification);
        swept += 1;

        // one probe inside every class, plus the exact edges, plus values well
        // beyond either end -- an open class must catch those and a closed one
        // must clip them in rather than dropping them
        const probes = [];
        if (breaks.kind === 'categories') {
          breaks.values.forEach((v, i) => probes.push([v, i]));
        } else {
          const edges = breaks.edges;
          const span = edges[edges.length - 1] - edges[0] || 1;
          classification.classes.forEach((cls, i) => {
            const low = cls.min === null ? edges[0] - span : cls.min;
            const high = cls.max === null ? edges[edges.length - 1] + span : cls.max;
            probes.push([low + (high - low) / 2, i]);
          });
          probes.push([edges[0] - span * 10, 0]);
          probes.push([
            edges[edges.length - 1] + span * 10,
            classification.classes.length - 1,
          ]);
        }
        for (const [value, expected] of probes) {
          const colour = evaluate(paint, { [classification.column]: value });
          const want = classification.classes[expected].color;
          if (colour !== want) {
            wrong.push(
              `${classification.column} @ ${value}: painted ${colour}, `
              + `class ${expected} is ${want}`,
            );
          }
        }
      }
    }
  }
  check(wrong.length === 0,
    `values painted into the wrong class: ${wrong.slice(0, 6).join(' | ')}`);
  console.log(`  ${swept} classified selections swept end to end, `
    + `${wrong.length} mispainted`);
}

// ---------------------------------------------------------------------------
section('hidden variables really are gone');
if (composite) {
  console.log('  a composite index dashboard: none of the general indicators');
} else {
  const exposed = new Set(indicators.families.flatMap((f) => f.columns));
  const gone = [
    'urban_heat_subnational_hdi', 'urban_heat_infant_mortality_rate',
    'urban_heat_ndvi', 'urban_heat_land_surface_temp_c',
  ];
  for (const column of gone) {
    check(!exposed.has(column), `${column} is not in the vocabulary`);
  }
  // ...but what they feed is still navigable
  for (const column of ['urban_heat_guhvi', 'urban_heat_exposure_index']) {
    check(exposed.has(column), `${column} is still in the vocabulary`);
  }
  console.log(`  ${gone.length} sub-indicators hidden, the composites kept`);
}

// ---------------------------------------------------------------------------
section('every family has a theme, a colour and a Spanish label');
if (composite) {
  console.log('  a composite index dashboard: no themes');
} else {
  const themes = new Map((indicators.themes || []).map((t) => [t.id, t]));
  check(themes.size > 0, 'themes are declared');
  const hex = /^#[0-9a-f]{6}$/i;
  for (const theme of themes.values()) {
    check(hex.test(theme.color || ''),
      `theme ${theme.id} has a hex colour (${theme.color})`);
    check(theme.label && theme.label.es,
      `theme ${theme.id} has a Spanish label`);
  }
  const noSpanishDescription = Object.entries(indicators.descriptions)
    .filter(([, d]) => !d.es);
  check(
    noSpanishDescription.length === 0,
    `${noSpanishDescription.length} columns have no Spanish description`,
  );
  const noTheme = indicators.families.filter((f) => !f.theme);
  const notSpanish = indicators.families.filter(
    (f) => !(f.label && f.label.es),
  );
  check(noTheme.length === 0,
    `families without a theme: ${noTheme.map((f) => f.id).join(', ')}`);
  check(notSpanish.length === 0,
    `families without a Spanish label: ${notSpanish.map((f) => f.id).join(', ')}`);
  // a theme that claims a family which does not exist would leave a dead entry
  // in the picker
  const ids = new Set(indicators.families.map((f) => f.id));
  for (const theme of themes.values()) {
    const dangling = theme.families.filter((f) => !ids.has(f));
    check(dangling.length === 0,
      `theme ${theme.id} lists unknown families: ${dangling.join(', ')}`);
  }
  console.log(`  ${themes.size} themes, ${indicators.families.length} families, `
    + `all themed and named`);
}

// ---------------------------------------------------------------------------
section('interventions are matched to themes that exist');
if (composite) {
  console.log('  a composite index dashboard: no interventions');
} else {
  const ids = new Set((indicators.themes || []).map((t) => t.id));
  const entries = indicators.interventions || [];
  check(entries.length > 0, 'interventions were parsed');
  let orphan = 0;
  let pairings = 0;
  let silent = 0;
  for (const entry of entries) {
    check(Boolean(entry.name), `intervention ${entry.n} has a name`);
    for (const [theme, impacts] of Object.entries(entry.themes || {})) {
      if (!ids.has(theme)) orphan += 1;
      pairings += 1;
      // the invariant: an intervention is only offered for a theme where the
      // catalogue says what it would do there
      if (!impacts.length) silent += 1;
    }
  }
  check(orphan === 0, `${orphan} intervention theme references are unknown`);
  check(silent === 0, `${silent} intervention/theme pairings carry no impact`);
  // and the case that prompted this: fresh food must offer nothing
  const freshFood = indicators.families.find((f) => f.id === 'fresh_food_market');
  const theirTheme = freshFood && freshFood.theme;
  const offered = entries.filter((e) => (e.themes || {})[theirTheme]);
  check(
    offered.length === 0,
    `fresh food still offers: ${offered.map((e) => e.name).join(', ')}`,
  );
  console.log(`  ${entries.length} interventions, ${pairings} theme pairings, `
    + `all with a stated impact`);
}

// ---------------------------------------------------------------------------
section('access is one distance, stated plainly');
if (composite) {
  console.log('  a composite index dashboard: none of the general indicators');
} else {
  const { legendTitle, legendDirection } = await module_('legend.js');
  const available = scaleColumns('manzanas');
  const at = (distance) => vocab.resolve(vocab.coerce(
    { family: 'blue_space', measure: 'access', network: 'walk', distance },
    available,
  ));
  const first = at(undefined);
  check(first.kind === 'continuous', 'access resolves as a continuous measure');
  check(Boolean(first.column), 'access resolves to a single mapped column');
  // the shortest band, when the selection names none: it is the one a reader
  // reaches for first, and leaving it null used to draw nothing at all
  check(String(first.distance) === String(first.bands[0]),
    `access defaults to its shortest distance (${first.distance})`);
  // ...but every band is still resolved, because the popup reads them all out
  // and the results table compares them
  check(first.columns.length === first.bands.length,
    'every band is still resolved, for the popup and the results table');

  const later = at(String(first.bands[first.bands.length - 1]));
  check(later.column !== first.column,
    'choosing a different distance maps a different column');
  check(later.columns.length === first.columns.length,
    'choosing a distance does not change which bands are resolved');

  // The bug this guards: the map used to be a proximity ramp titled
  // "Access (%)", so its own direction had to be overridden to "nearer is
  // better" or the legend read as though further away were better.  Now the
  // map *is* the percentage, so the measure's own direction is correct and the
  // two measures must disagree about it -- more access, less distance.
  const distance = vocab.resolve(vocab.coerce(
    { family: 'blue_space', measure: 'distance', network: 'walk' }, available,
  ));
  check(first.direction === 'higher_is_better',
    `access is higher-is-better (${first.direction})`);
  check(legendDirection(first) !== legendDirection(distance),
    'access and distance do not share a direction note');
  check(legendTitle(first).text === legendTitle(first).text.trim()
    && Boolean(legendTitle(first).text),
    'access titles itself with its own measure');
  console.log(`  access:   ${legendTitle(first).text} — ${legendDirection(first)}`
    + `  @ ${first.distance} m of ${first.bands.join('/')}`);
  console.log(`  distance: ${legendTitle(distance).text} — `
    + `${legendDirection(distance)}`);
}

// ---------------------------------------------------------------------------
section('every sentence the viewer needs has been written');
{
  const text = indicators.text || {};
  check(text.showing && text.notes, 'indicators.json carries its text defaults');
  const used = new Set();
  for (const family of indicators.families) {
    for (const measure of Object.keys(family.measures)) used.add(measure);
  }
  const known = new Set([
    'network', 'networkLabel', 'distance', 'bands', 'indicator', 'description',
  ]);
  const missing = [];
  const unknown = [];
  for (const measure of used) {
    for (const group of ['showing', 'notes']) {
      const entry = (text[group] || {})[measure];
      if (!entry || !entry.es || !entry.en) {
        missing.push(`${group}.${measure}`);
        continue;
      }
      for (const lang of ['es', 'en']) {
        for (const [, name] of entry[lang].matchAll(/\{(\w+)\}/g)) {
          if (!known.has(name)) unknown.push(`${group}.${measure}.${lang}: {${name}}`);
        }
      }
    }
  }
  check(missing.length === 0, `sentences not written: ${missing.join(', ')}`);
  check(unknown.length === 0, `unknown placeholders: ${unknown.join(', ')}`);
  // every network needs the form a sentence uses, not just the dropdown's
  const noPhrase = Object.entries(indicators.networks || {})
    .filter(([, net]) => !(net.phrase && net.phrase.es && net.phrase.en));
  check(noPhrase.length === 0,
    `networks with no sentence phrase: ${noPhrase.map(([k]) => k).join(', ')}`);

  // the editable file, if the site has one, must parse and must not invent keys
  const textPath = path.join(ROOT, 'data', slug, 'text.json');
  if (fs.existsSync(textPath)) {
    let overrides = null;
    try {
      overrides = JSON.parse(fs.readFileSync(textPath, 'utf8'));
    } catch (error) {
      check(false, `text.json does not parse: ${error.message}`);
    }
    if (overrides) {
      const groups = Object.keys(overrides).filter((k) => k !== '_readme');
      const allowed = new Set([
        'showing', 'notes', 'scale_note', 'measures', 'networks', 'strings',
      ]);
      const strange = groups.filter((g) => !allowed.has(g));
      check(strange.length === 0,
        `text.json has groups nothing reads: ${strange.join(', ')}`);
      console.log(`  text.json: ${groups.join(', ')}`);
    }
  }
  console.log(`  ${used.size} measures, all with a sentence and a note in `
    + `both languages`);
}

// ---------------------------------------------------------------------------
section('counts are cut where a count means something');
{
  // 0 to 64 produce shops within a kilometre: classifying that from its range
  // puts nearly every area in the bottom class.  None / one / a couple / plenty
  // is what the number is actually asking.
  let checked = 0;
  for (const family of indicators.families) {
    const measure = family.measures.count;
    if (!measure) continue;
    for (const byNetwork of Object.values(measure.groups || {})) {
      for (const byDistance of Object.values(byNetwork)) {
        for (const column of Object.values(byDistance)) {
          const breaks = indicators.breaks[column];
          if (!breaks) continue;
          checked += 1;
          check(
            breaks.edges.join(',') === '0,1,2,3,4,5'
              && !breaks.open_low && breaks.open_high,
            `${column}: expected the 0-5+ ladder, got `
            + `${breaks.edges.join(',')}`,
          );
        }
      }
    }
  }
  console.log(`  ${checked} count columns, all on 0 / 1 / 2 / 3 / 4 / 5+`);
}

// ---------------------------------------------------------------------------
section('composite indices carry their structure, and share one scale');
{
  const composites = indicators.families.filter((f) => f.composite);
  const featured = manifest.featured;
  check(!featured || vocab.family(featured),
    `manifest.featured resolves to a family (${featured})`);
  for (const family of composites) {
    const c = family.composite;
    const scores = [
      c.columns.index,
      c.columns.mean,
      ...c.domains.map((d) => d.column),
      ...c.domains.flatMap((d) => d.indicators.map((i) => i.column)),
    ].filter(Boolean);
    const missing = scores.filter((column) => !everywhere.has(column));
    check(missing.length === 0,
      `${family.id}: structure columns not exported: ${missing.slice(0, 4).join(', ')}`);
    for (const key of Object.keys(manifest.regions)) {
      const values = (manifest.region_values || {})[key] || {};
      check(c.columns.index in values,
        `${family.id}: region_values.${key} has ${c.columns.index}`);
    }
    // the profile colours every petal from the index's classes, which is only
    // honest if every score of the index is classified the same way
    const breaks = indicators.breaks[c.columns.index];
    check(breaks, `${family.id}: the index is classified`);
    const shared = JSON.stringify(breaks || null);
    const differing = scores.filter(
      (column) => JSON.stringify(indicators.breaks[column] || null) !== shared,
    );
    check(differing.length === 0,
      `${family.id}: scores not on the shared classes: ${differing.slice(0, 4).join(', ')}`);
    if (breaks) {
      check(breaks.ramp === 'vik', `${family.id}: drawn on the diverging ramp`);
      const edges = breaks.edges;
      const middle = edges.length / 2;
      check(
        edges.length % 2 === 0
          && Math.abs((edges[middle - 1] + edges[middle]) / 2
            - (c.reference_value ?? 100)) < 1e-9,
        `${family.id}: the reference is the middle of the middle class `
        + `(${edges.join(', ')})`,
      );
    }
    for (const domain of c.domains) {
      if (domain.name) {
        check(domain.label && domain.label.es && domain.label.en,
          `${family.id}: domain ${domain.name} is labelled in both languages`);
      }
      for (const indicator of domain.indicators) {
        check(indicator.label && indicator.label.es && indicator.label.en,
          `${family.id}: indicator ${indicator.id} is labelled in both languages`);
        // a lens, where given, is one the index labels (the framework's)
        check(!indicator.lens || (c.lenses || {})[indicator.lens],
          `${family.id}: indicator ${indicator.id} has a labelled lens (${indicator.lens})`);
      }
      // a domain colour, where given, is what the profile fills petals with
      if (domain.colour) {
        const hex = /^#[0-9a-fA-F]{6}$/;
        check(hex.test(domain.colour.fill || '') && hex.test(domain.colour.stroke || ''),
          `${family.id}: domain ${domain.name} has a fill and stroke colour`);
      }
    }
    // indicators listed once, each domain listing its members with their
    // shares of it: an indicator's shares sum to one, whatever domains it
    // counts towards, and the effective weights of those scored to one
    if (Array.isArray(c.indicators)) {
      const ids = c.indicators.map((i) => i.id);
      check(new Set(ids).size === ids.length, `${family.id}: indicators listed once each`);
      check(JSON.stringify(c.order || []) === JSON.stringify(ids),
        `${family.id}: indicators listed in the order presented`);
      const shares = new Map();
      for (const domain of c.domains) {
        for (const member of domain.indicators) {
          check(ids.includes(member.id),
            `${family.id}: ${domain.name} member ${member.id} is an indicator of the index`);
          shares.set(member.id, (shares.get(member.id) || 0) + Number(member.share || 1));
        }
        if (domain.scored === false) {
          check(!domain.column && !domain.indicators.length,
            `${family.id}: unscored domain ${domain.name} has no score and no members`);
        }
      }
      for (const [id, total] of shares) {
        check(Math.abs(total - 1) < 1e-6, `${family.id}: ${id}'s shares sum to one (${total})`);
      }
      const effective = c.indicators.filter((i) => i.active !== false && !i.dropped)
        .map((i) => Number(i.effective_weight));
      check(effective.every(Number.isFinite)
        && Math.abs(effective.reduce((a, b) => a + b, 0) - 1) < 1e-4,
      `${family.id}: effective weights of the indicators scored sum to one`);
      const sharedCount = c.indicators.filter((i) =>
        Object.keys(i.domains || {}).length > 1).length;
      console.log(`  ${family.id}: ${ids.length} indicators, ${sharedCount} shared by domains; `
        + `effective weights ${(Math.min(...effective) * 100).toFixed(1)}-`
        + `${(Math.max(...effective) * 100).toFixed(1)}%`);
    }
    const lensed = c.domains.flatMap((d) => d.indicators).filter((i) => i.lens).length;
    const coloured = c.domains.filter((d) => d.colour).length;
    console.log(`  ${family.id}: ${coloured} domains coloured, ${lensed} indicators with a lens`);
    console.log(`  ${family.id}: ${c.domains.length} domains, `
      + `${c.domains.reduce((n, d) => n + d.indicators.length, 0)} indicators, `
      + `classes ${((breaks || {}).edges || []).join(' / ')}`);
  }
  if (!composites.length) console.log('  no composite indices in this dataset');
}

// ---------------------------------------------------------------------------
section('the index settings: variants read exported scores, weights recompute');
{
  const {
    activeIndex, ampi, defaultSettings, referenceOf, variantFor, walkabilityOptions,
  } = await module_('uli.js');
  const composites = indicators.families.filter((f) => f.composite);
  for (const family of composites) {
    const c = family.composite;
    const variants = c.variants || [];
    if (!variants.length) {
      console.log(`  ${family.id}: no variants`);
      continue;
    }
    // the published index is the first variant, and the defaults show it
    check(variants[0].name === c.name, `${family.id}: the base index comes first`);
    const identity = activeIndex(c, defaultSettings());
    check(identity.remap(c.columns.index) === c.columns.index,
      `${family.id}: default settings show the published index`);
    const shared = JSON.stringify(indicators.breaks[c.columns.index] || null);
    for (const variant of variants) {
      for (const column of Object.values(variant.columns)
        .concat(Object.values(variant.domains || {}),
          Object.values(variant.indicators || {}))) {
        check(everywhere.has(column), `${family.id}: ${column} is exported`);
      }
      if (!variant.columns.penalty) continue;
      check(JSON.stringify(indicators.breaks[variant.columns.index] || null) === shared,
        `${family.id}: ${variant.name} shares the index's classes`);
      for (const key of Object.keys(manifest.regions)) {
        const values = (manifest.region_values || {})[key] || {};
        check(variant.columns.index in values,
          `${family.id}: region_values.${key} has ${variant.columns.index}`);
      }
      // every variant is reachable from the settings, and resolves to itself
      const settings = {
        ...defaultSettings(),
        attenuation: variant.attenuation !== false,
      };
      check((variantFor(c, settings) || {}).name === variant.name,
        `${family.id}: the settings reach ${variant.name}`);
      check(activeIndex(c, settings).remap(c.columns.index) === variant.columns.index,
        `${family.id}: ${variant.name} is mapped from its own index column`);
    }
    const options = walkabilityOptions(c);
    check(options.length < 2 || options[0].base,
      `${family.id}: the default walkability option is the published index`);
    console.log(`  ${family.id}: ${variants.length} variants; walkability ${
      options.map((o) => (o.attenuation ? 'attenuated' : 'plain')).join(' / ')}`);

    // an indicator listed but not counted says why, and is counted by the
    // variant that activates it
    for (const domain of c.domains) {
      for (const indicator of domain.indicators) {
        if (indicator.active !== false) continue;
        check(indicator.inactive_reason && indicator.inactive_reason.es
          && indicator.inactive_reason.en,
        `${family.id}: inactive ${indicator.id} says why, in both languages`);
        const by = variants.find((v) => (v.activates || []).includes(indicator.id));
        check(by, `${family.id}: a variant activates ${indicator.id}`);
        if (by) {
          const shown = activeIndex(c, { ...defaultSettings(),
            attenuation: by.attenuation !== false }).structure;
          const again = shown.domains.flatMap((d) => d.indicators)
            .find((i) => i.id === indicator.id);
          check(again && again.active,
            `${family.id}: ${by.name} counts ${indicator.id}`);
        }
      }
    }

    // custom weights: a domain of one indicator is that indicator's score
    // exactly, and the index recomputed at equal weights is near the published
    // one (it is the index of averages, not the average of indices)
    const firstDomain = c.domains.find((d) => d.name);
    const weights = { ...defaultSettings(),
      domains: { [firstDomain.name]: 2 } };
    const custom = activeIndex(c, weights);
    // scores reported relative to the reference are aggregated with it at 100
    const offset = 100 - referenceOf(c);
    check(custom.custom && custom.expression(custom.remap(c.columns.index)),
      `${family.id}: custom weights give a paint expression for the index`);
    for (const [key, values] of Object.entries(manifest.region_values || {})) {
      const scored = custom.values(values);
      for (const domain of custom.structure.domains) {
        const inputs = domain.indicators.filter((i) => i.column && !i.dropped);
        if (inputs.length === 1 && domain.column && values[inputs[0].column] !== undefined) {
          check(Math.abs(scored[domain.column] - values[inputs[0].column]) < 1e-9,
            `${family.id}: ${key} ${domain.name} is its one indicator's score`);
        }
      }
      // a domain's recomputed score weights each member by its share of it
      for (const domain of custom.structure.domains) {
        if (!domain.column) continue;
        const inputs = domain.indicators.filter((i) => i.column && !i.dropped && i.active);
        const direct = ampi(
          inputs.map((i) => (values[i.column] === undefined ? null
            : Number(values[i.column]) + offset)),
          inputs.map((i) => (Number(i.weight) || 1) * (Number(i.share) || 1)),
        );
        if (direct && Number.isFinite(scored[domain.column])) {
          check(Math.abs(direct.index - offset - scored[domain.column]) < 1e-9,
            `${family.id}: ${key} ${domain.name} recomputed with its members' shares`);
        }
      }
      const equal = ampi(
        c.domains.filter((d) => d.column).map((d) => Number(values[d.column]) + offset),
        c.domains.filter((d) => d.column).map(() => 1),
      );
      const published = Number(values[c.columns.index]);
      if (equal && Number.isFinite(published)) {
        check(Math.abs(equal.index - offset - published) < 5,
          `${family.id}: ${key} index of domain averages (${(equal.index - offset).toFixed(2)}) `
          + `near the published (${published.toFixed(2)})`);
      }
    }
  }
}

// ---------------------------------------------------------------------------
section('every column is tiled, in groups narrow enough to keep at every zoom');
{
  const groups = indicators.column_group || {};
  for (const [key, scale] of Object.entries(manifest.scales)) {
    const tiles = scale.tiles || {};
    check(Object.keys(tiles).length > 0, `${key}: tiled in groups`);
    const tiled = new Set(Object.values(tiles).flatMap((t) => t.columns));
    const context = new Set(['pop_est', 'area_sqkm', 'pop_per_sqkm',
      'intersection_count', 'intersections_per_sqkm']);
    const untiled = scale.columns.filter((c) => !tiled.has(c) && !context.has(c));
    check(untiled.length === 0,
      `${key}: columns in no tile group: ${untiled.slice(0, 4).join(', ')}`);
    for (const [group, tile] of Object.entries(tiles)) {
      const stray = tile.columns.filter((c) => groups[c] !== group);
      check(stray.length === 0,
        `${key}: ${group} holds columns recorded in another group: ${stray.slice(0, 3)}`);
      check(fs.existsSync(path.join(ROOT, 'data', slug, `${slug}_${tile.layer}.pmtiles`)),
        `${key}: ${tile.layer} archive is deployed`);
    }
  }
  const widest = Math.max(...Object.values(manifest.scales).flatMap((s) =>
    Object.values(s.tiles || {}).map((t) => t.columns.length)));
  console.log(`  ${Object.keys(manifest.scales).length} scales; widest tile group `
    + `${widest} columns`);
}

// ---------------------------------------------------------------------------
section('a composite dashboard compares its regions, and explains attenuation');
if (!indexed) {
  console.log('  a general dashboard');
} else {
  const file = path.join(ROOT, 'data', slug, manifest.distributions || '');
  check(manifest.distributions && fs.existsSync(file),
    'distributions.json is deployed');
  if (manifest.distributions && fs.existsSync(file)) {
    const d = read(manifest.distributions);
    const c = indicators.families.find((f) => f.composite).composite;
    for (const key of Object.keys(manifest.regions)) {
      const entry = (d.regions[key] || {})[c.columns.index];
      check(entry && entry.density.length === d.points,
        `distributions for ${key} on ${c.columns.index}`);
      if (entry) {
        const step = (d.x[c.columns.index][1] - d.x[c.columns.index][0]) / (d.points - 1);
        const area = entry.density.reduce((a, b) => a + b, 0) * step;
        check(Math.abs(area - 1) < 0.1,
          `${key}: the density integrates to about 1 (${area.toFixed(3)})`);
        console.log(`  ${key.padEnd(10)} ${entry.n} areas, weight ${
          Math.round(entry.weight)}, mean ${entry.mean}`);
      }
    }
  }
  const att = manifest.attenuation;
  const heat = att && att.heat ? Object.values(att.heat)[0] : null;
  check(heat && heat.bounds && heat.bounds[1] > heat.bounds[0],
    'walkability attenuation carries its thermal comfort bounds');
  if (heat && heat.bounds) {
    console.log(`  attenuation λ ${att.lambda}, P${att.percentiles.join('-P')} `
      + `${heat.bounds.map((b) => b.toFixed(2)).join(' – ')}`);
  }
}

// ---------------------------------------------------------------------------
section('a regular grid is written as a raster, for the smooth surface');
{
  let rasters = 0;
  for (const [key, scale] of Object.entries(manifest.scales)) {
    const raster = scale.raster;
    if (!raster) continue;
    rasters += 1;
    const file = (name) => path.join(ROOT, 'data', slug, name);
    check(fs.existsSync(file(raster.index))
      && fs.statSync(file(raster.index)).size === raster.areas * 4,
    `${key}: the cell index holds one cell per area`);
    check(raster.areas === scale.features, `${key}: raster areas === features`);
    for (const [group, entry] of Object.entries(raster.groups)) {
      check(fs.existsSync(file(entry.file))
        && fs.statSync(file(entry.file)).size === raster.areas * 4 * entry.columns.length,
      `${key}: ${group} values hold every column for every area`);
    }
    check(raster.corners.length === 4, `${key}: four corners`);
    console.log(`  ${key}: ${raster.nx} x ${raster.ny} cells of ${raster.cell} m, `
      + `${Object.keys(raster.groups).length} groups`);
  }
  if (!rasters) console.log('  no regular grid in this dataset');
}

// ---------------------------------------------------------------------------
section('access by distance: every band has a region figure');
{
  let banded = 0;
  for (const family of indicators.families) {
    const walk = ((family.measures.access || {}).networks || {}).walk;
    if (!walk || typeof walk === 'string' || Object.keys(walk).length < 2) continue;
    banded += 1;
    for (const [band, column] of Object.entries(walk)) {
      for (const key of Object.keys(manifest.regions)) {
        const values = (manifest.region_values || {})[key] || {};
        if (!everywhere.has(column)) continue;
        check(column in values,
          `${family.id}: region_values.${key} has the ${band} m band (${column})`);
      }
    }
  }
  const bands = [...new Set(indicators.families.flatMap((f) =>
    Object.keys(((f.measures.access || {}).networks || {}).walk || {})))]
    .sort((a, b) => a - b);
  console.log(`  ${banded} walking access families; bands ${bands.join(' / ')} m`);
}

// ---------------------------------------------------------------------------
section('each language\'s conceptual model is present');
{
  const models = manifest.conceptual_models || {};
  for (const [code, model] of Object.entries(models)) {
    const file = path.join(ROOT, 'data', slug, model.file);
    check(fs.existsSync(file), `conceptual model for ${code}: ${model.file} is deployed`);
    check(['image', 'document'].includes(model.type),
      `conceptual model for ${code}: shown as an image or a document (${model.type})`);
    if (fs.existsSync(file)) {
      console.log(`  ${code}: ${model.file} (${Math.round(fs.statSync(file).size / 1024)} KB)`);
    }
  }
  if (!Object.keys(models).length) console.log('  none configured');
}

// ---------------------------------------------------------------------------
section('region values are present for both regions');
for (const key of Object.keys(manifest.regions)) {
  const values = (manifest.region_values || {})[key];
  check(values, `region_values has ${key}`);
  if (values) {
    console.log(`  ${key.padEnd(12)} ${Object.keys(values).length} values`);
  }
}

console.log(
  failures ? `\n${failures} failure(s)` : '\nall checks passed',
);
process.exit(failures ? 1 : 0);
