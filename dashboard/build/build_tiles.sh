#!/bin/bash
# Build the dashboard's PMTiles archives from the GeoJSONSeq layers exported by
# process/_export_dashboard.py (run first, inside the ghsci container).
#
#   <slug>_scale_<scale>__<group>.pmtiles
#                            one per aggregation scale and tile group of
#                            columns (see _export_dashboard.tile_groups): each
#                            has its own tile budget, and no feature is heavy
#                            enough to be dropped from the zoomed out tiles
#   <slug>_network.pmtiles   the street network (dense; its own archive)
#   <slug>_context.pmtiles   destinations, open space entries, boundaries
#
# Each archive is a separate MapLibre source, so they may differ in maxzoom;
# what must not differ is the maxzoom of layers *joined into one* archive, which
# is why the context layers are tiled at a common -z and joined afterwards.
# IMPORTANT: never use --extend-zooms-if-still-dropping -- one layer extending
# past the others makes the joined archive's advertised maxzoom lie, and layers
# vanish at high zoom.
#
# Usage (from the dashboard directory): bash build/build_tiles.sh <slug>
# Requires: docker image tippecanoe:local (see build/Dockerfile) and the export
# already present in the analysis container at /tmp/dashboard_export/<slug>.
# Environment:
#   GHSCI_CONTAINER  container to copy the export from (default "ghsci")
#   REUSE_EXPORT=1   tile the copy already in build/_work/<slug> instead of
#                    re-copying, for iterating on tippecanoe flags
#   ONLY_CHANGED=1   keep each scale archive that is newer than its layer
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Scratch lives outside the repo: the repo is inside a OneDrive-synced
# folder and the intermediates run to about a gigabyte per city, which
# OneDrive would try to upload.  Set TILE_WORK to put it elsewhere.
WORK="${TILE_WORK:-/tmp/ghsci-dashboard}"
mkdir -p "$WORK"

# Docker Desktop on Windows needs a Windows-style path for -v; pwd -W (Git Bash)
# gives that directly, spaces and all.  Falls back to the plain path elsewhere.
if MOUNT="$(cd "$WORK" && pwd -W 2>/dev/null)"; then :; else MOUNT="$WORK"; fi
tc() { MSYS_NO_PATHCONV=1 docker run --rm -v "$MOUNT:/data" tippecanoe:local "$@"; }

# Below z11 keep only the roads that carry the map's shape, so overview zooms
# thin cartographically instead of dropping random segments.
NETWORK_FILTER='{"network":["any",[">=","$zoom",11],["in","highway","motorway","motorway_link","trunk","trunk_link","primary","primary_link","secondary","secondary_link","tertiary","tertiary_link","cycleway"]]}'

SCALE_MAXZOOM=14   # fine enough for a 120 m2 Condesa lot to keep its shape
CONTEXT_MAXZOOM=14
NETWORK_MAXZOOM=13

for slug in "$@"; do
  echo "== $slug"
  # Always re-copy, so a rebuild can never quietly tile the previous run's data.
  if [ -d "$WORK/$slug" ] && [ "${REUSE_EXPORT:-0}" = "1" ]; then
    echo "-- reusing existing export in _work/$slug (REUSE_EXPORT=1)"
  else
    rm -rf "${WORK:?}/$slug"
    # Both sides of docker cp need protecting from MSYS path conversion on
    # Windows: the container path must stay as written, and the host path
    # must be the Windows-style $MOUNT -- a Git Bash "/c/Users/..."
    # destination is read by Docker as relative to the C: drive, which
    # fails with a confusing "directory does not exist".
    MSYS_NO_PATHCONV=1 docker cp \
      "${GHSCI_CONTAINER:-ghsci}:/tmp/dashboard_export/$slug" "$MOUNT/"
  fi

  # One archive per scale and tile group.  Polygons are coalesced rather than
  # dropped: an area that vanishes at low zoom reads as missing data, which is
  # exactly the thing the left-joined export exists to avoid.  The export keeps
  # each group narrow enough that nothing should need dropping at all, so any
  # tile tippecanoe had to thin is reported, and fails the build unless
  # ALLOW_DROPS=1 (a scale that thins is one that empties when zoomed out).
  dropped=()
  for f in "$WORK/$slug"/scale_*.geojsonl; do
    [ -e "$f" ] || continue
    layer=$(basename "$f" .geojsonl)
    # ONLY_CHANGED=1 keeps an archive newer than its layer, so a re-export
    # that changed a few groups re-tiles only those
    if [ "${ONLY_CHANGED:-0}" = "1" ] && [ "$WORK/${slug}_${layer}.pmtiles" -nt "$f" ]; then
      echo "-- $layer (unchanged, kept)"
      continue
    fi
    echo "-- $layer"
    log="$WORK/$slug/$layer.tippecanoe.log"
    tc tippecanoe --force -o "/data/${slug}_${layer}.pmtiles" -l "$layer" \
      -Z6 -z$SCALE_MAXZOOM --maximum-tile-bytes=5000000 \
      --coalesce-smallest-as-needed --drop-smallest-as-needed \
      "/data/$slug/$layer.geojsonl" > "$log" 2>&1 || { cat "$log"; exit 1; }
    thinned=$(grep -c -e "Going to try" -e "too many features" -e "too much data" "$log" || true)
    if [ "$thinned" -gt 0 ]; then
      echo "   ! $thinned tiles thinned to fit (see $log)"
      dropped+=("$layer")
    fi
  done
  if [ ${#dropped[@]} -gt 0 ] && [ "${ALLOW_DROPS:-0}" != "1" ]; then
    echo "!! features were dropped from: ${dropped[*]}"
    echo "   narrow the tile groups (dashboard.tile_max_columns) and re-export,"
    echo "   or set ALLOW_DROPS=1 to accept it"
    exit 1
  fi

  if [ -e "$WORK/$slug/network.geojsonl" ]; then
    echo "-- network (own archive)"
    tc tippecanoe -q --force -o "/data/${slug}_network.pmtiles" -l network \
      -Z8 -z$NETWORK_MAXZOOM -j "$NETWORK_FILTER" \
      --maximum-tile-bytes=2500000 --drop-densest-as-needed \
      "/data/$slug/network.geojsonl"
  fi

  # Everything else joined into one context archive.
  parts=()
  for f in "$WORK/$slug"/*.geojsonl; do
    layer=$(basename "$f" .geojsonl)
    case "$layer" in scale_*|network) continue ;; esac
    case "$layer" in
      boundary|buffer) args="-Z4" ;;
      destinations)    args="-Z9 --drop-densest-as-needed" ;;
      *)               args="-Z10 --drop-densest-as-needed" ;;
    esac
    echo "-- $layer ($args)"
    tc tippecanoe -q --force -o "/data/$slug/$layer.pmtiles" -l "$layer" \
      -z$CONTEXT_MAXZOOM $args "/data/$slug/$layer.geojsonl"
    parts+=("/data/$slug/$layer.pmtiles")
  done
  if [ ${#parts[@]} -gt 0 ]; then
    tc tile-join -q --force -pk -o "/data/${slug}_context.pmtiles" "${parts[@]}"
  fi

  echo "-- built:"
  ls -lh "$WORK/${slug}"_context.pmtiles "$WORK/${slug}"_network.pmtiles "$WORK/${slug}"_scale_*.pmtiles 2>/dev/null
  echo "   run: bash build/deploy.sh $slug"
done
