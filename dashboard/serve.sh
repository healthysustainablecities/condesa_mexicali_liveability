#!/bin/bash
# Serve the dashboard locally.  PMTiles reads its archives with HTTP range
# requests, which file:// does not support, so the site needs a server even
# when everything it loads is on this machine.
cd "$(dirname "${BASH_SOURCE[0]}")"
PORT="${1:-8123}"
echo "http://localhost:$PORT/  (Ctrl+C to stop)"
python3 build/serve.py "$PORT" 2>/dev/null || python build/serve.py "$PORT"
