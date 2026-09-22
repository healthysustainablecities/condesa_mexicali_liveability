// A plain-language sentence describing what the map is currently showing.
//
// Ported in spirit from the validation site's `showingText()`, which was the
// single thing that made that dashboard readable by people who had not built
// it. Everything else names a variable; this names the idea.
//
// It is also what the exported image's caption uses. The export previously took
// its description from the widest band's data-dictionary entry, which produced
// "within 1500 m" on a map whose control said 500 m.
//
// The sentences themselves are not here. They come from the exporter, and are
// overridden by the site's own data/<slug>/text.json — see js/text.js. That is
// what lets the wording be revised for a workshop audience without a code
// change, which it has needed more than once.

import { label, t } from './strings.js';
import { measureLabel, partsFor, say } from './text.js';

/**
 * The sentence for the current selection.
 *
 * Composed from parts that are already translated — the measure, the network's
 * sentence phrase, the distance — rather than from the data dictionary, whose
 * prose is English only and describes one column rather than the map.
 */
export function showingSentence(resolved, vocab, lang) {
  if (!resolved) return '';
  return say('showing', resolved.measureKey, partsFor(resolved, vocab));
}

/** The indicator's own name, as a workshop card would print it. */
export function showingTitle(resolved, vocab) {
  if (!resolved) return '';
  const family = resolved.family;
  const parts = [label(family.label, family.id)];
  if (resolved.selection.variable) {
    // a composite index's own score is labelled as the index itself, and
    // "Index · Index" says nothing twice
    const variable = vocab.variableLabel(resolved.selection.variable);
    if (variable !== parts[0]) parts.push(variable);
  }
  if (resolved.selection.group) {
    parts.push(resolved.selection.group.replace(/_/g, ' '));
  }
  return parts.join(' · ');
}

/** The measure and distance the map is drawn from, under the title. */
export function showingMeasure(resolved) {
  if (!resolved) return '';
  const parts = [label(measureLabel(resolved), resolved.measureKey)];
  if (resolved.distance) parts.push(`${resolved.distance} m`);
  return parts.join(' · ');
}

/**
 * Render the title pill and sentence.
 *
 * The theme dot echoes the printed workshop cards, where an intervention card
 * carries a coloured dot for each theme it belongs to.
 */
export function renderShowing(element, resolved, vocab, lang, theme, onInfo) {
  if (!resolved) {
    element.innerHTML = '';
    return;
  }
  const dot = theme
    ? `<span class="theme-dot" style="background:${theme.color}"
             title="${label(theme.label, theme.id)}"></span>`
    : '';
  // the "i" sits with the indicator it explains, not in the app header
  element.innerHTML = `
    <div class="showing-head">
      ${dot}<span class="showing-title">${showingTitle(resolved, vocab)}</span>
      <button class="btn icon serif" id="infoBtn"
              title="${t('info')}" aria-label="${t('info')}">i</button>
    </div>
    <div class="showing-body">${showingSentence(resolved, vocab, lang)}</div>`;
  element.hidden = false;
  element.querySelector('#infoBtn').addEventListener('click', onInfo);
}
