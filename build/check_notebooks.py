"""Check generated notebooks for the two ways they quietly break.

Both are consequences of building notebooks by string templating, and
both are invisible until someone opens the file:

**Code cells that do not parse.** Cell sources are written as plain
(non-raw) Python string literals in ``build_notebooks.py``, so a
backslash escape inside one is interpreted at build time rather than
surviving into the notebook.  A ``\\n`` inside a quoted string becomes
a real line break and the cell no longer compiles.

**Markdown cells that render as code blocks.** Templates are indented
to match the surrounding python and dedented on the way out, but
``textwrap.dedent`` strips only the whitespace common to every line.
Interpolating a multi-line value built at zero indent drops that
common prefix to nothing, the dedent silently does nothing, and every
remaining line keeps its indentation -- which Markdown renders as a
grey code block instead of prose.

Run directly, or let ``build_notebooks.py`` run it for you::

    python build/check_notebooks.py
"""
import glob
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Four leading spaces is the Markdown indented-code-block threshold.
CODE_BLOCK_INDENT = 4


def check_code(name, index, source):
    """A code cell must compile."""
    try:
        compile(source, f'{name}:{index}', 'exec')
    except SyntaxError as error:
        return [
            f'{name} cell {index}: does not compile -- {error.msg} '
            f'(line {error.lineno})',
            '    ' + (error.text or '').strip()[:90],
        ]
    return []


def check_markdown(name, index, source):
    """A markdown cell must not be accidentally indented.

    Fenced blocks are skipped: indentation inside ``` fences is
    deliberate.
    """
    problems = []
    lines = source.split('\n')
    fenced = False
    indented = []
    for number, line in enumerate(lines, 1):
        if line.lstrip().startswith('```'):
            fenced = not fenced
            continue
        if fenced or not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent >= CODE_BLOCK_INDENT:
            indented.append((number, line))

    if not indented:
        return problems

    # A leading indent on the first content line means the whole cell
    # will render as a code block -- the failure that matters.
    first = next((line for line in lines if line.strip()), '')
    if len(first) - len(first.lstrip()) >= CODE_BLOCK_INDENT:
        problems.append(
            f'{name} cell {index}: starts with '
            f'{len(first) - len(first.lstrip())} spaces, so the whole '
            'cell renders as a code block'
        )
        problems.append(f'    {first.strip()[:80]}')
    elif len(indented) > len(
        [line for line in lines if line.strip()]
    ) // 2:
        problems.append(
            f'{name} cell {index}: {len(indented)} lines indented '
            f'{CODE_BLOCK_INDENT}+ spaces; likely a failed dedent'
        )
        problems.append(f'    line {indented[0][0]}: '
                        f'{indented[0][1].strip()[:70]}')
    return problems


def main():
    problems = []
    notebooks = sorted(
        glob.glob(os.path.join(ROOT, 'notebooks', '*.ipynb'))
    )
    for path in notebooks:
        nb = json.load(io.open(path, encoding='utf-8'))
        name = os.path.basename(path)
        for index, cell in enumerate(nb['cells'], 1):
            source = ''.join(cell['source'])
            if cell['cell_type'] == 'code':
                problems += check_code(name, index, source)
            elif cell['cell_type'] == 'markdown':
                problems += check_markdown(name, index, source)

    for line in problems:
        print(line)
    complaints = len([p for p in problems if not p.startswith('    ')])
    print(
        f'\n{complaints} problem(s) in {len(notebooks)} notebooks'
        if complaints
        else f'\n{len(notebooks)} notebooks OK: '
        'all code cells compile, no stray markdown indentation'
    )
    return 1 if complaints else 0


if __name__ == '__main__':
    sys.exit(main())
