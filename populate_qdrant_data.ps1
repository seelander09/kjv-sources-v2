# Populate Qdrant Database with Torah Data
# =========================================

Write-Host "🚀 Populating Qdrant Database with Torah Data" -ForegroundColor Cyan
Write-Host "=" * 60

# Check if data files exist
$outputDir = "output"
$books = @("Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy")
$availableBooks = @()

Write-Host "`n📁 Checking for data files..." -ForegroundColor Yellow
foreach ($book in $books) {
    $csvPath = Join-Path $outputDir $book "$book.csv"
    if (Test-Path $csvPath) {
        $size = (Get-Item $csvPath).Length / 1MB
        Write-Host "   ✅ $book - $([math]::Round($size, 2)) MB" -ForegroundColor Green
        $availableBooks += $book
    } else {
        Write-Host "   ❌ $book - Not found" -ForegroundColor Red
    }
}

if ($availableBooks.Count -eq 0) {
    Write-Host "`n❌ No data files found!" -ForegroundColor Red
    Write-Host "   Please run the pipeline first:" -ForegroundColor Yellow
    Write-Host "   python kjv_pipeline.py" -ForegroundColor White
    exit 1
}

Write-Host "`n📤 Uploading books to Qdrant..." -ForegroundColor Cyan
Write-Host "   This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

# Upload each book
foreach ($book in $availableBooks) {
    Write-Host "📖 Uploading $book..." -ForegroundColor Yellow
    python kjv_cli.py qdrant upload $book.ToLower()
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $book uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Failed to upload $book" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "=" * 60
Write-Host "✅ Data upload complete!" -ForegroundColor Green
Write-Host "`n🌐 You can now:" -ForegroundColor Cyan
Write-Host "   1. Refresh the browser to see data in visualizations" -ForegroundColor White
Write-Host "   2. Test API endpoints at http://127.0.0.1:8001/docs" -ForegroundColor White
Write-Host "   3. Open frontend/birds-eye-view.html for interactive visualizations" -ForegroundColor White

