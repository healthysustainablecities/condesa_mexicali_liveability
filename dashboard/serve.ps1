# Serve the dashboard locally.  PMTiles reads its archives with HTTP range
# requests, which file:// does not support, so the site needs a server even
# when everything it loads is on this machine.
param([int]$Port = 8123)
Set-Location $PSScriptRoot
Write-Host "http://localhost:$Port/  (Ctrl+C to stop)"
python build/serve.py $Port
