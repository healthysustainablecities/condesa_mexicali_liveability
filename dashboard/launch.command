#!/bin/bash
# One click on macOS: start the local server and open a browser.
cd "$(dirname "$0")"
PORT=8123
( sleep 1; open "http://localhost:$PORT/" ) &
python3 build/serve.py "$PORT"
