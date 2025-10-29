# Scriptural Truth Diagnostic Script
# ==================================
# This script diagnoses the current state of the Scriptural Truth download and processing

Write-Host "🔍 Scriptural Truth Diagnostic Report" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if scriptural-truth-website directory exists
if (Test-Path "scriptural-truth-website") {
    Write-Host "✅ scriptural-truth-website directory exists" -ForegroundColor Green
    
    # Get directory statistics
    $dirStats = Get-ChildItem "scriptural-truth-website" -Recurse | Measure-Object -Property Length -Sum
    $totalSizeGB = [math]::Round($dirStats.Sum / 1GB, 2)
    $fileCount = $dirStats.Count
    
    Write-Host "📊 Directory Statistics:" -ForegroundColor Yellow
    Write-Host "  Total Files: $fileCount" -ForegroundColor White
    Write-Host "  Total Size: $totalSizeGB GB" -ForegroundColor White
    
    # Check subdirectories
    $subdirs = Get-ChildItem "scriptural-truth-website" -Directory
    Write-Host "📁 Subdirectories:" -ForegroundColor Yellow
    foreach ($subdir in $subdirs) {
        $subdirStats = Get-ChildItem $subdir.FullName -Recurse | Measure-Object -Property Length -Sum
        $subdirSizeMB = [math]::Round($subdirStats.Sum / 1MB, 2)
        $subdirFileCount = $subdirStats.Count
        Write-Host "  $($subdir.Name): $subdirFileCount files, $subdirSizeMB MB" -ForegroundColor White
    }
    
    # Check for specific file types
    $pdfFiles = (Get-ChildItem "scriptural-truth-website" -Recurse -Filter "*.pdf").Count
    $htmlFiles = (Get-ChildItem "scriptural-truth-website" -Recurse -Filter "*.html").Count
    $mp3Files = (Get-ChildItem "scriptural-truth-website" -Recurse -Filter "*.mp3").Count
    $mp4Files = (Get-ChildItem "scriptural-truth-website" -Recurse -Filter "*.mp4").Count
    
    Write-Host "📄 File Type Breakdown:" -ForegroundColor Yellow
    Write-Host "  PDF Files: $pdfFiles" -ForegroundColor White
    Write-Host "  HTML Files: $htmlFiles" -ForegroundColor White
    Write-Host "  MP3 Files: $mp3Files" -ForegroundColor White
    Write-Host "  MP4 Files: $mp4Files" -ForegroundColor White
    
} else {
    Write-Host "❌ scriptural-truth-website directory not found" -ForegroundColor Red
    Write-Host "The scraper may not have been run yet" -ForegroundColor Yellow
}

# Check output directory
if (Test-Path "output") {
    Write-Host "✅ output directory exists" -ForegroundColor Green
    
    # Check for Scriptural Truth output files
    $stFiles = Get-ChildItem "output" -Filter "*scriptural_truth*"
    if ($stFiles.Count -gt 0) {
        Write-Host "📄 Scriptural Truth Output Files:" -ForegroundColor Yellow
        foreach ($file in $stFiles) {
            $fileSizeMB = [math]::Round($file.Length / 1MB, 2)
            Write-Host "  $($file.Name): $fileSizeMB MB" -ForegroundColor White
        }
        
        # Check summary file
        if (Test-Path "output/scriptural_truth_summary.json") {
            try {
                $summary = Get-Content "output/scriptural_truth_summary.json" | ConvertFrom-Json
                Write-Host "Processing Summary:" -ForegroundColor Yellow
                Write-Host "  Total Items: $($summary.total_items)" -ForegroundColor White
                Write-Host "  Content Types: $($summary.content_types | ConvertTo-Json -Compress)" -ForegroundColor White
                Write-Host "  Total Content Length: $($summary.total_content_length) characters" -ForegroundColor White
                Write-Host "  Items with Embeddings: $($summary.items_with_embeddings)" -ForegroundColor White
            } catch {
                Write-Host "Could not parse summary file" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "⚠️ No Scriptural Truth output files found" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ output directory not found" -ForegroundColor Red
}

# Check Qdrant data directory
if (Test-Path "qdrant_data") {
    Write-Host "✅ qdrant_data directory exists" -ForegroundColor Green
    
    $qdrantStats = Get-ChildItem "qdrant_data" -Recurse | Measure-Object -Property Length -Sum
    $qdrantSizeMB = [math]::Round($qdrantStats.Sum / 1MB, 2)
    Write-Host "📊 Qdrant Data Size: $qdrantSizeMB MB" -ForegroundColor White
} else {
    Write-Host "⚠️ qdrant_data directory not found" -ForegroundColor Yellow
}

# Check for log files
$logFiles = Get-ChildItem -Filter "*scriptural_truth*.log"
if ($logFiles.Count -gt 0) {
    Write-Host "📝 Log Files Found:" -ForegroundColor Yellow
    foreach ($logFile in $logFiles) {
        $logSizeKB = [math]::Round($logFile.Length / 1KB, 2)
        Write-Host "  $($logFile.Name): $logSizeKB KB" -ForegroundColor White
        
        # Check for errors in log file
        $errorCount = (Get-Content $logFile.FullName | Select-String "ERROR").Count
        if ($errorCount -gt 0) {
            Write-Host "    Contains $errorCount errors" -ForegroundColor Red
        }
    }
}

# Check system resources
Write-Host "💻 System Resources:" -ForegroundColor Yellow
$memory = Get-WmiObject -Class Win32_OperatingSystem
$totalMemoryGB = [math]::Round($memory.TotalVisibleMemorySize / 1024 / 1024, 2)
$freeMemoryGB = [math]::Round($memory.FreePhysicalMemory / 1024 / 1024, 2)
Write-Host "  Total Memory: $totalMemoryGB GB" -ForegroundColor White
Write-Host "  Free Memory: $freeMemoryGB GB" -ForegroundColor White

$diskSpace = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='E:'" | Select-Object @{Name="FreeSpaceGB";Expression={[math]::Round($_.FreeSpace/1GB,2)}}
Write-Host "  Free Disk Space: $($diskSpace.FreeSpaceGB) GB" -ForegroundColor White

# Check Python environment
Write-Host "🐍 Python Environment:" -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Python Version: $pythonVersion" -ForegroundColor White
} catch {
    Write-Host "  ❌ Python not found" -ForegroundColor Red
}

# Check required packages
$requiredPackages = @("sentence-transformers", "qdrant-client", "rich", "PyPDF2", "beautifulsoup4", "psutil")
Write-Host "📦 Required Packages:" -ForegroundColor Yellow
foreach ($package in $requiredPackages) {
    try {
        python -c "import $($package.Replace('-', '_'))" 2>$null
        Write-Host "  ✅ $package" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ $package" -ForegroundColor Red
    }
}

# Recommendations
Write-Host "Recommendations:" -ForegroundColor Cyan
if ($totalSizeGB -gt 50) {
    Write-Host "  Large dataset detected ($totalSizeGB GB) - consider using streaming processing" -ForegroundColor Yellow
}
if ($freeMemoryGB -lt 4) {
    Write-Host "  Low memory available ($freeMemoryGB GB) - may cause processing issues" -ForegroundColor Yellow
}
if ($diskSpace.FreeSpaceGB -lt 10) {
    Write-Host "  Low disk space ($($diskSpace.FreeSpaceGB) GB) - may cause storage issues" -ForegroundColor Yellow
}

Write-Host "🔍 Diagnostic complete!" -ForegroundColor Green
