// The application: loads the exported data, wires the controls to state, and
// repaints everything when state changes.
//
// Control flow is one-way throughout.  A control writes to `state` and nothing
// else; `render()` reads `state` and updates the DOM and both maps.  That is
// what makes two panes tractable, and what makes the URL hash a complete
// description of what is on screen.

import { classify } from './choropleth.js';
import { Dictionary } from './dictionary.js';
import { exportImage } from './imageexport.js';
import { renderInfo } from './info.js';
import { MeasureTool } from './measure.js';
import { Pane } from './pane.js';
import {
  activePanes, readHash, state, subscribe, batch, update, updateSilent,
} from './state.js';
import { renderLegend, renderLtsLegend, travelMinutes } from './legend.js';
import { renderResults } from './results.js';
import { renderDistribution } from './stats.js';
import { getLang, label, setLang, t } from './strings.js';
import { loadText, measureLabelFor } from './text.js';
import { renderShowing } from './showing.js';
import { applyStyle, contrastInk, Themes } from './theme.js';
import { Tour } from './tour.js';
import { Vocabulary } from './vocab.js';

const $ = (id) => document.getElementById(id);

/**
 * Wait for the next painted frame, or a moment, whichever comes first.
 *
 * A background or hidden tab never paints, so a bare `requestAnimationFrame`
 * await will hang there forever — and a render that hangs holds its lock and
 * freezes the app. The frame is what we want when it comes; the timeout is what
 * keeps a tab the user switched away from working when they switch back.
 */
const nextFrame = () => new Promise((resolve) => {
  let settled = false;
  const finish = () => {
    if (settled) return;
    settled = true;
    resolve();
  };
  requestAnimationFrame(finish);
  setTimeout(finish, 120);
});
const BASEMAP_KEYS = ['streets', 'satellite', 'none'];
// the only reasons a pane's pixel size can have changed
const LAYOUT_REASONS = new Set(['boot', 'layout']);
// Which region and scale each pane opens on, in order of preference. Condesa
// at lot scale is the subject; Mexicali's grid is the comparison.
const DEFAULT_REGIONS = [['condesa', 'mexicali'], ['mexicali', 'condesa']];
const DEFAULT_SCALES = [
  ['condesa_lotes', 'manzanas'],
  ['grid', 'manzanas'],
];
// the supporting layers, in the order they are offered, with the string keys
// for their label and their explanation
const OVERLAY_UI = [
  ['choropleth', 'overlayChoropleth'],
  ['destinations', 'overlayDestinations'],
  ['network', 'overlayNetwork'],
  ['population', 'overlayPopulation'],
  ['boundaries', 'overlayBoundaries'],
];

class App {
  constructor() {
    this.datasets = new Map();
    this.panes = [];
    this.resolved = null;
    this.classification = null;
  }

  async boot() {
    maplibregl.addProtocol('pmtiles', new pmtiles.Protocol().tile);
    readHash();
    setLang(state.lang);

    const index = await (await fetch('data/datasets.json')).json();
    if (!index.datasets.length) {
      this.toast('No datasets found in data/. Run build/deploy.sh first.');
      return;
    }
    this.index = index.datasets;
    for (const entry of index.datasets) {
      this.datasets.set(entry.slug, await this.loadDataset(entry.slug));
    }
    // one analysis backs both panes here, so one vocabulary describes both; a
    // second dataset from a different analysis would need its own, resolved
    // per pane rather than shared
    const first = this.datasets.get(this.index[0].slug);
    // the wording, before any of it is rendered: the exporter's defaults, with
    // the site's own data/<slug>/text.json over the top
    await loadText(first.slug, first.indicators.text);
    this.vocab = new Vocabulary(first.indicators);
    this.themes = new Themes(first.indicators);
    // the region's design tokens, before anything is drawn
    applyStyle(first.manifest.style);

    this.applyDefaults(first);
    this.buildPanes();
    this.wireControls();
    this.measure = new MeasureTool({
      box: $('measureBox'), total: $('measureTotal'), hint: $('measureHint'),
      undo: $('mUndo'), clear: $('mClear'), done: $('mDone'),
    });
    this.dictionary = new Dictionary($('dictPanel'));
    await this.dictionary.load(first);
    this.dictionary.setExposed(
      this.vocab.families.flatMap((f) => f.columns),
    );
    this.dictionary.setDescriptions(this.vocab.descriptions);

    this.tour = new Tour(this);
    subscribe((_, reason) => this.render(reason));
    // only the panes actually on screen; each fills itself in when its style
    // loads, via onPaneReady
    await this.ensurePanes();
    this.initialCameras();
    await this.render('boot');
    this.tour.offerOnFirstVisit();
  }

  async loadDataset(slug) {
    const base = `data/${slug}`;
    const [manifest, indicators, stats] = await Promise.all(
      ['manifest.json', 'indicators.json', 'stats.json'].map(async (file) =>
        (await fetch(`${base}/${file}`)).json()),
    );
    return {
      slug, manifest, indicators, stats,
      hasNetwork: Boolean((manifest.layers || {}).network),
    };
  }

  /** Fill in anything the hash did not supply. */
  applyDefaults(dataset) {
    const manifest = dataset.manifest;
    const regions = Object.keys(manifest.regions);
    batch((s) => {
      s.panes.forEach((pane, i) => {
        pane.dataset = pane.dataset && this.datasets.has(pane.dataset)
          ? pane.dataset : dataset.slug;
        const d = this.datasets.get(pane.dataset);
        const available = Object.keys(d.manifest.regions);
        if (!pane.region || !available.includes(pane.region)) {
          // Condesa is the subject of this workshop, so it opens; Mexicali is
          // what it gets compared against
          const preferred = DEFAULT_REGIONS[i] || [];
          pane.region = preferred.find((r) => available.includes(r))
            || available[Math.min(i, available.length - 1)]
            || regions[0];
        }
        const scales = d.manifest.regions[pane.region].scales;
        if (!pane.scale || !scales.includes(pane.scale)) {
          pane.scale = (DEFAULT_SCALES[i] || [])
            .find((k) => scales.includes(k))
            || scales.find((k) => k !== 'grid')
            || scales[0];
        }
      });
      if (!BASEMAP_KEYS.includes(s.basemap)) s.basemap = 'streets';
      if (!s.shared.family || !this.vocab.family(s.shared.family)) {
        Object.assign(s.shared, this.vocab.firstSelection(this.allColumns()));
      } else {
        Object.assign(
          s.shared, this.vocab.coerce(s.shared, this.allColumns()),
        );
      }
    }, 'defaults');
  }

  /** Every column any on-screen pane could show. */
  allColumns() {
    const columns = new Set();
    for (const pane of activePanes()) {
      const dataset = this.datasets.get(pane.dataset);
      if (!dataset) continue;
      const scale = dataset.manifest.scales[pane.scale];
      for (const column of (scale || {}).columns || []) columns.add(column);
    }
    return columns;
  }

  /** The Pane objects currently on screen. */
  visiblePanes() {
    return state.compare ? this.panes : [this.panes[0]];
  }

  /**
   * Build a map for each visible pane, once it is visible.
   *
   * Deferred rather than eager because a pane hidden by `display: none` has a
   * zero-size container, and MapLibre will not finish loading a style into one
   * — so building the second pane up front left boot waiting forever.
   */
  async ensurePanes() {
    for (const pane of this.visiblePanes()) {
      const dataset = this.datasets.get(pane.config.dataset);
      if (dataset && pane.dataset !== dataset) {
        // Unhide, then wait a frame before building: MapLibre measures the
        // container when the map is constructed, and a section unhidden in the
        // same tick still has no size — which left the second pane framed on
        // the whole world rather than on its region.
        document.querySelector(`.pane[data-pane="${pane.index}"]`).hidden = false;
        await nextFrame();
        pane.setDataset(dataset);
      }
    }
  }

  /**
   * A pane's style has loaded and its layers are in.
   *
   * Frame it, then repaint — this is what draws the data, and it happens
   * whenever the style actually arrives rather than being waited on.
   */
  onPaneReady(index) {
    const pane = this.panes[index];
    pane.resize();
    if (!pane.config.view) this.fitPaneToRegion(index);
    this.render('paneReady');
  }

  buildPanes() {
    document.querySelectorAll('.pane').forEach((section, i) => {
      this.panes.push(new Pane(i, section.querySelector('.map'), this));
    });
  }

  // ---- controls -----------------------------------------------------------

  wireControls() {
    $('langSel').value = getLang();
    $('langSel').addEventListener('change', (event) => {
      update((s) => { s.lang = setLang(event.target.value); }, 'lang');
    });
    $('compareBtn').addEventListener('click', () => {
      this.setCompare(!state.compare);
    });

    // one set of layer toggles for both panes: a layer is a property of the
    // view, not of one map, and duplicating them invited the reader to think
    // the two panes might be showing different things
    const toggles = $('layerToggles');
    toggles.innerHTML = OVERLAY_UI.map(([key]) =>
      `<label><input type="checkbox" data-overlay="${key}"><span></span></label>`,
    ).join('');
    toggles.querySelectorAll('[data-overlay]').forEach((input) => {
      input.addEventListener('change', () => {
        update((s) => {
          for (const pane of s.panes) {
            pane.overlays[input.dataset.overlay] = input.checked;
          }
        }, 'overlay');
      });
    });
    $('linkViewsChk').checked = state.linkViews;
    $('linkViewsChk').addEventListener('change', (event) => {
      update((s) => { s.linkViews = event.target.checked; }, 'link');
    });
    $('matchScaleBtn').addEventListener('click', () => this.matchScale());
    $('basemapSel').addEventListener('change', (event) => {
      update((s) => { s.basemap = event.target.value; }, 'basemap');
    });
    $('settingsBtn').addEventListener('click', () => {
      const drawer = $('settingsPanel');
      drawer.hidden = !drawer.hidden;
    });
    // three steps, then back to the top
    $('panelToggle').addEventListener('click', () => {
      update((s) => { s.panel = (s.panel + 1) % 3; }, 'panel');
    });

    for (const id of ['themeSel', 'familySel', 'measureSel', 'networkSel',
      'distanceSel', 'variableSel', 'groupSel']) {
      $(id).addEventListener('change', () => this.onIndicatorChange(id));
    }
    document.querySelectorAll('.pane').forEach((section, i) => {
      section.querySelector('.datasetSel').addEventListener('change', (e) => {
        update((s) => { s.panes[i].dataset = e.target.value; }, 'dataset');
      });
      section.querySelector('.regionSel').addEventListener('change', (e) => {
        update((s) => {
          s.panes[i].region = e.target.value;
          const scales = this.datasets.get(s.panes[i].dataset)
            .manifest.regions[e.target.value].scales;
          if (!scales.includes(s.panes[i].scale)) [s.panes[i].scale] = scales;
        }, 'scale');
        this.fitPaneToRegion(i);
      });
      section.querySelector('.scaleSel').addEventListener('change', (e) => {
        update((s) => { s.panes[i].scale = e.target.value; }, 'scale');
      });
    });

    $('tourBtn').addEventListener('click', () => this.tour.start());
    $('measureBtn').addEventListener('click', () => {
      // armed on every visible pane: the first click decides which map the
      // measurement belongs to.  It used to attach to whichever pane was last
      // hovered, which in practice meant the left one always won.
      if (this.measure.active) this.measure.stop();
      else this.measure.start(this.visiblePanes());
    });
    $('dictBtn').addEventListener('click', () => {
      this.dictionary.render($('dictSearch').value);
      this.openPanel('dictPanel');
    });
    $('dictSearch').addEventListener('input', (e) =>
      this.dictionary.render(e.target.value));
    // the settings drawer is a .drawer, not an .overlay-panel: matching only
    // the latter made closest() return null and the handler throw, which is why
    // the cog's Close button did nothing at all
    document.querySelectorAll('[data-close]').forEach((button) => {
      button.addEventListener('click', () =>
        button.closest('.overlay-panel, .drawer').setAttribute('hidden', ''));
    });
    $('exportBtn').addEventListener('click', () => this.exportCurrentView());
  }

  onIndicatorChange(changed) {
    batch((s) => {
      const next = { ...s.shared };
      if (changed === 'themeSel') {
        const theme = this.themes.get($('themeSel').value);
        if (theme && theme.families.length) [next.family] = theme.families;
      }
      if (changed === 'familySel') next.family = $('familySel').value;
      if (changed === 'measureSel') next.measure = $('measureSel').value;
      if (changed === 'networkSel') next.network = $('networkSel').value;
      if (changed === 'distanceSel') next.distance = $('distanceSel').value;
      if (changed === 'variableSel') next.variable = $('variableSel').value;
      if (changed === 'groupSel') next.group = $('groupSel').value;
      Object.assign(s.shared, this.vocab.coerce(next, this.allColumns()));
      s.isolated = null;
    }, 'indicator');
  }

  /** Fill a select whose options fall into named groups. */
  fillGrouped(select, options, value) {
    const groups = [];
    for (const option of options) {
      let group = groups.find((g) => g.name === option.group);
      if (!group) groups.push(group = { name: option.group, items: [] });
      group.items.push(option);
    }
    // with everything in one group the grouping says nothing, so drop it
    select.innerHTML = groups.length < 2
      ? groups.flatMap((g) => g.items).map((o) =>
        `<option value="${o.key}"${o.disabled ? ' disabled' : ''}>${o.text}</option>`,
      ).join('')
      : groups.map((g) =>
        `<optgroup label="${g.name}">${g.items.map((o) =>
          `<option value="${o.key}"${o.disabled ? ' disabled' : ''}>${o.text}</option>`,
        ).join('')}</optgroup>`).join('');
    if (options.some((o) => o.key === value)) select.value = value;
  }

  fill(select, options, value) {
    select.innerHTML = options.map(([key, text, disabled]) =>
      `<option value="${key}"${disabled ? ' disabled' : ''}>${text}</option>`)
      .join('');
    if (options.some(([key]) => key === value)) select.value = value;
  }

  renderControls() {
    const s = state.shared;
    const available = this.allColumns();
    const family = this.vocab.family(s.family);
    const theme = family ? this.themes.forFamily(family.id) : null;

    this.fill($('themeSel'), this.themes.options(getLang()),
      theme ? theme.id : null);
    this.fill($('familySel'),
      (theme ? theme.families : []).map((id) => {
        const f = this.vocab.family(id);
        return [id, f ? label(f.label, id) : id];
      }), s.family);

    const measures = this.vocab.measuresOf(s.family);
    // a single-option dropdown is furniture: an indicator with only "Value" to
    // report has nothing for the reader to choose between
    $('measureField').hidden = measures.length < 2;
    this.fill($('measureSel'), measures.map((key) => {
      const meta = this.vocab.measureMeta[key] || {};
      const usable = this.vocab.columnsFor({ ...s, measure: key })
        .some((c) => available.has(c));
      return [
        key,
        label(measureLabelFor(key, meta.label), key),
        !usable && key !== s.measure,
      ];
    }), s.measure);

    const networks = this.vocab.networksOf(s.family, s.measure);
    // grouped by mode rather than prefixed: an <optgroup> says "these are the
    // cycling ones" once, where a prefix says it on every line
    this.fillGrouped($('networkSel'), networks.map((key) => {
      const meta = this.vocab.networks[key] || {};
      const usable = this.vocab.columnsFor({ ...s, network: key })
        .some((c) => available.has(c));
      return {
        key,
        text: label(meta.label, key),
        group: meta.mode === 'cycle' ? t('cycling') : t('walking'),
        disabled: !usable && key !== s.network,
      };
    }), s.network);

    const distances = this.vocab.distancesOf(s.family, s.measure, s.network);
    // Live for access too, now that the map is drawn from one distance rather
    // than from all of them at once.  The travel time rides along here, where
    // it is chosen, instead of taking a column of the legend.
    $('distanceField').hidden = distances.length < 2;
    this.fill($('distanceSel'), distances.map((d) => {
      const minutes = travelMinutes(Number(d), s.network);
      return [d, minutes ? `${d} m (~${minutes} min)` : `${d} m`];
    }), this.resolved ? this.resolved.distance : s.distance);

    const variables = this.vocab.variablesOf(s.family);
    $('variableField').hidden = !variables.length;
    this.fill($('variableSel'), variables.map((v) =>
      [v, this.vocab.variableLabel(v)]), s.variable);

    const groups = this.vocab.groupsOf(s.family);
    $('groupField').hidden = !(groups.length && s.measure === 'count');
    this.fill($('groupSel'), groups.map((g) =>
      [g, g.replace(/_/g, ' ')]), s.group);

    // a network picker with one option is a control that cannot be used
    $('networkField').hidden = networks.length < 2;
    $('compareTools').hidden = !state.compare;

  }

  renderPaneControls() {
    document.querySelectorAll('.pane').forEach((section, i) => {
      const pane = state.panes[i];
      const dataset = this.datasets.get(pane.dataset);
      if (!dataset) return;
      const manifest = dataset.manifest;
      // a dropdown with one entry is furniture: the region selector below is
      // what actually identifies this pane
      section.querySelector('.datasetField').hidden = this.index.length < 2;
      this.fill(section.querySelector('.datasetSel'),
        this.index.map((d) => [d.slug, label(d.label, d.slug)]), pane.dataset);
      this.fill(section.querySelector('.regionSel'),
        Object.entries(manifest.regions).map(([key, region]) =>
          [key, label(region.label, key)]), pane.region);
      const scales = manifest.regions[pane.region].scales;
      this.fill(section.querySelector('.scaleSel'), scales.map((key) =>
        [key, label((manifest.scales[key] || {}).label, key)]), pane.scale);

    });
  }

  /** The shared layer toggles, labelled from the string table. */
  renderLayerToggles() {
    const toggles = $('layerToggles');
    const pane = state.panes[0];
    OVERLAY_UI.forEach(([key, stringKey]) => {
      const input = toggles.querySelector(`[data-overlay="${key}"]`);
      if (!input) return;
      input.checked = Boolean(pane.overlays[key]);
      input.nextElementSibling.textContent = t(stringKey);
      input.closest('label').title = t(`${stringKey}Help`);
    });
  }

  // ---- rendering ----------------------------------------------------------

  async render(reason) {
    // render awaits style rebuilds, so two rapid state changes could interleave
    // and leave the later one's layers behind the earlier one's paint.  Queue
    // instead: the last reason wins, which is what the user just asked for.
    if (this.rendering) {
      this.pendingReason = reason;
      return;
    }
    this.rendering = true;
    try {
      let next = reason;
      let passes = 0;
      while (next) {
        // A repaint that queues another repaint is a feedback loop, and a
        // silent one locks the page up with no clue why.  Camera and focus
        // changes are recorded silently for exactly this reason; if something
        // starts looping again, this says which reason is driving it.
        passes += 1;
        if (passes > 20) {
          console.warn(`render loop detected, last reason: ${next}`);
          break;
        }
        this.pendingReason = null;
        await this.renderOnce(next);
        next = this.pendingReason;
      }
    } finally {
      this.rendering = false;
      this.pendingReason = null;
    }
  }

  async renderOnce(reason) {
    document.body.classList.toggle('single', !state.compare);
    for (let i = 0; i < 3; i += 1) {
      document.body.classList.toggle(`panel-${i}`, state.panel === i);
    }
    document.querySelector('.pane[data-pane="1"]').hidden = !state.compare;
    this.applyStaticText();
    // give the browser a frame to lay the pane out before a map is built into
    // it, so MapLibre measures a container that has its size
    await nextFrame();

    await this.ensurePanes();
    // only a dataset change rebuilds the style; a basemap change is a layer
    // visibility toggle, applied in pane.render()
    if (reason === 'dataset') {
      for (const pane of this.visiblePanes()) pane.applyStyle();
    }

    this.resolved = this.vocab.resolve(state.shared);
    // A banded measure falls back to its shortest distance when the selection
    // names none.  Record that silently, so the hash, the exported caption and
    // the outlined table column all agree with the map -- and so that changing
    // indicator does not quietly reset a distance the reader chose.
    if (this.resolved && this.resolved.distance
        && this.resolved.distance !== state.shared.distance) {
      updateSilent((s) => { s.shared.distance = this.resolved.distance; });
    }
    const panes = activePanes();
    const statsEntries = panes.map((pane, i) => {
      const dataset = this.datasets.get(pane.dataset);
      return dataset ? dataset.stats[pane.scale] : null;
    });
    // one classification for both panes, straight from the export: see
    // choropleth.js on why nothing is derived here
    this.classification = this.resolved
      ? classify(
        this.resolved,
        this.vocab.breaksFor(this.resolved),
        this.vocab.targetFor(this.resolved),
      )
      : null;

    this.renderControls();
    this.renderPaneControls();

    for (let i = 0; i < this.panes.length; i += 1) {
      const pane = this.panes[i];
      if (!pane.ready || (!state.compare && i > 0)) continue;
      const dataset = this.datasets.get(state.panes[i].dataset);
      pane.setScale(state.panes[i].scale);
      const entry = dataset ? dataset.stats[state.panes[i].scale] : null;
      pane.render(this.resolved, this.classification, entry);
      // resizing moves the camera and emits moveend, so only do it when the
      // pane geometry can actually have changed
      if (LAYOUT_REASONS.has(reason)) pane.resize();
    }

    // one legend, one results table, one chart: all of them describe the
    // shared indicator, so all of them live in the sidebar
    renderLegend($('legend'), this.resolved, this.classification);
    renderLtsLegend($('ltsLegend'), state.panes[0].overlays.network);
    const datasets = panes.map((pane) => this.datasets.get(pane.dataset));
    renderResults(
      $('results'), this.resolved, panes, datasets, statsEntries,
    );
    renderDistribution(
      $('histo'), this.resolved, this.classification, panes, datasets,
      statsEntries,
    );
    this.renderLayerToggles();
    this.renderPanelToggle();
    this.fill(
      $('basemapSel'),
      BASEMAP_KEYS.map((key) => [key, t(key === 'none' ? 'none' : key)]),
      state.basemap,
    );
    const first = this.datasets.get(state.panes[0].dataset);
    if (first) {
      const title = label(first.manifest.title || first.manifest.label, '');
      $('appTitle').textContent = title;
      document.title = title;
      const theme = this.resolved
        ? this.themes.forFamily(this.resolved.family.id) : null;
      renderShowing(
        $('showing'), this.resolved, this.vocab, getLang(), theme,
        () => this.openPanel('infoPanel'),
      );
      renderInfo(
        $('infoBody'), this.resolved, this.vocab, first, activePanes(),
        this.themes, first.indicators.rules,
      );
    }
  }

  applyStaticText() {
    document.querySelectorAll('[data-s]').forEach((node) => {
      node.textContent = t(node.dataset.s);
    });
    $('compareBtn').classList.toggle('on', state.compare);
    document.documentElement.lang = getLang();
    $('dictSearch').placeholder = `${t('search')}…`;
  }

  initialCameras() {
    this.panes.forEach((pane, i) => {
      const config = state.panes[i];
      if (config.view) pane.applyView(config.view);
      else this.fitPaneToRegion(i);
    });
  }

  fitPaneToRegion(index) {
    const pane = this.panes[index];
    const config = state.panes[index];
    const dataset = this.datasets.get(config.dataset);
    if (!pane || !dataset) return;
    const region = dataset.manifest.regions[config.region] || {};
    pane.fitTo(region.bbox || dataset.manifest.bbox);
  }

  /** Same zoom on both panes, so a distance on screen means the same thing. */
  matchScale() {
    if (!state.compare) return;
    const source = this.panes[state.focus] || this.panes[0];
    const zoom = source.map.getZoom();
    for (const pane of this.panes) {
      if (pane === source || !pane.map) continue;
      pane.withoutMoveEvents(() => pane.map.setZoom(zoom));
    }
  }

  onPaneMoved(index) {
    if (!state.linkViews || !state.compare) return;
    const source = this.panes[index];
    const center = source.map.getCenter();
    for (const pane of this.panes) {
      if (pane === source || !pane.map) continue;
      pane.applyView({
        zoom: source.map.getZoom(), lat: center.lat, lng: center.lng,
      });
    }
  }

  /** Turn the comparison view on or off (used by the tour). */
  setCompare(on) {
    if (state.compare === on) return;
    update((s) => { s.compare = on; }, 'layout');
  }

  /** Turn a supporting layer on or off across both panes (used by the tour). */
  setOverlay(index, key, on) {
    if (state.panes[0].overlays[key] === on) return;
    update((s) => {
      for (const pane of s.panes) pane.overlays[key] = on;
    }, 'overlay');
  }

  measureActive(index) {
    return this.measure && this.measure.isActive(this.panes[index].map);
  }

  openPanel(id) {
    document.querySelectorAll('.overlay-panel').forEach((panel) =>
      panel.setAttribute('hidden', ''));
    $(id).removeAttribute('hidden');
  }

  /** The collapse control's tooltip follows what it will do next. */
  renderPanelToggle() {
    const button = $('panelToggle');
    button.textContent = state.panel === 2 ? '⭳' : '⭱';
    button.title = t(['collapsePanel', 'collapseFurther', 'expandPanel'][state.panel]);
  }

  async exportCurrentView() {
    const panes = state.compare ? this.panes : [this.panes[0]];
    const message = await exportImage({
      panes,
      datasets: panes.map((pane) => this.datasets.get(pane.config.dataset)),
      resolved: this.resolved,
      classification: this.classification,
      vocab: this.vocab,
      filename: `${state.shared.family}_${state.shared.measure}.png`,
    });
    if (message) this.toast(message);
  }

  toast(message) {
    const node = $('toast');
    node.textContent = message;
    node.hidden = false;
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => { node.hidden = true; }, 5000);
  }
}

const app = new App();
// exposed deliberately: this is a demonstration tool, and being able to poke at
// the state and the maps from the console is worth more here than hiding them
window.dashboard = app;
app.boot().catch((error) => {
  const node = $('toast');
  node.textContent = String(error && error.message ? error.message : error);
  node.hidden = false;
  throw error;
});
