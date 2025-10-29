#!/usr/bin/env pwsh
# Clean System Startup Script
# ===========================

Write-Host "🧹 Cleaning up existing processes..." -ForegroundColor Yellow

# Stop all Python processes
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "✅ All Python processes stopped" -ForegroundColor Green

# Wait a moment for cleanup
Start-Sleep -Seconds 3

Write-Host "🚀 Starting systems in sequence..." -ForegroundColor Cyan

# Start Scriptural Truth Scraper first
Write-Host "📥 Starting Scriptural Truth Scraper..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "scriptural_truth_scraper.py" -WindowStyle Hidden

# Wait for scraper to initialize
Start-Sleep -Seconds 5

# Start Official Elysia on port 8001
Write-Host "🌳 Starting Official Elysia on port 8001..." -ForegroundColor Yellow
$env:ELYSIA_PORT="8001"
Start-Process -FilePath "elysia" -ArgumentList "start", "--port", "8001" -WindowStyle Hidden

# Wait for Elysia to start
Start-Sleep -Seconds 10

Write-Host "🔍 Checking system status..." -ForegroundColor Cyan

# Check if systems are running
$scraperRunning = $false
$elysiaRunning = $false

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001" -TimeoutSec 5
    $elysiaRunning = $true
    Write-Host "✅ Official Elysia: Running at http://localhost:8001" -ForegroundColor Green
} catch {
    Write-Host "❌ Official Elysia: Not accessible" -ForegroundColor Red
}

# Check scraper status
$scraperProcesses = Get-Process | Where-Object {$_.ProcessName -eq "python" -and $_.CommandLine -like "*scriptural_truth_scraper*"}
if ($scraperProcesses) {
    $scraperRunning = $true
    Write-Host "✅ Scriptural Truth Scraper: Running in background" -ForegroundColor Green
} else {
    Write-Host "❌ Scriptural Truth Scraper: Not running" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 System Status Summary:" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host "Scriptural Truth Scraper: $(if($scraperRunning){'✅ Running'}else{'❌ Not Running'})" -ForegroundColor $(if($scraperRunning){'Green'}else{'Red'})
Write-Host "Official Elysia: $(if($elysiaRunning){'✅ Running at http://localhost:8001'}else{'❌ Not Running'})" -ForegroundColor $(if($elysiaRunning){'Green'}else{'Red'})

if ($elysiaRunning) {
    Write-Host ""
    Write-Host "🎉 Systems are running successfully!" -ForegroundColor Green
    Write-Host "🌐 Access Official Elysia at: http://localhost:8001" -ForegroundColor Cyan
    Write-Host "📚 API Documentation: http://localhost:8001/docs" -ForegroundColor Cyan
    Write-Host "📥 Scriptural Truth Scraper: Running in background" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "⚠️  Some systems failed to start. Check the logs above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host 'Press any key to continue...' -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
