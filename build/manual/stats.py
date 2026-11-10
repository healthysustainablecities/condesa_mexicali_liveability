"""Distribution summaries for the manual, from the full-precision results.

Values come from the results GeoPackage written by
``build/build_results_geopackage.py`` -- the per-scale ``indicators_<scale>``
tables at full precision, on the reference geometries -- not from the rounded
dashboard tiles.  Three summaries are given for each column:

``region``
    The value GHSCI reports for each region as a whole: ``mexicali`` is the
    study region (the Mexicali urban area together with the Condesa
    development), ``condesa`` the development alone.  These are checked against
    the dashboard manifest's ``region_values``.
``manzanas``
    The distribution over census blocks within the study region, weighted by
    their recorded population (``pop_est``, the 2020 census POBTOT); blocks
    without a recorded population count towards ``n`` but carry no weight.
``lots``
    The distribution over the Condesa lots, each weighted equally (every lot is
    assumed to house 3.2 residents, so weighting by that is weighting equally).

Quantiles use the same weighted interpolation as the dashboard exporter
(``_export_dashboard.weighted_quantile``).  For a distance censored at the
largest band searched, an area whose distance is missing but whose access at
that band is 0 found nothing within reach; its share is reported as
``beyond`` rather than dropped, as the dashboard does
(``_export_dashboard.censored_shares``).
"""

import numpy as np
import pandas as pd
import pyogrio

from sources import GPKG

REGIONS = ('mexicali', 'condesa')


def weighted_quantile(values, weights, q):
    order = np.lexsort((weights, values))
    v, w = values[order], weights[order]
    cw = np.cumsum(w)
    if not len(cw) or cw[-1] <= 0:
        return None
    return float(np.interp(q * cw[-1], cw, v))


def summarise(values, weights, censored=None, access=None):
    v = pd.to_numeric(values, errors='coerce').to_numpy(dtype=float)
    w = pd.to_numeric(weights, errors='coerce').fillna(0).to_numpy(dtype=float)
    valued = ~np.isnan(v)
    out = {'areas': int(len(v)), 'n': int(valued.sum())}
    if censored is not None and access is not None:
        a = pd.to_numeric(access, errors='coerce').to_numpy(dtype=float)
        beyond = ~valued & (a == 0)
        total = w[beyond | valued].sum()
        if beyond.any() and total > 0:
            out['beyond'] = float(w[beyond].sum() / total * 100)
            out['n_beyond'] = int(beyond.sum())
    if not valued.any():
        return out
    vv, ww = v[valued], w[valued]
    out['min'] = float(vv.min())
    out['max'] = float(vv.max())
    if ww.sum() > 0:
        out['mean'] = float(np.average(vv, weights=ww))
        for name, q in (('p25', 0.25), ('p50', 0.5), ('p75', 0.75)):
            out[name] = weighted_quantile(vv, ww, q)
    return out


class Results:
    """The results GeoPackage's layers, read once."""

    def __init__(self, path=GPKG):
        self.path = path
        self._frames = {}

    def layer(self, name, geometry=False):
        key = (name, geometry)
        if key not in self._frames:
            self._frames[key] = pyogrio.read_dataframe(
                self.path, layer=name, read_geometry=geometry,
            )
        return self._frames[key]

    def columns(self, name):
        return list(pyogrio.read_info(self.path, layer=name)['fields'])

    @property
    def regions(self):
        return self.layer('region').set_index('area_id')

    def region_values(self, column):
        frame = self.regions
        if column not in frame:
            return {}
        return {
            r: (None if pd.isna(frame.at[r, column]) else float(frame.at[r, column]))
            for r in REGIONS
            if r in frame.index
        }

    def summary(self, column, censored=None):
        """Region values and area distributions for one column."""
        access = (censored or {}).get('access')
        out = {'column': column, 'region': self.region_values(column)}
        manzanas = self.layer('manzanas')
        lots = self.layer('condesa_lotes')
        if column in manzanas:
            out['manzanas'] = summarise(
                manzanas[column], manzanas['pop_est'], censored,
                manzanas[access] if access in manzanas else None,
            )
        if column in lots:
            out['lots'] = summarise(
                lots[column], pd.Series(1.0, index=lots.index), censored,
                lots[access] if access in lots else None,
            )
        return out


def cross_check(results, manifest, columns):
    """Region values against the dashboard manifest; returns mismatches."""
    region_values = manifest.get('region_values') or {}
    problems = []
    for column in columns:
        ours = results.region_values(column)
        for region in REGIONS:
            theirs = (region_values.get(region) or {}).get(column)
            mine = ours.get(region)
            if theirs is None or mine is None:
                continue
            tolerance = max(0.0051, 0.001 * abs(theirs))
            if abs(mine - theirs) > tolerance:
                problems.append((column, region, mine, theirs))
    return problems
