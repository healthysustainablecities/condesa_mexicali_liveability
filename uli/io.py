"""Read and write indicator deliverables in the agreed layout.

Every indicator lands in its own directory under ``outputs/``::

    outputs/WP04_greenness_and_land_cover/vegetation_percent/
        vegetation_percent_results.csv
        vegetation_percent_metadata.yml
        vegetation_percent_validation.json

so that a work package can be zipped, reviewed or ingested on its own,
and so that two analysts can never overwrite each other.
"""

import datetime
import hashlib
import json
import os

import pandas as pd
import yaml

from . import validate, vocab

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'outputs')


def indicator_dir(metadata, output_dir=None):
    """Return (and create) the output directory for an indicator."""
    path = os.path.join(
        output_dir or OUTPUT_DIR,
        metadata['indicator']['work_package'],
        metadata['indicator']['code'],
    )
    os.makedirs(path, exist_ok=True)
    return path


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            digest.update(block)
    return digest.hexdigest()


def write_indicator(
    results,
    metadata,
    output_dir=None,
    validate_first=True,
    allow_failure=False,
):
    """Write results, metadata and a validation report to disk.

    By default nothing is written if validation fails -- publishing a
    known-broken deliverable helps nobody.  Pass
    ``allow_failure=True`` to write anyway while iterating (the
    validation report is written regardless, so the failure is
    recorded alongside the data).
    """
    code = metadata['indicator']['code']
    report = (
        validate.check(results, metadata)
        if validate_first
        else validate.Report(code)
    )
    target = indicator_dir(metadata, output_dir)
    report_path = os.path.join(target, f'{code}_validation.json')

    if not report and not allow_failure:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        print(report)
        raise ValueError(
            f'{code}: validation failed, nothing written except '
            f'{os.path.basename(report_path)}.  Fix the errors above, '
            'or pass allow_failure=True to write a draft.'
        )

    results_path = os.path.join(target, f'{code}_results.csv')
    results = results.reindex(columns=list(vocab.RESULT_COLUMNS))
    results.to_csv(results_path, index=False, encoding='utf-8')

    metadata = dict(metadata)
    metadata['provenance'] = {
        **metadata.get('provenance', {}),
        'computed_on': datetime.date.today().isoformat(),
        'results_file': os.path.basename(results_path),
        'results_sha256': _sha256(results_path),
        'row_count': int(len(results)),
    }
    metadata_path = os.path.join(target, f'{code}_metadata.yml')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(
            metadata,
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=72,
        )
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

    print(report)
    print(f'\nWritten to {target}')
    return {
        'results': results_path,
        'metadata': metadata_path,
        'validation': report_path,
        'report': report,
    }


def read_indicator(code, work_package=None, output_dir=None):
    """Read one indicator's results and metadata back from disk."""
    root = output_dir or OUTPUT_DIR
    packages = (
        [work_package]
        if work_package
        else sorted(
            name
            for name in os.listdir(root)
            if os.path.isdir(os.path.join(root, name))
        )
    )
    for package in packages:
        target = os.path.join(root, package, code)
        if not os.path.isdir(target):
            continue
        results = pd.read_csv(
            os.path.join(target, f'{code}_results.csv'),
            dtype={'geo_id': str},
        )
        with open(
            os.path.join(target, f'{code}_metadata.yml'), encoding='utf-8'
        ) as f:
            metadata = yaml.safe_load(f)
        return results, metadata
    raise FileNotFoundError(f'No delivered indicator named {code!r}')


def collect(output_dir=None, geo_level=None):
    """Read every delivered indicator into one long table.

    This is the ingestion step for the composite index and for
    Reimagina Urbana: it is deliberately the same code path an analyst
    can run to see how their own output will be consumed.
    """
    root = output_dir or OUTPUT_DIR
    frames, catalogue = [], []
    for package in sorted(os.listdir(root)):
        package_dir = os.path.join(root, package)
        if not os.path.isdir(package_dir):
            continue
        for code in sorted(os.listdir(package_dir)):
            results_path = os.path.join(
                package_dir, code, f'{code}_results.csv'
            )
            if not os.path.exists(results_path):
                continue
            results, metadata = read_indicator(code, package, root)
            if geo_level:
                results = results[results['geo_level'] == geo_level]
            frames.append(results)
            for measure in metadata.get('measures', []):
                catalogue.append(
                    {
                        'work_package': package,
                        'indicator_id': metadata['indicator']['id'],
                        'indicator_code': code,
                        'measure_id': measure['id'],
                        'lens': measure.get('lens'),
                        'name_en': measure.get('name_en'),
                        'unit': measure.get('unit'),
                        'value_type': measure.get('value_type'),
                        'direction': measure.get('direction'),
                        'native_scale': measure.get('native_scale'),
                        'include_in_index': measure.get(
                            'include_in_index'
                        ),
                        'status': metadata['indicator'].get('status'),
                    }
                )
    if not frames:
        return pd.DataFrame(columns=vocab.RESULT_COLUMNS), pd.DataFrame()
    return (
        pd.concat(frames, ignore_index=True),
        pd.DataFrame(catalogue),
    )


def to_wide(results, geo_level, value_column='value'):
    """Pivot long results to one column per measure for a geography."""
    subset = results[results['geo_level'] == geo_level]
    return subset.pivot_table(
        index='geo_id',
        columns='measure_id',
        values=value_column,
        aggfunc='first',
    ).reset_index()


def to_geopackage(results, path, levels=None):
    """Join delivered values to geometry and write a geopackage.

    One layer per reporting geography, wide format -- the shape
    Reimagina Urbana and QGIS both want.
    """
    from . import geography

    levels = levels or sorted(set(results['geo_level']))
    if os.path.exists(path):
        os.remove(path)
    for level in levels:
        wide = to_wide(results, level)
        if wide.empty:
            continue
        units = geography.load(level)
        merged = units.merge(wide, on='geo_id', how='left')
        merged.to_file(path, layer=level, driver='GPKG')
    return path
