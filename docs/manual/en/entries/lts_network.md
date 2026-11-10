# Cycling network by level of traffic stress (LTS)

[← Back to contents](../README.md)

Each OpenStreetMap network link is given a cycling facility type (bike path, shared path, separated lane, simple lane, shared street or none), a speed (`maxspeed`, or a default by road class) and an assumed average daily traffic (local 750, tertiary 3,000, secondary 10,000). LTS is assigned by cascade; the first rule met wins:

| LTS | Rules (summary of `assign_lts`) |
|---|---|
| 1 | bike path or shared path; off-road classes; separated lane ≤ 50 km/h; simple lane on a local/tertiary/secondary road with ADT ≤ 10,000 and ≤ 30 km/h; local road with ADT ≤ 2,000 and ≤ 30 km/h |
| 2 | separated lane ≤ 60; simple lane ≤ 50 (ADT ≤ 10,000); simple lane on a primary road (or ADT > 10,000) ≤ 40; local road with ADT ≤ 750 and ≤ 50, or ADT ≤ 2,000 and ≤ 40; local/tertiary with ADT ≤ 3,000 and ≤ 30 |
| 3 | simple lane ≤ 60; local with ADT ≤ 750 and ≤ 60; local/tertiary with ADT ≤ 3,000 and ≤ 50; secondary/primary (or ADT > 3,000) ≤ 40 |
| 4 | anything else |

The **low-stress** network is the links with LTS ≤ 2 where cycling, or dismounting to walk the bike, is permitted; its cost is length (tripled on links where one must dismount).

| Sample point variable | Area variable (measured value) | Description | Study region (Mexicali incl. Condesa) | Condesa |
|---|---|---|---|---|
| `sp_cycle_safe_nearest_node_fresh_food_pooled` | `avg_cycle_dist_safe_fresh_food_pooled` | Average distance (m) by cycling to the nearest fresh food market, supermarket or convenience store (pooled fresh food destinations), using a fully low-stress route (Level of Traffic Stress 1–2) | 826 m | 1,025 m |

## Method: practice

**Recipes:** [R6. Level of traffic stress and the low-stress cycling network](../03_recipes.md#r6)

**Configuration** ([`MX_Mexicali_2025_ULI.yml:698`](../../data/MX_Mexicali_2025_ULI.yml#L698)):

```yaml
cycling_indicators: true
```

**Code (GHSCI):**

- [`process/subprocesses/_cycling_lts_network.py:432`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_lts_network.py#L432) `classify_cycleway()`
- [`process/subprocesses/_cycling_lts_network.py:491`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_lts_network.py#L491) `assign_adt()`
- [`process/subprocesses/_cycling_lts_network.py:546`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_lts_network.py#L546) `assign_lts()`
- [`process/subprocesses/_cycling_lts_network.py:607`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_lts_network.py#L607) `add_impedance()`
- [`process/subprocesses/_cycling_accessibility.py:469`](https://github.com/healthysustainablecities/global-indicators/blob/f03909611dba336c2728fffab6d697779487d0b1/process/subprocesses/_cycling_accessibility.py#L469) `cycling_poi_distance()`

## Used by

[Food within 1.5 km by low-stress cycling](cycle_low_stress_food.md)
