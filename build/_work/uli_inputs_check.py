"""Check the ULI's candidate sample point inputs exist and vary; snapshot scores.

Run in the container from process/:
    /env/bin/python "data/MX/Mexicali Liveability/build/_work/uli_inputs_check.py"
"""
import sys

sys.path.insert(0, 'subprocesses')
import ghsci  # noqa: E402

r = ghsci.Region('data/MX/MX_Mexicali_2025_ULI.yml')
candidates = [
    'sp_urban_heat_exposure_index',
    'sp_urban_heat_sensitivity_index',
    'sp_urban_heat_adaptive_capability_index',
    'sp_urban_heat_guhvi',
    'sp_utci_day_mean',
    'sp_walk_nearest_node_blue_space',
    'sp_ext_ndvi',
    'sp_walk_nearest_node_public_open_space_any',
    'sp_access_large_public_green_space_score',
    'sp_ext_major_road_length_300m',
    'sp_walk_idx_300_tm',
    'sp_walk_idx_300',
    'sp_ext_block_perimeter_m',
    'sp_walk_nearest_node_pt_any',
    'sp_walk_nearest_node_denue_fresh_food',
    'sp_walk_diversity_fresh_food_500m',
    'sp_walk_nearest_node_denue_food_retail',
    'sp_walk_beyond_denue_petrol_station_250m',
    'sp_walk_nearest_node_denue_primary_school',
    'sp_walk_diversity_education_500m',
    'sp_walk_nearest_node_denue_primary_healthcare',
    'sp_walk_diversity_health_care_500m',
    'sp_walk_nearest_node_denue_care_support',
    'sp_walk_diversity_care_500m',
    'sp_walk_nearest_node_denue_ccr_any',
    'sp_walk_diversity_community_culture_recreation_500m',
    'sp_walk_access_denue_manufacturing_1000m',
    'sp_ext_economic_sector_diversity',
    'sp_euclid_dist_imip_police_station',
    'sp_euclid_dist_imip_fire_station',
    'sp_cycle_safe_nearest_node_fresh_food_pooled',
]
tables = [
    r.config['point_summary'],
    'sample_points_pedestrian',
    'sample_points_cycling',
    'sample_points_euclidean',
    'sample_points_linkage',
    'sample_points_walkability',
]
present = set(r.get_tables())
where = {}
for table in tables:
    if table not in present:
        continue
    cols = r.get_df(
        'SELECT column_name FROM information_schema.columns '
        f"WHERE table_name = '{table}'",
    )['column_name'].tolist()
    for c in cols:
        where.setdefault(c, table)
for c in candidates:
    table = where.get(c)
    if table is None:
        print(f'MISSING  {c}')
        continue
    row = r.get_df(
        f'SELECT count(*) n, count("{c}") nn, min("{c}") lo, max("{c}") hi, '
        f'count(DISTINCT "{c}") nd FROM {table}',
    ).iloc[0]
    print(
        f'{c:55s} {table:26s} n={row.n} nonnull={row.nn} '
        f'min={row.lo:.4g} max={row.hi:.4g} distinct={row.nd}'
        if row.nn
        else f'{c:55s} {table:26s} ALL NULL',
    )

# snapshot the current index scores, for comparison once re-scored
if 'sample_points_composite' in present:
    cols = r.get_df(
        'SELECT column_name FROM information_schema.columns '
        "WHERE table_name = 'sample_points_composite'",
    )['column_name'].tolist()
    keep = [
        c
        for c in cols
        if c == 'point_id' or c == 'grid_id' or c.startswith('sp_index_uli')
    ]
    keep = [c for c in keep if '__' not in c or c.count('__') == 1]
    snap = r.get_df(
        'SELECT ' + ', '.join(f'"{c}"' for c in keep)
        + ' FROM sample_points_composite',
    )
    out = '/export/uli_scores_before.parquet'
    snap.to_parquet(out)
    print(f'snapshot: {len(snap)} rows, {len(keep)} columns -> {out}')
