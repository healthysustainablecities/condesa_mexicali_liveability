"""Build the Mexicali Urban Liveability Index technical manual.

    python build/manual/manual.py [--lang es,en] [--no-maps] [--no-pdf]

Writes Markdown (for GitHub) to docs/manual/<lang>/, maps to
docs/manual/figures/<lang>/, the region configuration and composite
parameters to docs/manual/data/, and a PDF per language to docs/manual/pdf/.
Reads only files that already exist (see sources.py); needs no database.

``--no-maps`` reuses maps already drawn (it still draws any that are missing).
The build fails if a region value disagrees with the dashboard manifest, or if
a link or image does not resolve; it prints a report of every gap -- a field
the sources do not record -- which the pages mark as Pending.
"""

import argparse
import sys
import time
from collections import Counter

from render import Builder, to_pdf
from sources import DOCS, LANGS, Sources
from stats import Results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument('--lang', default=','.join(LANGS))
    parser.add_argument('--no-maps', action='store_true')
    parser.add_argument('--no-pdf', action='store_true')
    args = parser.parse_args(argv)
    langs = tuple(x.strip() for x in args.lang.split(',') if x.strip())
    started = time.time()
    builder = Builder(Sources(), Results(), make_maps=not args.no_maps,
                      langs=langs)
    if builder.problems:
        for column, region, ours, theirs in builder.problems:
            print(f'MISMATCH {column} {region}: results {ours} vs manifest {theirs}')
        raise SystemExit('Region values disagree with the dashboard manifest.')
    print('Region values agree with the dashboard manifest.')
    builder.build()
    broken = builder.check_links()
    for lang, page, href in broken:
        print(f'BROKEN LINK [{lang}] {page}: {href}')
    counts = Counter((lang, what.split(':')[0]) for lang, _, what in builder.gaps)
    print(f'\nGap report ({len(builder.gaps)} items):')
    for lang, page, what in builder.gaps:
        print(f'  [{lang}] {page}: {what}')
    if broken:
        raise SystemExit(f'{len(broken)} broken links.')
    if not args.no_pdf:
        for lang in langs:
            print('PDF:', to_pdf(builder, lang))
    print(f'\nWrote {DOCS} in {time.time() - started:.0f} s '
          f'({sum(len(p) for p in builder.pages.values())} pages).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
