"""Move indicator values between reporting geographies, consistently.

Analysts compute at whatever scale their data actually support (the
*native scale*), then call :func:`harmonise` to produce the full set of
reporting geographies from that single computation.  Everyone uses the
same crosswalk, so an AGEB value from one work package covers exactly
the same ground as an AGEB value from another.

Two rules underlie everything here:

1. Aggregate **up** with a weighted mean (population for anything
   people experience, area for land cover and exposure surfaces) or a
   share-apportioned sum for counts.
2. Never aggregate **down**.  If a value is only known for a coarse
   unit, it is *replicated* to the finer units and flagged as such --
   it carries no information at that scale and the composite index
   must know that.

There are also convenience builders (:func:`count_features`,
:func:`areal_share`, :func:`network_share`, :func:`zonal_statistic`)
for the four shapes of calculation that cover most of the indicator
set.
"""

import numpy as np
import pandas as pd

from . import geography, vocab

WEIGHTS = {
    'population': 'population',
    'area': 'area_sqm',
    'dwellings': 'dwellings',
}


def _finer(level_a, level_b):
    """True if ``level_a`` is finer than ``level_b``."""
    order = vocab.GEO_RESOLUTION_ORDER
    return order.index(level_a) > order.index(level_b)


def to_level(
    values,
    from_level,
    to_level,
    method='population_weighted_mean',
    value_column='value',
    id_column='geo_id',
    min_coverage=0.5,
):
    """Carry values from one reporting geography to another.

    Parameters
    ----------
    values : DataFrame
        Native-scale results, with an id column and a value column.
        Missing values are permitted and are excluded from the weights,
        which is what drives the reported ``coverage``.
    method : str
        One of ``population_weighted_mean``, ``area_weighted_mean``,
        ``dwelling_weighted_mean``, ``sum``, ``majority`` or
        ``replicated``.  Weighted means fall back to area weighting for
        target units with no resident population (the Condesa new
        development is the reason this matters).
    min_coverage : float
        Target units with a lower share of valid input are flagged
        ``low_coverage``.

    Returns
    -------
    DataFrame with ``geo_id``, ``value``, ``denominator``,
    ``coverage``, ``aggregation_method`` and ``quality_flag``.
    """
    if from_level == to_level:
        return _passthrough(values, value_column, id_column)
    if not _finer(from_level, to_level) and method != 'replicated':
        raise ValueError(
            f'{to_level!r} is finer than {from_level!r}; use '
            "method='replicated' and accept that the result carries "
            'no variation at the finer scale.'
        )

    link = geography.crosswalk(from_level, to_level)
    frame = link.merge(
        values[[id_column, value_column]].rename(
            columns={id_column: 'from_id', value_column: 'value'}
        ),
        on='from_id',
        how='left',
    )

    if method == 'replicated':
        result = _replicate(frame, to_level)
    elif method == 'sum':
        result = _sum(frame, to_level, min_coverage)
    elif method == 'majority':
        result = _majority(frame, to_level)
    else:
        result = _weighted_mean(frame, to_level, method, min_coverage)
    return _complete(result, to_level, method)


def _complete(result, to_level, method):
    """Emit a row for every unit, including those with no input.

    A unit that is silently absent looks like perfect coverage to
    everyone downstream.  Units the source data never reached are
    reported explicitly as ``no_data`` -- which is how the Condesa gap
    becomes visible instead of invisible.
    """
    try:
        all_ids = geography.units(to_level)['geo_id'].astype(str)
    except FileNotFoundError:
        return result
    missing = sorted(set(all_ids) - set(result['geo_id'].astype(str)))
    if not missing:
        return result
    filler = pd.DataFrame(
        {
            'geo_id': missing,
            'value': np.nan,
            'denominator': np.nan,
            'coverage': 0.0,
            'aggregation_method': method,
            'quality_flag': 'no_data',
        }
    )
    return pd.concat([result, filler], ignore_index=True)


def _passthrough(values, value_column, id_column):
    frame = values.rename(
        columns={id_column: 'geo_id', value_column: 'value'}
    )[['geo_id', 'value']].copy()
    frame['denominator'] = np.nan
    frame['coverage'] = np.where(frame['value'].notna(), 1.0, 0.0)
    frame['aggregation_method'] = 'native'
    frame['quality_flag'] = np.where(
        frame['value'].notna(), 'ok', 'no_data'
    )
    return frame


def _weighted_mean(frame, to_level, method, min_coverage):
    weight_key = {
        'population_weighted_mean': 'population',
        'area_weighted_mean': 'area',
        'dwelling_weighted_mean': 'dwellings',
    }[method]
    frame = frame.copy()
    frame['w'] = frame[WEIGHTS[weight_key]].fillna(0.0)
    # Fall back to area weighting where the preferred weight is absent
    # for a whole target unit -- e.g. new development with no 2020
    # census population.
    totals = frame.groupby('to_id')['w'].transform('sum')
    fallback = totals <= 0
    frame['method'] = method
    if weight_key != 'area' and fallback.any():
        frame.loc[fallback, 'w'] = frame.loc[fallback, 'area_sqm']
        frame.loc[fallback, 'method'] = 'area_weighted_mean'

    valid = frame['value'].notna()
    numerator = (
        frame.loc[valid]
        .assign(wv=lambda d: d['w'] * d['value'])
        .groupby('to_id')['wv']
        .sum()
    )
    weight_valid = frame.loc[valid].groupby('to_id')['w'].sum()
    weight_all = frame.groupby('to_id')['w'].sum()
    method_by_unit = frame.groupby('to_id')['method'].first()

    result = pd.DataFrame({'geo_id': weight_all.index})
    result['value'] = (
        result['geo_id'].map(numerator / weight_valid).values
    )
    result['denominator'] = result['geo_id'].map(weight_all).values
    result['coverage'] = (
        result['geo_id'].map(weight_valid / weight_all).fillna(0.0)
    ).values
    result['aggregation_method'] = (
        result['geo_id'].map(method_by_unit).values
    )
    return _flag(result, min_coverage)


def _sum(frame, to_level, min_coverage):
    frame = frame.copy()
    frame['apportioned'] = frame['share_of_from'] * frame['value']
    totals = frame.groupby('to_id')['apportioned'].sum(min_count=1)
    share_valid = (
        frame.loc[frame['value'].notna()]
        .groupby('to_id')['area_sqm']
        .sum()
    )
    share_all = frame.groupby('to_id')['area_sqm'].sum()
    result = pd.DataFrame({'geo_id': share_all.index})
    result['value'] = result['geo_id'].map(totals).values
    result['denominator'] = (
        result['geo_id'].map(frame.groupby('to_id')['population'].sum())
    ).values
    result['coverage'] = (
        result['geo_id'].map(share_valid / share_all).fillna(0.0).values
    )
    result['aggregation_method'] = 'sum'
    return _flag(result, min_coverage)


def _majority(frame, to_level):
    valid = frame[frame['value'].notna()]
    winner = (
        valid.groupby(['to_id', 'value'])['area_sqm']
        .sum()
        .reset_index()
        .sort_values('area_sqm', ascending=False)
        .drop_duplicates('to_id')
    )
    share_all = frame.groupby('to_id')['area_sqm'].sum()
    result = pd.DataFrame({'geo_id': share_all.index})
    result['value'] = result['geo_id'].map(
        winner.set_index('to_id')['value']
    ).values
    result['denominator'] = np.nan
    result['coverage'] = (
        result['geo_id']
        .map(
            valid.groupby('to_id')['area_sqm'].sum() / share_all
        )
        .fillna(0.0)
        .values
    )
    result['aggregation_method'] = 'majority'
    return _flag(result, 0.5)


def _replicate(frame, to_level):
    """Copy a coarse value down to the finer units it contains."""
    dominant = (
        frame.sort_values('area_sqm', ascending=False)
        .drop_duplicates('to_id')
        .set_index('to_id')
    )
    result = pd.DataFrame({'geo_id': dominant.index})
    result['value'] = result['geo_id'].map(dominant['value']).values
    result['denominator'] = (
        result['geo_id'].map(dominant['population']).values
    )
    result['coverage'] = np.where(result['value'].notna(), 1.0, 0.0)
    result['aggregation_method'] = 'replicated'
    result['quality_flag'] = np.where(
        result['value'].notna(), 'ok', 'no_data'
    )
    return result


def _flag(result, min_coverage):
    flag = np.where(result['value'].notna(), 'ok', 'no_data')
    low = result['value'].notna() & (result['coverage'] < min_coverage)
    flag = np.where(low, 'low_coverage', flag)
    result['quality_flag'] = flag
    return result


def harmonise(
    values,
    native_scale,
    method='population_weighted_mean',
    levels=None,
    value_column='value',
    id_column='geo_id',
    min_coverage=0.5,
    include_optional=True,
):
    """Produce every reporting geography from one native-scale result.

    Levels finer than the native scale are produced by replication and
    flagged accordingly; levels coarser than it use ``method``.
    """
    if native_scale not in vocab.GEO_LEVELS:
        raise ValueError(f'{native_scale!r} is not a reporting geography')
    if levels is None:
        levels = list(vocab.REQUIRED_GEO_LEVELS)
        if include_optional:
            levels += [
                level
                for level in vocab.OPTIONAL_GEO_LEVELS
                if not _finer(level, native_scale)
            ]
    outputs = []
    for level in levels:
        if level == native_scale:
            frame = _complete(
                _passthrough(values, value_column, id_column),
                level,
                'native',
            )
        elif _finer(level, native_scale):
            frame = to_level(
                values,
                native_scale,
                level,
                method='replicated',
                value_column=value_column,
                id_column=id_column,
            )
        else:
            frame = to_level(
                values,
                native_scale,
                level,
                method=method,
                value_column=value_column,
                id_column=id_column,
                min_coverage=min_coverage,
            )
        frame.insert(0, 'geo_level', level)
        frame['native_scale'] = native_scale
        outputs.append(frame)
    return pd.concat(outputs, ignore_index=True)


def label(harmonised, metadata, measure_id, note=None):
    """Attach indicator and measure identity to a harmonised frame.

    Turns the output of :func:`harmonise` into rows conforming to the
    results schema.
    """
    declared = {m['id'] for m in metadata.get('measures', [])}
    if measure_id not in declared:
        raise ValueError(
            f'{measure_id!r} is not declared in the metadata; declared '
            f'measures are {sorted(declared)}'
        )
    frame = harmonised.copy()
    frame['indicator_id'] = metadata['indicator']['id']
    frame['indicator_code'] = metadata['indicator']['code']
    frame['measure_id'] = measure_id
    frame['note'] = note
    return frame.reindex(columns=list(vocab.RESULT_COLUMNS))


def assemble(labelled):
    """Concatenate labelled frames into one deliverable table."""
    return pd.concat(list(labelled), ignore_index=True).reindex(
        columns=list(vocab.RESULT_COLUMNS)
    )


# --------------------------------------------------------------------
# Builders for common calculation shapes
# --------------------------------------------------------------------
def count_features(features, geo_level, per=None, predicate='intersects'):
    """Count features per unit, optionally normalised.

    ``per`` may be ``None`` (raw count), ``'sqkm'`` or
    ``'1000_persons'``.  Units with no resident population return NaN
    for the per-capita form rather than infinity.
    """
    import geopandas as gpd

    units = geography.load(geo_level)
    features = features.to_crs(units.crs)
    joined = gpd.sjoin(
        features[['geometry']],
        units[['geo_id', 'geometry']],
        how='inner',
        predicate=predicate,
    )
    counts = joined.groupby('geo_id').size()
    result = units[['geo_id', 'area_sqm', 'population']].copy()
    result['value'] = (
        result['geo_id'].map(counts).fillna(0).astype(float)
    )
    if per == 'sqkm':
        result['value'] = result['value'] / (result['area_sqm'] / 1e6)
    elif per == '1000_persons':
        population = result['population'].astype(float)
        result['value'] = np.where(
            population > 0,
            result['value'] / (population / 1000.0),
            np.nan,
        )
    elif per is not None:
        raise ValueError("per must be None, 'sqkm' or '1000_persons'")
    return result[['geo_id', 'value']]


def distance_to_nearest(features, geo_level, cap=None):
    """Straight-line distance (m) from each unit to the nearest feature.

    The ``proximity`` lens.  Distance is measured from the unit's
    representative point, **in a straight line** -- not along the
    street network.  Network distance is what people actually walk, so
    where it is available (the GHSCI pipeline produces it for WP01)
    prefer it, and say which you used in the measure description.

    ``cap`` truncates distances beyond a given value, which is often
    sensible: the difference between 4 km and 9 km from a library is
    not a difference anyone experiences.
    """
    import geopandas as gpd

    units = geography.load(geo_level)
    features = features.to_crs(units.crs)
    points = units.copy()
    points['geometry'] = points.representative_point()
    joined = gpd.sjoin_nearest(
        points[['geo_id', 'geometry']],
        features[['geometry']],
        how='left',
        distance_col='value',
    ).drop_duplicates(subset='geo_id')
    result = joined[['geo_id', 'value']].copy()
    if cap is not None:
        result['value'] = result['value'].clip(upper=cap)
    return result.reset_index(drop=True)


def dominant_class(polygons, geo_level, column):
    """The class covering most of each unit's area.

    For categorical surfaces -- land use type, climate zone, hazard
    category.  Returns the class label, not a number, so deliver it as
    an ``ordinal`` measure with a documented encoding, or use it to
    derive a share (e.g. "percent residential") which is usually more
    useful in a composite.
    """
    import geopandas as gpd

    units = geography.load(geo_level)
    polygons = polygons.to_crs(units.crs)
    pieces = gpd.overlay(
        units[['geo_id', 'geometry']],
        polygons[[column, 'geometry']],
        how='intersection',
        keep_geom_type=False,
    )
    pieces['a'] = pieces.geometry.area
    winner = (
        pieces.groupby(['geo_id', column])['a']
        .sum()
        .reset_index()
        .sort_values('a', ascending=False)
        .drop_duplicates('geo_id')
        .set_index('geo_id')
    )
    result = units[['geo_id']].copy()
    result['value'] = result['geo_id'].map(winner[column])
    return result


def areal_share(polygons, geo_level, as_percentage=False):
    """Share of each unit's area covered by ``polygons`` (0-1)."""
    import geopandas as gpd

    units = geography.load(geo_level)
    polygons = polygons.to_crs(units.crs)
    dissolved = gpd.GeoDataFrame(
        geometry=[polygons.union_all()], crs=units.crs
    )
    pieces = gpd.overlay(
        units[['geo_id', 'geometry']],
        dissolved,
        how='intersection',
        keep_geom_type=False,
    )
    covered = pieces.assign(a=pieces.geometry.area).groupby('geo_id')[
        'a'
    ].sum()
    result = units[['geo_id', 'area_sqm']].copy()
    result['value'] = (
        result['geo_id'].map(covered).fillna(0.0) / result['area_sqm']
    )
    if as_percentage:
        result['value'] = result['value'] * 100
    return result[['geo_id', 'value']]


def network_share(edges, geo_level, attribute, positive=1):
    """Length-weighted share of network segments meeting a condition.

    ``attribute`` is a boolean or 0/1 column on ``edges`` (e.g.
    'has_sidewalk', 'has_lighting').  Segments are cut at unit
    boundaries so that a long road is attributed to each unit it
    passes through.
    """
    import geopandas as gpd

    units = geography.load(geo_level)
    edges = edges.to_crs(units.crs)
    pieces = gpd.overlay(
        edges[[attribute, 'geometry']],
        units[['geo_id', 'geometry']],
        how='intersection',
        keep_geom_type=False,
    )
    pieces['length_m'] = pieces.geometry.length
    total = pieces.groupby('geo_id')['length_m'].sum()
    matching = (
        pieces[pieces[attribute] == positive]
        .groupby('geo_id')['length_m']
        .sum()
    )
    result = units[['geo_id']].copy()
    result['value'] = (
        result['geo_id'].map(matching).fillna(0.0)
        / result['geo_id'].map(total)
    )
    return result[['geo_id', 'value']]


def zonal_statistic(raster_path, geo_level, statistic='mean', band=1):
    """Summarise a raster within each unit of a reporting geography."""
    import rasterio
    from rasterio.mask import mask

    units = geography.load(geo_level)
    functions = {
        'mean': np.nanmean,
        'median': np.nanmedian,
        'max': np.nanmax,
        'min': np.nanmin,
        'sum': np.nansum,
    }
    if statistic not in functions:
        raise ValueError(f'statistic must be one of {sorted(functions)}')
    reduce = functions[statistic]
    values = []
    with rasterio.open(raster_path) as source:
        units = units.to_crs(source.crs)
        for geometry in units.geometry:
            try:
                data, _ = mask(
                    source, [geometry], crop=True, filled=True, nodata=np.nan
                )
            except ValueError:
                values.append(np.nan)
                continue
            window = data[band - 1].astype('float64')
            if source.nodata is not None:
                window[window == source.nodata] = np.nan
            values.append(
                np.nan if np.all(np.isnan(window)) else float(reduce(window))
            )
    result = geography.units(geo_level)[['geo_id']].copy()
    result['value'] = values
    return result
