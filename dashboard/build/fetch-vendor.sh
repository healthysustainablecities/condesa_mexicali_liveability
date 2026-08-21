#!/bin/bash
# Fetch the two runtime libraries into vendor/, once, so the site runs without
# the internet.  A workshop room's wifi is not a dependency worth taking.
#
#   bash build/fetch-vendor.sh
#
# Basemap raster tiles still need a connection; the "sin mapa base / no basemap"
# option exists for when there is none.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/vendor"
mkdir -p "$DIR"
MAPLIBRE=5.0.0
PMTILES=4.3.0
fetch() { curl -fsSL "$1" -o "$2" && echo "  $(basename "$2")"; }
echo "vendor/ <- maplibre-gl $MAPLIBRE, pmtiles $PMTILES"
fetch "https://unpkg.com/maplibre-gl@${MAPLIBRE}/dist/maplibre-gl.js"  "$DIR/maplibre-gl.js"
fetch "https://unpkg.com/maplibre-gl@${MAPLIBRE}/dist/maplibre-gl.css" "$DIR/maplibre-gl.css"
fetch "https://unpkg.com/pmtiles@${PMTILES}/dist/pmtiles.js"           "$DIR/pmtiles.js"
echo "done"
