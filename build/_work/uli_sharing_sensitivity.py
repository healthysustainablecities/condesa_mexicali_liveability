"""How much sharing indicators between domains changes the ULI.

Scores the configured index three ways, without writing anything:
  shared   as configured: each indicator split across the sheet's domains
  first    the same indicators, each in the first domain the sheet names
  flat     the same indicators, no domains (one composite of all)

Run in the container from process/:
    /env/bin/python "data/MX/Mexicali Liveability/build/_work/uli_sharing_sensitivity.py"
"""
import copy
import sys
import warnings

sys.path.insert(0, 'subprocesses')
import _composite_index as ci  # noqa: E402
import ghsci  # noqa: E402

warnings.simplefilter('ignore')
r = ghsci.Region('data/MX/MX_Mexicali_2025_ULI.yml')
config = r.config['composite_indices']['uli']


def variant(kind):
    spec = copy.deepcopy(config)
    spec.pop('variants', None)
    if kind == 'first':
        for item in spec['indicators']:
            item['domains'] = [item['domains'][0]]
    if kind == 'flat':
        spec.pop('domains')
        for item in spec['indicators']:
            item.pop('domains')
    return ci.normalise_index_spec('uli', spec)


specs = {k: variant(k) for k in ('shared', 'first', 'flat')}
frame = ci.load_indicator_frame(r, specs.values())
results = {}
for kind, spec in specs.items():
    prepared = ci.prepare(frame, spec)
    params = ci.resolve_parameters([prepared], spec)
    scores = ci.score(prepared, spec, params)
    results[kind] = scores
    column = 'sp_index_uli'
    domains = [c for c in scores if c.startswith('sp_index_uli__')
               and c[len('sp_index_uli__'):] in {d['name'] for d in spec['domains']}]
    spread = scores[domains].std(axis=1).mean() if domains else float('nan')
    weights = ci.effective_weights(spec, params)
    effective = [w['effective'] for w in weights.values()]
    print(
        f'{kind:7s} mean {scores[column].mean():6.2f}  penalty '
        f'{scores[column + "_penalty"].mean():5.2f}  mean SD between domains '
        f'{spread:5.2f}  effective weights {100 * min(effective):.1f}-'
        f'{100 * max(effective):.1f}%',
    )
    if domains:
        print(
            '        domain correlations (mean off-diagonal): '
            f'{scores[domains].corr().where(lambda m: m < 0.9999).stack().mean():.2f}',
        )
base = results['shared']['sp_index_uli']
for kind in ('first', 'flat'):
    print(
        f'Spearman shared vs {kind}: '
        f'{base.corr(results[kind]["sp_index_uli"], method="spearman"):.3f}',
    )
