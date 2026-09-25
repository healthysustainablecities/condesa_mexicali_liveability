// A regular grid drawn as a smooth surface.
//
// The 100 m population grid is a raster in the project's projection,
// polygonised for the tiles.  The exporter also writes it back as a raster
// (a scale's `raster` entry in the manifest): each area's cell, and each tile
// group's columns as little-endian 32-bit floats.  From those this module
// draws an image: the cell values smoothed (a Gaussian over the neighbouring
// cells, normalised by those that have a value, so an empty cell neither
// drags its neighbours down nor is painted), upsampled bilinearly, and
// coloured by the legend's own classes -- so the surface is continuous, but a
// colour on it still means what the legend says, and its edges follow the
// grid's footprint rather than squares.  The image is placed on the map by the
// grid's four corners, and the vector layer beneath it stays (transparent) to
// be clicked.

import { classOf } from './choropleth.js';

// the Gaussian's standard deviation, in cells: one cell's neighbours count,
// its neighbours' neighbours a little
const SIGMA = 1;
const RADIUS = 3;
// pixels per cell, within an image no wider than this
const MAX_WIDTH = 1800;
const LUT_SIZE = 1024;
const OPACITY = 0.78;
const ISOLATED_ALPHA = 0.85;
const DIMMED_ALPHA = 0.12;

const cache = new Map();

/** A little-endian binary file, as 32-bit integers ('i32') or floats. */
async function binary(url, kind) {
  if (!cache.has(url)) {
    cache.set(url, fetch(url).then(async (response) => {
      if (!response.ok) throw new Error(`${url}: ${response.status}`);
      const buffer = await response.arrayBuffer();
      return kind === 'i32' ? new Int32Array(buffer) : new Float32Array(buffer);
    }));
  }
  return cache.get(url);
}

/** The values of `columns` for each area, read from their groups' files. */
async function columnValues(dataset, raster, columns) {
  const base = `data/${dataset.slug}`;
  const out = {};
  for (const column of columns) {
    const group = Object.values(raster.groups)
      .find((g) => g.columns.includes(column));
    if (!group) return null;
    const values = await binary(`${base}/${group.file}`, 'f32');
    const offset = group.columns.indexOf(column) * raster.areas;
    out[column] = values.subarray(offset, offset + raster.areas);
  }
  return out;
}

/** A separable Gaussian, normalised by the cells that have a value. */
function smoothGrid(values, mask, nx, ny) {
  const kernel = [];
  for (let d = -RADIUS; d <= RADIUS; d += 1) {
    kernel.push(Math.exp(-(d * d) / (2 * SIGMA * SIGMA)));
  }
  const pass = (source, weight, horizontal) => {
    const sum = new Float32Array(nx * ny);
    const total = new Float32Array(nx * ny);
    for (let y = 0; y < ny; y += 1) {
      for (let x = 0; x < nx; x += 1) {
        let s = 0;
        let w = 0;
        for (let k = -RADIUS; k <= RADIUS; k += 1) {
          const xx = horizontal ? x + k : x;
          const yy = horizontal ? y : y + k;
          if (xx < 0 || yy < 0 || xx >= nx || yy >= ny) continue;
          const i = yy * nx + xx;
          const g = kernel[k + RADIUS] * weight[i];
          s += g * source[i];
          w += g;
        }
        sum[y * nx + x] = s;
        total[y * nx + x] = w;
      }
    }
    return [sum, total];
  };
  // weighted values and weights are blurred together; their ratio is the
  // smoothed value where any neighbour has one
  const weighted = new Float32Array(nx * ny);
  for (let i = 0; i < weighted.length; i += 1) weighted[i] = mask[i] ? values[i] : 0;
  const ones = new Float32Array(nx * ny).fill(1);
  const [s1] = pass(weighted, ones, true);
  const [w1] = pass(mask, ones, true);
  const [s2] = pass(s1, ones, false);
  const [w2] = pass(w1, ones, false);
  const out = new Float32Array(nx * ny);
  for (let i = 0; i < out.length; i += 1) out[i] = w2[i] > 1e-6 ? s2[i] / w2[i] : NaN;
  return out;
}

/** CSS colours as [r, g, b], through a canvas so any notation is read. */
function rgbOf(colour) {
  const context = rgbOf.context
    || (rgbOf.context = document.createElement('canvas').getContext('2d'));
  context.fillStyle = '#000';
  context.fillStyle = colour;
  const hex = context.fillStyle;
  if (hex.startsWith('#')) {
    return [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  }
  const parts = hex.match(/[\d.]+/g) || [0, 0, 0];
  return parts.slice(0, 3).map(Number);
}

/**
 * Draw the surface for a classified column as a data URL, or null where the
 * values cannot be read.  `computed` turns an area's input values into the
 * mapped one, for a score calculated in the browser (custom weights).
 */
export async function surfaceImage(given) {
  const {
    dataset, raster, classification, column, inputs, isolated,
  } = given;
  const index = await binary(`data/${dataset.slug}/${raster.index}`, 'i32');
  const read = await columnValues(dataset, raster, inputs);
  if (!read) return null;
  const { nx, ny } = raster;
  const values = new Float32Array(nx * ny).fill(NaN);
  const mask = new Float32Array(nx * ny);
  for (let i = 0; i < raster.areas; i += 1) {
    let v;
    if (given.computed) {
      const props = {};
      for (const c of inputs) props[c] = Number.isNaN(read[c][i]) ? null : read[c][i];
      v = given.computed(props);
    } else {
      v = read[column][i];
    }
    if (v === null || v === undefined || Number.isNaN(v)) continue;
    values[index[i]] = v;
    mask[index[i]] = 1;
  }
  const smoothed = smoothGrid(values, mask, nx, ny);

  // colour lookup over the smoothed range, class by class
  let lo = Infinity;
  let hi = -Infinity;
  for (let i = 0; i < smoothed.length; i += 1) {
    if (mask[i] && smoothed[i] < lo) lo = smoothed[i];
    if (mask[i] && smoothed[i] > hi) hi = smoothed[i];
  }
  if (!Number.isFinite(lo)) return null;
  if (!(hi > lo)) hi = lo + 1;
  const lut = new Uint8ClampedArray(LUT_SIZE * 4);
  const rgbCache = new Map();
  for (let j = 0; j < LUT_SIZE; j += 1) {
    const v = lo + ((hi - lo) * j) / (LUT_SIZE - 1);
    const cls = classOf(classification, v);
    if (!cls) continue;
    if (!rgbCache.has(cls.color)) rgbCache.set(cls.color, rgbOf(cls.color));
    const [r, g, b] = rgbCache.get(cls.color);
    let alpha = 255;
    if (isolated && isolated.kind === 'class') {
      alpha = cls.index === isolated.value ? 255 * ISOLATED_ALPHA / OPACITY : 255 * DIMMED_ALPHA;
    }
    lut.set([r, g, b, Math.min(255, alpha)], j * 4);
  }

  const k = Math.max(2, Math.min(8, Math.floor(MAX_WIDTH / nx)));
  const width = nx * k;
  const height = ny * k;
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  const image = context.createImageData(width, height);
  const data = image.data;
  const at = (x, y) => y * nx + x;
  for (let py = 0; py < height; py += 1) {
    const gy = (py + 0.5) / k - 0.5;
    const y0 = Math.max(0, Math.min(ny - 1, Math.floor(gy)));
    const y1 = Math.min(ny - 1, y0 + 1);
    const fy = Math.max(0, Math.min(1, gy - y0));
    for (let px = 0; px < width; px += 1) {
      const gx = (px + 0.5) / k - 0.5;
      const x0 = Math.max(0, Math.min(nx - 1, Math.floor(gx)));
      const x1 = Math.min(nx - 1, x0 + 1);
      const fx = Math.max(0, Math.min(1, gx - x0));
      const corners = [
        [at(x0, y0), (1 - fx) * (1 - fy)], [at(x1, y0), fx * (1 - fy)],
        [at(x0, y1), (1 - fx) * fy], [at(x1, y1), fx * fy],
      ];
      // the footprint, interpolated: a pixel is drawn where it is mostly
      // within cells that have a value, which rounds the grid's staircase
      let m = 0;
      let s = 0;
      let w = 0;
      for (const [i, weight] of corners) {
        m += weight * mask[i];
        if (!Number.isNaN(smoothed[i])) {
          s += weight * smoothed[i];
          w += weight;
        }
      }
      if (m < 0.5 || !(w > 0)) continue;
      const v = s / w;
      const j = Math.round(((v - lo) / (hi - lo)) * (LUT_SIZE - 1));
      const o = (py * width + px) * 4;
      data[o] = lut[j * 4];
      data[o + 1] = lut[j * 4 + 1];
      data[o + 2] = lut[j * 4 + 2];
      data[o + 3] = lut[j * 4 + 3];
    }
  }
  context.putImageData(image, 0, 0);
  return canvas.toDataURL('image/png');
}

/** Show `url` on a map as the smoothed layer, beneath the outlines. */
export function showSurface(map, url, corners) {
  const source = map.getSource('smooth');
  if (source) {
    source.updateImage({ url, coordinates: corners });
  } else {
    map.addSource('smooth', { type: 'image', url, coordinates: corners });
  }
  if (!map.getLayer('smooth')) {
    map.addLayer({
      id: 'smooth',
      type: 'raster',
      source: 'smooth',
      paint: {
        'raster-opacity': OPACITY,
        'raster-resampling': 'linear',
        'raster-fade-duration': 0,
      },
    }, map.getLayer('choropleth-outline') ? 'choropleth-outline' : undefined);
  }
  map.setLayoutProperty('smooth', 'visibility', 'visible');
}

export function hideSurface(map) {
  if (map.getLayer('smooth')) map.setLayoutProperty('smooth', 'visibility', 'none');
}
