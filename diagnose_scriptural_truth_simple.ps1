# Scriptural Truth Simple Diagnostic Script
Write-Host "Scriptural Truth Diagnostic Report" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check if scriptural-truth-website directory exists
if (Test-Path "scriptural-truth-website") {
    Write-Host "scriptural-truth-website directory exists" -ForegroundColor Green
    
    # Get directory statistics
    $dirStats = Get-ChildItem "scriptural-truth-website" -Recurse | Measure-Object -Property Length -Sum
    $totalSizeGB = [math]::Round($dirStats.Sum / 1GB, 2)
    $fileCount = $dirStats.Count
    
    Write-Host "Directory Statistics:" -ForegroundColor Yellow
    Write-Host "  Total Files: $fileCount" -ForegroundColor White
    Write-Host "  Total Size: $totalSizeGB GB" -ForegroundColor White
    
    # Check subdirectories
    $subdirs = Get-ChildItem "scriptural-truth-website" -Directory
    Write-Host "Subdirectories:" -ForegroundColor Yellow
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
    
    Write-Host "File Type Breakdown:" -ForegroundColor Yellow
    Write-Host "  PDF Files: $pdfFiles" -ForegroundColor White
    Write-Host "  HTML Files: $htmlFiles" -ForegroundColor White
    Write-Host "  MP3 Files: $mp3Files" -ForegroundColor White
    Write-Host "  MP4 Files: $mp4Files" -ForegroundColor White
    
} else {
    Write-Host "scriptural-truth-website directory not found" -ForegroundColor Red
}

# Check output directory
if (Test-Path "output") {
    Write-Host "output directory exists" -ForegroundColor Green
    
    # Check for Scriptural Truth output files
    $stFiles = Get-ChildItem "output" -Filter "*scriptural_truth*"
    if ($stFiles.Count -gt 0) {
        Write-Host "Scriptural Truth Output Files:" -ForegroundColor Yellow
        foreach ($file in $stFiles) {
            $fileSizeMB = [math]::Round($file.Length / 1MB, 2)
            Write-Host "  $($file.Name): $fileSizeMB MB" -ForegroundColor White
        }
    } else {
        Write-Host "No Scriptural Truth output files found" -ForegroundColor Yellow
    }
} else {
    Write-Host "output directory not found" -ForegroundColor Red
}

# Check system resources
Write-Host "System Resources:" -ForegroundColor Yellow
$memory = Get-WmiObject -Class Win32_OperatingSystem
$totalMemoryGB = [math]::Round($memory.TotalVisibleMemorySize / 1024 / 1024, 2)
$freeMemoryGB = [math]::Round($memory.FreePhysicalMemory / 1024 / 1024, 2)
Write-Host "  Total Memory: $totalMemoryGB GB" -ForegroundColor White
Write-Host "  Free Memory: $freeMemoryGB GB" -ForegroundColor White

$diskSpace = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='E:'" | Select-Object @{Name="FreeSpaceGB";Expression={[math]::Round($_.FreeSpace/1GB,2)}}
Write-Host "  Free Disk Space: $($diskSpace.FreeSpaceGB) GB" -ForegroundColor White

# Check Python environment
Write-Host "Python Environment:" -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Python Version: $pythonVersion" -ForegroundColor White
} catch {
    Write-Host "  Python not found" -ForegroundColor Red
}

Write-Host "Diagnostic complete!" -ForegroundColor Green
