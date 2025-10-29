# Document Ingestion Pipeline Runner
Write-Host "Starting Document Ingestion Pipeline..." -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\sources-env\Scripts\Activate.ps1"

# Run the pipeline
Write-Host "Running document ingestion pipeline..." -ForegroundColor Green
try {
    python document_ingestion_pipeline.py
    Write-Host "Pipeline completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Pipeline failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
