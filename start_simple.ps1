# KJV Sources - Simple Local Startup
# ==================================

param(
    [switch]$SkipDocker,
    [switch]$SkipWeaviate,
    [switch]$SkipAPI
)

Write-Host "Starting KJV Sources Local System" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Configuration
$DOCKER_CONTAINER_NAME = "weaviate"
$WEAVIATE_PORT = 8080
$API_PORT = 8001

function Test-Service {
    param([string]$Url, [string]$Name)
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -ErrorAction Stop
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

# Step 1: Check Docker
if (-not $SkipDocker) {
    Write-Host "Checking Docker..." -ForegroundColor Yellow
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker is running" -ForegroundColor Green
        } else {
            Write-Host "Docker is not running. Please start Docker Desktop." -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "Docker test failed" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Start Weaviate
if (-not $SkipWeaviate) {
    Write-Host "Starting Weaviate..." -ForegroundColor Yellow
    
    # Check if container exists
    $existingContainer = docker ps -a --filter "name=$DOCKER_CONTAINER_NAME" --format "{{.Names}}" 2>$null
    
    if ($existingContainer -eq $DOCKER_CONTAINER_NAME) {
        # Check if running
        $runningContainer = docker ps --filter "name=$DOCKER_CONTAINER_NAME" --format "{{.Names}}" 2>$null
        
        if ($runningContainer -eq $DOCKER_CONTAINER_NAME) {
            Write-Host "Weaviate container is already running" -ForegroundColor Green
        } else {
            Write-Host "Starting existing Weaviate container..." -ForegroundColor Yellow
            docker start $DOCKER_CONTAINER_NAME 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Weaviate container started" -ForegroundColor Green
            } else {
                Write-Host "Failed to start Weaviate container" -ForegroundColor Red
                exit 1
            }
        }
    } else {
        Write-Host "Creating new Weaviate container..." -ForegroundColor Yellow
        
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
            Write-Host "Weaviate container created and started" -ForegroundColor Green
        } else {
            Write-Host "Failed to create Weaviate container" -ForegroundColor Red
            exit 1
        }
    }
    
    # Wait for Weaviate to be ready
    Write-Host "Waiting for Weaviate to be ready..." -ForegroundColor Yellow
    $maxAttempts = 30
    $attempt = 0
    
    do {
        $attempt++
        Start-Sleep -Seconds 2
        
        if (Test-Service -Url "http://localhost:$WEAVIATE_PORT/v1/meta" -Name "Weaviate") {
            Write-Host "Weaviate is ready!" -ForegroundColor Green
            break
        }
        
        if ($attempt -eq $maxAttempts) {
            Write-Host "Weaviate failed to start after $maxAttempts attempts" -ForegroundColor Red
            exit 1
        }
        
    } while ($attempt -lt $maxAttempts)
}

# Step 3: Start API
if (-not $SkipAPI) {
    Write-Host "Starting Elysia API server..." -ForegroundColor Yellow
    
    # Check if API is already running
    if (Test-Service -Url "http://localhost:8000" -Name "Official Elysia") {
        Write-Host "Official Elysia is already running" -ForegroundColor Green
    } else {
        # Activate virtual environment
        if (Test-Path ".\sources-env\Scripts\Activate.ps1") {
            & ".\sources-env\Scripts\Activate.ps1"
            Write-Host "Virtual environment activated" -ForegroundColor Green
        }
        
        # Start official Elysia server in background
        $apiProcess = Start-Process -FilePath "elysia" -ArgumentList "start" -WindowStyle Hidden -PassThru
        
        if ($apiProcess) {
            Write-Host "Elysia API server process started (PID: $($apiProcess.Id))" -ForegroundColor Green
            
            # Wait for API to be ready
            Write-Host "Waiting for API to be ready..." -ForegroundColor Yellow
            $maxAttempts = 20
            $attempt = 0
            
            do {
                $attempt++
                Start-Sleep -Seconds 3
                
                if (Test-Service -Url "http://localhost:8000" -Name "Official Elysia") {
                    Write-Host "Official Elysia is ready!" -ForegroundColor Green
                    break
                }
                
                if ($attempt -eq $maxAttempts) {
                    Write-Host "Elysia API failed to start after $maxAttempts attempts" -ForegroundColor Red
                    exit 1
                }
                
            } while ($attempt -lt $maxAttempts)
        } else {
            Write-Host "Failed to start Elysia API server process" -ForegroundColor Red
            exit 1
        }
    }
}

# Show final status
Write-Host "`nSystem Status:" -ForegroundColor Cyan
Write-Host "==============" -ForegroundColor Cyan

if (Test-Service -Url "http://localhost:$WEAVIATE_PORT/v1/meta" -Name "Weaviate") {
    Write-Host "Weaviate: Running at http://localhost:$WEAVIATE_PORT" -ForegroundColor Green
} else {
    Write-Host "Weaviate: Not Running" -ForegroundColor Red
}

if (Test-Service -Url "http://localhost:8000" -Name "Official Elysia") {
    Write-Host "Official Elysia: Running at http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "Official Elysia: Not Running" -ForegroundColor Red
}

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Open Official Elysia: http://localhost:8000" -ForegroundColor White
Write-Host "2. View API documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "3. Test Weaviate: http://localhost:$WEAVIATE_PORT/v1/meta" -ForegroundColor White

Write-Host "`nLocal system startup completed!" -ForegroundColor Green
