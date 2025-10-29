# KJV Sources - Stop Local System
# ===============================
# 
# This script cleanly stops all local services:
# 1. Elysia API server
# 2. Weaviate container
# 3. Docker Desktop (optional)

param(
    [switch]$StopDocker,
    [switch]$Force,
    [switch]$ShowLogs
)

# Configuration
$DOCKER_CONTAINER_NAME = "kjv-weaviate"
$API_PORT = 8001

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

function Stop-API {
    Write-ColorOutput "🛑 Stopping Elysia API server..." $Colors.Header
    
    # Find and stop Elysia processes
    $apiProcesses = Get-Process | Where-Object {
        $_.ProcessName -eq "python" -and 
        ($_.CommandLine -like "*elysia*" -or $_.CommandLine -like "*uvicorn*")
    }
    
    if ($apiProcesses) {
        foreach ($process in $apiProcesses) {
            Write-ColorOutput "   Stopping API process (PID: $($process.Id))..." $Colors.Info
            if ($Force) {
                Stop-Process -Id $process.Id -Force
            } else {
                Stop-Process -Id $process.Id
            }
        }
        Write-ColorOutput "✅ Elysia API server stopped" $Colors.Success
    } else {
        Write-ColorOutput "ℹ️ No Elysia API server processes found" $Colors.Info
    }
    
    # Also try to stop any process using the API port
    try {
        $netstat = netstat -ano | Select-String ":$API_PORT "
        if ($netstat) {
            $pids = $netstat | ForEach-Object { ($_ -split '\s+')[-1] } | Sort-Object -Unique
            foreach ($pid in $pids) {
                if ($pid -and $pid -ne "0") {
                    Write-ColorOutput "   Stopping process using port $API_PORT (PID: $pid)..." $Colors.Info
                    if ($Force) {
                        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    } else {
                        Stop-Process -Id $pid -ErrorAction SilentlyContinue
                    }
                }
            }
        }
    }
    catch {
        # Ignore errors
    }
}

function Stop-Weaviate {
    Write-ColorOutput "🛑 Stopping Weaviate container..." $Colors.Header
    
    # Check if container exists
    $existingContainer = docker ps -a --filter "name=$DOCKER_CONTAINER_NAME" --format "{{.Names}}" 2>$null
    
    if ($existingContainer -eq $DOCKER_CONTAINER_NAME) {
        # Check if it's running
        $runningContainer = docker ps --filter "name=$DOCKER_CONTAINER_NAME" --format "{{.Names}}" 2>$null
        
        if ($runningContainer -eq $DOCKER_CONTAINER_NAME) {
            Write-ColorOutput "   Stopping Weaviate container..." $Colors.Info
            docker stop $DOCKER_CONTAINER_NAME 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Weaviate container stopped" $Colors.Success
            } else {
                Write-ColorOutput "❌ Failed to stop Weaviate container" $Colors.Error
            }
        } else {
            Write-ColorOutput "ℹ️ Weaviate container is already stopped" $Colors.Info
        }
        
        if ($Force) {
            Write-ColorOutput "   Removing Weaviate container..." $Colors.Info
            docker rm $DOCKER_CONTAINER_NAME 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✅ Weaviate container removed" $Colors.Success
            }
        }
    } else {
        Write-ColorOutput "ℹ️ No Weaviate container found" $Colors.Info
    }
}

function Stop-DockerDesktop {
    Write-ColorOutput "🛑 Stopping Docker Desktop..." $Colors.Header
    
    # Find Docker Desktop processes
    $dockerProcesses = Get-Process | Where-Object {
        $_.ProcessName -like "*Docker*" -or 
        $_.ProcessName -like "*docker*" -or
        $_.ProcessName -like "*com.docker*"
    }
    
    if ($dockerProcesses) {
        foreach ($process in $dockerProcesses) {
            Write-ColorOutput "   Stopping Docker process: $($process.ProcessName) (PID: $($process.Id))..." $Colors.Info
            if ($Force) {
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            } else {
                Stop-Process -Id $process.Id -ErrorAction SilentlyContinue
            }
        }
        Write-ColorOutput "✅ Docker Desktop stopped" $Colors.Success
    } else {
        Write-ColorOutput "ℹ️ No Docker Desktop processes found" $Colors.Info
    }
}

function Show-SystemStatus {
    Write-ColorOutput "`n📊 System Status After Shutdown" $Colors.Header
    Write-ColorOutput "===============================" $Colors.Header
    
    # Check API
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -Method GET -TimeoutSec 3 -ErrorAction Stop
        Write-ColorOutput "🌳 Official Elysia: ⚠️ Still Running" $Colors.Warning
    }
    catch {
        Write-ColorOutput "🌳 Official Elysia: ✅ Stopped" $Colors.Success
    }
    
    # Check Weaviate
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/v1/meta" -Method GET -TimeoutSec 3 -ErrorAction Stop
        Write-ColorOutput "🔍 Weaviate: ⚠️ Still Running" $Colors.Warning
    }
    catch {
        Write-ColorOutput "🔍 Weaviate: ✅ Stopped" $Colors.Success
    }
    
    # Check Docker
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "🐳 Docker Desktop: ⚠️ Still Running" $Colors.Warning
        } else {
            Write-ColorOutput "🐳 Docker Desktop: ✅ Stopped" $Colors.Success
        }
    }
    catch {
        Write-ColorOutput "🐳 Docker Desktop: ✅ Stopped" $Colors.Success
    }
}

function Show-Logs {
    Write-ColorOutput "`n📋 Final System Logs" $Colors.Header
    Write-ColorOutput "===================" $Colors.Header
    
    # Show Docker logs
    Write-ColorOutput "🐳 Weaviate Container Logs (last 10 lines):" $Colors.Info
    docker logs --tail 10 $DOCKER_CONTAINER_NAME 2>$null
    
    # Show API logs (if available)
    if (Test-Path "elysia_integration.log") {
        Write-ColorOutput "`n🌳 Elysia Integration Logs (last 10 lines):" $Colors.Info
        Get-Content "elysia_integration.log" -Tail 10
    }
}

# Main execution
Write-ColorOutput "🛑 KJV Sources - Stop Local System" $Colors.Header
Write-ColorOutput "=================================" $Colors.Header
Write-ColorOutput "Stopping all local services cleanly" $Colors.Info
Write-ColorOutput ""

# Step 1: Stop API
Stop-API

Start-Sleep -Seconds 2

# Step 2: Stop Weaviate
Stop-Weaviate

Start-Sleep -Seconds 2

# Step 3: Stop Docker Desktop (if requested)
if ($StopDocker) {
    Stop-DockerDesktop
}

# Step 4: Show final status
Show-SystemStatus

# Step 5: Show logs if requested
if ($ShowLogs) {
    Show-Logs
}

Write-ColorOutput "`n✅ Local system shutdown completed!" $Colors.Success

if (-not $ShowLogs) {
    Write-ColorOutput "`nPress any key to exit..." $Colors.Info
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}
