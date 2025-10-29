# NBCOT Test Files Pipeline Runner
# =================================
# This script runs the NBCOT pipeline to process occupational therapy documents
# and add them to the vector database for AI learning.

param(
    [switch]$InstallDependencies,
    [switch]$CheckQdrant,
    [switch]$RunPipeline,
    [switch]$All
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-QdrantConnection {
    Write-ColorOutput "Checking Qdrant connection..." $Blue
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:6333/collections" -Method GET -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "✓ Qdrant is running and accessible" $Green
            return $true
        } else {
            Write-ColorOutput "✗ Qdrant returned status code: $($response.StatusCode)" $Red
            return $false
        }
    }
    catch {
        Write-ColorOutput "✗ Qdrant is not running or not accessible" $Red
        Write-ColorOutput "Please start Qdrant first:" $Yellow
        Write-ColorOutput "  docker run -p 6333:6333 qdrant/qdrant" $Yellow
        return $false
    }
}

function Install-NBCOTDependencies {
    Write-ColorOutput "Installing NBCOT pipeline dependencies..." $Blue
    
    $dependencies = @(
        "PyPDF2",
        "sentence-transformers",
        "qdrant-client"
    )
    
    foreach ($dep in $dependencies) {
        Write-ColorOutput "Installing $dep..." $Yellow
        try {
            pip install $dep
            Write-ColorOutput "✓ $dep installed successfully" $Green
        }
        catch {
            Write-ColorOutput "✗ Failed to install $dep" $Red
            return $false
        }
    }
    
    Write-ColorOutput "✓ All dependencies installed successfully" $Green
    return $true
}

function Test-NBCOTFiles {
    Write-ColorOutput "Checking NBCOT Test files..." $Blue
    
    $nbcotFolder = "NBCOT Test files"
    if (-not (Test-Path $nbcotFolder)) {
        Write-ColorOutput "✗ NBCOT Test files folder not found: $nbcotFolder" $Red
        return $false
    }
    
    $files = Get-ChildItem -Path $nbcotFolder -File
    if ($files.Count -eq 0) {
        Write-ColorOutput "✗ No files found in NBCOT Test files folder" $Red
        return $false
    }
    
    Write-ColorOutput "✓ Found $($files.Count) files in NBCOT Test files folder:" $Green
    foreach ($file in $files) {
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        Write-ColorOutput "  - $($file.Name) ($sizeMB MB)" $Yellow
    }
    
    return $true
}

function Run-NBCOTPipeline {
    Write-ColorOutput "Running NBCOT pipeline..." $Blue
    
    if (-not (Test-Path "nbcot_pipeline.py")) {
        Write-ColorOutput "✗ nbcot_pipeline.py not found" $Red
        return $false
    }
    
    try {
        Write-ColorOutput "Starting pipeline processing..." $Yellow
        python nbcot_pipeline.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ NBCOT pipeline completed successfully" $Green
            return $true
        } else {
            Write-ColorOutput "✗ NBCOT pipeline failed with exit code $LASTEXITCODE" $Red
            return $false
        }
    }
    catch {
        Write-ColorOutput "✗ Error running NBCOT pipeline: $($_.Exception.Message)" $Red
        return $false
    }
}

function Show-NBCOTStatus {
    Write-ColorOutput "NBCOT Pipeline Status" $Blue
    Write-ColorOutput "====================" $Blue
    
    # Check Qdrant
    $qdrantOk = Test-QdrantConnection
    
    # Check files
    $filesOk = Test-NBCOTFiles
    
    # Check dependencies
    Write-ColorOutput "Checking Python dependencies..." $Blue
    try {
        python -c "import PyPDF2, sentence_transformers, qdrant_client; print('✓ All dependencies available')"
        $depsOk = $true
    }
    catch {
        Write-ColorOutput "✗ Missing dependencies" $Red
        $depsOk = $false
    }
    
    # Check output folder
    $outputFolder = "nbcot_output"
    if (Test-Path $outputFolder) {
        $outputFiles = Get-ChildItem -Path $outputFolder -File | Measure-Object
        Write-ColorOutput "✓ Output folder exists with $($outputFiles.Count) files" $Green
    } else {
        Write-ColorOutput "ℹ Output folder does not exist yet" $Yellow
    }
    
    return ($qdrantOk -and $filesOk -and $depsOk)
}

# Main execution
Write-ColorOutput "NBCOT Test Files Pipeline Runner" $Blue
Write-ColorOutput "=================================" $Blue

if ($InstallDependencies -or $All) {
    Install-NBCOTDependencies
}

if ($CheckQdrant -or $All) {
    Test-QdrantConnection
}

if ($RunPipeline -or $All) {
    $status = Show-NBCOTStatus
    if ($status) {
        Run-NBCOTPipeline
    } else {
        Write-ColorOutput "Cannot run pipeline - please fix the issues above" $Red
    }
}

if (-not ($InstallDependencies -or $CheckQdrant -or $RunPipeline -or $All)) {
    Write-ColorOutput "Usage:" $Yellow
    Write-ColorOutput "  .\run_nbcot_pipeline.ps1 -InstallDependencies" $Yellow
    Write-ColorOutput "  .\run_nbcot_pipeline.ps1 -CheckQdrant" $Yellow
    Write-ColorOutput "  .\run_nbcot_pipeline.ps1 -RunPipeline" $Yellow
    Write-ColorOutput "  .\run_nbcot_pipeline.ps1 -All" $Yellow
    Write-ColorOutput ""
    Write-ColorOutput "Or run without parameters to see status" $Yellow
    
    Show-NBCOTStatus
}
