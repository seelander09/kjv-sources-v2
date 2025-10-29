# Scriptural Truth to Qdrant Migration Runner
# ===========================================
# Runs the migration in background with status monitoring

Write-Host "🚀 Starting Scriptural Truth to Qdrant Migration" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\sources-env\Scripts\Activate.ps1"

# Create status monitoring
$statusFile = "migration_status.json"
$logFile = "scriptural_truth_migration.log"

# Initialize status
$status = @{
    "started" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    "status" = "Starting"
    "current_step" = "Initializing"
    "progress" = 0
    "pages_found" = 0
    "pages_processed" = 0
    "content_items" = 0
    "embeddings_created" = 0
    "qdrant_points" = 0
    "errors" = @()
}

$status | ConvertTo-Json | Out-File -FilePath $statusFile -Encoding UTF8

Write-Host "📊 Status monitoring enabled" -ForegroundColor Green
Write-Host "   Status file: $statusFile" -ForegroundColor Gray
Write-Host "   Log file: $logFile" -ForegroundColor Gray

# Start migration in background
Write-Host "🔄 Starting migration process..." -ForegroundColor Yellow
$job = Start-Job -ScriptBlock {
    param($statusFile, $logFile)
    
    # Activate virtual environment in job
    & ".\sources-env\Scripts\Activate.ps1"
    
    # Run migration
    python scriptural_truth_qdrant_migration.py 2>&1 | Tee-Object -FilePath $logFile
    
} -ArgumentList $statusFile, $logFile

Write-Host "✅ Migration job started (ID: $($job.Id))" -ForegroundColor Green

# Monitor progress
Write-Host "`n📈 Monitoring progress..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring (migration will continue in background)" -ForegroundColor Yellow

try {
    while ($job.State -eq "Running") {
        # Update status from log file
        if (Test-Path $logFile) {
            $logContent = Get-Content $logFile -Tail 10
            if ($logContent) {
                $lastLine = $logContent[-1]
            }
            
            # Extract progress information
            if ($lastLine -match "Found (\d+) pages") {
                $status.pages_found = [int]$matches[1]
            }
            if ($lastLine -match "Processed (\d+) items") {
                $status.content_items = [int]$matches[1]
            }
            if ($lastLine -match "Creating embeddings") {
                $status.current_step = "Creating AI embeddings"
            }
            if ($lastLine -match "Storing in Qdrant") {
                $status.current_step = "Storing in Qdrant"
            }
            
            $status | ConvertTo-Json | Out-File -FilePath $statusFile -Encoding UTF8
        }
        
        # Display current status
        Clear-Host
        Write-Host "🚀 Scriptural Truth Migration Status" -ForegroundColor Green
        Write-Host "=" * 40 -ForegroundColor Cyan
        Write-Host "Job ID: $($job.Id)" -ForegroundColor White
        Write-Host "Status: $($job.State)" -ForegroundColor White
        Write-Host "Current Step: $($status.current_step)" -ForegroundColor Yellow
        Write-Host "Pages Found: $($status.pages_found)" -ForegroundColor White
        Write-Host "Content Items: $($status.content_items)" -ForegroundColor White
        Write-Host "Embeddings: $($status.embeddings_created)" -ForegroundColor White
        Write-Host "Qdrant Points: $($status.qdrant_points)" -ForegroundColor White
        
        if (Test-Path $logFile) {
            Write-Host "`n📝 Recent Log Entries:" -ForegroundColor Cyan
            $recentLogs = Get-Content $logFile -Tail 5
            foreach ($log in $recentLogs) {
                Write-Host "   $log" -ForegroundColor Gray
            }
        }
        
        Write-Host "`n⏱️  Elapsed: $((Get-Date) - [DateTime]$status.started)" -ForegroundColor White
        Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
        
        Start-Sleep -Seconds 5
    }
    
    # Job completed
    $result = Receive-Job $job
    Remove-Job $job
    
    Write-Host "`n🎉 Migration completed!" -ForegroundColor Green
    Write-Host "Final result:" -ForegroundColor White
    $result | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    
} catch {
    Write-Host "`n⚠️  Monitoring stopped by user" -ForegroundColor Yellow
    Write-Host "Migration is still running in background (Job ID: $($job.Id))" -ForegroundColor White
    Write-Host "Check status with: Get-Job -Id $($job.Id)" -ForegroundColor Gray
    Write-Host "View logs with: Get-Content $logFile -Tail 20" -ForegroundColor Gray
}

Write-Host "`n📊 Migration Status:" -ForegroundColor Cyan
if (Test-Path $statusFile) {
    $finalStatus = Get-Content $statusFile | ConvertFrom-Json
    Write-Host "   Started: $($finalStatus.started)" -ForegroundColor White
    Write-Host "   Pages Found: $($finalStatus.pages_found)" -ForegroundColor White
    Write-Host "   Content Items: $($finalStatus.content_items)" -ForegroundColor White
    Write-Host "   Embeddings: $($finalStatus.embeddings_created)" -ForegroundColor White
    Write-Host "   Qdrant Points: $($finalStatus.qdrant_points)" -ForegroundColor White
}

Write-Host "`n💡 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Check migration results in scriptural_truth_data/ folder" -ForegroundColor White
Write-Host "   2. Verify Qdrant collection with: python -c \"from qdrant_client import QdrantClient; client = QdrantClient(path='qdrant_data'); print(client.get_collection('scriptural_truth'))\"" -ForegroundColor White
Write-Host "   3. Configure Elysia to use new Qdrant collection" -ForegroundColor White

Write-Host "`nPress any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
