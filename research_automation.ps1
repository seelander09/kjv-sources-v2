# Research Automation Script for KJV Sources Project
# =================================================
# This PowerShell script automates scholarly research using the DuckDuckGo MCP server
# integration for biblical text analysis and documentary hypothesis research.

param(
    [string]$Book = "",
    [string]$Source = "",
    [string]$Action = "research",
    [int]$MaxResults = 10,
    [switch]$Validate,
    [switch]$Update,
    [switch]$Report
)

# Configuration
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ProjectRoot "duckduckgo_research_tool.py"
$OutputDir = Join-Path $ProjectRoot "research_output"
$LogFile = Join-Path $ProjectRoot "logs\research_automation.log"

# Ensure output directory exists
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Ensure logs directory exists
$LogsDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

# Function to run Python research tool
function Invoke-ResearchTool {
    param(
        [string]$Command,
        [hashtable]$Parameters = @{}
    )
    
    try {
        Write-Log "Executing research command: $Command"
        
        # Build Python command
        $PythonCmd = "python `"$PythonScript`""
        
        # Add parameters
        foreach ($key in $Parameters.Keys) {
            $PythonCmd += " --$key `"$($Parameters[$key])`""
        }
        
        Write-Log "Python command: $PythonCmd"
        
        # Execute command
        $Result = Invoke-Expression $PythonCmd 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Research command completed successfully"
            return $Result
        } else {
            Write-Log "Research command failed with exit code: $LASTEXITCODE" "ERROR"
            Write-Log "Error output: $Result" "ERROR"
            return $null
        }
        
    } catch {
        Write-Log "Error executing research tool: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

# Function to conduct comprehensive research
function Start-ComprehensiveResearch {
    param([string]$BookName = "")
    
    Write-Log "Starting comprehensive research for: $BookName"
    
    $Parameters = @{
        "action" = "comprehensive"
        "max_results" = $MaxResults
    }
    
    if ($BookName) {
        $Parameters["book"] = $BookName
    }
    
    $Result = Invoke-ResearchTool -Command "research" -Parameters $Parameters
    
    if ($Result) {
        Write-Log "Comprehensive research completed successfully"
        
        # Generate report if requested
        if ($Report) {
            Start-ReportGeneration -BookName $BookName
        }
        
        return $Result
    } else {
        Write-Log "Comprehensive research failed" "ERROR"
        return $null
    }
}

# Function to validate source attributions
function Start-SourceValidation {
    param([string]$SourceId, [string]$BookName = "")
    
    Write-Log "Starting source validation for: $SourceId"
    
    $Parameters = @{
        "action" = "validate"
        "source" = $SourceId
        "max_results" = $MaxResults
    }
    
    if ($BookName) {
        $Parameters["book"] = $BookName
    }
    
    $Result = Invoke-ResearchTool -Command "validate" -Parameters $Parameters
    
    if ($Result) {
        Write-Log "Source validation completed successfully"
        return $Result
    } else {
        Write-Log "Source validation failed" "ERROR"
        return $null
    }
}

# Function to update existing research
function Start-ResearchUpdate {
    param([string]$BookName = "")
    
    Write-Log "Starting research update for: $BookName"
    
    $Parameters = @{
        "action" = "update"
        "max_results" = $MaxResults
    }
    
    if ($BookName) {
        $Parameters["book"] = $BookName
    }
    
    $Result = Invoke-ResearchTool -Command "update" -Parameters $Parameters
    
    if ($Result) {
        Write-Log "Research update completed successfully"
        return $Result
    } else {
        Write-Log "Research update failed" "ERROR"
        return $null
    }
}

# Function to generate research reports
function Start-ReportGeneration {
    param([string]$BookName = "")
    
    Write-Log "Generating research report for: $BookName"
    
    $Parameters = @{
        "action" = "report"
    }
    
    if ($BookName) {
        $Parameters["book"] = $BookName
    }
    
    $Result = Invoke-ResearchTool -Command "report" -Parameters $Parameters
    
    if ($Result) {
        Write-Log "Report generation completed successfully"
        return $Result
    } else {
        Write-Log "Report generation failed" "ERROR"
        return $null
    }
}

# Function to search for specific scholarly topics
function Start-ScholarlySearch {
    param([string]$Query, [string]$BookName = "")
    
    Write-Log "Starting scholarly search for: $Query"
    
    $Parameters = @{
        "action" = "search"
        "query" = $Query
        "max_results" = $MaxResults
    }
    
    if ($BookName) {
        $Parameters["book"] = $BookName
    }
    
    $Result = Invoke-ResearchTool -Command "search" -Parameters $Parameters
    
    if ($Result) {
        Write-Log "Scholarly search completed successfully"
        return $Result
    } else {
        Write-Log "Scholarly search failed" "ERROR"
        return $null
    }
}

# Function to validate all sources for a book
function Start-AllSourceValidation {
    param([string]$BookName)
    
    Write-Log "Starting validation for all sources in: $BookName"
    
    $Sources = @("J", "E", "P", "D", "R")
    $ValidationResults = @{}
    
    foreach ($SourceId in $Sources) {
        Write-Log "Validating $SourceId source for $BookName"
        $Result = Start-SourceValidation -SourceId $SourceId -BookName $BookName
        
        if ($Result) {
            $ValidationResults[$SourceId] = $Result
            Write-Log "Validation completed for $SourceId source"
        } else {
            Write-Log "Validation failed for $SourceId source" "ERROR"
        }
    }
    
    return $ValidationResults
}

# Function to display research summary
function Show-ResearchSummary {
    param([hashtable]$Results)
    
    Write-Host "`n" + "="*80
    Write-Host "RESEARCH SUMMARY"
    Write-Host "="*80
    
    if ($Results.Count -gt 0) {
        foreach ($Key in $Results.Keys) {
            Write-Host "`n$Key Source:"
            Write-Host "-" * 40
            
            if ($Results[$Key]) {
                Write-Host "  Status: Completed"
                Write-Host "  Results: Available"
            } else {
                Write-Host "  Status: Failed"
                Write-Host "  Results: None"
            }
        }
    } else {
        Write-Host "No research results available"
    }
    
    Write-Host "`n" + "="*80
}

# Main execution logic
Write-Log "Starting research automation script"
Write-Log "Parameters: Book=$Book, Source=$Source, Action=$Action, MaxResults=$MaxResults"

try {
    switch ($Action.ToLower()) {
        "research" {
            if ($Book) {
                $Result = Start-ComprehensiveResearch -BookName $Book
            } else {
                $Result = Start-ComprehensiveResearch
            }
            
            if ($Result) {
                Write-Log "Research completed successfully"
            } else {
                Write-Log "Research failed" "ERROR"
                exit 1
            }
        }
        
        "validate" {
            if ($Source) {
                $Result = Start-SourceValidation -SourceId $Source -BookName $Book
            } elseif ($Book) {
                $Result = Start-AllSourceValidation -BookName $Book
                Show-ResearchSummary -Results $Result
            } else {
                Write-Log "Source validation requires either -Source or -Book parameter" "ERROR"
                exit 1
            }
        }
        
        "update" {
            if ($Book) {
                $Result = Start-ResearchUpdate -BookName $Book
            } else {
                $Result = Start-ResearchUpdate
            }
            
            if ($Result) {
                Write-Log "Research update completed successfully"
            } else {
                Write-Log "Research update failed" "ERROR"
                exit 1
            }
        }
        
        "report" {
            $Result = Start-ReportGeneration -BookName $Book
            if ($Result) {
                Write-Log "Report generation completed successfully"
            } else {
                Write-Log "Report generation failed" "ERROR"
                exit 1
            }
        }
        
        "search" {
            if (-not $Source) {
                Write-Log "Search action requires -Source parameter for query" "ERROR"
                exit 1
            }
            
            $Result = Start-ScholarlySearch -Query $Source -BookName $Book
            if ($Result) {
                Write-Log "Scholarly search completed successfully"
            } else {
                Write-Log "Scholarly search failed" "ERROR"
                exit 1
            }
        }
        
        default {
            Write-Log "Unknown action: $Action" "ERROR"
            Write-Log "Valid actions: research, validate, update, report, search" "ERROR"
            exit 1
        }
    }
    
    Write-Log "Research automation script completed successfully"
    
} catch {
    Write-Log "Script execution failed: $($_.Exception.Message)" "ERROR"
    exit 1
}

# Display usage information
function Show-Usage {
    Write-Host @"
Research Automation Script for KJV Sources Project
=================================================

Usage: .\research_automation.ps1 [Parameters]

Parameters:
  -Book <string>      Biblical book name (e.g., Genesis, Exodus)
  -Source <string>    Source identifier (J, E, P, D, R) or search query
  -Action <string>    Action to perform (research, validate, update, report, search)
  -MaxResults <int>   Maximum number of results (default: 10)
  -Validate          Validate source attributions
  -Update            Update existing research
  -Report            Generate research report

Examples:
  .\research_automation.ps1 -Action research -Book Genesis
  .\research_automation.ps1 -Action validate -Source J -Book Genesis
  .\research_automation.ps1 -Action search -Source "documentary hypothesis"
  .\research_automation.ps1 -Action update -Book Exodus -Report
"@
}

# Show usage if no parameters provided
if ($args.Count -eq 0 -and -not $Book -and -not $Source -and -not $Action) {
    Show-Usage
}
