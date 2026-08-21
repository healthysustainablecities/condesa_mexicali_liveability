// Regenerate data/<slug>/text.json — every string the viewer shows, in one
// editable file.
//
//   node build/make_text.mjs [slug]
//
// The file is what the site actually reads (js/text.js), so editing it and
// refreshing the browser is the whole loop: no exporter run, no rebuild.
//
// Run this again after adding a string to js/strings.js or a sentence to
// DEFAULT_TEXT in _export_dashboard.py, and it will pick them up. It **merges**
// rather than overwrites: anything already edited in text.json is kept, and
// only genuinely new keys are added, so regenerating never silently reverts a
// revision. Delete a key to fall back to the exporter's default.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const slug = process.argv[2] || 'mexicali';
const dir = path.join(ROOT, 'data', slug);
const target = path.join(dir, 'text.json');

const { allStrings } = await import(
  pathToFileURL(path.join(ROOT, 'js', 'strings.js')).href
);
const indicators = JSON.parse(
  fs.readFileSync(path.join(dir, 'indicators.json'), 'utf8'),
);

const existing = fs.existsSync(target)
  ? JSON.parse(fs.readFileSync(target, 'utf8'))
  : {};

/**
 * Existing wins; new keys are added underneath it; retired keys are dropped.
 *
 * Pruning matters as much as merging: a string the viewer no longer reads would
 * otherwise sit in this file forever, inviting somebody to edit it and wonder
 * why nothing changed.
 */
const merge = (was, now) => {
  const out = { ...now };
  for (const [key, value] of Object.entries(was || {})) {
    if (key in now) out[key] = value;
  }
  return out;
};

const text = indicators.text || {};
const built = {
  _readme:
    'Every string the explorer shows. Edit any of them and refresh the '
    + 'browser — nothing needs rebuilding. Delete a key to fall back to the '
    + 'exporter default. Placeholders: {network} {networkLabel} {distance} '
    + '{bands} {indicator} {description}. See README.md.',
  showing: merge(existing.showing, text.showing || {}),
  notes: merge(existing.notes, text.notes || {}),
  scale_note: existing.scale_note || text.scale_note || {},
  measures: merge(
    existing.measures,
    Object.fromEntries(
      Object.entries(indicators.measures || {})
        .map(([key, meta]) => [key, meta.label]),
    ),
  ),
  networks: merge(
    existing.networks,
    Object.fromEntries(
      Object.entries(indicators.networks || {})
        .map(([key, net]) => [key, net.phrase || net.label]),
    ),
  ),
  strings: merge(existing.strings, allStrings()),
};

fs.writeFileSync(target, `${JSON.stringify(built, null, 2)}\n`, 'utf8');
const count = ['showing', 'notes', 'measures', 'networks', 'strings']
  .reduce((n, key) => n + Object.keys(built[key]).length, 0);
console.log(`${path.relative(ROOT, target)}: ${count} strings`);
