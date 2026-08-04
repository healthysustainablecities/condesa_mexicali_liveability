"""Guard against the escape-sequence trap in generated notebooks.

Cell sources are written as plain (non-raw) Python string literals in
build_notebooks.py, so a backslash escape in them is interpreted at
build time rather than surviving into the notebook.  A `\\n` inside a
quoted string in a cell becomes a real line break and the cell no
longer parses.  This checks every generated code cell compiles.
"""
import glob
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

bad = 0
for path in sorted(glob.glob(os.path.join(ROOT, 'notebooks', '*.ipynb'))):
    nb = json.load(io.open(path, encoding='utf-8'))
    name = os.path.basename(path)
    for i, cell in enumerate(nb['cells'], 1):
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        try:
            compile(source, f'{name}:{i}', 'exec')
        except SyntaxError as error:
            bad += 1
            print(f'{name} cell {i}: {error.msg} (line {error.lineno})')
            print('    ' + (error.text or '').strip()[:90])

print(f'\n{bad} cells fail to compile' if bad else '\nall code cells compile')
sys.exit(1 if bad else 0)
