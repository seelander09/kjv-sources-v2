# Stop API Server and Upload Data to Qdrant
# ==========================================

Write-Host "🛑 Stopping API Server..." -ForegroundColor Yellow

# Find and stop uvicorn processes
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
$uvicornProcesses = $pythonProcesses | Where-Object {
    $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
    $cmdLine -like "*uvicorn*" -or $cmdLine -like "*api*"
}

if ($uvicornProcesses) {
    foreach ($proc in $uvicornProcesses) {
        Write-Host "   Stopping process $($proc.Id)..." -ForegroundColor Gray
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "✅ API server stopped" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "   No API server process found (may already be stopped)" -ForegroundColor Gray
}

Write-Host "`n📤 Uploading Torah data to Qdrant..." -ForegroundColor Cyan
Write-Host "=" * 60

# Upload all books
python kjv_cli.py qdrant upload-all

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Upload complete!" -ForegroundColor Green
    Write-Host "`n🚀 You can now restart the API server:" -ForegroundColor Cyan
    Write-Host "   .\start_api_server.ps1" -ForegroundColor White
} else {
    Write-Host "`n❌ Upload failed. Check the error messages above." -ForegroundColor Red
}

