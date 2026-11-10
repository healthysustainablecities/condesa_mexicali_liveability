"""Distribution maps for the manual: manzanas across the study region, with
the Condesa development's lots alongside.

Each map uses the dashboard's own classes for its column (``indicators.json``
``breaks``, computed by the exporter from the data) and the dashboard's ramps,
so a figure here and the same column in the dashboard read alike:

- raw values on batlow, reversed where a low value is the good outcome, so the
  favourable end is always the same colour;
- index, domain and indicator scores on vik, symmetric about the study region
  average (0), blue where better;
- areas without a value in light grey ("no data"), and, for a distance
  censored at the largest band searched, areas that found nothing within reach
  in dark grey ("beyond").

Colours and ramps are those of ``dashboard/js/choropleth.js``.  The scale bar
and north arrow follow ``_utils.add_scalebar`` / ``add_localised_north_arrow``
in GHSCI, redrawn here so the manual needs no GHSCI installation.
"""

import math

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import to_hex, to_rgb  # noqa: E402
from matplotlib.patches import FancyArrow, Patch, Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

from numbers_fmt import fmt  # noqa: E402

BATLOW = ['#011959', '#12557C', '#3E7A5E', '#8C963F', '#DFA050', '#FACCFA']
VIK = [
    '#001261', '#02397a', '#116496', '#5496b7', '#a7c9da', '#ebe6e2',
    '#e2baa2', '#cd8961', '#b85c28', '#872406', '#5b0108',
]
BEYOND = '#6e6a63'
NO_DATA = '#c9c4bd'
INK = '#4a443c'
CONDESA = '#c2185b'
DPI = 150


def ramp_at(stops, t):
    x = max(0.0, min(1.0, t)) * (len(stops) - 1)
    i = min(int(math.floor(x)), len(stops) - 2)
    a, b = np.array(to_rgb(stops[i])), np.array(to_rgb(stops[i + 1]))
    return to_hex(a + (b - a) * (x - i))


def classes_for(breaks, values):
    """Class intervals ``[(low, high), ...]`` from the exporter's breaks."""
    if breaks and breaks.get('edges'):
        edges = [float(e) for e in breaks['edges']]
        out = [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]
        if breaks.get('open_low'):
            out.insert(0, (-math.inf, edges[0]))
        if breaks.get('open_high'):
            out.append((edges[-1], math.inf))
        return out
    v = pd.to_numeric(values, errors='coerce').dropna()
    edges = np.unique(np.quantile(v, np.linspace(0, 1, 6))) if len(v) else [0, 1]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]


def colours_for(n, direction, diverging):
    if diverging:
        stops = [ramp_at(VIK, i / max(1, n - 1)) for i in range(n)]
        return stops if direction == 'lower_is_better' else stops[::-1]
    stops = [ramp_at(BATLOW, i / max(1, n - 1)) for i in range(n)]
    return stops[::-1] if direction == 'lower_is_better' else stops


def class_index(values, classes):
    v = pd.to_numeric(values, errors='coerce').to_numpy(dtype=float)
    out = np.full(len(v), -1)
    for i, (low, high) in enumerate(classes):
        last = i == len(classes) - 1
        inside = (v >= low) & ((v <= high) if last else (v < high))
        out[(out == -1) & inside] = i
    # values outside closed classes fall into the nearest end class
    finite = ~np.isnan(v) & (out == -1)
    out[finite & (v < classes[0][0])] = 0
    out[finite & (v > classes[-1][1])] = len(classes) - 1
    return out


def class_label(low, high, digits, lang, unit=''):
    u = f' {unit}' if unit else ''
    if low == -math.inf:
        return f'< {fmt(high, digits, lang)}{u}'
    if high == math.inf:
        return f'≥ {fmt(low, digits, lang)}{u}'
    return f'{fmt(low, digits, lang)} – {fmt(high, digits, lang)}{u}'


def edge_digits(classes):
    edges = [e for pair in classes for e in pair if math.isfinite(e)]
    for digits in range(0, 4):
        if all(abs(round(e, digits) - e) < 1e-9 for e in edges):
            return digits
    return 3


def nice_length(span):
    target = span / 4
    exponent = 10 ** math.floor(math.log10(target))
    for m in (5, 2, 1):
        if m * exponent <= target:
            return m * exponent
    return exponent


def add_scalebar(ax, lang, location=(0.05, 0.05)):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    length = nice_length(x1 - x0)
    x = x0 + location[0] * (x1 - x0)
    y = y0 + location[1] * (y1 - y0)
    h = (y1 - y0) * 0.012
    for i in range(2):
        ax.add_patch(Rectangle(
            (x + i * length / 2, y), length / 2, h,
            facecolor=INK if i == 0 else 'white', edgecolor=INK, lw=0.6,
            zorder=10,
        ))
    unit, scale = ('km', 1000) if length >= 1000 else ('m', 1)
    for value, at in ((0, x), (length / scale, x + length)):
        ax.text(at, y + h * 1.8, fmt(value, 0 if float(value).is_integer() else 1, lang),
                ha='center', va='bottom', fontsize=6.5, color=INK, zorder=10)
    ax.text(x + length + (x1 - x0) * 0.012, y + h / 2, unit, ha='left',
            va='center', fontsize=6.5, color=INK, zorder=10)


def add_north_arrow(ax, location=(0.94, 0.88)):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    x = x0 + location[0] * (x1 - x0)
    y = y0 + location[1] * (y1 - y0)
    length = (y1 - y0) * 0.07
    ax.add_patch(FancyArrow(
        x, y, 0, length, width=(x1 - x0) * 0.006,
        head_width=(x1 - x0) * 0.03, head_length=length * 0.45,
        length_includes_head=True, color=INK, zorder=10,
    ))
    ax.text(x, y + length * 1.15, 'N', ha='center', va='bottom',
            fontsize=8, fontweight='bold', color=INK, zorder=10)


def _plot(ax, frame, colours):
    # edges drawn in each polygon's own colour close the antialiasing seams
    # that would otherwise show as a white mesh between adjacent blocks
    if len(frame):
        frame.plot(ax=ax, facecolor=colours, edgecolor=colours,
                   linewidth=0.15, rasterized=True)


def render(spec, results, target, lang, words):
    """Draw one map.

    ``spec`` holds ``column``, ``breaks``, ``direction``, ``diverging``,
    ``unit`` (legend text), ``title`` and, for a censored distance,
    ``censored`` (with its ``access`` column and ``distance``).
    """
    column = spec['column']
    manzanas = results.layer('manzanas', geometry=True)
    lots = results.layer('condesa_lotes', geometry=True)
    regions = results.layer('region', geometry=True).set_index('area_id')
    study = regions.loc[['mexicali']]
    condesa = regions.loc[['condesa']]
    values = pd.concat([
        manzanas.get(column, pd.Series(dtype=float)),
        lots.get(column, pd.Series(dtype=float)),
    ])
    classes = classes_for(spec.get('breaks'), values)
    palette = colours_for(len(classes), spec['direction'], spec['diverging'])
    digits = edge_digits(classes)

    def colours(frame):
        if column not in frame:
            return [NO_DATA] * len(frame)
        idx = class_index(frame[column], classes)
        out = np.array([palette[i] if i >= 0 else NO_DATA for i in idx],
                       dtype=object)
        censored = spec.get('censored')
        if censored and censored.get('access') in frame:
            access = pd.to_numeric(frame[censored['access']], errors='coerce')
            out[(idx == -1) & (access == 0).to_numpy()] = BEYOND
        return list(out)

    fig = plt.figure(figsize=(7.2, 6.6), dpi=DPI)
    grid = fig.add_gridspec(
        2, 2, width_ratios=[1, 1.25], height_ratios=[1.45, 1],
        wspace=0.06, hspace=0.12, left=0.01, right=0.99, top=0.95,
        bottom=0.01,
    )
    main = fig.add_subplot(grid[0, :])
    inset = fig.add_subplot(grid[1, 0])
    legend_ax = fig.add_subplot(grid[1, 1])
    for ax in (main, inset, legend_ax):
        ax.set_axis_off()

    _plot(main, manzanas, colours(manzanas))
    study.boundary.plot(ax=main, color=INK, linewidth=0.6)
    condesa.boundary.plot(ax=main, color=CONDESA, linewidth=0.5)
    xmin, ymin, xmax, ymax = study.total_bounds
    pad = 0.02 * max(xmax - xmin, ymax - ymin)
    main.set_xlim(xmin - pad, xmax + pad)
    main.set_ylim(ymin - pad, ymax + pad)
    main.set_aspect('equal')
    cx0, cy0, cx1, cy1 = condesa.total_bounds
    main.add_patch(Rectangle(
        (cx0, cy0), cx1 - cx0, cy1 - cy0, fill=False, edgecolor=CONDESA,
        linewidth=0.9, linestyle='--', zorder=9,
    ))
    main.text(cx1, cy0, ' Condesa', color=CONDESA, fontsize=7,
              ha='left', va='top', zorder=10)
    add_scalebar(main, lang)
    add_north_arrow(main)
    main.set_title(words['manzanas'], fontsize=8, color=INK, loc='left')

    _plot(inset, lots, colours(lots))
    condesa.boundary.plot(ax=inset, color=CONDESA, linewidth=0.6)
    pad = 0.04 * max(cx1 - cx0, cy1 - cy0)
    inset.set_xlim(cx0 - pad, cx1 + pad)
    inset.set_ylim(cy0 - pad, cy1 + pad)
    inset.set_aspect('equal')
    add_scalebar(inset, lang, location=(0.06, 0.04))
    add_north_arrow(inset, location=(0.9, 0.8))
    inset.set_title(words['lots'], fontsize=8, color=INK, loc='left')
    for side in inset.spines.values():
        side.set_visible(True)
        side.set_edgecolor(CONDESA)

    handles = [
        Patch(facecolor=palette[i], edgecolor='none',
              label=class_label(low, high, digits, lang))
        for i, (low, high) in enumerate(classes)
    ]
    if spec.get('censored'):
        distance = spec['censored'].get('distance')
        handles.append(Patch(
            facecolor=BEYOND, edgecolor='none',
            label=f"> {fmt(distance, 0, lang)} m" if distance else words['beyond'],
        ))
    handles.append(Patch(facecolor=NO_DATA, edgecolor='none',
                         label=words['no_data']))
    handles.append(Patch(facecolor='none', edgecolor=CONDESA,
                         label=words['condesa']))
    legend_ax.legend(
        handles=handles, loc='upper left', frameon=False, fontsize=7,
        title=spec.get('unit') or None, title_fontsize=7.5,
        alignment='left', handlelength=1.6, handleheight=1.0,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=DPI, facecolor='white')
    plt.close(fig)
    # A map is a few flat class colours: a 256-colour palette loses nothing
    # visible and makes each figure a quarter of the size in the repository.
    with Image.open(target) as image:
        quantised = image.convert('RGB').quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    quantised.save(target, optimize=True)
    return target
