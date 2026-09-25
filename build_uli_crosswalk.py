"""
Build the Mexicali ULI core measure crosswalk.

Joins ``uli_core_measure_crosswalk.yml`` -- which states which GHSCI variables
answer which workbook sub-variable, and how well -- against the region's
*generated* data dictionary, so that units, statistic and plain language
descriptions come from GHSCI rather than being retyped, and match
``OUTPUT_SPECIFICATION.md`` section 6 without further work.

Reports both directions of mismatch:

  - variables claimed by the crosswalk but not produced by the region.  Usually
    a typo, a renamed indicator, or an analysis step that did not run.
  - variables produced by the region but claimed by no core measure.  This is
    the more useful direction: it is how columns nobody asked for get either
    claimed or dropped, rather than shipped unexplained.

Run from this directory, inside the container::

    python build_uli_crosswalk.py [region_codename]

Outputs, alongside this script:

    uli_core_measure_crosswalk.csv     one row per core measure / sub-variable / variable
    uli_core_measure_coverage.csv      one row per core measure
    uli_core_measure_crosswalk.md      the summary, for reading
"""

import os
import re
import sys

import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
CROSSWALK = os.path.join(HERE, 'uli_core_measure_crosswalk.yml')

# Relations that count as covering a sub-variable.  'complementary' is included
# because the construct is measured, if by a different method; 'component' is
# not, because a part is not the whole.
COVERING = {'direct', 'complementary'}
RELATIONS = {'direct', 'proxy', 'component', 'complementary', 'not_covered'}


def load_crosswalk(path=CROSSWALK):
    """Read the crosswalk, checking the relation vocabulary is respected."""
    with open(path, encoding='utf-8') as f:
        crosswalk = yaml.safe_load(f)
    unknown = set()
    for measure in crosswalk['core_measures'].values():
        for sub in measure['sub_variables']:
            if sub.get('relation') not in RELATIONS:
                unknown.add(sub.get('relation'))
    if unknown:
        raise ValueError(
            f'Unknown relation(s) {sorted(unknown)} in {path}; '
            f'expected one of {sorted(RELATIONS)}.',
        )
    return crosswalk


def region_dictionary(codename):
    """The region's generated data dictionary, indexed by variable name.

    Produced by the generate step (data_dictionary.generate_data_dictionary),
    so it describes the columns the region actually output rather than the
    catalogue of everything GHSCI could in principle produce.
    """
    path = os.path.join(
        HERE, '..', '..', '_study_region_outputs', codename,
        f'{codename}_data_dictionary.csv',
    )
    path = os.path.normpath(path)
    if not os.path.exists(path):
        raise SystemExit(
            f'No generated data dictionary found at {path}.\n'
            f'Run the generate step for {codename} first.',
        )
    dictionary = pd.read_csv(path)
    # generate_data_dictionary writes Category / Indicator / Variable / Scale,
    # adding Units and Statistic
    dictionary = dictionary.rename(columns={'Indicator': 'Description'})
    return dictionary.drop_duplicates(subset='Variable').set_index('Variable')


def rows(crosswalk, dictionary):
    """One row per core measure / sub-variable / variable."""
    records = []
    for number, measure in sorted(crosswalk['core_measures'].items()):
        for sub in measure['sub_variables']:
            variables = sub.get('variables') or [None]
            for variable in variables:
                known = variable in dictionary.index if variable else False
                entry = dictionary.loc[variable] if known else None
                records.append({
                    'measure': number,
                    'core_measure': measure['core_measure'],
                    'domains': '; '.join(measure.get('domains') or []),
                    'owner': measure.get('owner', ''),
                    'sub_variable_id': sub.get('id', ''),
                    'sub_variable': sub.get('name', ''),
                    'relation': sub.get('relation'),
                    'direction': sub.get('direction', ''),
                    'variable': variable or '',
                    'produced': bool(known),
                    'description': entry['Description'] if known else '',
                    'units': entry.get('Units', '') if known else '',
                    'statistic': entry.get('Statistic', '') if known else '',
                    'scale': entry.get('Scale', '') if known else '',
                    'notes': (sub.get('notes') or '').strip().replace('\n', ' '),
                })
    return pd.DataFrame(records)


def coverage(crosswalk, table):
    """One row per core measure: how much of it we answer, and how."""
    records = []
    for number, measure in sorted(crosswalk['core_measures'].items()):
        subs = measure['sub_variables']
        relations = [s.get('relation') for s in subs]
        covered = sum(1 for x in relations if x in COVERING)
        if covered == len(subs):
            status = 'full'
        elif covered:
            status = 'partial'
        elif any(x in ('proxy', 'component') for x in relations):
            status = 'indirect'
        else:
            status = 'none'
        produced = table[table['measure'] == number]
        records.append({
            'measure': number,
            'core_measure': measure['core_measure'],
            'owner': measure.get('owner', ''),
            'status': status,
            'sub_variables': len(subs),
            'covered': covered,
            'relations': '; '.join(sorted(set(relations))),
            'variables_claimed': int((produced['variable'] != '').sum()),
            'variables_produced': int(produced['produced'].sum()),
        })
    for entry in crosswalk.get('not_covered') or []:
        records.append({
            'measure': entry['measure'],
            'core_measure': entry['core_measure'],
            'owner': entry.get('owner', ''),
            'status': 'not ours',
            'sub_variables': 0,
            'covered': 0,
            'relations': '',
            'variables_claimed': 0,
            'variables_produced': 0,
        })
    return pd.DataFrame(records).sort_values('measure')


# Data dictionary categories holding indicator estimates.  Everything else is
# structural -- identifiers, geometry, study region metadata, sample point
# counts -- and is not something a core measure would ever claim.
INDICATOR_CATEGORIES = (
    'Indicator estimates: access (walking)',
    'Indicator estimates: cycling accessibility',
    'Indicator estimates: urban heat vulnerability',
    'Indicator estimates: walkability',
)


def family(variable):
    """The measure a variable belongs to, ignoring scale and distance band.

    ``pct_access_walk_denue_pharmacy_500m``, its 1000 m and 1500 m siblings and
    the population-weighted ``pop_`` variant are one measure reported four ways,
    not four measures.  Collapsing them is what makes the unclaimed list
    readable: without it a single unclaimed destination appears a dozen times
    and the genuinely unaccounted-for measures are lost in the repetition.
    """
    variable = re.sub(r'^pop_', '', str(variable))
    return re.sub(r'_\d+m$', '', variable)


def unclaimed(dictionary, table):
    """Indicator measures the region produced that no core measure claims.

    Reported per measure rather than per variable, and restricted to the
    indicator categories: the point is to surface measures that need either a
    home in the crosswalk or a decision not to deliver them, which a list
    repeating every band and scale of the same measure would obscure.
    """
    claimed = {family(x) for x in table.loc[table['variable'] != '', 'variable']}
    indicators = dictionary[dictionary['Category'].isin(INDICATOR_CATEGORIES)]
    # Sample point variables are an intermediate, not a deliverable: the output
    # specification asks for one row per area, and a variable reported only at
    # sample points is not available at any of the five reporting scales.  The
    # dictionary's own Scale column decides this rather than the name.
    scale = indicators['Scale'].fillna('')
    reported = ~scale.str.replace(
        r'sample point[^,]*', '', regex=True,
    ).str.strip(' ,').eq('')
    remaining = indicators[
        reported & ~indicators.index.to_series().map(family).isin(claimed)
    ]
    grouped = (
        remaining.assign(measure=remaining.index.to_series().map(family))
        .groupby('measure')
        .agg(
            variables=('Description', 'size'),
            category=('Category', 'first'),
            description=('Description', 'first'),
        )
        .reset_index()
    )
    return grouped


def markdown(crosswalk, table, summary, missing, extra):
    """The summary as a readable page."""
    lines = [
        '# Mexicali ULI: GHSCI outputs by core measure',
        '',
        f"Region: `{crosswalk['region']}`  ",
        f"Workbook: {crosswalk['workbook']}  ",
        f"Work package: {crosswalk['work_package']}",
        '',
        'Generated by `build_uli_crosswalk.py`. Relations: **direct** measures '
        'the sub-variable as specified; **proxy** measures something related '
        'but not the same quantity; **component** supplies an input, not the '
        'whole; **complementary** measures the same construct by a different '
        'method and will not reproduce the specified numbers.',
        '',
        '## Coverage',
        '',
        '| # | Core measure | Owner | Status | Sub-variables | Covered | Variables produced |',
        '|---|---|---|---|---|---|---|',
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['measure']} | {row['core_measure']} | {row['owner']} | "
            f"{row['status']} | {row['sub_variables']} | {row['covered']} | "
            f"{row['variables_produced']} |",
        )
    lines += ['', '## Where our method differs by design', '']
    for _, row in table[table['relation'] == 'complementary'].iterrows():
        if row['notes']:
            lines.append(f"**{row['core_measure']} — {row['sub_variable']}**")
            lines.append('')
            lines.append(row['notes'])
            lines.append('')
    lines += ['## Validation', '']
    if len(missing):
        lines.append(
            f'{len(missing)} variable(s) claimed by the crosswalk but not '
            f'produced by the region:',
        )
        lines.append('')
        for x in missing:
            lines.append(f'- `{x}`')
    else:
        lines.append('Every variable claimed by the crosswalk was produced.')
    lines += ['']
    lines.append(
        f'{len(extra)} measure(s) produced but claimed by no core measure '
        f'(counting each measure once, however many bands and scales it is '
        f'reported at). See `uli_core_measure_unclaimed.csv`; each needs '
        f'either a home in the crosswalk or a decision not to deliver it.',
    )
    lines += ['']
    return '\n'.join(lines)


def main():
    codename = sys.argv[1] if len(sys.argv) > 1 else None
    crosswalk = load_crosswalk()
    codename = codename or crosswalk['region']
    dictionary = region_dictionary(codename)
    table = rows(crosswalk, dictionary)
    summary = coverage(crosswalk, table)
    missing = sorted(
        set(table.loc[(table['variable'] != '') & ~table['produced'], 'variable']),
    )
    extra = unclaimed(dictionary, table)

    table.to_csv(
        os.path.join(HERE, 'uli_core_measure_crosswalk.csv'), index=False,
    )
    summary.to_csv(
        os.path.join(HERE, 'uli_core_measure_coverage.csv'), index=False,
    )
    extra.to_csv(
        os.path.join(HERE, 'uli_core_measure_unclaimed.csv'), index=False,
    )
    with open(
        os.path.join(HERE, 'uli_core_measure_crosswalk.md'), 'w',
        encoding='utf-8', newline='\n',
    ) as f:
        f.write(markdown(crosswalk, table, summary, missing, extra))

    print(f'Region: {codename}')
    print(f'  {len(table)} crosswalk rows over {len(summary)} core measures')
    print(f"  status: {summary['status'].value_counts().to_dict()}")
    print(f'  claimed but not produced: {len(missing)}')
    for x in missing:
        print(f'    - {x}')
    print(f'  produced but not claimed: {len(extra)} measures')
    for _, row in extra.head(20).iterrows():
        print(f"    - {row['measure']} ({row['variables']} variables)")
    if len(extra) > 20:
        print(f'    ... and {len(extra) - 20} more (see the CSV)')


if __name__ == '__main__':
    main()
