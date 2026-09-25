"""What node --check cannot tell you, and the browser here will not.

    python build/check.py

Parsing is not resolution: a function deleted in a refactor with one call site
left behind is a ReferenceError that fires only when that branch runs -- which
is how a leftover pick() emptied the whole info panel, twice, with the rest of
the page rendering perfectly around it.

Run this alongside build/smoke.mjs. That one checks the data contract between
the exporter and the viewer; this one checks the viewer against itself: names
resolve, every element id exists, every string key is defined, the stylesheet
balances, no media query has crept back in, and nothing still refers to code
that has been removed.
"""
import io
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(BASE, 'js')
ok = True


def fail(message):
    global ok
    ok = False
    print(f'  FAIL  {message}')


def read(path):
    return io.open(path, encoding='utf-8').read()


js_files = sorted(f for f in os.listdir(JS) if f.endswith('.js'))
html = read(os.path.join(BASE, 'index.html'))
# every stylesheet the page links: the print sheet is held to the same rules
css = '\n'.join(
    read(os.path.join(BASE, 'css', name))
    for name in ('app.css', 'print.css')
    if os.path.exists(os.path.join(BASE, 'css', name))
)
sources = {f: read(os.path.join(JS, f)) for f in js_files}

# ---- syntax ---------------------------------------------------------------
for name in js_files:
    result = subprocess.run(
        ['node', '--check', os.path.join(JS, name)],
        capture_output=True, text=True,
    )
    if result.returncode:
        fail(f'{name}: {result.stderr.strip().splitlines()[-1]}')
print('syntax checked')

# ---- imports resolve ------------------------------------------------------
for name, src in sources.items():
    for spec in re.findall(r"from '\./([\w.]+)'", src):
        if spec not in sources:
            fail(f'{name} imports missing module {spec}')
    for imported in re.findall(r"import \{([^}]+)\} from '\./([\w.]+)'", src):
        names = [n.strip() for n in imported[0].split(',') if n.strip()]
        target = sources.get(imported[1], '')
        for symbol in names:
            symbol = symbol.split(' as ')[0].strip()
            if not re.search(
                rf'export (?:async )?(?:function|const|class|let) '
                rf'{re.escape(symbol)}\b',
                target,
            ):
                fail(f'{name} imports {symbol}, not exported by {imported[1]}')
print('imports resolve')

# ---- every function called is one that exists -----------------------------
# node --check parses; it does not resolve names.  A function deleted in a
# refactor while one call site survives is a runtime ReferenceError that only
# shows when that branch runs -- which is how a leftover pick() emptied the
# whole info panel twice.
GLOBALS = {
    'if', 'for', 'while', 'switch', 'catch', 'return', 'function', 'typeof',
    'await', 'new', 'super', 'this', 'Number', 'String', 'Boolean', 'Array',
    'Object', 'Math', 'JSON', 'Map', 'Set', 'Promise', 'Error', 'Date',
    'parseInt', 'parseFloat', 'isNaN', 'fetch', 'setTimeout', 'clearTimeout',
    'setInterval', 'requestAnimationFrame', 'console', 'document', 'window',
    'maplibregl', 'pmtiles', 'URLSearchParams', 'history', 'location', 'import',
    'RegExp', 'Intl', 'AbortController', 'CustomEvent', 'Blob', 'URL',
    'Float32Array', 'Int32Array', 'Uint8ClampedArray',
    'of', 'in', 'do', 'else', 'yield', 'delete', 'void', 'instanceof',
}
def strip_prose(src):
    """Code only: comments and string bodies are not call sites.

    Scanned character by character rather than by regex, because template
    literals nest ``${...}`` holes of real code inside them and no regex keeps
    the holes while dropping the prose around them.
    """
    out = []
    i = 0
    n = len(src)
    # stack of open template literals, so a ${...} hole is scanned as code
    templates = []
    while i < n:
        c = src[i]
        two = src[i:i + 2]
        if two == '//':
            i = src.find('\n', i)
            if i < 0:
                break
            continue
        if two == '/*':
            i = src.find('*/', i)
            i = n if i < 0 else i + 2
            continue
        if c in '\'"':
            i += 1
            while i < n and src[i] != c:
                i += 2 if src[i] == '\\' else 1
            i += 1
            out.append('""')
            continue
        if c == '`':
            templates.append(True)
            i += 1
            while i < n:
                if src[i] == '\\':
                    i += 2
                    continue
                if src[i] == '`':
                    i += 1
                    templates.pop()
                    break
                if src[i:i + 2] == '${':
                    out.append(' ')
                    depth = 1
                    i += 2
                    start = i
                    while i < n and depth:
                        if src[i] == '{':
                            depth += 1
                        elif src[i] == '}':
                            depth -= 1
                        i += 1
                    out.append(strip_prose(src[start:i - 1]))
                    continue
                i += 1
            out.append(' ')
            continue
        out.append(c)
        i += 1
    return ''.join(out)


for name, src in sources.items():
    code = strip_prose(src)
    declared = set(re.findall(
        r'\b(?:function|const|let|var|class)\s+([A-Za-z_]\w*)', code,
    ))
    # class methods, and object-literal shorthand
    declared |= set(re.findall(r'^\s+(?:async\s+)?([A-Za-z_]\w*)\(', code, re.M))
    # accessors: `get armed() {` declares a property, not a call
    # read from the raw source: the scanner above is good enough
    # to find call sites, but not to be the only place a
    # declaration can be seen
    declared |= set(
        re.findall(r'\b(?:get|set)\s+([A-Za-z_]\w*)\s*\(', src),
    )
    for group in re.findall(r'import\s*\{([^}]+)\}', code):
        for symbol in group.split(','):
            declared.add(symbol.split(' as ')[-1].strip())
    # arrow-function parameters, which are callable inside their own body
    for params in re.findall(r'\(([^)]*)\)\s*=>', code):
        declared |= set(re.findall(r'\b([A-Za-z_]\w*)\b', params))
    declared |= set(re.findall(r'\b([A-Za-z_]\w*)\s*=>', code))
    called = set(re.findall(r'(?<![.\w$])([a-zA-Z_]\w*)\s*\(', code))
    unknown = sorted(called - declared - GLOBALS)
    if unknown:
        fail(f'{name} calls undefined: {unknown}')
print('every called function is declared or imported')

# ---- getElementById targets exist ----------------------------------------
ids = set(re.findall(r'id="([\w-]+)"', html))
referenced = set()
for name, src in sources.items():
    referenced |= set(re.findall(r"\$\('([\w-]+)'\)", src))
    referenced |= set(re.findall(r"getElementById\('([\w-]+)'\)", src))
# created at runtime rather than declared in the document
runtime = {'infoBtn', 'tourSpot'}
missing = sorted(referenced - ids - runtime)
if missing:
    fail(f'ids referenced but not in index.html: {missing}')
print(f'ids: {len(referenced)} referenced, all present')

# ---- css selectors used by the JS ----------------------------------------
classes = set(re.findall(r'\.([a-zA-Z][\w-]*)', css))
used = set()
for src in sources.values():
    used |= set(re.findall(r'class="([^"$]+)"', src))
flat = {c for entry in used for c in entry.split()}
unstyled = sorted(c for c in flat if c not in classes and '{' not in c)
if unstyled:
    print(f'  note: classes with no CSS rule: {unstyled}')

# ---- strings --------------------------------------------------------------
strings = read(os.path.join(JS, 'strings.js'))
defined = set(re.findall(r'^  ([a-zA-Z]\w*): \{', strings, re.M))
keys = set()
for src in sources.values():
    keys |= set(re.findall(r"\bt\('([\w]+)'\)", src))
keys |= set(re.findall(r'data-s="([\w]+)"', html))
undefined = sorted(keys - defined)
if undefined:
    fail(f'strings referenced but not defined: {undefined}')
print(f'{len(defined)} strings defined, {len(keys)} referenced, all present')

# ---- css sanity -----------------------------------------------------------
if css.count('{') != css.count('}'):
    fail(f'css braces unbalanced: {css.count("{")} vs {css.count("}")}')
media = css.count('@media')
print(f'css braces balanced; media queries: {media}')
if media:
    fail('a media query crept back in')

# ---- variables referenced in css are defined -----------------------------
declared = set(re.findall(r'^\s*(--[\w-]+):', css, re.M))
consumed = set(re.findall(r'var\((--[\w-]+)', css))
orphan = sorted(consumed - declared)
if orphan:
    fail(f'css variables used but never declared: {orphan}')
print(f'{len(declared)} css variables declared, {len(consumed)} used')

# ---- nothing still refers to what was removed ----------------------------
gone = ['classSel', 'classField', 'sourcesPanel', 'renderSources',
        'fixedBreaks', 'unionRange', 'declaredRange', 'quartileNotes',
        'map-info', 'state.classification', 'leg-rows']
for token in gone:
    hits = [n for n, s in sources.items() if token in s]
    if token in html:
        hits.append('index.html')
    if token in css:
        hits.append('app.css')
    if hits:
        fail(f'removed thing "{token}" still referenced in {hits}')
print('removed code has no stragglers')

print('\nall checks passed' if ok else '\nCHECKS FAILED')
sys.exit(0 if ok else 1)
