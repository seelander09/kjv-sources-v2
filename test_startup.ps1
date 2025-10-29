# Simple test script for startup functionality
param(
    [switch]$TestDocker,
    [switch]$TestWeaviate
)

Write-Host "🧪 Testing KJV Sources Startup Components" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Test Docker
if ($TestDocker) {
    Write-Host "`n🐳 Testing Docker..." -ForegroundColor Yellow
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker is running" -ForegroundColor Green
        } else {
            Write-Host "❌ Docker is not running" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Docker test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test Weaviate
if ($TestWeaviate) {
    Write-Host "`n🔍 Testing Weaviate..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/v1/meta" -Method GET -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Weaviate is running" -ForegroundColor Green
        } else {
            Write-Host "❌ Weaviate returned status: $($response.StatusCode)" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Weaviate test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n🎯 Test completed!" -ForegroundColor Green
