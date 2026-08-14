"""Controlled vocabularies for the Mexicali Urban Liveability Index.

Every enumeration used by the output schema is defined here once, so
that the JSON schemas, the validator and the notebooks cannot drift
apart.  If a term is not in this module, it is not a valid value.
"""

SCHEMA_VERSION = '1.0.0'

PROJECT_CRS = 'EPSG:6366'  # Mexico ITRF2008 / UTM zone 11N
PROJECT_CRS_NAME = 'Mexico ITRF2008 / UTM zone 11N'

# --------------------------------------------------------------------
# Geography
# --------------------------------------------------------------------
# Reporting geographies, finest to coarsest.  Every indicator must be
# delivered for the REQUIRED_GEO_LEVELS; the others are encouraged
# where the underlying data genuinely support them.
GEO_LEVELS = {
    'grid_100m': (
        '100 m regular grid over the study region (optional; supply '
        'only where the source data are genuinely this fine)'
    ),
    'manzana': (
        'INEGI census block (manzana); geo_id is the 16-character '
        'CVEGEO'
    ),
    'condesa_lote': (
        'Individual lot within the Condesa new development area '
        '(optional detail scale)'
    ),
    'condesa_fraccionamiento': (
        'Condesa new-development subdivision polygon; the project '
        'focus area in south-east Mexicali'
    ),
    'grid_1000m': '1 km regular grid over the study region',
    'ageb': (
        'INEGI basic geostatistical area (AGEB); geo_id is the '
        '13-character CVEGEO'
    ),
    'city': 'The Mexicali study region as a whole (single unit)',
}

REQUIRED_GEO_LEVELS = (
    'city',
    'ageb',
    'manzana',
    'grid_1000m',
    'condesa_fraccionamiento',
)

OPTIONAL_GEO_LEVELS = ('grid_100m', 'condesa_lote')

# Coarse-to-fine ordering used when checking that a result has not
# been presented at a finer scale than it was measured at.  Ordered by
# the median unit area of the Mexicali reference geographies, so AGEBs
# (median 0.36 km²) sit inside the 1 km grid, and manzanas (median
# 0.006 km²) inside the 100 m grid.
GEO_RESOLUTION_ORDER = (
    'city',
    'grid_1000m',
    'ageb',
    'condesa_fraccionamiento',
    'grid_100m',
    'manzana',
    'condesa_lote',
)

# --------------------------------------------------------------------
# Analytical lenses ("Lens / Enfoque" in the indicator workbook)
# --------------------------------------------------------------------
LENSES = {
    'proximity': (
        'Distance to the closest instance (m), measured along the '
        'pedestrian network unless otherwise documented'
    ),
    'accessibility': (
        'Whether an instance is reachable within a policy-relevant '
        'threshold; reported as the share of population (or of the '
        'unit) meeting the threshold'
    ),
    'quantity': 'Count or amount within an area or threshold distance',
    'density': (
        'Amount relative to another unit (per km², per 1,000 persons, '
        'or percentage coverage)'
    ),
    'diversity': 'Mix or evenness (e.g. entropy) within an area',
    'quality': (
        'A graded or composite assessment of condition or suitability'
    ),
    'equity': (
        'Distributional summary across the population.  Derived '
        'centrally from the finest-scale results -- analysts do not '
        'compute this lens themselves (see the schema document)'
    ),
}

# Lenses an analyst may submit.  'equity' is produced centrally.
ANALYST_LENSES = tuple(k for k in LENSES if k != 'equity')

# --------------------------------------------------------------------
# Measure properties (recorded in the indicator metadata)
# --------------------------------------------------------------------
VALUE_TYPES = {
    'continuous': 'Unbounded or interval-scaled real number',
    'count': 'Non-negative integer count',
    'proportion': 'Bounded 0-1',
    'percentage': 'Bounded 0-100',
    'rate': 'Count per denominator (per capita, per km², per 1,000)',
    'index': 'Constructed score, bounded or standardised',
    'ordinal': 'Ordered categories encoded as integers',
    'binary': '0 or 1',
}

# How a higher value should be read for the liveability composite.
DIRECTIONS = {
    'higher_is_better': 'A higher value indicates better liveability',
    'lower_is_better': 'A higher value indicates worse liveability',
    'non_monotonic': (
        'Neither extreme is desirable; a target range or transform '
        'must be supplied in the metadata'
    ),
    'descriptive': (
        'Context variable; not a candidate for the composite index'
    ),
}

# How values were carried from the native scale to a reporting scale.
AGGREGATION_METHODS = {
    'native': 'Computed directly at this scale; no aggregation applied',
    'population_weighted_mean': (
        'Mean over finer units weighted by resident population '
        '(use for anything experienced by people)'
    ),
    'area_weighted_mean': (
        'Mean over finer units weighted by area (use for land cover, '
        'coverage and exposure surfaces)'
    ),
    'length_weighted_mean': (
        'Mean over network segments weighted by segment length'
    ),
    'sum': 'Sum of finer units (use for counts and totals)',
    'areal_share': (
        'Area of a feature falling inside the unit, divided by unit '
        'area'
    ),
    'majority': 'Modal category of the finer units',
    'replicated': (
        'The value of a coarser unit copied down to finer units; the '
        'result carries no spatial variation at this scale'
    ),
    'zonal_statistic': 'Zonal summary of a raster within the unit',
    'nearest_feature': (
        'Value taken from the nearest measurement location (e.g. an '
        'air quality monitor); document the maximum distance used'
    ),
    'interpolated': (
        'Value from a fitted spatial model or interpolation surface'
    ),
}

# How a measure summarises over time.  Several indicators in the
# workbook are the same construct at different time bases -- an air
# quality index value, that value evaluated against a standard, and the
# frequency of compliance across a year; or mean July temperature
# versus days above a comfort threshold.  Declaring the time basis
# lets those be delivered as one coherent measure family instead of
# being mistaken for separate indicators.
TEMPORAL_BASES = {
    'point_in_time': 'A single date, epoch or snapshot',
    'annual_mean': 'Mean over a year',
    'seasonal_mean': (
        'Mean over a named season (declare which in parameters; in '
        'Mexicali the summer maximum period is usually the one that '
        'matters)'
    ),
    'monthly_mean': 'Mean over a named month',
    'daytime_mean': 'Mean over daytime hours',
    'annual_maximum': 'Maximum observed within a year',
    'threshold_exceedance_days': (
        'Count of days in a year exceeding a threshold'
    ),
    'threshold_compliance_days': (
        'Count of days in a year meeting a standard'
    ),
    'threshold_share': (
        'Share of the period meeting or exceeding a threshold'
    ),
    'multi_year_mean': 'Mean over several years',
    'not_applicable': 'The measure has no meaningful time basis',
}

QUALITY_FLAGS = {
    'ok': 'Value is fit for use',
    'low_coverage': (
        'Fewer than the required share of the unit had valid input '
        'data; interpret with caution'
    ),
    'imputed': 'Value was filled from a model or a neighbouring unit',
    'suppressed': (
        'Value withheld (e.g. small counts risking disclosure); value '
        'must be empty'
    ),
    'not_applicable': (
        'The measure is undefined for this unit (e.g. no resident '
        'population); value must be empty'
    ),
    'no_data': 'No input data available for this unit; value empty',
}

DENOMINATOR_TYPES = {
    'population': 'Resident population used to weight or normalise',
    'area_sqkm': 'Unit area in km²',
    'dwellings': 'Dwelling or lot count',
    'network_length_km': 'Pedestrian/road network length in km',
    'sample_points': 'Count of network sample points',
    'none': 'No denominator applies',
}

# --------------------------------------------------------------------
# Canonical parameters, so that measures are comparable between
# analysts.  Deviate only with a documented, evidence-based reason.
# --------------------------------------------------------------------
DISTANCE_THRESHOLDS_M = (300, 500, 800, 1000, 1600)

ACCESSIBILITY_BANDS_M = (
    (0, 300),
    (300, 600),
    (600, 1200),
    (1200, 1500),
    (1500, None),
)

# --------------------------------------------------------------------
# Results table
# --------------------------------------------------------------------
RESULT_COLUMNS = (
    'indicator_id',
    'indicator_code',
    'measure_id',
    'geo_level',
    'geo_id',
    'value',
    'denominator',
    'native_scale',
    'aggregation_method',
    'coverage',
    'quality_flag',
    'note',
)

RESULT_COLUMN_DESCRIPTIONS = {
    'indicator_id': (
        "Integer '#' of the parent indicator in the ULI workbook"
    ),
    'indicator_code': 'Stable snake_case slug for the parent indicator',
    'measure_id': (
        'Unique slug for this specific measure, of the form '
        '<indicator_code>__<lens>[_<parameter>]'
    ),
    'geo_level': 'One of the reporting geographies (see GEO_LEVELS)',
    'geo_id': (
        'Identifier of the unit within that geography, exactly as '
        'supplied in the reference geopackage'
    ),
    'value': (
        'The measured value; empty only where quality_flag is '
        'suppressed, not_applicable or no_data'
    ),
    'denominator': (
        'Population, area or other denominator underlying the value '
        '(type declared per measure in the metadata)'
    ),
    'native_scale': (
        'The geography level at which the measure was actually '
        'computed before aggregation'
    ),
    'aggregation_method': (
        'How the native-scale value was carried to this geo_level'
    ),
    'coverage': (
        'Share (0-1) of the unit -- by population or area, as declared '
        'in the metadata -- with valid input data'
    ),
    'quality_flag': 'One of QUALITY_FLAGS',
    'note': 'Optional free text for this row',
}

# Rows with these flags must have an empty value.
EMPTY_VALUE_FLAGS = ('suppressed', 'not_applicable', 'no_data')

# --------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------
# Strength of the health evidence offered for an indicator.  Analysts
# should aim for 'systematic_review' or better; 'expert_guidance'
# (e.g. WHO, UN-Habitat) is acceptable where trials are impossible.
EVIDENCE_TYPES = {
    'meta_analysis': 'Meta-analysis of multiple studies',
    'systematic_review': 'Systematic review without pooled estimate',
    'expert_guidance': (
        'Guidance from a reputable body (WHO, UN-Habitat, national '
        'health authority)'
    ),
    'cohort': 'Longitudinal / cohort study',
    'natural_experiment': 'Natural or quasi-experiment',
    'case_control': 'Case-control study',
    'cross_sectional': 'Cross-sectional study',
    'modelling': 'Health impact assessment or simulation study',
    'narrative_review': 'Narrative or scoping review',
}

# Pathways from the built environment to health.  Each measure must
# name at least one, to keep the indicator set anchored to health and
# wellbeing rather than to convention.
HEALTH_PATHWAYS = {
    'physical_activity_transport': (
        'Supports walking or cycling for transport'
    ),
    'physical_activity_recreation': (
        'Supports recreational walking, play, sport or exercise'
    ),
    'social_interaction': (
        'Supports social contact, community participation and reduced '
        'loneliness'
    ),
    'heat_exposure': 'Alters exposure to heat and heat stress',
    'air_pollution_exposure': 'Alters exposure to air pollutants',
    'noise_exposure': 'Alters exposure to noise',
    'injury_risk': 'Alters risk of traffic or other injury',
    'crime_and_safety': 'Alters crime exposure or perceived safety',
    'food_environment': 'Alters access to affordable, healthy food',
    'healthcare_access': 'Alters access to health and social services',
    'education_access': 'Alters access to education',
    'economic_security': (
        'Alters income, employment or housing cost burden, and so the '
        'resources available for health'
    ),
    'housing_conditions': 'Alters dwelling conditions or crowding',
    'hazard_exposure': (
        'Alters exposure to flooding, fire, industrial or waste '
        'hazards'
    ),
    'restoration_and_mental_health': (
        'Supports psychological restoration and mental wellbeing '
        '(e.g. greenness, blue space)'
    ),
}

LICENCE_HINTS = (
    'CC-BY-4.0',
    'CC-BY-SA-4.0',
    'CC0-1.0',
    'ODbL-1.0',
    'INEGI Terminos de Libre Uso de la Informacion',
    'Government of Mexico open data',
    'Proprietary - redistribution not permitted',
    'Unknown - to be confirmed',
)
