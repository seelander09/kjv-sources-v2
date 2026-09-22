# Get KJV Sources project up and running: deps, Qdrant data, API, and dashboard.
# Run from project root. Requires Python 3.8+.

param(
    [switch]$SkipDeps,
    [switch]$SkipData,
    [int]$ApiPort = 8001,
    [int]$FrontendPort = 8080
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "KJV Sources - Starting project" -ForegroundColor Cyan
Write-Host ""

# 1. Dependencies
if (-not $SkipDeps) {
    Write-Host "[1/4] Installing dependencies..." -ForegroundColor Yellow
    $req = @("requirements.txt", "api_requirements.txt")
    foreach ($r in $req) {
        if (Test-Path $r) {
            python -m pip install -q -r $r
            if ($LASTEXITCODE -ne 0) { Write-Host "pip install -r $r failed" -ForegroundColor Red; exit 1 }
        }
    }
    Write-Host "      Done." -ForegroundColor Green
} else {
    Write-Host "[1/4] Skipping dependencies (SkipDeps)." -ForegroundColor Gray
}

# 2. Qdrant data (local kjv_sources collection)
if (-not $SkipData) {
    Write-Host "[2/4] Ensuring Qdrant data (qdrant_data / kjv_sources)..." -ForegroundColor Yellow
    $env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
    python ensure_qdrant_data.py
    if ($LASTEXITCODE -ne 0 -and (Test-Path "qdrant_data")) {
        Write-Host "      Backing up incompatible qdrant_data and retrying..." -ForegroundColor Yellow
        $bak = "qdrant_data.bak." + (Get-Date -Format "yyyyMMdd_HHmmss")
        Rename-Item -Path "qdrant_data" -NewName $bak -ErrorAction SilentlyContinue
        python ensure_qdrant_data.py
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      No data yet. API and dashboard will start; bird-eye endpoints need data (run pipeline then ensure_qdrant_data)." -ForegroundColor Yellow
    } else {
        Write-Host "      Done." -ForegroundColor Green
    }
} else {
    Write-Host "[2/4] Skipping data check (SkipData)." -ForegroundColor Gray
}

# 3. Start API in background
Write-Host "[3/4] Starting API on port $ApiPort..." -ForegroundColor Yellow
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
$apiJob = Start-Job -ScriptBlock {
    param($root, $port)
    Set-Location $root
    $env:PYTHONPATH = "$root;$env:PYTHONPATH"
    python -m uvicorn src.kjv_sources.api:app --host 0.0.0.0 --port $port
} -ArgumentList $PWD, $ApiPort

Start-Sleep -Seconds 2
$apiState = Get-Job -Id $apiJob.Id | Select-Object -ExpandProperty State
if ($apiState -eq "Running") {
    Write-Host "      API running (job $($apiJob.Id))." -ForegroundColor Green
} else {
    Receive-Job -Id $apiJob.Id
    Write-Host "      API job failed to stay running." -ForegroundColor Red
    exit 1
}

# 4. Start frontend in background
Write-Host "[4/4] Starting dashboard on port $FrontendPort..." -ForegroundColor Yellow
if (-not (Test-Path "frontend")) {
    Write-Host "      frontend/ not found; skipping dashboard." -ForegroundColor Yellow
} else {
    $feJob = Start-Job -ScriptBlock {
        param($root, $port)
        Set-Location (Join-Path $root "frontend")
        python -m http.server $port
    } -ArgumentList $PWD, $FrontendPort
    Start-Sleep -Seconds 1
    Write-Host "      Dashboard running (job $($feJob.Id))." -ForegroundColor Green
}

Write-Host ""
Write-Host "Project is up." -ForegroundColor Green
Write-Host "  API:        http://localhost:$ApiPort" -ForegroundColor White
Write-Host "  API docs:   http://localhost:$ApiPort/docs" -ForegroundColor White
if (Test-Path "frontend") {
    Write-Host "  Dashboard:  http://localhost:$FrontendPort/index.html" -ForegroundColor White
}
Write-Host ""
Write-Host "To stop: Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor Gray
Write-Host ""

# Optional: open browser
try {
    if (Test-Path "frontend") {
        Start-Process "http://localhost:$FrontendPort/index.html"
    } else {
        Start-Process "http://localhost:$ApiPort/docs"
    }
} catch {
    # ignore
}

# Keep script running so jobs stay alive; user can Ctrl+C
Wait-Job -Id $apiJob.Id
