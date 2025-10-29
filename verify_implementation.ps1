# Verify Birds-Eye Dashboard Implementation
# PowerShell script to test all functionality

Write-Host "Birds-Eye Dashboard Implementation Verification" -ForegroundColor Green
Write-Host "=" * 60

# Check if frontend server is running
Write-Host "`n1. Checking Frontend Server..." -ForegroundColor Yellow
$frontendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend server is running at http://localhost:5173" -ForegroundColor Green
        $frontendRunning = $true
    }
} catch {
    Write-Host "❌ Frontend server is not running" -ForegroundColor Red
    Write-Host "   Run: cd frontend; npm run dev" -ForegroundColor Yellow
}

# Check if API server is running
Write-Host "`n2. Checking API Server..." -ForegroundColor Yellow
$apiRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API server is running at http://localhost:8000" -ForegroundColor Green
        $apiRunning = $true
    }
} catch {
    Write-Host "❌ API server is not running" -ForegroundColor Red
    Write-Host "   Run: python -m uvicorn src.kjv_sources.api:app --host 127.0.0.1 --port 8000" -ForegroundColor Yellow
}

# Check if dependencies are installed
Write-Host "`n3. Checking Dependencies..." -ForegroundColor Yellow
$depsInstalled = $false
if (Test-Path "frontend/node_modules") {
    Write-Host "✅ Frontend dependencies are installed" -ForegroundColor Green
    $depsInstalled = $true
} else {
    Write-Host "❌ Frontend dependencies not installed" -ForegroundColor Red
    Write-Host "   Run: cd frontend; npm install" -ForegroundColor Yellow
}

# Check if visualization components exist
Write-Host "`n4. Checking Visualization Components..." -ForegroundColor Yellow
$componentsExist = $false
$components = @(
    "frontend/src/components/BirdsEyeDashboard.tsx",
    "frontend/src/components/visualizations/SourceTreemap.tsx",
    "frontend/src/components/visualizations/SourceDistribution.tsx",
    "frontend/src/components/visualizations/DoubletSankey.tsx",
    "frontend/src/components/visualizations/TimelineHeatmap.tsx",
    "frontend/src/components/visualizations/SourceAlluvial.tsx",
    "frontend/src/components/visualizations/DoubletComparison.tsx"
)

$allComponentsExist = $true
foreach ($component in $components) {
    if (Test-Path $component) {
        Write-Host "✅ $component" -ForegroundColor Green
    } else {
        Write-Host "❌ $component" -ForegroundColor Red
        $allComponentsExist = $false
    }
}

if ($allComponentsExist) {
    Write-Host "✅ All visualization components exist" -ForegroundColor Green
    $componentsExist = $true
}

# Check if styles exist
Write-Host "`n5. Checking Styles..." -ForegroundColor Yellow
$stylesExist = $false
if (Test-Path "frontend/src/styles/birds-eye-dashboard.css") {
    Write-Host "✅ Birds-eye dashboard styles exist" -ForegroundColor Green
    $stylesExist = $true
} else {
    Write-Host "❌ Birds-eye dashboard styles missing" -ForegroundColor Red
}

# Check if mock data exists
Write-Host "`n6. Checking Mock Data..." -ForegroundColor Yellow
$mockDataExists = $false
if (Test-Path "frontend/src/mockData.ts") {
    Write-Host "✅ Mock data exists for testing" -ForegroundColor Green
    $mockDataExists = $true
} else {
    Write-Host "❌ Mock data missing" -ForegroundColor Red
}

# Summary
Write-Host "`n" + "=" * 60
Write-Host "VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 60

$totalChecks = 6
$passedChecks = 0

if ($frontendRunning) { $passedChecks++ }
if ($apiRunning) { $passedChecks++ }
if ($depsInstalled) { $passedChecks++ }
if ($componentsExist) { $passedChecks++ }
if ($stylesExist) { $passedChecks++ }
if ($mockDataExists) { $passedChecks++ }

Write-Host "Passed: $passedChecks/$totalChecks checks" -ForegroundColor $(if ($passedChecks -eq $totalChecks) { "Green" } else { "Yellow" })

if ($passedChecks -eq $totalChecks) {
    Write-Host "`n🎉 ALL CHECKS PASSED!" -ForegroundColor Green
    Write-Host "Birds-Eye Dashboard is ready to use!" -ForegroundColor Green
    Write-Host "`nAccess the dashboard at: http://localhost:5173" -ForegroundColor Cyan
    Write-Host "Toggle to 'Birds-Eye View' to see the new visualizations" -ForegroundColor Cyan
} else {
    Write-Host "`n⚠️ Some checks failed. Please address the issues above." -ForegroundColor Yellow
}

Write-Host "`nQuick Start Commands:" -ForegroundColor Cyan
Write-Host "1. Start Frontend: cd frontend; npm run dev" -ForegroundColor White
Write-Host "2. Start API: python -m uvicorn src.kjv_sources.api:app --host 127.0.0.1 --port 8000" -ForegroundColor White
Write-Host "3. Open Dashboard: start http://localhost:5173" -ForegroundColor White
