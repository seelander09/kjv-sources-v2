<#!
.SYNOPSIS
    Stop the KJV dashboard services launched by start_dashboard.ps1.
.DESCRIPTION
    Reads the state file to discover running PIDs, attempts graceful shutdown with
    retries, surfaces log pointers, and cleans up state when complete.
#>
param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend
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

function Get-StateFile {
    param([string]$Root)
    return Join-Path (Join-Path $Root 'temp') 'dashboard_state.json'
}

function Load-State {
    param([string]$StateFile)
    if (-not (Test-Path $StateFile)) {
        Write-Status "No dashboard state file found at $StateFile." 'WARN'
        return $null
    }
    try {
        return Get-Content -Raw -Path $StateFile | ConvertFrom-Json
    }
    catch {
        Write-Status "Failed to parse state file; manual cleanup may be required." 'ERROR'
        throw
    }
}

function Stop-ServiceProcess {
    param(
        [string]$Name,
        [pscustomobject]$Entry
    )
    if (-not $Entry) {
        Write-Status "No saved state for $Name." 'WARN'
        return $false
    }
    $pid = $Entry.pid
    if (-not $pid) {
        Write-Status "$Name entry missing PID information." 'WARN'
        return $false
    }
    try {
        $process = Get-Process -Id $pid -ErrorAction Stop
    }
    catch {
        Write-Status "$Name process (PID $pid) is not running." 'WARN'
        return $true
    }

    Write-Status "Stopping $Name (PID $pid)..." 'INFO'
    $exited = $false
    try {
        Stop-Process -Id $pid -ErrorAction Stop
        try {
            Wait-Process -Id $pid -Timeout 5 -ErrorAction Stop
            $exited = $true
        }
        catch {
            $exited = $false
        }
        if (-not $exited) {
            Write-Status "$Name did not exit within timeout; forcing stop" 'WARN'
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    }
    catch {
        Write-Status "Error stopping $Name: $($_.Exception.Message)" 'ERROR'
        return $false
    }
    Write-Status "$Name stopped." 'OK'
    if ($Entry.log -and (Test-Path $Entry.log)) {
        Write-Status "$Name log: $($Entry.log)" 'INFO'
    }
    return $true
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$stateFile = Get-StateFile -Root $root
$state = Load-State -StateFile $stateFile
if (-not $state) { return }

$updated = @{}

if (-not $SkipBackend) {
    if (-not (Stop-ServiceProcess -Name 'FastAPI backend' -Entry $state.api)) {
        $updated['api'] = $state.api
    }
}
else {
    $updated['api'] = $state.api
}

if (-not $SkipFrontend) {
    if (-not (Stop-ServiceProcess -Name 'Vite dev server' -Entry $state.frontend)) {
        $updated['frontend'] = $state.frontend
    }
}
else {
    $updated['frontend'] = $state.frontend
}

if ($updated.Count -eq 0) {
    if (Test-Path $stateFile) {
        Remove-Item -Path $stateFile -ErrorAction SilentlyContinue
        Write-Status "Removed $stateFile" 'INFO'
    }
    Write-Status "Dashboard shutdown complete." 'OK'
}
else {
    Write-Status "Some services could not be stopped automatically; state retained at $stateFile" 'WARN'
    ($updated | ConvertTo-Json -Depth 4) | Set-Content -Path $stateFile -Encoding UTF8
}
