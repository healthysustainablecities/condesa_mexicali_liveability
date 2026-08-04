"""Shared tooling for the Mexicali Urban Liveability Index (ULI).

A thin layer over pandas/geopandas whose only job is to make results
produced by different analysts, from different data, at different
scales, land in the same shape::

    import uli

    reg = uli.register.load()               # what am I calculating?
    meta = uli.metadata_stub(91)            # documentation skeleton
    native = ...                            # your calculation
    results = uli.harmonise(native, 'manzana')
    uli.write_indicator(results, meta)      # validated deliverable

See ``docs/analyst_guide.md`` to get started and
``schema/ULI_output_schema.md`` for the specification.
"""

from . import (
    aggregate,
    exposure,
    geography,
    io,
    register,
    templates,
    validate,
    vocab,
)
from .aggregate import (
    areal_share,
    assemble,
    count_features,
    harmonise,
    label,
    network_share,
    to_level,
    zonal_statistic,
)
from .exposure import exposed_share, score, weighted_summary
from .io import collect, read_indicator, to_geopackage, to_wide, write_indicator
from .templates import metadata_stub, todos
from .validate import check, validate_metadata, validate_results
from .vocab import SCHEMA_VERSION

__version__ = SCHEMA_VERSION

__all__ = [
    'aggregate',
    'areal_share',
    'assemble',
    'check',
    'collect',
    'count_features',
    'exposed_share',
    'exposure',
    'geography',
    'harmonise',
    'io',
    'label',
    'metadata_stub',
    'network_share',
    'read_indicator',
    'score',
    'register',
    'templates',
    'to_geopackage',
    'to_level',
    'to_wide',
    'weighted_summary',
    'todos',
    'validate',
    'validate_metadata',
    'validate_results',
    'vocab',
    'write_indicator',
    'zonal_statistic',
]
