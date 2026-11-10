# Mexicali Urban Liveability Index: Walkability (300 m), without thermal comfort attenuation

[← Back to contents](../README.md)

> Average of the Mexicali Urban Liveability Index's domain scores, each summarising its normalised sub-indicators, less a penalty for variation across domains that rewards balanced performance. Expressed as points above or below the study region average (0).

The Urban Liveability Index draws on the Adjusted Mazziotta-Pareto Index (AMPI): each sub-indicator is re-scaled so that 0 is the study region average (its mean over all sample points), and scores are points above or below it. Each domain is the weighted mean of its sub-indicators less a penalty for imbalance between them, and the index is likewise the mean of the domains less a penalty for imbalance between domains. A sub-indicator bearing on several domains counts an equal share of its weight in each (a third in each of three), so that in all it weighs no more than one in a single domain. Scored at sample points along the pedestrian network, and averaged to grid cells and, weighted by population, to larger areas.

A variant of the index in which walkability is not attenuated by thermal comfort (`sp_walk_idx_300`) and daytime thermal comfort (`sp_utci_day_mean`) is scored as an ambient environment indicator instead, so that thermal comfort counts exactly once. It is scored against its own goalposts.

## Domains

| Domains | n | Region score: Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|---|
| [Ambient environment](domain_ambient_environment.md) | 9 | −1.8 | +1.0 |
| [Built environment](domain_built_environment.md) | 8 | +1.5 | −16.5 |
| [Economic development](domain_economic_development.md) | 6 | +1.9 | −14.8 |
| [Housing](domain_housing.md) | – | – | – |
| [Mobility and transport](domain_mobility_transport.md) | 10 | +2.0 | −14.4 |
| [Safety and protection](domain_safety.md) | 5 | +2.2 | −20.7 |
| [Social infrastructure](domain_social_infrastructure.md) | 13 | +2.3 | −11.6 |
| [Sociodemographic characteristics](domain_sociodemographics.md) | – | – | – |

## Method: theory

```text
r_i      = 100 ± 60 · (x_i − Ref_i) / (Max_i − Min_i)                 (R11)
domain_d = M_d − S_d · (S_d / M_d),  w_i ∝ weight_i · share_{i,d}       (R12)
index    = M − S · (S / M)  over the six scored domains, equal weights
reported = index − 100   (0 = study region average)
```

**Recipes:** [R10. Transforms: soft thresholds and stepped ladders](../03_recipes.md#r10), [R11. Normalisation: the Adjusted Mazziotta–Pareto Index (AMPI)](../03_recipes.md#r11), [R12. Aggregation: domains, shared indicators and the index](../03_recipes.md#r12), [R13. From sample points to areas](../03_recipes.md#r13), [R14. Frozen goalposts and recalculating a scenario](../03_recipes.md#r14)

## Method: practice

**Configuration:** [`MX_Mexicali_2025_ULI.yml:1019`](../../data/MX_Mexicali_2025_ULI.yml#L1019); [`MX_Mexicali_2025_ULI_composite_uli_plain_parameters.yml`](../../data/MX_Mexicali_2025_ULI_composite_uli_plain_parameters.yml)

**Code (GHSCI):** [`process/subprocesses/_composite_index.py:1602`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1602) `resolve_parameters()`, [`process/subprocesses/_composite_index.py:1874`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1874) `score()`, [`process/subprocesses/_composite_index.py:1838`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L1838) `mpi_aggregate()`, [`process/subprocesses/_composite_index.py:2062`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_composite_index.py#L2062) `propagate()`

## Recalculation (Reimagina Urbano)

With the frozen goalposts of the parameters file (`Ref`, `Min`, `Max`, R14), a new score is `r = 100 ± 60·(x − Ref)/(Max − Min)` without re-resolving goalposts; the domain and index are recomputed by R12, less 100. A scenario is then compared with the baseline on the same scale.

[R14. Frozen goalposts and recalculating a scenario](../03_recipes.md#r14)

## Results

| Measure | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|
| Region score (`uli_plain`) | +1.0 | −13.5 |
| Region score (`uli_plain_mean`) | +1.3 | −12.6 |
| Region score (`uli_plain_penalty`) | 0.36 | 0.86 |
| Areas with a value | 14,145 of 14,252 manzanas | 12,186 of 14,988 lots |
| Median (P25–P75), weighted | +0.8 (−3.1 – +4.1) | −12.3 (−17.5 – −10.7) |
| Range | −20.1 – +14.3 | −20.5 – −3.3 |

*Distributions: study region manzanas weighted by census population (2020); Condesa lots weighted equally (3.2 residents assumed per lot). Region values are those GHSCI reports for each region as a whole.*

- The study region (Mexicali with Condesa) scores +1.0, and Condesa −13.5: 13.5 points below the study region average. The penalty measures imbalance between domains (`_penalty`, not centred).

## Map

![Mexicali Urban Liveability Index: Walkability (300 m), without thermal comfort attenuation](../../figures/en/uli_plain.png)

*Map. Mexicali Urban Liveability Index: Walkability (300 m), without thermal comfort attenuation: score by manzana across the study region and by lot in Condesa (inset), in points from the study region average (0); blue is better.*

## Caveats and open questions

- The index is provisional: the indicators in each domain and how it is calculated are still under review.
