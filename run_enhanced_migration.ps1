# Enhanced Scriptural Truth Migration Runner
# Provides better monitoring and control

param(
    [switch]$Status,
    [switch]$Errors,
    [switch]$Cleanup,
    [int]$ErrorLimit = 10
)

Write-Host "🚀 Enhanced Scriptural Truth Migration Manager" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Check if we're just showing status
if ($Status) {
    Write-Host "📊 Checking migration status..." -ForegroundColor Yellow
    python enhanced_migration_status.py
    exit
}

# Check if we're showing errors
if ($Errors) {
    Write-Host "⚠️ Showing recent errors..." -ForegroundColor Yellow
    python enhanced_migration_status.py --errors --limit $ErrorLimit
    exit
}

# Check if we're cleaning up
if ($Cleanup) {
    Write-Host "🧹 Cleaning up progress files..." -ForegroundColor Yellow
    python enhanced_migration_status.py --cleanup
    exit
}

# Check if migration is already running
Write-Host "🔍 Checking if migration is already running..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
$migrationRunning = $false

foreach ($proc in $pythonProcesses) {
    try {
        $cmdline = (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
        if ($cmdline -and $cmdline.Contains("scriptural_truth_migration")) {
            $migrationRunning = $true
            Write-Host "⚠️ Migration is already running (PID: $($proc.Id))" -ForegroundColor Yellow
            break
        }
    }
    catch {
        # Ignore errors when checking process command line
    }
}

if ($migrationRunning) {
    $choice = Read-Host "Migration is already running. Do you want to (s)how status, (k)ill existing process, or (c)ancel? [s/k/c]"
    
    switch ($choice.ToLower()) {
        "s" {
            python enhanced_migration_status.py
            exit
        }
        "k" {
            Write-Host "🛑 Stopping existing migration..." -ForegroundColor Red
            taskkill /f /im python.exe
            Start-Sleep -Seconds 2
        }
        "c" {
            Write-Host "❌ Cancelled" -ForegroundColor Red
            exit
        }
        default {
            Write-Host "❌ Invalid choice. Cancelled." -ForegroundColor Red
            exit
        }
    }
}

# Show current status before starting
Write-Host "📊 Current migration status:" -ForegroundColor Yellow
python enhanced_migration_status.py

Write-Host "`n🚀 Starting enhanced migration..." -ForegroundColor Green
Write-Host "💡 Press Ctrl+C to gracefully stop and save progress" -ForegroundColor Cyan
Write-Host "💡 Use 'python enhanced_migration_status.py' to check status anytime" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Green

# Start the migration
try {
    python enhanced_scriptural_truth_migration.py
}
catch {
    Write-Host "❌ Migration failed: $_" -ForegroundColor Red
}

# Show final status
Write-Host "`n📊 Final migration status:" -ForegroundColor Yellow
python enhanced_migration_status.py

Write-Host "`n✅ Migration process completed" -ForegroundColor Green
