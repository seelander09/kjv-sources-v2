# Scriptural Truth Fixed Ingestion Pipeline
# =========================================
# This script runs the fixed version of the Scriptural Truth ingestion pipeline
# that addresses the major issues found in the original implementation.

Write-Host "🚀 Scriptural Truth Fixed Ingestion Pipeline" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "scriptural_truth_fixed_ingestion.py")) {
    Write-Host "❌ scriptural_truth_fixed_ingestion.py not found in current directory" -ForegroundColor Red
    Write-Host "Please run this script from the KJV Sources project root directory" -ForegroundColor Yellow
    exit 1
}

# Check if scriptural-truth-website directory exists
if (-not (Test-Path "scriptural-truth-website")) {
    Write-Host "❌ scriptural-truth-website directory not found" -ForegroundColor Red
    Write-Host "Please run the scraper first to download content" -ForegroundColor Yellow
    exit 1
}

# Check available disk space
$diskSpace = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='E:'" | Select-Object @{Name="FreeSpaceGB";Expression={[math]::Round($_.FreeSpace/1GB,2)}}
Write-Host "💾 Available disk space: $($diskSpace.FreeSpaceGB) GB" -ForegroundColor Green

# Check memory usage
$memory = Get-WmiObject -Class Win32_OperatingSystem
$freeMemoryGB = [math]::Round($memory.FreePhysicalMemory/1024/1024, 2)
Write-Host "🧠 Available memory: $freeMemoryGB GB" -ForegroundColor Green

# Check if Qdrant server is running
Write-Host "🔍 Checking Qdrant server status..." -ForegroundColor Yellow
try {
    $qdrantResponse = Invoke-WebRequest -Uri "http://localhost:6333/collections" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Qdrant server is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Qdrant server not running - will use local storage" -ForegroundColor Yellow
}

# Check Python environment
Write-Host "🐍 Checking Python environment..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found in PATH" -ForegroundColor Red
    exit 1
}

# Check required packages
Write-Host "📦 Checking required packages..." -ForegroundColor Yellow
$requiredPackages = @("sentence-transformers", "qdrant-client", "rich", "PyPDF2", "beautifulsoup4", "psutil")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        python -c "import $($package.Replace('-', '_'))" 2>$null
        Write-Host "✅ $package is installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ $package is missing" -ForegroundColor Red
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "📦 Installing missing packages..." -ForegroundColor Yellow
    foreach ($package in $missingPackages) {
        Write-Host "Installing $package..." -ForegroundColor Blue
        pip install $package
    }
}

# Create output directory if it doesn't exist
if (-not (Test-Path "output")) {
    New-Item -ItemType Directory -Path "output" | Out-Null
    Write-Host "📁 Created output directory" -ForegroundColor Green
}

# Run the fixed ingestion pipeline
Write-Host "🚀 Starting fixed ingestion pipeline..." -ForegroundColor Cyan
Write-Host "This may take a while due to the large amount of data (90GB+)" -ForegroundColor Yellow

try {
    python scriptural_truth_fixed_ingestion.py
    Write-Host "✅ Fixed ingestion pipeline completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Fixed ingestion pipeline failed: $_" -ForegroundColor Red
    exit 1
}

# Display results
Write-Host "📊 Checking results..." -ForegroundColor Yellow
if (Test-Path "output/scriptural_truth_fixed_summary.json") {
    $summary = Get-Content "output/scriptural_truth_fixed_summary.json" | ConvertFrom-Json
    Write-Host "📈 Processing Summary:" -ForegroundColor Cyan
    Write-Host "  Total Files: $($summary.total_files)" -ForegroundColor White
    Write-Host "  Processed: $($summary.processed_files)" -ForegroundColor Green
    Write-Host "  Failed: $($summary.failed_files)" -ForegroundColor Red
    Write-Host "  Skipped: $($summary.skipped_files)" -ForegroundColor Yellow
    Write-Host "  Content Length: $($summary.total_content_length) characters" -ForegroundColor White
    Write-Host "  Max Memory Usage: $($summary.max_memory_usage_mb) MB" -ForegroundColor White
}

Write-Host "🎉 Scriptural Truth fixed ingestion completed!" -ForegroundColor Green
Write-Host "📚 Content is now ready for AI learning and Elysia integration" -ForegroundColor Green
