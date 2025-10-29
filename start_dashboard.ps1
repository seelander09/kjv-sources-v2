<#!
.SYNOPSIS
    Bring up the KJV dashboard (FastAPI backend + Vite frontend) with one command.
.DESCRIPTION
    Ensures required directories exist, checks for occupied ports, starts both services with
    retries and readiness checks, and records process metadata so stop_dashboard.ps1
    can shut everything down cleanly later.
#>
param(
    [int]$ApiPort = 8000,
    [int]$UiPort = 5173,
    [int]$MaxRetries = 2,
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$OpenBrowser
)

$ErrorActionPreference = 'Stop'

function Write-Status {
    param(
        [string]$Message,
        [ValidateSet('INFO','OK','WARN','ERROR')]
        [string]$Level = 'INFO'
    )
    $color = switch ($Level) {
        'OK' { 'Green' }
        'WARN' { 'Yellow' }
        'ERROR' { 'Red' }
        default { 'Cyan' }
    }
    $timestamp = Get-Date -Format 'HH:mm:ss'
    Write-Host "[$timestamp][$Level] $Message" -ForegroundColor $color
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Get-StateFile {
    param([string]$Root)
    $stateDir = Join-Path $Root 'temp'
    Ensure-Directory $stateDir
    return Join-Path $stateDir 'dashboard_state.json'
}

function Load-State {
    param([string]$StateFile)
    if (Test-Path $StateFile) {
        try {
            return Get-Content -Raw -Path $StateFile | ConvertFrom-Json
        }
        catch {
            Write-Status "State file at $StateFile is corrupt; ignoring" 'WARN'
        }
    }
    return [pscustomobject]@{}
}

function Save-State {
    param(
        [string]$StateFile,
        [hashtable]$State
    )
    $json = $State | ConvertTo-Json -Depth 4
    Set-Content -Path $StateFile -Value $json -Encoding UTF8
}

function Ensure-PortAvailable {
    param(
        [int]$Port,
        [string]$ServiceName,
        [int]$ExpectedPid
    )
    $listeners = Get-NetTCPConnection -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -eq $Port -and $_.State -eq 'Listen' }
    if ($listeners) {
        $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
        $sameProcess = $ExpectedPid -and ($pids -contains $ExpectedPid)
        if ($sameProcess) {
            Write-Status "$ServiceName appears to be running already (PID $ExpectedPid); stopping stale process" 'WARN'
            Stop-Process -Id $ExpectedPid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
        else {
            throw "Port $Port is already in use by process(es): $($pids -join ', '). Stop those before continuing."
        }
    }
}

function Wait-ForHttp {
    param(
        [string]$Url,
        [string]$ServiceName,
        [int]$Attempts = 20,
        [int]$DelaySeconds = 2
    )
    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    Write-Status "$ServiceName did not become ready after $Attempts attempts" 'ERROR'
    return $false
}

function Start-Backend {
    param(
        [string]$Root,
        [int]$Port,
        [int]$MaxRetries,
        [int]$PreviousPid
    )
    $logsDir = Join-Path $Root 'logs'
    Ensure-Directory $logsDir
    $attempt = 0
    while ($attempt -lt $MaxRetries) {
        $attempt++
        Ensure-PortAvailable -Port $Port -ServiceName 'FastAPI backend' -ExpectedPid $PreviousPid
        $logFile = Join-Path $logsDir ("dashboard-backend-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
        $stderrFile = [System.IO.Path]::ChangeExtension($logFile, '.stderr.log')
        Write-Status "Starting FastAPI backend (attempt $attempt/$MaxRetries)..." 'INFO'
        $arguments = "-m", "uvicorn", "kjv_sources.api:app", "--host", "0.0.0.0", "--port", $Port, "--reload"
        $proc = Start-Process -FilePath "python" -ArgumentList $arguments -WorkingDirectory (Join-Path $Root 'src') -PassThru -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $stderrFile
        Start-Sleep -Seconds 1
        if (Wait-ForHttp -Url "http://localhost:$Port/openapi.json" -ServiceName 'FastAPI backend') {
            Write-Status "FastAPI backend ready on port $Port (PID $($proc.Id))" 'OK'
            return @{ pid = $proc.Id; log = $logFile; errLog = $stderrFile }
        }
        Write-Status "Backend failed readiness check; tailing log from $logFile" 'WARN'
        if (Test-Path $logFile) {
            Write-Host '    [stdout]'
            Get-Content -Path $logFile -Tail 30 | ForEach-Object { Write-Host "    $_" }
        }
        if (Test-Path $stderrFile) {
            Write-Host '    [stderr]'
            Get-Content -Path $stderrFile -Tail 30 | ForEach-Object { Write-Host "    $_" }
        }
        if ($proc -and !$proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
    throw "FastAPI backend failed to start after $MaxRetries attempts"
}

function Ensure-NpmDependencies {
    param([string]$FrontendDir)
    $nodeModules = Join-Path $FrontendDir 'node_modules'
    if (-not (Test-Path $nodeModules)) {
        Write-Status "node_modules missing; running npm install (this may take a minute)" 'WARN'
        $install = Start-Process -FilePath 'npm.cmd' -ArgumentList 'install' -WorkingDirectory $FrontendDir -NoNewWindow -Wait -PassThru
        if ($install.ExitCode -ne 0) {
            throw "npm install failed with exit code $($install.ExitCode)"
        }
    }
}

function Start-Frontend {
    param(
        [string]$Root,
        [int]$Port,
        [int]$MaxRetries,
        [int]$PreviousPid
    )
    $frontendDir = Join-Path $Root 'frontend'
    Ensure-NpmDependencies -FrontendDir $frontendDir
    $logsDir = Join-Path $Root 'logs'
    Ensure-Directory $logsDir
    $attempt = 0
    while ($attempt -lt $MaxRetries) {
        $attempt++
        Ensure-PortAvailable -Port $Port -ServiceName 'Vite dev server' -ExpectedPid $PreviousPid
        $logFile = Join-Path $logsDir ("dashboard-frontend-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
        $stderrFile = [System.IO.Path]::ChangeExtension($logFile, '.stderr.log')
        Write-Status "Starting Vite dev server (attempt $attempt/$MaxRetries)..." 'INFO'
        $args = @('run','dev','--','--host','127.0.0.1','--port',$Port,'--strictPort')
        $proc = Start-Process -FilePath 'npm.cmd' -ArgumentList $args -WorkingDirectory $frontendDir -PassThru -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $stderrFile
        Start-Sleep -Seconds 2
        if (Wait-ForHttp -Url "http://localhost:$Port" -ServiceName 'Vite dev server') {
            Write-Status "Vite dev server ready on port $Port (PID $($proc.Id))" 'OK'
            return @{ pid = $proc.Id; log = $logFile; errLog = $stderrFile }
        }
        Write-Status "Frontend failed readiness check; tailing log from $logFile" 'WARN'
        if (Test-Path $logFile) {
            Write-Host '    [stdout]'
            Get-Content -Path $logFile -Tail 30 | ForEach-Object { Write-Host "    $_" }
        }
        if (Test-Path $stderrFile) {
            Write-Host '    [stderr]'
            Get-Content -Path $stderrFile -Tail 30 | ForEach-Object { Write-Host "    $_" }
        }
        if ($proc -and !$proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
    throw "Vite dev server failed to start after $MaxRetries attempts"
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$stateFile = Get-StateFile -Root $root
$existingState = Load-State -StateFile $stateFile
$updatedState = @{}

try {
    if (-not $SkipBackend) {
        $previousPid = ($existingState.api.pid) 2>$null
        $backendMeta = Start-Backend -Root $root -Port $ApiPort -MaxRetries $MaxRetries -PreviousPid $previousPid
        $updatedState['api'] = @{
            pid = $backendMeta.pid
            port = $ApiPort
            log = $backendMeta.log
            errLog = $backendMeta.errLog
            started = (Get-Date).ToString('o')
        }
    }
    elseif ($existingState.api) {
        $updatedState['api'] = $existingState.api
    }

    if (-not $SkipFrontend) {
        $previousFrontPid = ($existingState.frontend.pid) 2>$null
        $frontendMeta = Start-Frontend -Root $root -Port $UiPort -MaxRetries $MaxRetries -PreviousPid $previousFrontPid
        $updatedState['frontend'] = @{
            pid = $frontendMeta.pid
            port = $UiPort
            log = $frontendMeta.log
            errLog = $frontendMeta.errLog
            started = (Get-Date).ToString('o')
        }
    }
    elseif ($existingState.frontend) {
        $updatedState['frontend'] = $existingState.frontend
    }

    if ($updatedState.Count -gt 0) {
        Save-State -StateFile $stateFile -State $updatedState
        Write-Status "State saved to $stateFile" 'INFO'
    }

    if ($OpenBrowser -and -not $SkipFrontend) {
        Start-Process "http://localhost:$UiPort" | Out-Null
    }

    Write-Status "Dashboard startup complete." 'OK'
    if ($updatedState.api) {
        Write-Status "Backend: http://localhost:$ApiPort (PID $($updatedState.api.pid))" 'INFO'
    }
    if ($updatedState.frontend) {
        Write-Status "Frontend: http://localhost:$UiPort (PID $($updatedState.frontend.pid))" 'INFO'
    }
}
catch {
    Write-Status $_.Exception.Message 'ERROR'
    throw
}

