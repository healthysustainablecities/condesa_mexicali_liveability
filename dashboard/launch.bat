@echo off
REM One click: start the local server, open a browser, hold the window open.
REM Close this window to stop the server.
cd /d "%~dp0"
set PORT=8123
start "" "http://localhost:%PORT%/"
python build\serve.py %PORT%
