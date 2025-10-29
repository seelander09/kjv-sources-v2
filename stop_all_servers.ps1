# Stop All Servers - Clean Shutdown Script
# ========================================
# This script stops all running servers and processes

Write-Host "🛑 Stopping All Servers..." -ForegroundColor Red
Write-Host "=" * 40 -ForegroundColor Cyan

# Stop Python processes (including uvicorn servers)
Write-Host "🔍 Stopping Python processes..." -ForegroundColor Yellow
$pythonProcesses = Get-Process | Where-Object {$_.ProcessName -like "*python*"}
if ($pythonProcesses) {
    $pythonProcesses | Stop-Process -Force
    Write-Host "✅ Stopped $($pythonProcesses.Count) Python processes" -ForegroundColor Green
} else {
    Write-Host "ℹ️ No Python processes found" -ForegroundColor Gray
}

# Stop Elysia processes
Write-Host "🔍 Stopping Elysia processes..." -ForegroundColor Yellow
$elysiaProcesses = Get-Process | Where-Object {$_.ProcessName -like "*elysia*"}
if ($elysiaProcesses) {
    $elysiaProcesses | Stop-Process -Force
    Write-Host "✅ Stopped $($elysiaProcesses.Count) Elysia processes" -ForegroundColor Green
} else {
    Write-Host "ℹ️ No Elysia processes found" -ForegroundColor Gray
}

# Stop any uvicorn processes
Write-Host "🔍 Stopping uvicorn processes..." -ForegroundColor Yellow
$uvicornProcesses = Get-Process | Where-Object {$_.ProcessName -like "*uvicorn*"}
if ($uvicornProcesses) {
    $uvicornProcesses | Stop-Process -Force
    Write-Host "✅ Stopped $($uvicornProcesses.Count) uvicorn processes" -ForegroundColor Green
} else {
    Write-Host "ℹ️ No uvicorn processes found" -ForegroundColor Gray
}

# Check for any remaining web servers
Write-Host "🔍 Checking for remaining web servers..." -ForegroundColor Yellow
$webProcesses = Get-Process | Where-Object {$_.ProcessName -like "*http*" -or $_.ProcessName -like "*server*"}
if ($webProcesses) {
    Write-Host "⚠️ Found additional web processes:" -ForegroundColor Yellow
    $webProcesses | ForEach-Object { Write-Host "   • $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor White }
} else {
    Write-Host "✅ No additional web servers found" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 All servers stopped!" -ForegroundColor Green
Write-Host "You can now start Elysia cleanly with: .\start_elysia_only.ps1" -ForegroundColor Cyan
