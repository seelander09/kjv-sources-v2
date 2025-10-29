# KJV Sources - Complete Local System Startup
# ===========================================
# 
# This script provides a robust, comprehensive startup sequence for:
# 1. Docker Desktop (if not running)
# 2. Weaviate vector database
# 3. Elysia API server
# 4. Health checks and status monitoring
#
# Designed to work without API keys for local development

param(
    [switch]$SkipDocker,
    [switch]$SkipWeaviate,
    [switch]$SkipAPI,
    [switch]$ForceRestart,
    [switch]$ShowLogs
)

# Configuration
$DOCKER_CONTAINER_NAME = "kjv-weaviate"
$WEAVIATE_PORT = 8080
$API_PORT = 8001
$HEALTH_CHECK_TIMEOUT = 30
$STARTUP_DELAY = 5

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

function Test-ServiceHealth {
    param(
        [string]$Url,
        [string]$ServiceName,
        [int]$TimeoutSeconds = 10
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec $TimeoutSeconds -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "✅ $ServiceName is healthy" $Colors.Success
            return $true
        }
    }
    catch {
        Write-ColorOutput "❌ $ServiceName health check failed: $($_.Exception.Message)" $Colors.Error
        return $false
    }
    return $false
}

function Wait-ForService {
    param(
        [string]$Url,
        [string]$ServiceName,
        [int]$MaxAttempts = 30,
        [int]$DelaySeconds = 2
    )
    
    Write-ColorOutput "⏳ Waiting for $ServiceName to be ready..." $Colors.Info
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        Write-ColorOutput "   Attempt $i/$MaxAttempts - Testing $ServiceName..." $Colors.Info
        
        if (Test-ServiceHealth -Url $Url -ServiceName $ServiceName -TimeoutSeconds 3) {
            Write-ColorOutput "✅ $ServiceName is ready!" $Colors.Success
            return $true
        }
        
        if ($i -lt $MaxAttempts) {
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    
    Write-ColorOutput "❌ $ServiceName failed to start after $MaxAttempts attempts" $Colors.Error
    return $false
}

function Start-DockerDesktop {
    Write-ColorOutput "🐳 Checking Docker Desktop..." $Colors.Header
    
    # Check if Docker is running
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Docker Desktop is running" $Colors.Success
            return $true
        }
    }
    catch {
        Write-ColorOutput "❌ Docker Desktop is not running" $Colors.Error
    }
    
    if ($SkipDocker) {
        Write-ColorOutput "⚠️ Skipping Docker startup (-SkipDocker specified)" $Colors.Warning
        return $false
    }
    
    Write-ColorOutput "🚀 Starting Docker Desktop..." $Colors.Info
    
    # Try to start Docker Desktop
    try {
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
        Write-ColorOutput "⏳ Docker Desktop is starting... (this may take 1-2 minutes)" $Colors.Warning
        
        # Wait for Docker to be ready
        $maxWait = 120 # 2 minutes
        $waited = 0
        
        do {
            Start-Sleep -Seconds 5
            $waited += 5
            
            try {
                $dockerInfo = docker info 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-ColorOutput "✅ Docker Desktop is ready!" $Colors.Success
                    return $true
                }
            }
            catch {
                # Continue waiting
            }
            
            Write-ColorOutput "   Still waiting for Docker... ($waited/$maxWait seconds)" $Colors.Info
            
        } while ($waited -lt $maxWait)
        
        Write-ColorOutput "❌ Docker Desktop failed to start within $maxWait seconds" $Colors.Error
        Write-ColorOutput "💡 Please start Docker Desktop manually and try again" $Colors.Warning
        return $false
        
    }
    catch {
        Write-ColorOutput "❌ Failed to start Docker Desktop: $($_.Exception.Message)" $Colors.Error
        Write-ColorOutput "💡 Please start Docker Desktop manually" $Colors.Warning
        return $false
    }
}

function Start-Weaviate {
    Write-ColorOutput "🔍 Starting Weaviate vector database..." $Colors.Header
    
    if ($SkipWeaviate) {
        Write-ColorOutput "⚠️ Skipping Weaviate startup (-SkipWeaviate specified)" $Colors.Warning
        return $true
    }
    
    # Check if container already exists
    $existingContainer = docker ps -a --filter "name=$DOCKER_CONTAINER_NAME" --format "{{.Names}}" 2>$null
    
    if ($existingContainer -eq $DOCKER_CONTAINER_NAME) {
        Write-ColorOutput "📦 Found existing Weaviate container" $Colors.Info
        
        # Check if it's running
        $runningContainer = docker ps --filter "name=$DOCKER_CONTAINER_NAME" --format "{{.Names}}" 2>$null
        
        if ($runningContainer -eq $DOCKER_CONTAINER_NAME) {
            Write-ColorOutput "✅ Weaviate container is already running" $Colors.Success
        } else {
            if ($ForceRestart) {
                Write-ColorOutput "🔄 Restarting existing Weaviate container..." $Colors.Info
                docker stop $DOCKER_CONTAINER_NAME 2>$null
                docker rm $DOCKER_CONTAINER_NAME 2>$null
            } else {
                Write-ColorOutput "🚀 Starting existing Weaviate container..." $Colors.Info
                docker start $DOCKER_CONTAINER_NAME 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-ColorOutput "✅ Weaviate container started" $Colors.Success
                } else {
                    Write-ColorOutput "❌ Failed to start Weaviate container" $Colors.Error
                    return $false
                }
            }
        }
    } else {
        Write-ColorOutput "🆕 Creating new Weaviate container..." $Colors.Info
        
        # Create Weaviate container with proper configuration
        $dockerCommand = @(
            "docker", "run", "-d",
            "--name", $DOCKER_CONTAINER_NAME,
            "-p", "${WEAVIATE_PORT}:${WEAVIATE_PORT}",
            "-p", "50051:50051",
            "-e", "QUERY_DEFAULTS_LIMIT=25",
            "-e", "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true",
            "-e", "PERSISTENCE_DATA_PATH=/var/lib/weaviate",
            "-e", "DEFAULT_VECTORIZER_MODULE=none",
            "-e", "ENABLE_MODULES=",
            "-e", "CLUSTER_HOSTNAME=node1",
            "-v", "weaviate_data:/var/lib/weaviate",
            "semitechnologies/weaviate:latest"
        )
        
        & $dockerCommand[0] $dockerCommand[1..($dockerCommand.Length-1)]
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Weaviate container created and started" $Colors.Success
        } else {
            Write-ColorOutput "❌ Failed to create Weaviate container" $Colors.Error
            return $false
        }
    }
    
    # Wait for Weaviate to be ready
    $weaviateUrl = "http://localhost:$WEAVIATE_PORT/v1/meta"
    if (-not (Wait-ForService -Url $weaviateUrl -ServiceName "Weaviate")) {
        return $false
    }
    
    Write-ColorOutput "🌐 Weaviate is ready at: http://localhost:$WEAVIATE_PORT" $Colors.Success
    return $true
}

function Start-API {
    Write-ColorOutput "🚀 Starting Elysia API server..." $Colors.Header
    
    if ($SkipAPI) {
        Write-ColorOutput "⚠️ Skipping API startup (-SkipAPI specified)" $Colors.Warning
        return $true
    }
    
    # Check if API is already running
    if (Test-ServiceHealth -Url "http://localhost:$API_PORT/api/elysia/status" -ServiceName "Elysia API" -TimeoutSeconds 3) {
        Write-ColorOutput "✅ Elysia API is already running" $Colors.Success
        return $true
    }
    
    # Activate virtual environment
    Write-ColorOutput "🔧 Activating virtual environment..." $Colors.Info
    if (Test-Path ".\sources-env\Scripts\Activate.ps1") {
        & ".\sources-env\Scripts\Activate.ps1"
        Write-ColorOutput "✅ Virtual environment activated" $Colors.Success
    } else {
        Write-ColorOutput "⚠️ Virtual environment not found, using system Python" $Colors.Warning
    }
    
    # Start the API server in background
    Write-ColorOutput "🎯 Starting Elysia API server on port $API_PORT..." $Colors.Info
    
    $apiProcess = Start-Process -FilePath "python" -ArgumentList "elysia_api_server.py" -WindowStyle Hidden -PassThru
    
    if ($apiProcess) {
        Write-ColorOutput "✅ Elysia API server process started (PID: $($apiProcess.Id))" $Colors.Success
        
        # Wait for API to be ready
        $apiUrl = "http://localhost:$API_PORT/api/elysia/status"
        if (Wait-ForService -Url $apiUrl -ServiceName "Elysia API" -MaxAttempts 20 -DelaySeconds 3) {
            Write-ColorOutput "🌐 Elysia API is ready at: http://localhost:$API_PORT" $Colors.Success
            return $true
        } else {
            Write-ColorOutput "❌ Elysia API failed to start properly" $Colors.Error
            return $false
        }
    } else {
        Write-ColorOutput "❌ Failed to start Elysia API server process" $Colors.Error
        return $false
    }
}

function Show-SystemStatus {
    Write-ColorOutput "`n📊 System Status Summary" $Colors.Header
    Write-ColorOutput "========================" $Colors.Header
    
    # Check Docker
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "🐳 Docker Desktop: ✅ Running" $Colors.Success
        } else {
            Write-ColorOutput "🐳 Docker Desktop: ❌ Not Running" $Colors.Error
        }
    }
    catch {
        Write-ColorOutput "🐳 Docker Desktop: ❌ Not Running" $Colors.Error
    }
    
    # Check Weaviate
    if (Test-ServiceHealth -Url "http://localhost:$WEAVIATE_PORT/v1/meta" -ServiceName "Weaviate" -TimeoutSeconds 3) {
        Write-ColorOutput "🔍 Weaviate: ✅ Running at http://localhost:$WEAVIATE_PORT" $Colors.Success
    } else {
        Write-ColorOutput "🔍 Weaviate: ❌ Not Running" $Colors.Error
    }
    
    # Check API
    if (Test-ServiceHealth -Url "http://localhost:$API_PORT/api/elysia/status" -ServiceName "Elysia API" -TimeoutSeconds 3) {
        Write-ColorOutput "🌳 Elysia API: ✅ Running at http://localhost:$API_PORT" $Colors.Success
    } else {
        Write-ColorOutput "🌳 Elysia API: ❌ Not Running" $Colors.Error
    }
    
    Write-ColorOutput "`n🎯 Next Steps:" $Colors.Info
    Write-ColorOutput "  1. 🌐 Open Elysia web interface: http://localhost:$API_PORT" $Colors.Info
    Write-ColorOutput "  2. 📚 View API documentation: http://localhost:$API_PORT/docs" $Colors.Info
    Write-ColorOutput "  3. 🔍 Test Weaviate: http://localhost:$WEAVIATE_PORT/v1/meta" $Colors.Info
    Write-ColorOutput "  4. 📊 Monitor system: python system_status_summary.py" $Colors.Info
}

function Show-Logs {
    Write-ColorOutput "`n📋 System Logs" $Colors.Header
    Write-ColorOutput "==============" $Colors.Header
    
    # Show Docker logs
    Write-ColorOutput "🐳 Docker Container Logs:" $Colors.Info
    docker logs --tail 10 $DOCKER_CONTAINER_NAME 2>$null
    
    # Show API logs (if available)
    if (Test-Path "elysia_integration.log") {
        Write-ColorOutput "`n🌳 Elysia Integration Logs:" $Colors.Info
        Get-Content "elysia_integration.log" -Tail 10
    }
}

# Main execution
Write-ColorOutput "🚀 KJV Sources - Complete Local System Startup" $Colors.Header
Write-ColorOutput "=============================================" $Colors.Header
Write-ColorOutput "Starting all services for local development (no API keys required)" $Colors.Info
Write-ColorOutput ""

# Step 1: Start Docker Desktop
if (-not (Start-DockerDesktop)) {
    Write-ColorOutput "❌ Cannot proceed without Docker Desktop" $Colors.Error
    exit 1
}

Start-Sleep -Seconds $STARTUP_DELAY

# Step 2: Start Weaviate
if (-not (Start-Weaviate)) {
    Write-ColorOutput "❌ Cannot proceed without Weaviate" $Colors.Error
    exit 1
}

Start-Sleep -Seconds $STARTUP_DELAY

# Step 3: Start API
if (-not (Start-API)) {
    Write-ColorOutput "❌ Cannot proceed without API server" $Colors.Error
    exit 1
}

# Step 4: Show status
Show-SystemStatus

# Step 5: Show logs if requested
if ($ShowLogs) {
    Show-Logs
}

Write-ColorOutput "`n🎉 Local system startup completed!" $Colors.Success
Write-ColorOutput "All services are running and ready for use." $Colors.Success

# Keep script running if requested
if (-not $ShowLogs) {
    Write-ColorOutput "`nPress any key to exit..." $Colors.Info
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}
