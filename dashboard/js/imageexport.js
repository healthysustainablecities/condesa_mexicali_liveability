// Export the current view as a PNG, with everything needed to read it away
// from the app: title, indicator description, legend, scale bar and attribution.
//
// A screenshot of the map alone is not publishable — it carries no legend and
// no source — which is why this composes rather than just saving the canvas.

import { getLang, label, number, t } from './strings.js';
import { attributionLines } from './info.js';
import { classLabel, legendTitle } from './legend.js';
import { showingSentence } from './showing.js';

const MARGIN = 24;
const HEADER = 76;
const FOOTER = 64;
const LEGEND_W = 250;
const GAP = 16;

function wrap(ctx, text, maxWidth) {
  const words = String(text || '').split(/\s+/);
  const lines = [];
  let line = '';
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (ctx.measureText(candidate).width > maxWidth && line) {
      lines.push(line);
      line = word;
    } else {
      line = candidate;
    }
  }
  if (line) lines.push(line);
  return lines;
}

/** Metres per pixel at a map's current centre and zoom. */
function metresPerPixel(map) {
  const lat = map.getCenter().lat;
  return (156543.03392 * Math.cos((lat * Math.PI) / 180)) / 2 ** map.getZoom();
}

function drawScaleBar(ctx, map, x, y) {
  const mpp = metresPerPixel(map);
  const candidates = [
    50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000,
  ];
  const target = 140 * mpp;
  const metres = candidates.find((c) => c >= target) || candidates[candidates.length - 1];
  const width = metres / mpp;
  ctx.strokeStyle = '#1b1b1b';
  ctx.fillStyle = '#1b1b1b';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x, y - 6);
  ctx.lineTo(x, y);
  ctx.lineTo(x + width, y);
  ctx.lineTo(x + width, y - 6);
  ctx.stroke();
  ctx.font = '12px system-ui, sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText(
    metres >= 1000 ? `${metres / 1000} km` : `${metres} m`, x + width + 6, y,
  );
}

function drawLegend(ctx, x, y, width, resolved, classification) {
  ctx.textAlign = 'left';
  ctx.fillStyle = '#1b1b1b';
  ctx.font = '600 13px system-ui, sans-serif';
  const title = legendTitle(resolved).text;
  let cursor = y;
  for (const line of wrap(ctx, title, width)) {
    ctx.fillText(line, x, cursor);
    cursor += 17;
  }
  cursor += 4;
  ctx.font = '12px system-ui, sans-serif';
  // classLabel handles the open ends and the ordinal codes, so the exported
  // image and the on-screen legend always read the same
  const entries = classification.classes.map((cls, i) => ({
    color: cls.color,
    text: classLabel(classification, i),
  }));
  entries.push({ color: '#c9c4bd', text: t('noData') });
  for (const entry of entries) {
    ctx.fillStyle = entry.color;
    ctx.fillRect(x, cursor - 10, 16, 12);
    ctx.strokeStyle = 'rgba(0,0,0,0.25)';
    ctx.lineWidth = 1;
    ctx.strokeRect(x + 0.5, cursor - 9.5, 15, 11);
    ctx.fillStyle = '#1b1b1b';
    ctx.fillText(entry.text, x + 24, cursor);
    cursor += 19;
  }
  return cursor;
}

/**
 * Compose and download the current view.
 *
 * Returns null on success, or a message when the browser refuses to read the
 * canvas back.  That happens when a basemap's tiles are served without CORS
 * headers, which taints the drawing buffer; switching basemap is the fix, so
 * the message says so rather than failing silently.
 */
export async function exportImage({ panes, datasets, resolved, classification,
  vocab, filename }) {
  const maps = panes.map((pane) => pane.map).filter(Boolean);
  if (!maps.length || !resolved) return 'nothing to export';

  // preserveDrawingBuffer keeps the buffer from being cleared, but its contents
  // are only reliably readable straight after a frame — reading from an idle
  // map returns a blank canvas.  Force a render on each map and read inside it.
  await Promise.all(maps.map((map) => new Promise((resolve) => {
    map.once('render', resolve);
    map.triggerRepaint();
  })));
  const canvases = maps.map((map) => map.getCanvas());
  const height = Math.max(...canvases.map((c) => c.height));
  const mapsWidth = canvases.reduce((sum, c) => sum + c.width, 0)
    + GAP * (canvases.length - 1);
  const width = mapsWidth + LEGEND_W + GAP;

  const out = document.createElement('canvas');
  out.width = width + MARGIN * 2;
  out.height = height + HEADER + FOOTER + MARGIN * 2;
  const ctx = out.getContext('2d');
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, out.width, out.height);

  // header: what is being shown, and by whom
  ctx.fillStyle = '#1b1b1b';
  ctx.textAlign = 'left';
  ctx.font = '600 19px system-ui, sans-serif';
  ctx.fillText(vocab.title(resolved.selection), MARGIN, MARGIN + 20);
  ctx.font = '13px system-ui, sans-serif';
  ctx.fillStyle = '#55504a';
  const captions = panes.map((pane, i) => {
    const manifest = datasets[i].manifest;
    const region = (manifest.regions[pane.config.region] || {}).label;
    const scale = (manifest.scales[pane.config.scale] || {}).label;
    return {
      region: label(region, pane.config.region),
      scale: label(scale, pane.config.scale),
    };
  });
  const subtitle = captions
    .map((c) => `${c.region} — ${c.scale}`)
    .join('     ');
  ctx.fillText(subtitle, MARGIN, MARGIN + 44);

  let x = MARGIN;
  const top = MARGIN + HEADER;
  canvases.forEach((canvas, i) => {
    ctx.drawImage(canvas, x, top);
    ctx.strokeStyle = 'rgba(0,0,0,0.25)';
    ctx.lineWidth = 1;
    ctx.strokeRect(x + 0.5, top + 0.5, canvas.width - 1, canvas.height - 1);
    // caption each panel with its region rather than an A/B badge: the letters
    // were a way of talking about the layout, never something a reader needs
    if (canvases.length > 1) {
      ctx.font = '600 13px system-ui, sans-serif';
      const text = captions[i].region;
      const width = ctx.measureText(text).width + 16;
      ctx.fillStyle = 'rgba(255,255,255,0.92)';
      ctx.fillRect(x + 8, top + 8, width, 24);
      ctx.strokeStyle = 'rgba(0,0,0,0.25)';
      ctx.strokeRect(x + 8.5, top + 8.5, width - 1, 23);
      ctx.fillStyle = '#1b1b1b';
      ctx.fillText(text, x + 16, top + 25);
    }
    ctx.font = '12px system-ui, sans-serif';
    drawScaleBar(ctx, maps[i], x + 12, top + canvas.height - 14);
    x += canvas.width + GAP;
  });

  drawLegend(ctx, x, top + 16, LEGEND_W - GAP, resolved, classification);

  // footer: description then attribution, so the map can be read on its own
  ctx.textAlign = 'left';
  ctx.font = '12px system-ui, sans-serif';
  ctx.fillStyle = '#55504a';
  let cursor = top + height + 22;
  // the same sentence the app shows, not the widest band's dictionary entry:
  // that described one column and read "within 1500 m" on a map of every band
  const caption = showingSentence(resolved, vocab, getLang());
  for (const line of wrap(ctx, caption, width).slice(0, 2)) {
    ctx.fillText(line, MARGIN, cursor);
    cursor += 16;
  }
  const attribution = attributionLines(datasets[0].manifest).join(' · ');
  ctx.fillStyle = '#7a746c';
  ctx.font = '11px system-ui, sans-serif';
  for (const line of wrap(ctx, attribution, width).slice(0, 2)) {
    ctx.fillText(line, MARGIN, cursor);
    cursor += 14;
  }

  try {
    const blob = await new Promise((resolve, reject) => {
      out.toBlob((b) => (b ? resolve(b) : reject(new Error('empty'))), 'image/png');
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename || 'indicator-map.png';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    return null;
  } catch (error) {
    return `${error.name === 'SecurityError' ? 'basemap tiles blocked the export'
      : error.message}`;
  }
}
