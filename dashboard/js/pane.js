// One map pane: its MapLibre instance, its style, and the layers it draws.
//
// A pane owns a dataset, a region, an aggregation scale and its own camera.
// It does not own the indicator — that is shared, so that the two panes always
// answer the same question — and it reads everything else from `state`.

import { hideSurface, showSurface, surfaceImage } from './smooth.js';
import {
  choroplethPaint, ltsPaint, LTS_COLORS, NO_DATA,
} from './choropleth.js';
import { renderPopulationLegend } from './legend.js';
import { state, update, updateSilent } from './state.js';
import { integer, label, number, t } from './strings.js';

const BASEMAPS = {
  streets: {
    // Esri World Light Gray Canvas: CARTO's light_all tiles now carry an "API
    // KEY REQUIRED" watermark without a key.  This one needs none, sends CORS
    // headers (so the image export can read the canvas), and is as quiet under
    // a choropleth.
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    ],
    attribution: 'Esri, HERE, Garmin, © OpenStreetMap contributors',
    maxzoom: 16,
  },
  satellite: {
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    ],
    attribution: 'Esri, Maxar, Earthstar Geographics',
  },
  // No basemap at all: raster tiles need the internet, and a workshop room may
  // not have it.  The indicator layers still render, on a plain ground.
  none: { tiles: null, attribution: '', background: '#f4f1ec' },
};

// Context layers drawn as points or lines, coloured so that a destination set
// stays distinguishable from the network beneath it.
const OVERLAY_STYLE = {
  destinations: { color: '#d94801', radius: 4 },
  default: { color: '#6a51a3', radius: 3.5 },
};

// The outline of the area a composite index profile is describing.
const SELECTED_PAINT = { 'line-color': '#1b1b1b', 'line-width': 3 };
const NOTHING_SELECTED = ['==', ['get', 'area_id'], '__none__'];

export class Pane {
  constructor(index, container, app) {
    this.index = index;
    this.app = app;
    this.container = container;
    this.map = null;
    this.dataset = null;
    this.scaleSources = new Set();
    this.ready = false;
  }

  get config() {
    return state.panes[this.index];
  }

  /**
   * Build (or rebuild) the map for this pane's dataset.
   *
   * Deliberately does **not** await the style. MapLibre parses a style inside a
   * requestAnimationFrame, and a hidden or background tab never paints, so
   * awaiting it there hangs forever — and an awaited hang during boot freezes
   * the whole app with nothing on screen. Instead the pane reports itself ready
   * when its style arrives, and the app repaints then.
   */
  setDataset(dataset) {
    const changed = !this.dataset || this.dataset.slug !== dataset.slug;
    this.dataset = dataset;
    if (!this.map) {
      this.createMap(this.styleFor());
      this.whenStyleReady().then(() => this.installLayers());
      return;
    }
    if (changed) this.applyStyle();
  }

  createMap(style) {
    this.map = new maplibregl.Map({
      container: this.container,
      style,
      center: [0, 0],
      zoom: 2,
      // each map states where its basemap came from, as the validation site
      // does; the indicator's own sources live behind the sidebar's `i`
      attributionControl: { compact: true },
      // required for the map image export: without it the drawing buffer is
      // cleared after each frame and getCanvas() reads back blank
      preserveDrawingBuffer: true,
    });
    this.map.addControl(new maplibregl.NavigationControl({ showCompass: false }));
    // bottom-right, stacked over the attribution: at bottom-left the first
    // pane's scale bar sits behind the floating toolbar and the button bar, and
    // a scale bar you cannot see is a scale bar you have lost
    this.map.addControl(
      new maplibregl.ScaleControl({ maxWidth: 120, unit: 'metric' }),
      'bottom-right',
    );
    this.map.on('moveend', () => {
      if (this.suppressMove) return;
      const center = this.map.getCenter();
      // silent: the camera is worth recording in the hash, but nothing on
      // screen is derived from it, and repainting here would loop back through
      // resize() into another moveend
      updateSilent((s) => {
        s.panes[this.index].view = {
          zoom: this.map.getZoom(), lat: center.lat, lng: center.lng,
        };
      });
      this.app.onPaneMoved(this.index);
    });
    this.armStyleReady();
    this.map.on('click', (event) => this.onClick(event));
    this.map.getContainer().addEventListener('mouseenter', () => {
      updateSilent((s) => { s.focus = this.index; });
    });
  }

  /**
   * The style, with every basemap declared at once.
   *
   * Switching basemap used to rebuild the whole style. MapLibre's `setStyle`
   * diffs by default, and a diff that succeeds applies in place **without
   * firing `style.load`** — so the promise waiting on that event never settled,
   * the render loop held its lock, and the pane froze with no console error.
   * Declaring all three up front makes a basemap change a visibility toggle:
   * instant, and it never touches the vector layers or the camera.
   */
  styleFor() {
    const slug = this.dataset.slug;
    const base = `data/${slug}/${slug}`;
    const url = (name) =>
      `pmtiles://${new URL(`${base}_${name}.pmtiles`, window.location.href).href}`;
    const sources = { context: { type: 'vector', url: url('context') } };
    for (const [key, basemap] of Object.entries(BASEMAPS)) {
      if (!basemap.tiles) continue;
      sources[`basemap-${key}`] = {
        type: 'raster', tiles: basemap.tiles, tileSize: 256,
        attribution: basemap.attribution,
        // beyond its last level a basemap is overzoomed, not requested
        ...(basemap.maxzoom ? { maxzoom: basemap.maxzoom } : {}),
      };
    }
    if (this.dataset.hasNetwork) {
      sources.network = { type: 'vector', url: url('network') };
    }
    // one archive per scale and tile group of columns, or per scale for an
    // export from before tile groups
    for (const key of Object.keys(this.dataset.manifest.scales)) {
      for (const name of this.sourcesOf(key)) {
        sources[name] = { type: 'vector', url: url(name) };
      }
    }
    // no glyphs URL: nothing here is a symbol layer, and pointing at a font
    // server would be one more thing to fail in a room without wifi
    return {
      version: 8,
      sources,
      layers: [
        // the plain ground sits under every raster, so "no basemap" is simply
        // all rasters hidden
        {
          id: 'basemap-none',
          type: 'background',
          paint: { 'background-color': BASEMAPS.none.background },
        },
        ...Object.keys(BASEMAPS)
          .filter((key) => BASEMAPS[key].tiles)
          .map((key) => ({
            id: `basemap-${key}`,
            type: 'raster',
            source: `basemap-${key}`,
            layout: { visibility: 'none' },
          })),
      ],
    };
  }

  /** Show one basemap and hide the others. */
  setBasemap(key) {
    const map = this.map;
    if (!map || !map.getLayer('basemap-none')) return;
    for (const name of Object.keys(BASEMAPS)) {
      const id = `basemap-${name}`;
      if (name !== 'none' && map.getLayer(id)) {
        map.setLayoutProperty(id, 'visibility', name === key ? 'visible' : 'none');
      }
    }
  }

  /**
   * Arm a promise that settles when the style becomes loadable.
   *
   * The listener is registered before the style starts loading, because the
   * event cannot be recovered afterwards. `addLayer` requires only that the
   * style spec has been parsed — which is exactly what `style.load` reports.
   *
   * Not `isStyleLoaded()`, and not the `load` event: both of those also wait
   * for the first screenful of tiles, including the raster basemap, so with no
   * internet they never come true. And not `getStyle()`, which returns the
   * pending style before it is loadable and so let layers be added too early.
   */
  armStyleReady() {
    const map = this.map;
    this.styleReady = new Promise((resolve) => {
      // A style that never loads would otherwise hang with nothing on screen
      // and nothing in the console. MapLibre parses the style inside a
      // requestAnimationFrame, so a tab that is never displayed never gets
      // there — worth saying out loud rather than looking broken.
      // The warning does not resolve the promise: proceeding without a loaded
      // style guarantees an exception from addLayer, which is worse than
      // waiting. Say what is wrong, and carry on waiting for the event.
      const timer = setTimeout(() => {
        console.warn(
          `pane ${this.index}: style not loaded after 15s. If this page is in a `
          + 'hidden or background tab, MapLibre parses the style inside a '
          + 'requestAnimationFrame and will not get there until it is shown.',
        );
        this.setNotice(t('styleSlow'));
      }, 15000);
      map.once('style.load', () => {
        clearTimeout(timer);
        this.setNotice('');
        resolve();
      });
    });
  }

  whenStyleReady() {
    return this.styleReady || Promise.resolve();
  }

  /**
   * Rebuild the style for a new dataset.
   *
   * Only ever called when the dataset changes.  A basemap change must not come
   * through here: `setStyle` would diff rather than reload, `style.load` would
   * never fire, and the await below would never return.
   */
  applyStyle() {
    // armed before setStyle, so the event cannot fire before we are listening
    this.armStyleReady();
    this.map.setStyle(this.styleFor());
    return this.whenStyleReady().then(() => this.installLayers());
  }

  installLayers() {
    try {
      this.addLayers();
    } catch (error) {
      // a layer that cannot be added leaves a blank map, which reads as "no
      // data here"; say so instead
      console.error(`pane ${this.index}: could not add layers`, error);
      this.setNotice(String(error && error.message ? error.message : error));
    }
    // addLayers points the choropleth at the grid's first archive
    this.currentSource = this.sourceFor('grid');
    // a new style has no smoothed surface yet
    this.smoothKey = null;
    this.wireHover();
    this.ready = true;
    // the app has already drawn its controls; this is what fills in the map
    if (this.app.onPaneReady) this.app.onPaneReady(this.index);
  }

  addLayers() {
    const map = this.map;
    const manifest = this.dataset.manifest;

    // the population grid sits under the choropleth: it is context for how the
    // aggregation was weighted, not a competing result
    const grid = this.sourceFor('grid');
    if (manifest.scales.grid) {
      map.addLayer({
        id: 'population', type: 'fill', source: grid,
        'source-layer': grid, layout: { visibility: 'none' },
        paint: {
          'fill-color': [
            'interpolate', ['linear'], ['coalesce', ['get', 'pop_est'], 0],
            0, 'rgba(0,0,0,0)', 25, '#f3e6d8', 100, '#dba368', 250, '#a1591f',
          ],
          'fill-opacity': 0.75,
        },
      });
    }

    map.addLayer({
      id: 'choropleth', type: 'fill', source: grid,
      'source-layer': grid,
      paint: { 'fill-color': NO_DATA, 'fill-opacity': 0.7 },
    });
    map.addLayer({
      id: 'choropleth-outline', type: 'line', source: grid,
      'source-layer': grid,
      paint: {
        'line-color': 'rgba(60,55,50,0.35)',
        'line-width': ['interpolate', ['linear'], ['zoom'], 11, 0.1, 16, 0.7],
      },
    });
    map.addLayer({
      id: 'choropleth-selected', type: 'line', source: grid,
      'source-layer': grid, filter: NOTHING_SELECTED,
      paint: SELECTED_PAINT,
    });

    if (this.dataset.hasNetwork) {
      map.addLayer({
        id: 'network', type: 'line', source: 'network',
        'source-layer': 'network', layout: {
          visibility: 'none', 'line-cap': 'round', 'line-join': 'round',
        },
        paint: {
          ...ltsPaint(null),
          'line-width': ['interpolate', ['linear'], ['zoom'], 10, 0.4, 16, 2.5],
        },
      });
    }

    for (const [name, layer] of Object.entries(manifest.layers || {})) {
      if (name === 'network') continue;
      if (name === 'boundary' || name === 'buffer') {
        map.addLayer({
          id: `boundary-${name}`, type: 'line', source: 'context',
          'source-layer': name, layout: { visibility: 'none' },
          paint: {
            'line-color': name === 'boundary' ? '#2b2b2b' : '#7a7a7a',
            'line-width': name === 'boundary' ? 1.8 : 1,
            'line-dasharray': name === 'boundary' ? [1, 0] : [3, 2],
          },
        });
        continue;
      }
      const style = OVERLAY_STYLE[name] || OVERLAY_STYLE.default;
      // the exporter records each layer's real geometry type: the open space
      // "..._nodes_30m_line" layers are points despite their name, so guessing
      // from the name would draw them as invisible zero-length lines
      const isLine = layer.geometry === 'line';
      map.addLayer(
        isLine
          ? {
            id: `overlay-${name}`, type: 'line', source: 'context',
            'source-layer': name, layout: { visibility: 'none' },
            paint: { 'line-color': style.color, 'line-width': 2.5 },
          }
          : {
            id: `overlay-${name}`, type: 'circle', source: 'context',
            'source-layer': name, layout: { visibility: 'none' },
            paint: {
              'circle-color': style.color,
              'circle-stroke-color': '#ffffff',
              'circle-stroke-width': 0.8,
              'circle-radius': [
                'interpolate', ['linear'], ['zoom'],
                9, style.radius * 0.5, 14, style.radius, 17, style.radius * 2,
              ],
            },
          },
      );
    }
    // region outlines, so a pane always shows which region it is looking at
    for (const key of Object.keys(manifest.regions || {})) {
      const region = manifest.regions[key];
      if (!region.summary_scale || !manifest.scales[region.summary_scale]) continue;
      const source = this.sourceFor(region.summary_scale);
      map.addLayer({
        id: `region-${key}`, type: 'line', source,
        'source-layer': source,
        layout: { visibility: 'none' },
        paint: { 'line-color': '#1b1b1b', 'line-width': 2 },
      });
    }
  }

  /**
   * Hover tooltips on the point and network layers, with a pointer cursor.
   *
   * Ported from the validation site: a destination that cannot be identified
   * without clicking it is a dot, and a map of dots explains nothing.
   */
  wireHover() {
    const map = this.map;
    const tip = document.getElementById('hoverTip');
    if (!tip) return;
    const show = (html, event) => {
      map.getCanvas().style.cursor = 'pointer';
      tip.innerHTML = html;
      tip.style.left = `${event.originalEvent.clientX + 14}px`;
      tip.style.top = `${event.originalEvent.clientY + 10}px`;
      tip.style.display = 'block';
    };
    const hide = () => {
      map.getCanvas().style.cursor = '';
      tip.style.display = 'none';
    };
    this.hoverLayers = [];
    for (const name of Object.keys(this.dataset.manifest.layers || {})) {
      const id = name === 'network' ? 'network' : `overlay-${name}`;
      if (!map.getLayer(id)) continue;
      this.hoverLayers.push(id);
      map.on('mousemove', id, (event) => {
        if (!event.features.length) return;
        show(this.hoverHTML(id, event.features[0].properties), event);
      });
      map.on('mouseleave', id, hide);
    }
  }

  hoverHTML(layerId, p) {
    if (layerId === 'network') {
      const bits = [
        p.highway,
        p.lvl_traf_stress ? `LTS ${p.lvl_traf_stress}` : null,
        p.maxspeed_kmh ? `${p.maxspeed_kmh} km/h` : null,
      ].filter(Boolean).join(' · ');
      return `<b>${p.name || t('networkLayer')}</b>${bits ? `<br>${bits}` : ''}`;
    }
    if (layerId === 'overlay-destinations') {
      return `<b>${p.dest_name_full || p.dest_name || ''}</b>`;
    }
    // the open-space and activity-centre layers are entry points rather than
    // named places, so the layer's own label is the useful thing to say
    const name = layerId.replace('overlay-', '');
    const family = (this.app.vocab.families || []).find(
      (f) => f.overlay && f.overlay.layer === name,
    );
    const heading = family ? label(family.label, name) : name.replace(/_/g, ' ');
    const extra = p.aos_ha ? `<br>${p.aos_ha} ha` : '';
    return `<b>${heading}</b>${extra}`;
  }

  /** The archives (sources) a scale is tiled as. */
  sourcesOf(scaleKey) {
    const entry = this.dataset.manifest.scales[scaleKey] || {};
    const tiles = Object.values(entry.tiles || {});
    return tiles.length ? tiles.map((tile) => tile.layer) : [`scale_${scaleKey}`];
  }

  /**
   * The archive of a scale holding a column, which is also its layer's name.
   *
   * The exporter tiles each scale in groups of columns, so that no feature
   * carries so many values that the zoomed out tiles must drop it; the group
   * a column is in is recorded in indicators.json.  Every archive holds the
   * area ids and context columns (population), so any will do for those.
   */
  sourceFor(scaleKey, column = null) {
    const entry = this.dataset.manifest.scales[scaleKey] || {};
    const tiles = entry.tiles || {};
    const groups = Object.keys(tiles);
    if (!groups.length) return `scale_${scaleKey}`;
    const group = ((this.dataset.indicators || {}).column_group || {})[column];
    return tiles[group && tiles[group] ? group : groups[0]].layer;
  }

  /** Point the choropleth at the pane's current scale, and the column's archive. */
  setScale(scaleKey, column = null) {
    const map = this.map;
    if (!map || !map.getLayer('choropleth')) return;
    const source = this.sourceFor(scaleKey, column);
    if (!map.getSource(source)) return;
    // MapLibre cannot re-point a layer at another source, so changing scale
    // (or the archive a column is in) means replacing the layer.  Only do it
    // when the source actually changed.
    if (this.currentSource === source) return;
    this.currentSource = source;
    for (const id of ['choropleth', 'choropleth-outline', 'choropleth-selected']) {
      // order matters: the replacement must go back beneath the overlays
      const before = this.firstOverlayId();
      const existing = map.getLayer(id);
      const definition = {
        id,
        type: existing.type,
        source,
        'source-layer': source,
        paint: {},
      };
      let paint = id === 'choropleth'
        ? { 'fill-color': NO_DATA, 'fill-opacity': 0.7 }
        : {
          'line-color': 'rgba(60,55,50,0.35)',
          'line-width': ['interpolate', ['linear'], ['zoom'], 11, 0.1, 16, 0.7],
        };
      if (id === 'choropleth-selected') {
        paint = SELECTED_PAINT;
        definition.filter = NOTHING_SELECTED;
      }
      map.removeLayer(id);
      map.addLayer({ ...definition, paint }, before);
    }
  }

  /**
   * Draw a regular grid as a smooth surface, where the pane asks for one.
   *
   * The cells stay on the map, transparent, so an area can still be clicked;
   * the image is recomputed only when what it shows has changed.
   */
  renderSmooth(resolved, classification, drawable) {
    const map = this.map;
    const raster = (this.dataset.manifest.scales[this.config.scale] || {}).raster;
    const on = Boolean(this.config.overlays.smooth && raster && drawable
      && resolved && classification && classification.kind === 'classes');
    if (!on) {
      hideSurface(map);
      return;
    }
    map.setPaintProperty('choropleth', 'fill-opacity', 0);
    map.setLayoutProperty('choropleth-outline', 'visibility', 'none');
    // a score computed from custom weights is computed here too, cell by cell
    const uli = this.app.uli;
    const computed = uli && String(resolved.column).startsWith('~')
      ? (props) => {
        const out = uli.values(props);
        return out ? out[resolved.column] : null;
      }
      : null;
    const inputs = computed ? resolved.columns : [resolved.column];
    const key = JSON.stringify([
      this.dataset.slug, this.config.scale, resolved.column, inputs,
      classification.classes.map((c) => [c.min, c.max, c.color]),
      state.isolated, computed ? state.uli : null,
    ]);
    if (key === this.smoothKey) {
      if (map.getLayer('smooth')) map.setLayoutProperty('smooth', 'visibility', 'visible');
      return;
    }
    this.smoothKey = key;
    this.smoothToken = (this.smoothToken || 0) + 1;
    const token = this.smoothToken;
    surfaceImage({
      dataset: this.dataset,
      raster,
      classification,
      column: resolved.column,
      inputs,
      computed,
      isolated: state.isolated,
    }).then((url) => {
      // a later request has superseded this one, or the reader turned it off
      if (token !== this.smoothToken || !url || !this.config.overlays.smooth) return;
      showSurface(map, url, raster.corners);
    }).catch((error) => {
      this.smoothKey = null;
      console.warn('smooth surface', error);
    });
  }

  firstOverlayId() {
    const ids = this.map.getStyle().layers.map((l) => l.id);
    return ids.find((id) => id.startsWith('overlay-') || id === 'network');
  }

  /** Repaint everything that depends on the shared indicator or the pane. */
  render(resolved, classification, statsEntry) {
    if (!this.ready || !this.map) return;
    const map = this.map;
    const config = this.config;

    if (map.getLayer('choropleth')) {
      const available = new Set(
        (this.dataset.manifest.scales[config.scale] || {}).columns || [],
      );
      const usable =
        resolved && resolved.columns.every((c) => available.has(c));
      const paint = usable
        ? choroplethPaint(classification, state.isolated)
        : { 'fill-color': NO_DATA, 'fill-opacity': 0.35 };
      for (const [property, value] of Object.entries(paint)) {
        map.setPaintProperty('choropleth', property, value);
      }
      // turning the choropleth off is what makes the population grid beneath
      // it visible; without that the population overlay looks broken
      const showFill = config.overlays.choropleth !== false;
      for (const id of ['choropleth', 'choropleth-outline']) {
        if (map.getLayer(id)) {
          map.setLayoutProperty(
            id, 'visibility', showFill ? 'visible' : 'none',
          );
        }
      }
      this.setNotice(usable && showFill ? '' : (usable ? '' : t('notAvailable')));
      this.renderSmooth(resolved, classification, usable && showFill);
    }
    // outline the area the profile is describing, on the pane it was chosen in
    if (map.getLayer('choropleth-selected')) {
      const selected = state.selected;
      const mine = selected && selected.pane === this.index
        && selected.scale === config.scale;
      map.setFilter(
        'choropleth-selected',
        mine ? ['==', ['get', 'area_id'], selected.id] : NOTHING_SELECTED,
      );
    }

    this.setBasemap(state.basemap);
    const overlays = config.overlays;
    if (map.getLayer('population')) {
      map.setLayoutProperty(
        'population', 'visibility', overlays.population ? 'visible' : 'none',
      );
    }
    if (map.getLayer('network')) {
      map.setLayoutProperty(
        'network', 'visibility', overlays.network ? 'visible' : 'none',
      );
      const paint = ltsPaint(state.isolated);
      for (const [property, value] of Object.entries(paint)) {
        map.setPaintProperty('network', property, value);
      }
    }
    this.renderIndicatorOverlay(resolved, overlays.destinations);
    for (const id of ['boundary-boundary', 'boundary-buffer']) {
      if (map.getLayer(id)) {
        map.setLayoutProperty(
          id, 'visibility',
          overlays.boundaries && id === 'boundary-boundary' ? 'visible' : 'none',
        );
      }
    }
    for (const key of Object.keys(this.dataset.manifest.regions || {})) {
      const id = `region-${key}`;
      if (map.getLayer(id)) {
        map.setLayoutProperty(
          id, 'visibility',
          overlays.boundaries && key === config.region ? 'visible' : 'none',
        );
      }
    }
    this.renderLegends();
    this.statsEntry = statsEntry;
  }

  /**
   * Show the destination points the selected indicator was measured to.
   *
   * The mapping is read from the indicator's own overlay spec rather than from
   * a hand-written table, so a blue-space indicator shows blue-space entries
   * and a pharmacy indicator shows pharmacies, without either being enumerated
   * here.
   */
  renderIndicatorOverlay(resolved, visible) {
    const map = this.map;
    const wanted = visible && resolved && resolved.overlay
      ? resolved.overlay
      : null;
    for (const name of Object.keys(this.dataset.manifest.layers || {})) {
      const id = `overlay-${name}`;
      if (!map.getLayer(id)) continue;
      const on = wanted && wanted.layer === name;
      map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none');
      if (on && name === 'destinations') {
        map.setFilter(id, wanted.dest_names && wanted.dest_names.length
          ? ['match', ['get', 'dest_name'], wanted.dest_names, true, false]
          : null);
      }
      if (on && state.isolated) {
        const property = map.getLayer(id).type === 'line'
          ? 'line-opacity' : 'circle-opacity';
        map.setPaintProperty(id, property, 0.3);
      } else if (on) {
        const property = map.getLayer(id).type === 'line'
          ? 'line-opacity' : 'circle-opacity';
        map.setPaintProperty(id, property, 1);
      }
    }
  }

  /**
   * Only the population legend stays on the map.
   *
   * The indicator legend and the traffic-stress legend describe the shared
   * indicator, so they belong in the sidebar, drawn once. The population grid
   * is a per-pane overlay, so its key stays with it.
   */
  renderLegends() {
    const pop = this.container.parentElement.querySelector('.pop-legend');
    if (pop) renderPopulationLegend(pop, this.config.overlays.population);
  }

  setNotice(text) {
    const node = this.container.parentElement.querySelector('.pane-notice');
    if (!node) return;
    node.textContent = text;
    node.hidden = !text;
  }

  onClick(event) {
    if (this.app.measureActive(this.index)) return;
    const layers = ['choropleth', 'network'].filter((id) =>
      this.map.getLayer(id));
    const features = this.map.queryRenderedFeatures(event.point, { layers });
    if (!features.length) return;
    // With a composite index showing, clicking an area makes it the subject of
    // the profile in the sidebar rather than opening a popup over the map: the
    // profile is the fuller answer to "what is this area like".
    const area = features.find((f) => f.layer.id === 'choropleth');
    if (area && this.app.resolved && this.app.resolved.composite) {
      this.app.selectArea(this.index, area);
      return;
    }
    const feature = features[0];
    const html = feature.layer.id === 'network'
      ? this.networkPopup(feature)
      : this.areaPopup(feature);
    new maplibregl.Popup({ closeButton: true, maxWidth: '320px' })
      .setLngLat(event.lngLat)
      .setHTML(html)
      .addTo(this.map);
  }

  /**
   * The popup for one area.
   *
   * Row labels are composed in the active language from parts that are already
   * translated — the measure and its band — rather than taken from the data
   * dictionary, whose prose is English only. The dictionary sentence is kept as
   * the row's tooltip, which is where a long English definition belongs.
   */
  areaPopup(feature) {
    const resolved = this.app.resolved;
    const properties = feature.properties || {};
    const rows = [];
    if (resolved) {
      const measure = label(resolved.measure.label, resolved.measureKey);
      resolved.columns.forEach((column, i) => {
        const value = properties[column];
        const described = this.app.vocab.description(column) || {};
        const band = resolved.bands[i];
        const heading = band ? `${measure} · ${band} m` : measure;
        rows.push(
          `<tr title="${(described.en || '').replace(/"/g, '&quot;')}">
            <th>${heading}</th>
            <td>${this.formatValue(value, resolved, properties, column)}</td></tr>`,
        );
      });
    }
    const scale = this.dataset.manifest.scales[this.config.scale] || {};
    // a scale weighted by a literal figure rather than a count carries an
    // assumption, and a population read off the map should say so
    const assumed = Number.isFinite(Number(scale.weight))
      ? t('assumedPopulation').replace('{n}', scale.weight) : '';
    for (const [column, key, digits] of [
      ['pop_est', 'populationEstimate', 0],
      ['area_sqkm', 'areaKm2', 2],
    ]) {
      if (properties[column] !== undefined && properties[column] !== null) {
        rows.push(`<tr><th>${t(key)}</th>
          <td>${number(Number(properties[column]), digits)}</td></tr>`);
      }
    }
    return `<div class="popup">
      <div class="popup-title">${label(scale.label, this.config.scale)}
        · ${properties.area_id || ''}</div>
      <table>${rows.join('')}</table>
      ${assumed ? `<div class="popup-note">${assumed}</div>` : ''}</div>`;
  }

  /**
   * A value with the unit its indicator is measured in.  A distance missing
   * because nothing was found within the distance searched says so.
   */
  formatValue(value, resolved, properties = {}, column = null) {
    if (value === undefined || value === null) {
      const censored = ((this.dataset.indicators || {}).censored || {})[column];
      if (censored && censored.access && Number(properties[censored.access]) === 0) {
        return t('censoredBeyond').replace('{d}',
          `${integer(censored.distance)} m`);
      }
      return t('noData');
    }
    const units = (resolved.units || '').toLowerCase();
    const n = Number(value);
    if (units.includes('percent')) {
      return `${number(n, 1)}<span class="unit"> %</span>`;
    }
    if (units.includes('metre')) {
      return `${integer(n)}<span class="unit"> m</span>`;
    }
    if (units.includes('index')) return number(n, 2);
    return number(n, 1);
  }

  networkPopup(feature) {
    const p = feature.properties || {};
    const rows = [
      ['name', p.name], ['highway', p.highway],
      ['LTS', p.lvl_traf_stress], ['km/h', p.maxspeed_kmh],
      ['ADT', p.adt], ['m', p.length_m],
    ].filter(([, value]) => value !== undefined && value !== null && value !== '');
    return `<div class="popup"><div class="popup-title"
      style="color:${LTS_COLORS[p.lvl_traf_stress] || '#333'}">
      ${p.name || t('networkLayer')}</div>
      <table>${rows.map(([k, v]) =>
    `<tr><th>${k}</th><td>${typeof v === 'number' ? integer(v) : v}</td></tr>`)
    .join('')}</table></div>`;
  }

  /**
   * Hold the moveend guard across a programmatic camera change.
   *
   * The event does not always arrive synchronously, so clearing the guard on
   * the next line would let our own camera move be handled as if the user had
   * panned.  Released a tick later instead.
   */
  withoutMoveEvents(change) {
    this.suppressMove = true;
    change();
    setTimeout(() => { this.suppressMove = false; }, 0);
  }

  fitTo(bbox, options = {}) {
    if (!this.map || !bbox) return;
    // Padding has to fit inside the canvas: MapLibre refuses to move at all
    // when it does not, warning and leaving the map wherever it was — which is
    // how a pane in a short window ended up framed on the whole world.
    const canvas = this.map.getContainer();
    const padding = Math.max(
      0,
      Math.min(30, Math.floor(Math.min(canvas.clientWidth, canvas.clientHeight) / 6)),
    );
    this.withoutMoveEvents(() => this.map.fitBounds(
      [[bbox[0], bbox[1]], [bbox[2], bbox[3]]],
      { padding, duration: 0, ...options },
    ));
  }

  applyView(view) {
    if (!this.map || !view) return;
    this.withoutMoveEvents(
      () => this.map.jumpTo({ center: [view.lng, view.lat], zoom: view.zoom }),
    );
  }

  resize() {
    if (!this.map) return;
    // resize re-centres, which emits moveend; the guard keeps that from being
    // mistaken for the user panning
    this.suppressMove = true;
    this.map.resize();
    this.suppressMove = false;
  }
}
