# Auto-Restart Scriptural Truth Migration
# Automatically restarts the migration if it stops or gets stuck

Write-Host "🔄 Scriptural Truth Migration Auto-Restart Manager" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Check if migration is already running
Write-Host "🔍 Checking for existing migration processes..." -ForegroundColor Yellow
$existingProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*enhanced_scriptural_truth_migration.py*"
}

if ($existingProcesses) {
    Write-Host "⚠️ Found existing migration processes:" -ForegroundColor Yellow
    $existingProcesses | ForEach-Object {
        Write-Host "   PID: $($_.Id) - Started: $($_.StartTime)" -ForegroundColor Yellow
    }
    
    $choice = Read-Host "Do you want to (k)ill existing processes, (c)ontinue with auto-restart, or (s)top? [k/c/s]"
    
    switch ($choice.ToLower()) {
        "k" {
            Write-Host "🛑 Stopping existing migration processes..." -ForegroundColor Red
            $existingProcesses | Stop-Process -Force
            Start-Sleep -Seconds 2
        }
        "c" {
            Write-Host "✅ Continuing with auto-restart manager..." -ForegroundColor Green
        }
        "s" {
            Write-Host "❌ Stopped by user" -ForegroundColor Red
            exit
        }
        default {
            Write-Host "❌ Invalid choice. Stopping." -ForegroundColor Red
            exit
        }
    }
}

# Show current migration status
Write-Host "📊 Current migration status:" -ForegroundColor Yellow
python enhanced_migration_status.py

Write-Host "`n🚀 Starting auto-restart manager..." -ForegroundColor Green
Write-Host "💡 This will automatically restart the migration if it stops or gets stuck" -ForegroundColor Cyan
Write-Host "💡 Press Ctrl+C to stop the auto-restart manager" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Green

# Start the auto-restart manager
try {
    python auto_restart_migration.py
}
catch {
    Write-Host "❌ Auto-restart manager failed: $_" -ForegroundColor Red
}

Write-Host "`n✅ Auto-restart manager stopped" -ForegroundColor Green
