param(
    [int]$Port = 8080
)

Write-Host "Starting Bird's Eye dashboard at http://localhost:$Port/index.html" -ForegroundColor Cyan

if (-not (Test-Path "frontend")) {
    Write-Host "frontend directory not found." -ForegroundColor Red
    exit 1
}

Push-Location "frontend"
try {
    python -m http.server $Port
}
finally {
    Pop-Location
}
