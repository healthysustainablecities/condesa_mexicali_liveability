# 3. Method recipes

Each recipe states a shared method once, in theory (what is computed) and in practice (where GHSCI computes it). It ends with what a re-implementation needs to hold to recalculate it. Indicator entries cite these recipes by number.

<a id="r1"></a>
## R1. Sample points and the pedestrian network

**Theory.** Liveability is measured at locations people live and walk from: points every 30 m along the pedestrian network. Each point lies on an edge between two nodes `n1` and `n2`, at along-edge distances `d1` and `d2` from them. A network distance from a point is the lesser of the two routes through its end nodes.

**Practice.**

- The network is built with OSMnx from the configured pedestrian query, which retains private and gated access in Mexicali, with `retain_all` so that disconnected gated communities are kept. Dangles shorter than half the sampling interval are pruned ([`process/subprocesses/_03_create_network_resources.py:776`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_03_create_network_resources.py#L776) `prune_short_dangles()`).
- Points are generated every `point_sampling_interval` = 30 m along each edge, from its start, excluding trunk roads and ways with `foot = no` ([`process/subprocesses/_07_locate_origins_destinations.py:16`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_07_locate_origins_destinations.py#L16) `nearest_node_locations()`).
- Duplicate points at junctions are dropped, points inside open space removed, and the set restricted to the urban study region.
- Because `sampling.sample_unpopulated_areas` is set, points are kept where no population is recorded (Condesa). One further point per Condesa lot is snapped to its nearest edge within 100 m ([`MX_Mexicali_2025_ULI.yml:108`](../data/MX_Mexicali_2025_ULI.yml#L108)). Lots further than 100 m from a mapped street lie in subdivisions whose streets are not in OpenStreetMap, and are left without a value rather than credited with access they do not have.

The analysis has 154,239 sample points.

**Recalculation.** Hold the points with their `n1`, `n2`, `d1`, `d2` and the network graph (edges with lengths). A network edit changes the graph, and the points on new edges.

<a id="r2"></a>
## R2. Network distance to the nearest destination, censored

**Theory.** For a destination set `D`, attached to the network at the end nodes of its nearest edge with offsets, the node distance is `D(n) = min over destinations (network distance(n, node) + offset)`. The point distance is

```text
d(p) = min( D(n1) + d1 ,  D(n2) + d2 )
```

Distances are searched in bands (300, 500, 1,000, 1,500 m) and censored at the largest: a node with no destination within 1,500 m has no distance, so neither does the point. A point's value can exceed 1,500 m by up to its offset along the edge.

**Practice.**

- Routing is undirected on edge length: pgRouting `pgr_drivingDistance` or, in memory, one Dijkstra from a super-source per destination set, limited to the largest band ([`process/subprocesses/_accessibility_spec.py:806`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L806) `_banded_distances()`, [`process/subprocesses/_accessibility_spec.py:1116`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L1116) `_nearest_distances_inmemory()`). Only origins not yet within reach of every destination are re-routed at each larger band.
- Point distances are taken from the node distances ([`process/subprocesses/setup_sp.py:888`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/setup_sp.py#L888) `create_full_nodes()`, [`process/subprocesses/setup_sp.py:951`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/setup_sp.py#L951) `process_distant_nodes()`).
- Each destination is a configured specification ([`MX_Mexicali_2025_ULI.yml:464`](../data/MX_Mexicali_2025_ULI.yml#L464)). Its distance is `sp_walk_nearest_node_<name>` at points and `avg_walk_dist_<name>` in areas.

**Recalculation.** Adding or removing a destination changes `d` only where it becomes, or stops being, the nearest. Run a Dijkstra from the changed destinations, limited to 1,500 m, and take the minimum with the stored distance; a removal needs the next-nearest, so store the second-nearest or re-route locally.

<a id="r3"></a>
## R3. Banded access, and distance from a disamenity

**Theory.** Binary access within distance `D`: `a = 1` if `d ≤ D`, else 0, where a missing distance (nothing within 1,500 m) is 0. For a disamenity (`direction: avoid`), the indicator is distance *from* it: `b = 1 − a`, so nothing within reach scores 1. For an area, the percentage of its sample points with access, `pct_access_walk_<name>_<D>m` (or `pct_beyond_…`).

**Practice.** [`process/subprocesses/_accessibility_spec.py:1272`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L1272) `sample_point_access()`, [`process/subprocesses/setup_sp.py:1057`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/setup_sp.py#L1057) `binary_access_score()`. A specification may set its own distances, as the petrol station does (250 m).

<a id="r4"></a>
## R4. Diversity of what is reachable

**Theory.** For a set of `k` configured sub-types, `c_g` is the number of distinct destinations of sub-type `g` reachable within distance `D`. Then

```text
p_g = c_g / Σ c          H = − Σ_{p_g > 0} p_g · ln p_g  /  ln k          (0 … 1)
R   = #{g : c_g > 0} / k                                                  (richness)
```

`k` is the number of configured sub-types, not the number present, so the score is comparable between places. Reaching nothing, or one sub-type only, scores 0. Counts at a point are interpolated from its end nodes, `c(p) = Σ_i (1 − d_i/(d1 + d2)) · c(n_i)`, so they may be fractional.

**Practice.** [`process/subprocesses/_accessibility_spec.py:299`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L299) `diversity_sets()`, [`process/subprocesses/_accessibility_spec.py:929`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L929) `_banded_counts()`, [`process/subprocesses/_accessibility_spec.py:466`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L466) `normalised_entropy()`, [`process/subprocesses/_accessibility_spec.py:493`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_accessibility_spec.py#L493) `richness()`. Sets are configured under [`MX_Mexicali_2025_ULI.yml:595`](../data/MX_Mexicali_2025_ULI.yml#L595). The ULI uses `sp_walk_diversity_<set>_500m`.

**Recalculation.** A destination added within `D` of a point adds 1 to its sub-type's count; recompute `H` at the points affected.

<a id="r5"></a>
## R5. Straight-line catchments

**Theory.** `d(p)` is the straight-line distance to the nearest station, searched to `max_distance`. Beyond it there is no value.

**Practice.**

- Each specification reads its own file and filter, clipped to the study region buffered by `max_distance` and outside the exclusion region ([`process/subprocesses/_euclidean_accessibility.py:66`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_euclidean_accessibility.py#L66) `resolve_spec()`, [`process/subprocesses/_euclidean_accessibility.py:177`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_euclidean_accessibility.py#L177) `import_destinations()`).
- The nearest station is found by a KNN search ([`process/subprocesses/_euclidean_accessibility.py:247`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_euclidean_accessibility.py#L247) `nearest_distances()`).
- Outputs are `sp_euclid_dist_<name>` and `avg_euclid_dist_<name>` ([`MX_Mexicali_2025_ULI.yml:679`](../data/MX_Mexicali_2025_ULI.yml#L679)).

<a id="r6"></a>
## R6. Level of traffic stress and the low-stress cycling network

**Theory.** Each link gets a level of traffic stress (LTS) from 1 (suitable for all) to 4, from its cycling facility, speed and assumed traffic. The low-stress network is the links with LTS ≤ 2 where cycling (or walking the bike) is permitted. Distance to the nearest destination along it follows R2, with bands of 500, 1,000, 2,000 and 5,000 m. The rules are in the entry [Cycling network by level of traffic stress](entries/lts_network.md).

**Practice.** [`process/subprocesses/_cycling_lts_network.py:546`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_lts_network.py#L546) `assign_lts()`, [`process/subprocesses/_cycling_lts_network.py:607`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_lts_network.py#L607) `add_impedance()`, [`process/subprocesses/_cycling_accessibility.py:469`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_accessibility.py#L469) `cycling_poi_distance()`. Output: `sp_cycle_safe_nearest_node_<dest>`.

<a id="r7"></a>
## R7. Linking externally prepared indicators

**Theory.** A value prepared outside GHSCI for a set of areas is attached to the matching reference areas and then replicated to the sample points the areas contain, so that it can be scored like any other indicator.

**Practice.**

- **Match by identifier** (`match: id`, UTCI) or **by geometry** (`match: geometry`, the work-package file, which has no identifiers) ([`process/subprocesses/_linkage_indicators.py:403`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_linkage_indicators.py#L403) `match_by_geometry()`). By geometry, an exact normalised match is tried first; failing that, the reference area holding the largest share, if at least half.
- Parts matched to one area are combined as an area-weighted mean ([`process/subprocesses/_linkage_indicators.py:479`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_linkage_indicators.py#L479) `combine_matched()`).
- `null_as` fills missing values, then `mask` blanks unreliable ones ([`process/subprocesses/_linkage_indicators.py:512`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_linkage_indicators.py#L512) `apply_rules()`).
- **To sample points:** from the first configured layer holding a value, by containment or within a distance ([`process/subprocesses/_linkage_indicators.py:537`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_linkage_indicators.py#L537) `sample_point_values()`), giving `sp_<prefix><column>`. These are replicated values: every point in an area has that area's value.

<a id="r8"></a>
## R8. Earth Engine: heat vulnerability and large green space

**Theory.**

- **GUHVI** (Turner et al. 2025) combines exposure, sensitivity and adaptive capability, each a mean of inputs min–max normalised to 0–100 within the region. Details are in the entry [GUHVI and its inputs](entries/guhvi.md).
- **Large public urban green space** is public open space of at least 1 ha with annual mean NDVI ≥ 0.2.

**Practice.** [`process/subprocesses/_earth_engine_indicators.py:846`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_earth_engine_indicators.py#L846) `guhvi_analysis()`, [`process/subprocesses/_earth_engine_indicators.py:1105`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_earth_engine_indicators.py#L1105) `normalise_band()`. Sample points take the value of the GUHVI cell containing them. Access to large green space follows R2 and R3 at 500 m. These need the Earth Engine container and `gee: true`.

<a id="r9"></a>
## R9. Walkability, and its attenuation by thermal comfort

**Theory.**

```text
DL   = a_fresh_food_market(300) + a_convenience(300) + a_pt_any(300)          (0 … 3)
W    = z(DL) + z(population density) + z(intersection density)
         z(x) = (x − mean(x)) / sd(x), over all urban sample points (sample SD)
h′   = clip( (UTCI − 30) / (50 − 30), 0, 1 )
W_tm = percentile_rank(W) · (1 − λ · h′),   λ = 0.5
```

The densities are neighbourhood averages within 1,000 m along the network. The percentile rank averages ties and lies in (0, 1]. Attenuation by multiplication means shade cannot make up for having nothing to walk to: a place with nothing within reach scores low however cool it is.

**Practice.** [`process/subprocesses/_11_neighbourhood_analysis.py:115`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_11_neighbourhood_analysis.py#L115) `compute_nodes_pop_intersect_density()`, [`process/subprocesses/_walkability_variants.py:275`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_walkability_variants.py#L275) `compute_variants()`, [`process/subprocesses/_walkability_variants.py:270`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_walkability_variants.py#L270) `percentile_rank()`, [`process/subprocesses/_walkability_variants.py:261`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_walkability_variants.py#L261) `rescale()` ([`MX_Mexicali_2025_ULI.yml:909`](../data/MX_Mexicali_2025_ULI.yml#L909)). The bounds each heat measure was re-scaled between are recorded in the comment of the `sample_points_walkability` table. The observed 5th and 95th percentiles of daytime UTCI were 43.8 and 46.0 °C.

<a id="r10"></a>
## R10. Transforms: soft thresholds and stepped ladders

**Theory.** A distance enters the index through a transform, so that being nearer counts, but less so far past a threshold:

```text
soft threshold:  s(d) = 1 / (1 + exp( k · (d − t) / t )),   k = 5
                 s(0) ≈ 0.993,  s(t) = 0.5,  s(2t) ≈ 0.007;  missing d → 0
stepped ladder:  s(d) = score of the first step with d ≤ distance;  beyond or missing → beyond score
```

For example, with a 300 m threshold, 150 m scores 0.92, 300 m scores 0.50 and 450 m scores 0.08. GHSCI warns if the censoring distance is below `2t`. That is why distances are searched to 1,500 m (five times 300 m) and police stations to 45 km.

**Practice.** [`process/subprocesses/_composite_index.py:1457`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1457) `soft_threshold()`, [`process/subprocesses/_composite_index.py:423`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L423) `stepped_score()`, [`process/subprocesses/_composite_index.py:1504`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1504) `prepare()`. Each indicator's `transform` is in [`MX_Mexicali_2025_ULI.yml:1019`](../data/MX_Mexicali_2025_ULI.yml#L1019).

<a id="r11"></a>
## R11. Normalisation: the Adjusted Mazziotta–Pareto Index (AMPI)

**Theory.** Each prepared indicator `x` (transformed where it has a transform) is re-scaled against goalposts:

```text
r = 100 ± 60 · (x − Ref) / (Max − Min)        + where higher is better, − where lower is better
Ref = mean of x over all sample points of the study region
Min, Max = Ref ∓ (sup − inf) / 2              inf, sup = observed minimum and maximum
```

So `Max − Min` is the observed range, and `r` spans 70–130 about the reference at 100. An indicator with configured goalposts (the GUHVI sub-indices: 0 and 100) uses those. An indicator that does not vary is dropped with a warning. Polarity is configured, or inferred from the variable's name.

**Practice.** [`process/subprocesses/_composite_index.py:1602`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1602) `resolve_parameters()`, [`process/subprocesses/_composite_index.py:1819`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1819) `normalise()`, [`process/subprocesses/_composite_index.py:234`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L234) `infer_polarity()`. The goalposts used are written to `MX_Mexicali_2025_ULI_composite_<index>_parameters.yml`, published with this manual ([`data/`](../data/)) and tabulated in [Appendix C](C_goalposts.md). Each indicator's skewness, kurtosis and tied share are recorded there too (`distribution`).

<a id="r12"></a>
## R12. Aggregation: domains, shared indicators and the index

**Theory.** A domain score is the weighted Mazziotta–Pareto composite of its indicators' scores `r_i`. An indicator listed in `k` domains counts `1/k` of its weight in each (`share`), so that in all it weighs no more than an indicator in one domain:

```text
w_i = weight_i · share_{i,d} / Σ_j weight_j · share_{j,d}       (over indicators with a value)
M   = Σ w_i r_i        S = √( Σ w_i (r_i − M)² )        cv = S / M
domain = M − S · cv                       (penalty S·cv: imbalance lowers the score)
index  = the same over the six scored domains, each weight 1
reported score = score − 100              (centre: 0; the penalty is reported as is)
```

The penalty divides by the mean, which is why scores are calculated at 100 and reported less 100. A point is scored only where all of a domain's indicators and all domains have a value (`min_valid`: all). An indicator's **effective weight** is its share of the index's mean level:

```text
e_i = Σ_d (W_d / Σ W) · (weight_i · share_{i,d} / Σ_j weight_j · share_{j,d})
```

For Mexicali these range from 1.7% to 6.2%.

**Practice.** [`process/subprocesses/_composite_index.py:1838`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1838) `mpi_aggregate()`, [`process/subprocesses/_composite_index.py:1874`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1874) `score()`, [`process/subprocesses/_composite_index.py:783`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L783) `share_of()`, [`process/subprocesses/_composite_index.py:1057`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1057) `effective_weights()`.

**Variants.** `uli_plain` replaces attenuated walkability with walkability alone and activates thermal comfort as an ambient environment indicator, against its own goalposts ([`process/subprocesses/_composite_index.py:857`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L857) `expand_variants()`).

<a id="r13"></a>
## R13. From sample points to areas

**Theory.** Scores are computed at sample points and then averaged. An area's index score is the mean of its points' index scores, not a composite of the area's mean domain scores.

| Area | Value |
|---|---|
| 100 m grid | unweighted mean of the sample points in the cell |
| AGEB, region (study region) | mean of grid cells weighted by `pop_est × area share` |
| Manzanas | unweighted mean of the sample points within 30 m |
| Condesa lots | unweighted mean of the sample points within 15 m |
| Subdivisions, region (Condesa) | mean of lots (each 3.2 residents) by area share |

Access columns (`pct_*`) are multiplied by 100 on aggregation.

**Practice.** [`process/subprocesses/_12_aggregation.py:1036`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_12_aggregation.py#L1036) `_propagate_sample_point_columns()`, [`process/subprocesses/_12_aggregation.py:626`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_12_aggregation.py#L626) `custom_aggregation()`, [`process/subprocesses/_12_aggregation.py:940`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_12_aggregation.py#L940) `_custom_area_query()`, [`process/subprocesses/_composite_index.py:2062`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L2062) `propagate()`. The aggregation plans are recorded in the database's `aggregation_plans` table.

<a id="r14"></a>
## R14. Frozen goalposts and recalculating a scenario

The goalposts make scores comparable: a scenario scored against the baseline's goalposts is on the same scale, and its scores may move beyond 70–130 if it improves on the best observed. To recalculate a sample point after a change, for example a new park, a shaded street or a new school:

```python
params = yaml.safe_load(open('MX_Mexicali_2025_ULI_composite_uli_parameters.yml'))

def indicator_score(i, raw):                    # raw: the point's measured value
    spec = params['indicators'][i]
    x = transform(spec['transform'], raw)        # R10: soft threshold, steps, or as is
    sign = 1 if spec['polarity'] == 'positive' else -1
    return 100 + sign * 60 * (x - spec['reference']) / (spec['max'] - spec['min'])

def mpi(scores, weights):                        # R12
    w = {i: weights[i] / sum(weights[j] for j in scores) for i in scores}
    M = sum(w[i] * scores[i] for i in scores)
    S = (sum(w[i] * (scores[i] - M) ** 2 for i in scores)) ** 0.5
    return M - S * S / M

r = {i: indicator_score(i, raw[i]) for i in params['indicators']}
domains = {d: mpi({i: r[i] for i in r if d in params['indicators'][i]['domains']},
                  {i: params['indicators'][i]['weight'] * params['indicators'][i]['domains'][d]
                   for i in r if d in params['indicators'][i]['domains']})
           for d in params['domains']}
uli = mpi(domains, params['domains']) - 100     # report as points from the average
```

Then average to areas as in R13. A useful check of a re-implementation: re-scoring the baseline's measured values against these goalposts should reproduce the published `sp_index_uli` (this manual has not run that check, which needs the sample point tables in the database). GHSCI does this with `r.composite_index(goalposts=…)` ([`process/subprocesses/_composite_index.py:1785`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1785) `load_goalposts()`).

What changes when:

- **A destination** (shop, school, stop): recompute its distances (R2), diversity counts (R4) and walkability's daily living score (R9) near it.
- **Shade, vegetation or materials:** the linked UTCI and NDVI of the areas affected (R7), then walkability's attenuation (R9).
- **Streets or crossings:** the network, hence every distance near the change (R2), intersection density (R9) and, for cycling, LTS (R6).
- **New residents:** population density (R9) and population weights in areas (R13).
