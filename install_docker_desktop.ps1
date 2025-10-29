# Install Docker Desktop for Windows
# ==================================

Write-Host "Installing Docker Desktop for Windows" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if Docker is already installed
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "Docker is already installed: $dockerVersion" -ForegroundColor Green
        Write-Host "You can proceed to start Weaviate!" -ForegroundColor Yellow
        exit 0
    }
} catch {
    Write-Host "Docker not found. Proceeding with installation..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Installation Options:" -ForegroundColor Yellow
Write-Host "1. Download Docker Desktop installer (Recommended)" -ForegroundColor White
Write-Host "2. Use Windows Package Manager (winget)" -ForegroundColor White
Write-Host "3. Manual download instructions" -ForegroundColor White
Write-Host ""

# Try winget first (if available)
try {
    Write-Host "Attempting to install via Windows Package Manager..." -ForegroundColor Yellow
    winget install Docker.DockerDesktop
    Write-Host "Docker Desktop installed via winget!" -ForegroundColor Green
    Write-Host "Please restart your computer and start Docker Desktop" -ForegroundColor Yellow
    exit 0
} catch {
    Write-Host "winget installation failed, trying manual download..." -ForegroundColor Yellow
}

# Manual download approach
Write-Host ""
Write-Host "Manual Installation Steps:" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Download Docker Desktop from:" -ForegroundColor Yellow
Write-Host "   https://www.docker.com/products/docker-desktop/" -ForegroundColor White
Write-Host ""
Write-Host "2. Run the installer as Administrator" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Enable WSL 2 integration when prompted" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Restart your computer after installation" -ForegroundColor Yellow
Write-Host ""
Write-Host "5. Start Docker Desktop from Start Menu" -ForegroundColor Yellow
Write-Host ""

# Create a simple download script
$downloadScript = @"
# Download Docker Desktop Installer
# =================================

Write-Host "Downloading Docker Desktop installer..." -ForegroundColor Yellow

# Docker Desktop download URL (latest stable)
`$dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
`$installerPath = "DockerDesktopInstaller.exe"

try {
    Write-Host "Downloading Docker Desktop installer..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri `$dockerUrl -OutFile `$installerPath
    Write-Host "Download complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To install Docker Desktop:" -ForegroundColor Cyan
    Write-Host "   1. Right-click on DockerDesktopInstaller.exe" -ForegroundColor White
    Write-Host "   2. Select 'Run as administrator'" -ForegroundColor White
    Write-Host "   3. Follow the installation wizard" -ForegroundColor White
    Write-Host "   4. Restart your computer when prompted" -ForegroundColor White
    Write-Host ""
    Write-Host "After installation, run: .\start_weaviate_docker.ps1" -ForegroundColor Yellow
} catch {
    Write-Host "Download failed: `$(`$_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please download manually from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
}
"@

$downloadFile = "download_docker.ps1"
$downloadScript | Out-File -FilePath $downloadFile -Encoding UTF8

Write-Host "Created download script: $downloadFile" -ForegroundColor Green
Write-Host ""
Write-Host "Quick Start Options:" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 1 - Automatic Download:" -ForegroundColor Yellow
Write-Host "   .\download_docker.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Option 2 - Manual Download:" -ForegroundColor Yellow
Write-Host "   Visit: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
Write-Host ""
Write-Host "After Docker is installed and running:" -ForegroundColor Cyan
Write-Host "   .\start_weaviate_docker.ps1" -ForegroundColor White