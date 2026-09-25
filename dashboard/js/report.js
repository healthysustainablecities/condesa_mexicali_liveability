// The liveability report: what the dashboard is showing of its composite index,
// laid out as a printable document -- saved as a PDF from the print dialogue.
//
// Printed rather than drawn: the report is the dashboard's own markup, styled
// by css/print.css with the dashboard's own tokens (theme.js sets them on the
// document), so its type, colours and figures are the dashboard's, and the
// profile is the same SVG the sidebar draws.  A PDF library would have meant a
// second, hand-drawn copy of all of it, which would drift.
//
// The report describes what is on screen: the subject the profile describes (a
// clicked area, or the first pane's region), read against the other region on
// screen, the index as the settings show it, and the map as it is framed.

import {
  methodParts, modelFor, references, technicalReportPath, variantParagraphs,
} from './model.js';
import { composeView } from './imageexport.js';
import { attributionLines } from './info.js';
import { profileSubjects } from './profile.js';
import { activePanes, state } from './state.js';
import { getLang, label, number, t } from './strings.js';
import { say } from './text.js';
import {
  modificationNote, referenceOf, shareOf, shareText,
} from './uli.js';

const attr = (text) => String(text === undefined || text === null ? '' : text)
  .replace(/&/g, '&amp;').replace(/\x22/g, '&quot;').replace(/</g, '&lt;');

function numeric(value) {
  if (value === undefined || value === null || value === '') return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

/** Points from the reference, signed. */
function signed(value, reference, digits = 1) {
  if (value === null) return '–';
  const d = value - reference;
  const size = number(Math.abs(d), digits);
  if (Number(Math.abs(d).toFixed(digits)) === 0) return size;
  return `${d > 0 ? '+' : '−'}${size}`;
}

/** A bar about the reference, as the profile's list draws it. */
function bar(value, reference, reach, colour) {
  if (value === null) return '<span class="rbar"></span>';
  const at = (v) => ((Math.max(-reach, Math.min(reach, v - reference)) + reach)
    / (2 * reach)) * 100;
  const left = Math.min(at(value), 50);
  const width = Math.abs(at(value) - 50);
  return `<span class="rbar"><i style="left:${left.toFixed(1)}%;width:${
    width.toFixed(1)}%;background:${attr(colour.fill || '#9a948c')};border-color:${
    attr(colour.stroke || colour.fill || '#9a948c')}"></i><b></b></span>`;
}

/** Wait for every image in an element to load (or fail), briefly. */
function imagesLoaded(element) {
  const pending = [...element.querySelectorAll('img')]
    .filter((img) => !img.complete)
    .map((img) => new Promise((resolve) => {
      img.addEventListener('load', resolve, { once: true });
      img.addEventListener('error', resolve, { once: true });
    }));
  return Promise.race([
    Promise.all(pending),
    new Promise((resolve) => { setTimeout(resolve, 4000); }),
  ]);
}

/** The domains and indicators as a table: scores, weights and subdomains. */
function domainTable(structure, subject, references, reference) {
  const valueOf = (who, column) => numeric(((who || {}).values || {})[column]);
  const all = structure.domains.flatMap((d) => [d.column,
    ...d.indicators.map((i) => i.column)]).filter(Boolean);
  const reach = Math.max(10, ...all.map((c) => Math.abs(
    (valueOf(subject, c) === null ? reference : valueOf(subject, c)) - reference,
  )));
  const weighted = Boolean(structure.custom);
  const heads = references.map((ref) => `<th class="num">${attr(ref.name)}</th>`)
    .join('');
  const rows = structure.domains
    .filter((d) => d.name && d.scored !== false && d.indicators.length).map((domain) => {
    const colour = domain.colour || {};
    const swatch = `<i class="rswatch" style="background:${attr(colour.fill || '#ddd')};
      border-color:${attr(colour.stroke || '#999')}"></i>`;
    const domainValue = domain.column ? valueOf(subject, domain.column) : null;
    const head = `<tr class="rdomain">
      <th>${swatch}${attr(label(domain.label, domain.name))}${weighted
  ? ` <small>×${number(domain.weight, 1)}</small>` : ''}</th>
      <td>${bar(domainValue, reference, reach, colour)}</td>
      <td class="num">${signed(domainValue, reference)}</td>
      ${references.map((ref) => `<td class="num">${signed(
    domain.column ? valueOf(ref, domain.column) : null, reference)}</td>`).join('')}
    </tr>`;
    const items = domain.indicators.filter((i) => i.column || i.dropped)
      .map((indicator) => {
        // an indicator the index does not count under these settings is
        // listed, but has no score of its own here
        const inactive = indicator.active === false;
        const scored = (who) => (indicator.column && !inactive
          ? valueOf(who, indicator.column) : null);
        const v = scored(subject);
        const notes = [label(indicator.subdomain, '')];
        if (shareOf(indicator) < 1) {
          notes.push(`${shareText(shareOf(indicator))} ${t('profileWeight')}`);
        }
        if (indicator.dropped) notes.push(t('profileExcluded'));
        if (inactive) notes.push(t('profileInactive'));
        if (weighted && indicator.weight !== 1) {
          notes.push(indicator.weight > 0
            ? `×${number(indicator.weight, 1)}` : t('uliWeightExcluded'));
        }
        return `<tr class="rindicator">
          <th>${attr(label(indicator.label, indicator.id))}<small>${
  attr(notes.filter(Boolean).join(' · '))}</small></th>
          <td>${bar(v, reference, reach, colour)}</td>
          <td class="num">${signed(v, reference)}</td>
          ${references.map((ref) => `<td class="num">${signed(
    scored(ref), reference)}</td>`)
    .join('')}
        </tr>`;
      }).join('');
    return head + items;
  }).join('');
  return `<table class="rtable">
    <thead><tr><th></th><th>${attr(t('reportScore'))}</th>
      <th class="num">${attr(subject.name)}</th>${heads}</tr></thead>
    <tbody>${rows}</tbody></table>`;
}

/**
 * Build the report for what is on screen and open the print dialogue.
 *
 * Returns null, or a message for the toast where there was nothing to report.
 */
export async function printReport(app) {
  // the report is of the composite index: show it first if something else is
  if (!app.resolved || !app.resolved.composite) {
    app.showFeatured();
    // a render already under way queues this one rather than awaiting it, so
    // wait until rendering has settled
    await app.render('report');
    for (let i = 0; i < 100 && app.rendering; i += 1) {
      await new Promise((resolve) => { setTimeout(resolve, 50); });
    }
  }
  if (!app.resolved || !app.resolved.composite) return t('reportNoIndex');

  const structure = app.resolved.composite;
  const base = app.uli ? app.uli.base : structure;
  const panes = activePanes();
  const datasets = panes.map((pane) => app.datasets.get(pane.dataset));
  const dataset = datasets[0];
  const reference = referenceOf(structure);
  const { subject, references: others } = profileSubjects(app, panes, datasets);
  const index = numeric(subject.values[structure.columns.index]);
  const mean = numeric(subject.values[structure.columns.mean]);
  const penalty = numeric(subject.values[structure.columns.penalty]);
  const note = modificationNote(base, state.uli);
  // the published index, named by its walkability where it has variants
  const published = ((base.variants || [])[0] || {}).label;
  const unmodified = `${t('reportPublished')}${
    published ? `: ${label(published, '')}` : ''}.`;
  const core = (typeof structure.colour === 'string' ? structure.colour
    : (structure.colour || {}).fill) || '#4E8EF7';
  const lang = getLang();

  // the map, composed as the image export composes it
  let map = '';
  try {
    const canvas = await composeView({
      panes: app.visiblePanes(),
      datasets,
      resolved: app.resolved,
      classification: app.classification,
      vocab: app.vocab,
    });
    if (canvas) {
      map = `<img class="rmap" src="${canvas.toDataURL('image/png')}" alt="">`;
    }
  } catch (error) {
    map = `<p class="rnote">${attr(t('reportMapFailed'))}</p>`;
  }

  const profile = document.querySelector('#profile .profile-chart');
  const model = modelFor(dataset, lang);
  const figure = model && model.type !== 'document'
    ? `<img class="rmodel" src="data/${attr(dataset.slug)}/${attr(model.file)}"
        alt="${attr(model.alt || t('conceptualModel'))}">` : '';
  const parts = methodParts(structure, dataset.manifest);
  // as the technical report sets them out, more briefly
  const methods = [
    say('methods', 'intro', parts),
    parts.thresholds ? say('methods', 'threshold', parts) : '',
    parts.steps ? say('methods', 'steps', parts) : '',
    say('methods', structure.method === 'mpi' ? 'normalise_mpi' : 'normalise', parts),
    say('methods', 'aggregate', parts),
    structure.shared ? say('methods', 'shared', parts) : '',
    say('methods', 'scale', parts),
    say('methods', 'reading', parts),
    ...variantParagraphs(structure, parts),
  ].filter(Boolean).map((p) => `<p>${attr(p)}</p>`).join('');
  const sources = attributionLines(dataset.manifest)
    .map((line) => `<li>${attr(line)}</li>`).join('');
  const title = label(dataset.manifest.title || dataset.manifest.label, '');
  const date = new Date().toLocaleDateString(lang === 'es' ? 'es-MX' : 'en-AU',
    { year: 'numeric', month: 'long', day: 'numeric' });
  const comparisons = others.map((ref) => `<li>${attr(ref.name)}: <b>${
    signed(numeric(ref.values[structure.columns.index]), reference)}</b></li>`).join('');

  const element = document.getElementById('report');
  element.style.setProperty('--core', core);
  element.innerHTML = `
    <header class="rhead">
      <div class="rkicker">${attr(t('reportTitle'))} · ${attr(title)}</div>
      <h1>${attr(label(structure.label, structure.name))}</h1>
      <div class="rmeta">${attr(t('reportSubject'))}: <b>${attr(subject.name)}</b>
        · ${attr(t('reportGenerated'))}: ${attr(date)}</div>
    </header>
    <section class="rsummary">
      <div class="rscore">
        <span class="rbig">${signed(index, reference)}</span>
        <span class="rsub">${attr(t('reportScore'))}</span>
        <span class="rsub">${attr(t('profileMean'))} ${signed(mean, reference)} −
          ${attr(t('profilePenalty'))} ${penalty === null ? '–' : number(penalty, 1)}</span>
      </div>
      <div class="rsettings">
        <h3>${attr(t('reportSettings'))}</h3>
        <p>${note ? `${attr(note)}${structure.custom
    ? ` — <em>${attr(t('uliExploratoryHelp'))}</em>` : ''}`
    : attr(unmodified)}</p>
        ${comparisons ? `<ul>${comparisons}</ul>` : ''}
        <p class="rnote">${attr(t('profileReference'))}</p>
      </div>
    </section>
    <section class="rprofile">${profile ? profile.outerHTML : ''}</section>
    <section class="rdomains">
      <h2>${attr(t('reportDomains'))}</h2>
      ${domainTable(structure, subject, others, reference)}
    </section>
    <section class="rmapsec">
      <h2>${attr(t('reportMaps'))}</h2>
      ${map}
    </section>
    <section class="rmethods">
      <h2>${attr(t('reportMethods'))}</h2>
      ${figure}
      ${methods}
      <p><a href="${attr(new URL(technicalReportPath(dataset, lang), document.baseURI))}">${
  attr(t('technicalReport'))}</a></p>
      ${references(structure)}
    </section>
    <section class="rsources">
      <h2>${attr(t('reportSources'))}</h2>
      <ul>${sources}</ul>
    </section>`;
  element.hidden = false;
  await imagesLoaded(element);
  const done = () => {
    element.hidden = true;
    element.innerHTML = '';
  };
  window.addEventListener('afterprint', done, { once: true });
  const previous = document.title;
  // the browser offers the title as the PDF's file name
  document.title = `${t('reportTitle')} - ${subject.name}`;
  window.print();
  document.title = previous;
  return null;
}
