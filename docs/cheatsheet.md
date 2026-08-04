# Cheat sheet

One page. Print it, keep it open, ignore the rest until you need it.

## The whole job

```python
import uli

meta   = uli.metadata_stub(91, analyst=ANALYST)   # documentation, pre-filled
native = <one of the recipes below>               # geo_id + value
results = uli.harmonise(native, native_scale='grid_100m',
                        method='population_weighted_mean')
results = uli.label(results, meta, 'my_code__density_per_sqkm')
print(uli.check(results, meta))                   # validate
uli.write_indicator(results, meta)                # deliver
```

Everything you produce is a two-column table: **`geo_id`** and **`value`**.

## Recipes → [`notebooks/00b_cookbook.ipynb`](../notebooks/00b_cookbook.ipynb)

| Your data | Call | Recipe |
|---|---|---|
| Points, want a count or density | `uli.count_features(pts, level, per='sqkm')` | 1 |
| Points, want distance to nearest | `uli.distance_to_nearest(pts, level, cap=3000)` | 2 |
| Polygons, want % of area covered | `uli.areal_share(poly, level, as_percentage=True)` | 3 |
| Polygons with a category | `uli.dominant_class(poly, level, 'class_col')` | 4 |
| Lines with a yes/no attribute | `uli.network_share(edges, level, 'has_x')` | 5 |
| A raster | `uli.zonal_statistic('r.tif', level, 'mean')` | 6 |
| A table already per unit | `df.rename(columns={'CVEGEO': 'geo_id'})` | 7 |
| One city-wide number | `native_scale='city'`, let it replicate | 8 |

`per=` is `None`, `'sqkm'` or `'1000_persons'`.
`zonal_statistic` takes `'mean'`, `'median'`, `'min'`, `'max'`, `'sum'`.

## Reporting geographies

| Level | Units | Use it when |
|---|---|---|
| `grid_100m` | 22,355 | your data is fine-grained — **reaches all 40 Condesa units** |
| `manzana` | 14,236 | census block data — reaches only 33 of 40 Condesa units |
| `condesa_lote` | 14,989 | lot-level detail in the development |
| `ageb` | 436 | census or survey data |
| `condesa_fraccionamiento` | 40 | the focus area |
| `grid_1000m` | 302 | coarse surfaces |
| `city` | 1 | a single city-wide figure |

```python
uli.geography.load('ageb')     # GeoDataFrame, with geometry
uli.geography.units('ageb')    # just the table
```

## Which `method` for `harmonise`

| Your measure is… | Use |
|---|---|
| experienced by people (access, exposure, comfort) | `population_weighted_mean` |
| a property of land (cover, temperature, land use) | `area_weighted_mean` |
| a property of streets | `length_weighted_mean` |
| a count of things | `sum` |

## Filling in the metadata

```python
uli.todos(meta)          # what is still outstanding
```

Minimum before it will validate:

- `rationale.statement` — why it matters, rewritten
- `rationale.health_pathways` — at least one, from `uli.vocab.HEALTH_PATHWAYS`
- `rationale.evidence` — at least one **independent** citation, with an effect
  size
- `data_sources` — citation, URL, `date_retrieved`, `licence`,
  `condesa_coverage`
- every measure — `unit`, `value_type`, `direction`, `native_scale`,
  `aggregation_method`
- `method.summary` and `method.condesa_treatment`

## Rules that are not negotiable

- **Natural units.** No normalising, no rescaling, no z-scores. Set
  `direction` instead.
- **No reverse-coding.** A high value that is bad stays high; declare
  `lower_is_better`.
- **Honest `native_scale`.** Never claim a finer scale than you measured.
- **Cover Condesa**, or say in `method.condesa_treatment` why you cannot.

## Sanity check before you call it done

```python
units = uli.geography.load('manzana').merge(
    results.query("geo_level == 'manzana'"), on='geo_id', how='left')
ax = units.plot(column='value', legend=True, figsize=(10, 6),
                missing_kwds={'color': 'lightgrey'})
uli.geography.load('condesa_fraccionamiento').boundary.plot(
    ax=ax, color='red', linewidth=1)
```

Are the extremes where you would expect? Does Condesa look plausible, or
suspiciously empty?

## Vocabulary

```python
uli.vocab.HEALTH_PATHWAYS       uli.vocab.EVIDENCE_TYPES
uli.vocab.GEO_LEVELS            uli.vocab.AGGREGATION_METHODS
uli.vocab.VALUE_TYPES           uli.vocab.TEMPORAL_BASES
uli.vocab.DIRECTIONS            uli.vocab.QUALITY_FLAGS
uli.vocab.DISTANCE_THRESHOLDS_M  # 300, 500, 800, 1000, 1600
```

## Stuck?

Cookbook §11 lists the common error messages and what they mean. If that does
not cover it, bring the error and the cell to the group — early is cheap.
