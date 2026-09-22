#!/bin/bash
# Copy a built dataset into the site and register it in data/datasets.json.
#
# Usage (from the dashboard directory): bash build/deploy.sh <slug> [<slug> ...]
# Expects build/build_tiles.sh to have run, so that build/_work holds both the
# exported JSON (in _work/<slug>/) and the archives (_work/<slug>_*.pmtiles).
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE="$(cd "$SCRIPT_DIR/.." && pwd)"
# Must match build_tiles.sh.  The scratch lives outside the repo because the
# repo is inside a OneDrive-synced folder and the intermediates are about a
# gigabyte per city -- OneDrive would try to upload every byte of them.
WORK="${TILE_WORK:-/tmp/ghsci-dashboard}"

for slug in "$@"; do
  src="$WORK/$slug"
  dest="$SITE/data/$slug"
  [ -d "$src" ] || { echo "no export at $src"; exit 1; }
  mkdir -p "$dest"
  echo "== $slug -> data/$slug"
  for f in manifest.json indicators.json stats.json \
           data_dictionary.csv data_dictionary.xlsx data_dictionary.pdf; do
    [ -e "$src/$f" ] && cp "$src/$f" "$dest/$f"
  done
  # each language's conceptual model figure, where the region configures one
  cp "$src"/conceptual_model_* "$dest/" 2>/dev/null || true
  cp "$WORK/${slug}"_*.pmtiles "$dest/" 2>/dev/null || true
  ls -lh "$dest"
done

# datasets.json is the site's index of what is available.  It is rebuilt from
# whatever manifests are actually present rather than maintained by hand, so a
# dataset cannot be listed and missing (the cycling validation site hardcoded
# its city list in the HTML, which had to be patched on every publish).
python - "$SITE" <<'PY'
import json, os, sys
site = sys.argv[1]
root = os.path.join(site, 'data')
datasets = []
for slug in sorted(os.listdir(root)):
    path = os.path.join(root, slug, 'manifest.json')
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as f:
        m = json.load(f)
    datasets.append({
        'slug': m['slug'],
        'label': m.get('label') or {'en': m.get('name')},
        'codename': m.get('codename'),
        'year': m.get('year'),
        'bbox': m.get('bbox'),
        'regions': {
            k: v.get('label') for k, v in (m.get('regions') or {}).items()
        },
    })
out = os.path.join(root, 'datasets.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump({'datasets': datasets}, f, ensure_ascii=False, indent=1)
print(f'datasets.json: {len(datasets)} dataset(s)')
PY
