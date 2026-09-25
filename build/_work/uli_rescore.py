"""Re-score the Mexicali ULI and compare it with the snapshot taken before.

Run in the container from process/:
    /env/bin/python "data/MX/Mexicali Liveability/build/_work/uli_rescore.py"
"""
import sys
import warnings

sys.path.insert(0, 'subprocesses')
import ghsci  # noqa: E402
import pandas as pd  # noqa: E402

r = ghsci.Region('data/MX/MX_Mexicali_2025_ULI.yml')
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    scores, parameters = r.composite_index()
for w in caught:
    if 'index' in str(w.message).lower():
        print('WARNING:', w.message)

for name, params in parameters.items():
    print(f'\n{name}: dropped {params.get("dropped")}')
    effective = params.get('effective_weights') or {}
    print(
        f'  effective weights sum {sum(effective.values()):.6f}; '
        f'{len(effective)} indicators',
    )

before = pd.read_parquet('/export/uli_scores_before.parquet')
after = scores[['grid_id', 'sp_index_uli', 'sp_index_uli_penalty']].copy()
after.index.name = 'point_id'
after = after.reset_index()
merged = before.merge(
    after,
    on='point_id',
    suffixes=('_before', '_after'),
)
print('\nSample points compared:', len(merged))
for column in ('sp_index_uli', 'sp_index_uli_penalty'):
    b, a = merged[f'{column}_before'], merged[f'{column}_after']
    print(
        f'{column}: mean {b.mean():.2f} -> {a.mean():.2f}; '
        f'Spearman {b.corr(a, method="spearman"):.3f}',
    )
grid = merged.groupby('grid_id_after')[
    ['sp_index_uli_before', 'sp_index_uli_after']
].mean()
print(
    f'grid cells: {len(grid)}; Spearman '
    f'{grid.sp_index_uli_before.corr(grid.sp_index_uli_after, method="spearman"):.3f}',
)
grid['change'] = grid.sp_index_uli_after - grid.sp_index_uli_before
print('\nlargest movers (grid cells):')
print(grid.reindex(grid.change.abs().sort_values(ascending=False).index).head(10))
for name in ('uli_plain',):
    column = f'sp_index_{name}'
    if column in scores:
        print(
            f'{name}: mean {scores[column].mean():.2f}; Spearman with uli '
            f'{scores[column].corr(scores["sp_index_uli"], method="spearman"):.3f}',
        )
