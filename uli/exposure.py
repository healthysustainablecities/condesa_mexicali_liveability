"""Population exposure statistics over delivered indicator results.

This is the reporting side of the project, not the analyst side.  Work
packages deliver indicator values for units of geography; this module
turns those into statements about *people* -- what share of the
population experiences what -- and into population-weighted summaries
that the composite index can build on.

Analysts calculating urban fabric and exposure surfaces do not need
anything here; choosing a population denominator is a decision for the
reporting step, made once, in one place.

Population bases
----------------
Every function takes a ``population`` argument naming which denominator
to weight by:

``population``
    GHS-POP 2025.  Observed population today.  Use for statements
    about people who currently live in Mexicali.
``population_2030``
    GHS-POP 2030.  The projection as published.  Note it adds ~20,000
    people city-wide but only 5 to Condesa: it grows existing built-up
    cells and does not discover the development.
``population_planned``
    Condesa only: one household per residential lot at the assumed
    mean household size.  Zero everywhere else.
``population_scenario_2030``
    GHS-POP 2030 outside the Condesa footprint, plus the planned
    occupancy inside it.  This is the scenario denominator: *if the
    development is fully occupied by 2030, on top of the projected
    city*.  Results derived from it are conditional on a declared
    assumption, and should be reported as such.
``pop_census_2020``
    INEGI 2020, retained for reference and comparison.
"""

import numpy as np
import pandas as pd

from . import geography

POPULATION_BASES = (
    'population',
    'population_2030',
    'population_planned',
    'population_scenario_2030',
    'pop_census_2020',
)

DEFAULT_POPULATION = 'population_scenario_2030'
DEFAULT_LEVEL = 'grid_100m'


def _frame(results, measure_id, geo_level, population):
    """Join one measure at one geography to its population weights."""
    if population not in POPULATION_BASES:
        raise ValueError(
            f'{population!r} is not a population basis; expected one '
            f'of {list(POPULATION_BASES)}'
        )
    subset = results[
        (results['measure_id'] == measure_id)
        & (results['geo_level'] == geo_level)
    ]
    if subset.empty:
        raise ValueError(
            f'No results for measure {measure_id!r} at {geo_level!r}'
        )
    units = geography.units(geo_level)[['geo_id', population, 'area_sqm']]
    frame = subset.merge(units, on='geo_id', how='left')
    frame['weight'] = frame[population].fillna(0.0)
    return frame


def areas(geo_level=DEFAULT_LEVEL):
    """Return ``{'Condesa': ids, 'Rest of city': ids}`` for a level.

    At `condesa_fraccionamiento` and `condesa_lote` the split is
    exact.  At grid and census levels a unit counts as Condesa if it
    *overlaps* the development, so a cell straddling the boundary is
    attributed wholly to Condesa; the group population is therefore
    slightly overstated (about 0.6% at 100 m).  Report Condesa at
    `condesa_fraccionamiento` when the exact figure matters.
    """
    condesa = geography.condesa_ids(geo_level)
    everything = set(geography.units(geo_level)['geo_id'])
    return {
        'Condesa': condesa,
        'Rest of city': everything - condesa,
    }


def exposed_share(
    results,
    measure_id,
    threshold,
    comparison='at_or_below',
    geo_level=DEFAULT_LEVEL,
    population=DEFAULT_POPULATION,
    groups=None,
):
    """Share of population whose unit meets a threshold.

    ``comparison`` is ``at_or_below``, ``below``, ``at_or_above`` or
    ``above``.  Returns a DataFrame with one row per group (the whole
    study area, plus Condesa and the rest of the city by default),
    carrying the population meeting the threshold, the population with
    a value at all, and the share.

    Population with no value is reported separately rather than being
    treated as unexposed -- an indicator that does not reach an area
    is not evidence that the area is fine.
    """
    frame = _frame(results, measure_id, geo_level, population)
    tests = {
        'at_or_below': lambda v: v <= threshold,
        'below': lambda v: v < threshold,
        'at_or_above': lambda v: v >= threshold,
        'above': lambda v: v > threshold,
    }
    if comparison not in tests:
        raise ValueError(f'comparison must be one of {sorted(tests)}')
    frame['meets'] = tests[comparison](frame['value'])
    groups = groups or areas(geo_level)

    rows = [_exposure_row('Study area', frame, threshold, comparison)]
    for name, ids in groups.items():
        rows.append(
            _exposure_row(
                name,
                frame[frame['geo_id'].isin(ids)],
                threshold,
                comparison,
            )
        )
    return pd.DataFrame(rows)


def _exposure_row(name, frame, threshold, comparison):
    valued = frame[frame['value'].notna()]
    with_value = valued['weight'].sum()
    meeting = valued.loc[valued['meets'], 'weight'].sum()
    return {
        'group': name,
        'measure_id': frame['measure_id'].iloc[0] if len(frame) else None,
        'comparison': f'{comparison} {threshold}',
        'population_total': frame['weight'].sum(),
        'population_with_value': with_value,
        'population_meeting': meeting,
        'share_meeting': (
            meeting / with_value if with_value > 0 else np.nan
        ),
        'population_without_value': frame['weight'].sum() - with_value,
        'units': len(frame),
    }


def weighted_summary(
    results,
    measure_id,
    geo_level=DEFAULT_LEVEL,
    population=DEFAULT_POPULATION,
    groups=None,
):
    """Population-weighted mean, median and quartiles of one measure."""
    frame = _frame(results, measure_id, geo_level, population)
    groups = groups or areas(geo_level)
    rows = [_summary_row('Study area', frame)]
    for name, ids in groups.items():
        rows.append(
            _summary_row(name, frame[frame['geo_id'].isin(ids)])
        )
    return pd.DataFrame(rows)


def _summary_row(name, frame):
    valued = frame[frame['value'].notna() & (frame['weight'] > 0)]
    if valued.empty:
        return {
            'group': name,
            'population': frame['weight'].sum(),
            'mean': np.nan,
            'p25': np.nan,
            'median': np.nan,
            'p75': np.nan,
        }
    values = valued['value'].to_numpy(dtype=float)
    weights = valued['weight'].to_numpy(dtype=float)
    return {
        'group': name,
        'population': frame['weight'].sum(),
        'mean': float(np.average(values, weights=weights)),
        'p25': _weighted_quantile(values, weights, 0.25),
        'median': _weighted_quantile(values, weights, 0.5),
        'p75': _weighted_quantile(values, weights, 0.75),
    }


def _weighted_quantile(values, weights, quantile):
    """Population-weighted quantile of a set of unit values."""
    order = np.argsort(values)
    values, weights = values[order], weights[order]
    cumulative = np.cumsum(weights) - 0.5 * weights
    cumulative /= weights.sum()
    return float(np.interp(quantile, cumulative, values))


# --------------------------------------------------------------------
# Provisional composite
# --------------------------------------------------------------------
def minmax(series, direction, lower=None, upper=None):
    """Scale a measure to 0-1, oriented so that 1 is always better.

    The default normalisation.  How the composite index is actually
    built is a later decision; this exists so the plumbing can be
    exercised end to end now, and so that swapping in a different
    normalisation is a one-argument change rather than a rewrite.
    """
    values = pd.to_numeric(series, errors='coerce')
    lower = values.min() if lower is None else lower
    upper = values.max() if upper is None else upper
    if upper == lower:
        return pd.Series(np.nan, index=values.index)
    scaled = (values - lower) / (upper - lower)
    scaled = scaled.clip(0, 1)
    return scaled if direction == 'higher_is_better' else 1 - scaled


def score(
    results,
    catalogue,
    geo_level=DEFAULT_LEVEL,
    population=DEFAULT_POPULATION,
    weights=None,
    normalise=minmax,
    measures=None,
    groups=None,
):
    """Assemble a provisional population-weighted liveability score.

    PROVISIONAL.  Equal weights, min-max normalisation, simple mean of
    available measures.  The point is to demonstrate that delivered
    results compose without renegotiation, and to give the eventual
    index step a working harness -- not to assert how the Mexicali
    Liveability Index should be calculated.

    Only measures flagged ``include_in_index`` are used, and only those
    whose values vary at ``geo_level`` -- a measure replicated from a
    coarser scale is a constant there and contributes nothing but
    noise to a within-city comparison.

    Returns ``(unit_scores, group_summary)``.
    """
    catalogue = catalogue[catalogue['include_in_index'].fillna(False)]
    if measures is not None:
        catalogue = catalogue[catalogue['measure_id'].isin(measures)]
    if catalogue.empty:
        raise ValueError('No measures flagged for inclusion in the index')

    units = geography.units(geo_level)[['geo_id', population]]
    columns, used, skipped = {}, [], []
    for row in catalogue.itertuples():
        subset = results[
            (results['measure_id'] == row.measure_id)
            & (results['geo_level'] == geo_level)
        ]
        if subset.empty:
            skipped.append((row.measure_id, 'no results at this scale'))
            continue
        if (subset['aggregation_method'] == 'replicated').all():
            skipped.append(
                (row.measure_id, 'replicated: constant at this scale')
            )
            continue
        aligned = units.merge(
            subset[['geo_id', 'value']], on='geo_id', how='left'
        )
        columns[row.measure_id] = normalise(
            aligned['value'], row.direction
        ).values
        used.append(row.measure_id)

    if not used:
        raise ValueError(
            'No measures survived: ' + '; '.join(f'{m} ({w})' for m, w in skipped)
        )

    frame = pd.DataFrame(columns, index=units.index)
    if weights:
        applied = pd.Series(
            {m: weights.get(m, 0.0) for m in used}, dtype=float
        )
    else:
        applied = pd.Series(1.0, index=used)
    applied = applied / applied.sum()

    weighted = frame.mul(applied, axis=1)
    present = frame.notna().mul(applied, axis=1).sum(axis=1)
    unit_scores = pd.DataFrame(
        {
            'geo_id': units['geo_id'],
            'geo_level': geo_level,
            'score': weighted.sum(axis=1) / present.replace(0, np.nan),
            'measures_available': frame.notna().sum(axis=1),
            'weight_available': present,
            population: units[population],
        }
    )

    groups = groups or areas(geo_level)
    rows = [_score_row('Study area', unit_scores, population)]
    for name, ids in groups.items():
        rows.append(
            _score_row(
                name,
                unit_scores[unit_scores['geo_id'].isin(ids)],
                population,
            )
        )
    summary = pd.DataFrame(rows)
    summary.attrs['measures_used'] = used
    summary.attrs['measures_skipped'] = skipped
    summary.attrs['population_basis'] = population
    return unit_scores, summary


def _score_row(name, frame, population):
    valued = frame[
        frame['score'].notna() & (frame[population].fillna(0) > 0)
    ]
    values = valued['score'].to_numpy(dtype=float)
    weights = valued[population].to_numpy(dtype=float)
    return {
        'group': name,
        'population': frame[population].sum(),
        'population_scored': weights.sum(),
        'mean_score_population_weighted': (
            float(np.average(values, weights=weights))
            if len(values)
            else np.nan
        ),
        'mean_score_unweighted': (
            float(values.mean()) if len(values) else np.nan
        ),
        'units': len(frame),
    }
