# Start API Server for KJV Sources
# ==================================

Write-Host "Starting KJV Sources API Server..." -ForegroundColor Cyan

# Change to project root
Set-Location $PSScriptRoot

# Set PYTHONPATH to include project root (so 'src' is in path)
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"

Write-Host "PYTHONPATH set to: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "Starting server on http://127.0.0.1:8001" -ForegroundColor Green
Write-Host "API docs available at: http://127.0.0.1:8001/docs" -ForegroundColor Cyan
Write-Host ""

# Start the server
python -m uvicorn src.kjv_sources.api:app --reload --port 8001

