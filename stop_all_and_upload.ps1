# Stop All Processes and Upload Data to Qdrant
# =============================================

Write-Host "Stopping all processes accessing Qdrant..." -ForegroundColor Yellow

# Find all Python processes
$allPython = Get-Process python -ErrorAction SilentlyContinue

if ($allPython) {
    Write-Host "Found $($allPython.Count) Python processes" -ForegroundColor Gray
    
    foreach ($proc in $allPython) {
        try {
            $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine -like "*uvicorn*" -or $cmdLine -like "*api*" -or $cmdLine -like "*qdrant*") {
                Write-Host "   Stopping process $($proc.Id)..." -ForegroundColor Gray
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        } catch {
            # Process might have already terminated
        }
    }
}

Write-Host "Stopped processes" -ForegroundColor Green
Write-Host ""
Write-Host "Waiting for file locks to release..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Uploading Torah data to Qdrant..." -ForegroundColor Cyan
Write-Host ("=" * 60)

# Set encoding to avoid emoji issues
$env:PYTHONIOENCODING = 'utf-8'

# Try to upload
python upload_torah_with_progress.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Upload complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Restart the API server with:" -ForegroundColor Cyan
    Write-Host "   .\start_api_server.ps1" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "If upload still fails, you may need to:" -ForegroundColor Yellow
    Write-Host "   1. Close all terminal windows" -ForegroundColor White
    Write-Host "   2. Wait a few more seconds and try again" -ForegroundColor White
    Write-Host "   3. Or use Qdrant server mode instead of local file mode" -ForegroundColor White
}
