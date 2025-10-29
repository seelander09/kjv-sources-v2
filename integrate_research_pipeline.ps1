# Integrate Research Pipeline with Existing KJV Sources Project
# ===========================================================
# This PowerShell script integrates the new research validation pipeline
# with the existing parse_wikitext.py and other components.

param(
    [string]$Book = "",
    [string]$Action = "integrate",
    [switch]$Validate,
    [switch]$Research,
    [switch]$Enhanced,
    [switch]$FullPipeline
)

# Configuration
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ProjectRoot "parse_wikitext.py"
$ResearchTool = Join-Path $ProjectRoot "duckduckgo_research_tool.py"
$ValidationPipeline = Join-Path $ProjectRoot "research_validation_pipeline.py"
$EnhancedLightRAG = Join-Path $ProjectRoot "enhanced_lightrag_research.py"
$OutputDir = Join-Path $ProjectRoot "output"
$ResearchOutputDir = Join-Path $ProjectRoot "research_output"
$LogFile = Join-Path $ProjectRoot "logs\integration.log"

# Ensure directories exist
@($OutputDir, $ResearchOutputDir, (Join-Path $ProjectRoot "logs")) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

# Function to run the original parsing pipeline
function Invoke-OriginalParsing {
    param([string]$BookName = "")
    
    try {
        Write-Log "Running original parsing pipeline for: $BookName"
        
        if ($BookName) {
            $Command = "python `"$PythonScript`" $BookName"
        } else {
            $Command = "python `"$PythonScript`" pipeline"
        }
        
        Write-Log "Executing: $Command"
        $Result = Invoke-Expression $Command 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Original parsing completed successfully"
            return $true
        } else {
            Write-Log "Original parsing failed with exit code: $LASTEXITCODE" "ERROR"
            Write-Log "Error output: $Result" "ERROR"
            return $false
        }
        
    } catch {
        Write-Log "Error running original parsing: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Function to run research validation
function Invoke-ResearchValidation {
    param([string]$BookName = "")
    
    try {
        Write-Log "Running research validation for: $BookName"
        
        $Command = "python `"$ValidationPipeline`""
        if ($BookName) {
            $Command += " --book `"$BookName`""
        }
        
        Write-Log "Executing: $Command"
        $Result = Invoke-Expression $Command 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Research validation completed successfully"
            return $true
        } else {
            Write-Log "Research validation failed with exit code: $LASTEXITCODE" "ERROR"
            Write-Log "Error output: $Result" "ERROR"
            return $false
        }
        
    } catch {
        Write-Log "Error running research validation: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Function to run enhanced LightRAG research
function Invoke-EnhancedLightRAG {
    param([string]$BookName = "")
    
    try {
        Write-Log "Running enhanced LightRAG research for: $BookName"
        
        $Command = "python `"$EnhancedLightRAG`""
        if ($BookName) {
            $Command += " --book `"$BookName`""
        }
        
        Write-Log "Executing: $Command"
        $Result = Invoke-Expression $Command 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Enhanced LightRAG research completed successfully"
            return $true
        } else {
            Write-Log "Enhanced LightRAG research failed with exit code: $LASTEXITCODE" "ERROR"
            Write-Log "Error output: $Result" "ERROR"
            return $false
        }
        
    } catch {
        Write-Log "Error running enhanced LightRAG research: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Function to run comprehensive research
function Invoke-ComprehensiveResearch {
    param([string]$BookName = "")
    
    try {
        Write-Log "Running comprehensive research for: $BookName"
        
        $Command = "python `"$ResearchTool`""
        if ($BookName) {
            $Command += " --book `"$BookName`""
        }
        
        Write-Log "Executing: $Command"
        $Result = Invoke-Expression $Command 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Comprehensive research completed successfully"
            return $true
        } else {
            Write-Log "Comprehensive research failed with exit code: $LASTEXITCODE" "ERROR"
            Write-Log "Error output: $Result" "ERROR"
            return $false
        }
        
    } catch {
        Write-Log "Error running comprehensive research: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Function to integrate all components
function Start-FullIntegration {
    param([string]$BookName = "")
    
    Write-Log "Starting full integration pipeline for: $BookName"
    
    $Steps = @(
        @{Name="Original Parsing"; Function="Invoke-OriginalParsing"; Required=$true},
        @{Name="Research Validation"; Function="Invoke-ResearchValidation"; Required=$false},
        @{Name="Enhanced LightRAG"; Function="Invoke-EnhancedLightRAG"; Required=$false},
        @{Name="Comprehensive Research"; Function="Invoke-ComprehensiveResearch"; Required=$false}
    )
    
    $Results = @{}
    $SuccessCount = 0
    
    foreach ($Step in $Steps) {
        Write-Log "Executing step: $($Step.Name)"
        
        $StepResult = & $Step.Function -BookName $BookName
        $Results[$Step.Name] = $StepResult
        
        if ($StepResult) {
            $SuccessCount++
            Write-Log "Step '$($Step.Name)' completed successfully"
        } else {
            Write-Log "Step '$($Step.Name)' failed" "ERROR"
            
            if ($Step.Required) {
                Write-Log "Required step failed, stopping pipeline" "ERROR"
                break
            }
        }
    }
    
    Write-Log "Integration pipeline completed: $SuccessCount/$($Steps.Count) steps successful"
    return $Results
}

# Function to create integration summary
function New-IntegrationSummary {
    param([hashtable]$Results, [string]$BookName = "")
    
    $Summary = @{
        Book = $BookName
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Results = $Results
        SuccessCount = ($Results.Values | Where-Object { $_ -eq $true }).Count
        TotalSteps = $Results.Count
        Status = if (($Results.Values | Where-Object { $_ -eq $true }).Count -eq $Results.Count) { "Success" } else { "Partial" }
    }
    
    $SummaryFile = Join-Path $ResearchOutputDir "integration_summary_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $Summary | ConvertTo-Json -Depth 3 | Out-File -FilePath $SummaryFile -Encoding UTF8
    
    Write-Log "Integration summary saved to: $SummaryFile"
    return $Summary
}

# Function to display integration results
function Show-IntegrationResults {
    param([hashtable]$Results)
    
    Write-Host "`n" + "="*80
    Write-Host "INTEGRATION RESULTS"
    Write-Host "="*80
    
    foreach ($Step in $Results.Keys) {
        $Status = if ($Results[$Step]) { "✓ SUCCESS" } else { "✗ FAILED" }
        $Color = if ($Results[$Step]) { "Green" } else { "Red" }
        Write-Host "$Step`: " -NoNewline
        Write-Host $Status -ForegroundColor $Color
    }
    
    $SuccessCount = ($Results.Values | Where-Object { $_ -eq $true }).Count
    $TotalSteps = $Results.Count
    $SuccessRate = [math]::Round(($SuccessCount / $TotalSteps) * 100, 1)
    
    Write-Host "`nOverall Success Rate: $SuccessCount/$TotalSteps ($SuccessRate%)"
    
    if ($SuccessRate -eq 100) {
        Write-Host "Integration Status: " -NoNewline
        Write-Host "COMPLETE SUCCESS" -ForegroundColor Green
    } elseif ($SuccessRate -ge 75) {
        Write-Host "Integration Status: " -NoNewline
        Write-Host "MOSTLY SUCCESSFUL" -ForegroundColor Yellow
    } else {
        Write-Host "Integration Status: " -NoNewline
        Write-Host "NEEDS ATTENTION" -ForegroundColor Red
    }
    
    Write-Host "="*80
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Log "Checking prerequisites..."
    
    $Prerequisites = @(
        @{Name="Python"; Command="python --version"; Required=$true},
        @{Name="DuckDuckGo Research Tool"; Path=$ResearchTool; Required=$true},
        @{Name="Validation Pipeline"; Path=$ValidationPipeline; Required=$true},
        @{Name="Enhanced LightRAG"; Path=$EnhancedLightRAG; Required=$false},
        @{Name="Original Parser"; Path=$PythonScript; Required=$true}
    )
    
    $AllGood = $true
    
    foreach ($Prereq in $Prerequisites) {
        if ($Prereq.Command) {
            try {
                $Result = Invoke-Expression $Prereq.Command 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "✓ $($Prereq.Name): Available"
                } else {
                    Write-Log "✗ $($Prereq.Name): Not available" "ERROR"
                    if ($Prereq.Required) { $AllGood = $false }
                }
            } catch {
                Write-Log "✗ $($Prereq.Name): Error checking" "ERROR"
                if ($Prereq.Required) { $AllGood = $false }
            }
        } elseif ($Prereq.Path) {
            if (Test-Path $Prereq.Path) {
                Write-Log "✓ $($Prereq.Name): Available"
            } else {
                Write-Log "✗ $($Prereq.Name): Not found at $($Prereq.Path)" "ERROR"
                if ($Prereq.Required) { $AllGood = $false }
            }
        }
    }
    
    return $AllGood
}

# Main execution logic
Write-Log "Starting research pipeline integration"
Write-Log "Parameters: Book=$Book, Action=$Action, Validate=$Validate, Research=$Research, Enhanced=$Enhanced, FullPipeline=$FullPipeline"

try {
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Log "Prerequisites check failed. Please ensure all required components are available." "ERROR"
        exit 1
    }
    
    # Execute based on action
    switch ($Action.ToLower()) {
        "integrate" {
            if ($FullPipeline) {
                $Results = Start-FullIntegration -BookName $Book
                $Summary = New-IntegrationSummary -Results $Results -BookName $Book
                Show-IntegrationResults -Results $Results
            } else {
                # Run individual components based on flags
                if ($Validate) {
                    $Result = Invoke-ResearchValidation -BookName $Book
                    Write-Log "Research validation result: $Result"
                }
                
                if ($Research) {
                    $Result = Invoke-ComprehensiveResearch -BookName $Book
                    Write-Log "Comprehensive research result: $Result"
                }
                
                if ($Enhanced) {
                    $Result = Invoke-EnhancedLightRAG -BookName $Book
                    Write-Log "Enhanced LightRAG result: $Result"
                }
                
                if (-not $Validate -and -not $Research -and -not $Enhanced) {
                    Write-Log "No specific actions specified. Use -Validate, -Research, -Enhanced, or -FullPipeline" "WARNING"
                }
            }
        }
        
        "parse" {
            $Result = Invoke-OriginalParsing -BookName $Book
            if ($Result) {
                Write-Log "Parsing completed successfully"
            } else {
                Write-Log "Parsing failed" "ERROR"
                exit 1
            }
        }
        
        "validate" {
            $Result = Invoke-ResearchValidation -BookName $Book
            if ($Result) {
                Write-Log "Validation completed successfully"
            } else {
                Write-Log "Validation failed" "ERROR"
                exit 1
            }
        }
        
        "research" {
            $Result = Invoke-ComprehensiveResearch -BookName $Book
            if ($Result) {
                Write-Log "Research completed successfully"
            } else {
                Write-Log "Research failed" "ERROR"
                exit 1
            }
        }
        
        "enhanced" {
            $Result = Invoke-EnhancedLightRAG -BookName $Book
            if ($Result) {
                Write-Log "Enhanced LightRAG completed successfully"
            } else {
                Write-Log "Enhanced LightRAG failed" "ERROR"
                exit 1
            }
        }
        
        default {
            Write-Log "Unknown action: $Action" "ERROR"
            Write-Log "Valid actions: integrate, parse, validate, research, enhanced" "ERROR"
            exit 1
        }
    }
    
    Write-Log "Integration script completed successfully"
    
} catch {
    Write-Log "Script execution failed: $($_.Exception.Message)" "ERROR"
    exit 1
}

# Display usage information
function Show-Usage {
    Write-Host @"
Research Pipeline Integration Script
===================================

Usage: .\integrate_research_pipeline.ps1 [Parameters]

Parameters:
  -Book <string>        Biblical book name (e.g., Genesis, Exodus)
  -Action <string>      Action to perform (integrate, parse, validate, research, enhanced)
  -Validate            Run research validation
  -Research            Run comprehensive research
  -Enhanced            Run enhanced LightRAG research
  -FullPipeline        Run complete integration pipeline

Examples:
  .\integrate_research_pipeline.ps1 -Action integrate -FullPipeline -Book Genesis
  .\integrate_research_pipeline.ps1 -Action parse -Book Exodus
  .\integrate_research_pipeline.ps1 -Action validate -Book Genesis
  .\integrate_research_pipeline.ps1 -Action research -Book Exodus
  .\integrate_research_pipeline.ps1 -Action enhanced -Book Genesis
"@
}

# Show usage if no parameters provided
if ($args.Count -eq 0 -and -not $Book -and -not $Action) {
    Show-Usage
}
