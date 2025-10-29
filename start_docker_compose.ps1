# KJV Sources - Docker Compose Startup
# ====================================
# 
# Alternative startup method using docker-compose
# This provides a more containerized approach

param(
    [string]$Profile = "weaviate",
    [switch]$Build,
    [switch]$ForceRecreate,
    [switch]$ShowLogs
)

# Colors for output
$Colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White",
        [string]$Prefix = ""
    )
    if ($Prefix) {
        Write-Host "$Prefix " -NoNewline -ForegroundColor $Color
    }
    Write-Host $Message -ForegroundColor $Color
}

function Test-DockerCompose {
    Write-ColorOutput "🔍 Checking docker-compose availability..." $Colors.Info
    
    try {
        $version = docker-compose --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Docker Compose is available" $Colors.Success
            return $true
        }
    }
    catch {
        # Try docker compose (newer syntax)
        try {
            $version = docker compose version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Docker Compose (new syntax) is available" $Colors.Success
                return $true
            }
        }
        catch {
            Write-ColorOutput "❌ Docker Compose not found" $Colors.Error
            return $false
        }
    }
    
    return $false
}

function Start-DockerCompose {
    param(
        [string]$Profile,
        [bool]$Build,
        [bool]$ForceRecreate
    )
    
    Write-ColorOutput "🚀 Starting services with profile: $Profile" $Colors.Header
    
    # Build command
    $command = @("docker-compose")
    
    # Add profile
    $command += "--profile", $Profile
    
    # Add build flag if requested
    if ($Build) {
        $command += "--build"
    }
    
    # Add force recreate if requested
    if ($ForceRecreate) {
        $command += "--force-recreate"
    }
    
    # Add up command
    $command += "up", "-d"
    
    Write-ColorOutput "   Command: $($command -join ' ')" $Colors.Info
    
    # Execute command
    & $command[0] $command[1..($command.Length-1)]
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✅ Services started successfully" $Colors.Success
        return $true
    } else {
        Write-ColorOutput "❌ Failed to start services" $Colors.Error
        return $false
    }
}

function Show-ServiceStatus {
    Write-ColorOutput "`n📊 Service Status" $Colors.Header
    Write-ColorOutput "================" $Colors.Header
    
    # Check Weaviate
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/v1/meta" -Method GET -TimeoutSec 3 -ErrorAction Stop
        Write-ColorOutput "🔍 Weaviate: ✅ Running at http://localhost:8080" $Colors.Success
    }
    catch {
        Write-ColorOutput "🔍 Weaviate: ❌ Not Running" $Colors.Error
    }
    
    # Check API (if started with api profile)
    if ($Profile -eq "api" -or $Profile -eq "production") {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8001/api/elysia/status" -Method GET -TimeoutSec 3 -ErrorAction Stop
            Write-ColorOutput "🌳 Elysia API: ✅ Running at http://localhost:8001" $Colors.Success
        }
        catch {
            Write-ColorOutput "🌳 Elysia API: ❌ Not Running" $Colors.Error
        }
    }
    
    # Show running containers
    Write-ColorOutput "`n🐳 Running Containers:" $Colors.Info
    docker ps --filter "name=kjv" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

function Show-Logs {
    Write-ColorOutput "`n📋 Service Logs" $Colors.Header
    Write-ColorOutput "===============" $Colors.Header
    
    # Show logs for the profile
    $command = @("docker-compose", "--profile", $Profile, "logs", "--tail", "20")
    & $command[0] $command[1..($command.Length-1)]
}

# Main execution
Write-ColorOutput "🐳 KJV Sources - Docker Compose Startup" $Colors.Header
Write-ColorOutput "======================================" $Colors.Header
Write-ColorOutput "Starting services using docker-compose with profile: $Profile" $Colors.Info
Write-ColorOutput ""

# Check docker-compose availability
if (-not (Test-DockerCompose)) {
    Write-ColorOutput "❌ Cannot proceed without Docker Compose" $Colors.Error
    Write-ColorOutput "💡 Please install Docker Desktop which includes Docker Compose" $Colors.Warning
    exit 1
}

# Start services
if (-not (Start-DockerCompose -Profile $Profile -Build $Build -ForceRecreate $ForceRecreate)) {
    Write-ColorOutput "❌ Failed to start services" $Colors.Error
    exit 1
}

# Wait a moment for services to start
Start-Sleep -Seconds 5

# Show status
Show-ServiceStatus

# Show logs if requested
if ($ShowLogs) {
    Show-Logs
}

Write-ColorOutput "`n🎉 Docker Compose startup completed!" $Colors.Success

# Show available profiles
Write-ColorOutput "`n📋 Available Profiles:" $Colors.Info
Write-ColorOutput "  weaviate    - Start only Weaviate vector database" $Colors.Info
Write-ColorOutput "  api         - Start Weaviate + API server" $Colors.Info
Write-ColorOutput "  qdrant      - Start Qdrant vector database (alternative)" $Colors.Info
Write-ColorOutput "  cache       - Start Redis cache" $Colors.Info
Write-ColorOutput "  production  - Start all services with Nginx" $Colors.Info

Write-ColorOutput "`n💡 Usage Examples:" $Colors.Info
Write-ColorOutput "  .\start_docker_compose.ps1 -Profile weaviate" $Colors.Info
Write-ColorOutput "  .\start_docker_compose.ps1 -Profile api -Build" $Colors.Info
Write-ColorOutput "  .\start_docker_compose.ps1 -Profile production -ShowLogs" $Colors.Info

if (-not $ShowLogs) {
    Write-ColorOutput "`nPress any key to exit..." $Colors.Info
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}
