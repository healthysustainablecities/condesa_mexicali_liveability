// The measure tool, ported from the cycling validation site.
//
// Straight-line great-circle distance, deliberately: it answers "how far apart
// are these two things" without implying a route, which is the question people
// ask when they are looking at an access map and want to sanity-check a band.
// Network distance is what the indicators already report.
//
// Two changes from the original: the tool takes a pane rather than closing over
// a single global map, so it can attach to whichever pane has focus; and it
// waits on the style rather than on tiles (see start()).

import { integer, t } from './strings.js';

const R = 6371008.8;

function haversineM(a, b) {
  const rad = Math.PI / 180;
  const dLat = (b.lat - a.lat) * rad;
  const dLng = (b.lng - a.lng) * rad;
  const lat1 = a.lat * rad;
  const lat2 = b.lat * rad;
  const h = Math.sin(dLat / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

export class MeasureTool {
  constructor(ui) {
    this.ui = ui; // {box, total, hint, undo, clear, done}
    this.map = null;
    this.points = [];
    this.markers = [];
    this.active = false;
    this.handlers = new Map();
    this.wire();
  }

  wire() {
    const { undo, clear, done } = this.ui;
    if (undo) {
      undo.addEventListener('click', () => {
        this.points.pop();
        this.redraw();
      });
    }
    if (clear) clear.addEventListener('click', () => this.reset());
    if (done) done.addEventListener('click', () => this.stop());
    window.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && this.active) this.stop();
    });
  }

  isActive(map) {
    return this.active && this.map === map;
  }

  /** True while the tool is armed, on whichever pane. */
  get armed() {
    return this.active;
  }

  /**
   * Attach to a pane.  Takes the pane rather than its map so it can wait on
   * `whenStyleReady()`, which resolves on the style being parsed.
   *
   * The previous version gated on `map.isStyleLoaded()` with an `once('idle')`
   * fallback.  Both of those wait for *tiles*, not for the style: Condesa's 40
   * features settle and the tool worked there, while Mexicali's 100 m grid
   * streams tiles continuously, never goes idle, and so never got its layers.
   * Do not reintroduce either test here.
   */
  async start(panes) {
    if (this.active) this.stop();
    this.armedPanes = Array.isArray(panes) ? panes : [panes];
    this.active = true;
    this.map = null;
    this.points = [];
    this.ui.box.hidden = false;
    this.ui.hint.textContent = t('measureHint');
    document.body.classList.add('measuring');
    this.handlers = new Map();
    for (const pane of this.armedPanes) {
      if (!pane.map) continue;
      pane.map.getCanvas().style.cursor = 'crosshair';
      pane.map.doubleClickZoom.disable();
      const handler = (event) => this.onClick(pane, event.lngLat);
      this.handlers.set(pane, handler);
      pane.map.on('click', handler);
    }
  }

  /**
   * The first click chooses the map.
   *
   * Every visible pane is armed, and whichever is clicked first becomes the one
   * being measured; the others are released. Previously the tool bound to
   * whichever pane was last hovered, so in practice it only ever worked on the
   * left one.
   */
  async onClick(pane, lngLat) {
    if (!this.map) {
      this.map = pane.map;
      for (const [other, handler] of this.handlers) {
        if (other === pane) continue;
        other.map.off('click', handler);
        other.map.getCanvas().style.cursor = '';
        other.map.doubleClickZoom.enable();
      }
      await pane.whenStyleReady();
      if (!this.active || this.map !== pane.map) return;
      this.ensureLayers();
    }
    this.addPoint(lngLat);
  }

  stop() {
    document.body.classList.remove('measuring');
    for (const [pane, handler] of this.handlers || []) {
      if (!pane.map) continue;
      pane.map.off('click', handler);
      pane.map.getCanvas().style.cursor = '';
      pane.map.doubleClickZoom.enable();
    }
    this.handlers = new Map();
    this.active = false;
    this.ui.box.hidden = true;
    this.reset();
    this.map = null;
  }

  reset() {
    this.points = [];
    this.redraw();
  }

  ensureLayers() {
    const map = this.map;
    if (map.getSource('measure')) return;
    map.addSource('measure', {
      type: 'geojson',
      data: { type: 'FeatureCollection', features: [] },
    });
    map.addLayer({
      id: 'measure_halo', type: 'line', source: 'measure',
      filter: ['==', ['geometry-type'], 'LineString'],
      paint: { 'line-color': '#ffffff', 'line-width': 5 },
    });
    map.addLayer({
      id: 'measure_line', type: 'line', source: 'measure',
      filter: ['==', ['geometry-type'], 'LineString'],
      paint: {
        'line-color': '#1b1b1b', 'line-width': 2, 'line-dasharray': [2, 1.5],
      },
    });
    map.addLayer({
      id: 'measure_pts', type: 'circle', source: 'measure',
      filter: ['==', ['geometry-type'], 'Point'],
      paint: {
        'circle-radius': 4.5, 'circle-color': '#1b1b1b',
        'circle-stroke-color': '#ffffff', 'circle-stroke-width': 2,
      },
    });
  }

  addPoint(lngLat) {
    this.points.push({ lng: lngLat.lng, lat: lngLat.lat });
    this.redraw();
  }

  redraw() {
    for (const marker of this.markers) marker.remove();
    this.markers = [];
    if (!this.map) return;
    const source = this.map.getSource('measure');
    if (!source) return;

    const coordinates = this.points.map((p) => [p.lng, p.lat]);
    const features = this.points.map((p) => ({
      type: 'Feature', geometry: { type: 'Point', coordinates: [p.lng, p.lat] },
      properties: {},
    }));
    if (coordinates.length > 1) {
      features.push({
        type: 'Feature',
        geometry: { type: 'LineString', coordinates },
        properties: {},
      });
    }
    source.setData({ type: 'FeatureCollection', features });

    let total = 0;
    for (let i = 1; i < this.points.length; i += 1) {
      total += haversineM(this.points[i - 1], this.points[i]);
      const element = document.createElement('div');
      element.className = 'measure-label';
      element.textContent = `${integer(total)} m`;
      this.markers.push(
        new maplibregl.Marker({ element, anchor: 'bottom' })
          .setLngLat([this.points[i].lng, this.points[i].lat])
          .addTo(this.map),
      );
    }
    this.ui.total.textContent = this.points.length > 1
      ? `${t('total')}: ${integer(total)} m`
      : '';
  }
}
