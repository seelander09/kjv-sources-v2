# Setup ICT Content Pipeline
# ==========================

$ict_project_path = "E:\Projects\ICTcontent"

Write-Host "Setting up ICT Content Pipeline in: $ict_project_path" -ForegroundColor Cyan

# Step 1: Navigate to ICT content folder
if (Test-Path $ict_project_path) {
    Set-Location $ict_project_path
    Write-Host "Working in: $ict_project_path" -ForegroundColor Green
} else {
    Write-Host "Error: ICT content folder not found at $ict_project_path" -ForegroundColor Red
    exit 1
}

# Step 2: Create directory structure
$directories = @(
    "data",
    "output", 
    "scripts",
    "config",
    "logs",
    "models",
    "training_data"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    Write-Host "Created directory: $dir" -ForegroundColor Green
}

# Step 3: Create pipeline configuration
$config = @{
    project_name = "ICT Content Pipeline"
    project_type = "AI Learning Pipeline"
    created_date = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    pipeline_version = "1.0.0"
    data_sources = @()
    output_formats = @("csv", "json", "jsonl", "parquet")
    ai_models = @("sentence-transformers", "transformers", "torch")
    features = @("text_processing", "embedding_generation", "training_data_prep")
}

$config | ConvertTo-Json -Depth 3 | Out-File "config\pipeline_config.json" -Encoding UTF8

# Step 4: Create main pipeline script
$pipeline_script = @"
#!/usr/bin/env python3
"""
ICT Content Pipeline
AI Learning Pipeline for ICT (Information and Communication Technology) content
"""

import os
import sys
import json
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)

class ICTContentPipeline:
    def __init__(self, config_path: str = "config/pipeline_config.json"):
        """Initialize the ICT content pipeline."""
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Setup paths
        self.base_path = Path.cwd()
        self.data_dir = self.base_path / "data"
        self.output_dir = self.base_path / "output"
        self.models_dir = self.base_path / "models"
        self.training_dir = self.base_path / "training_data"
        
        # Ensure directories exist
        for dir_path in [self.data_dir, self.output_dir, self.models_dir, self.training_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.logger.info(f"ICT Content Pipeline initialized in {self.base_path}")
    
    def load_data(self, data_path: Optional[str] = None) -> pd.DataFrame:
        """Load ICT content data from various sources."""
        self.logger.info("Loading ICT content data...")
        
        if data_path and os.path.exists(data_path):
            # Load from specific path
            if data_path.endswith('.csv'):
                data = pd.read_csv(data_path)
            elif data_path.endswith('.json'):
                data = pd.read_json(data_path)
            elif data_path.endswith('.jsonl'):
                data = pd.read_json(data_path, lines=True)
            else:
                raise ValueError(f"Unsupported file format: {data_path}")
        else:
            # Look for data files in data directory
            data_files = list(self.data_dir.glob("*.*"))
            if not data_files:
                self.logger.warning("No data files found in data directory")
                return pd.DataFrame()
            
            # Load first available file
            data_path = data_files[0]
            if data_path.suffix == '.csv':
                data = pd.read_csv(data_path)
            elif data_path.suffix == '.json':
                data = pd.read_json(data_path)
            elif data_path.suffix == '.jsonl':
                data = pd.read_json(data_path, lines=True)
            else:
                self.logger.warning(f"Skipping unsupported file: {data_path}")
                return pd.DataFrame()
        
        self.logger.info(f"Loaded {len(data)} records from {data_path}")
        return data
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess ICT content data for AI learning."""
        self.logger.info("Preprocessing ICT content data...")
        
        if data.empty:
            self.logger.warning("No data to preprocess")
            return data
        
        # Basic preprocessing steps
        processed_data = data.copy()
        
        # Remove duplicates
        initial_count = len(processed_data)
        processed_data = processed_data.drop_duplicates()
        if len(processed_data) < initial_count:
            self.logger.info(f"Removed {initial_count - len(processed_data)} duplicate records")
        
        # Handle missing values
        missing_counts = processed_data.isnull().sum()
        if missing_counts.sum() > 0:
            self.logger.info(f"Missing values found: {missing_counts.to_dict()}")
        
        # Basic text cleaning (if text columns exist)
        text_columns = processed_data.select_dtypes(include=['object']).columns
        for col in text_columns:
            if processed_data[col].dtype == 'object':
                # Remove extra whitespace
                processed_data[col] = processed_data[col].astype(str).str.strip()
                # Remove empty strings
                processed_data = processed_data[processed_data[col] != '']
        
        self.logger.info(f"Preprocessing completed. Final dataset: {len(processed_data)} records")
        return processed_data
    
    def generate_training_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate AI training data from ICT content."""
        self.logger.info("Generating AI training data...")
        
        if data.empty:
            self.logger.warning("No data to generate training data from")
            return {}
        
        training_data = {
            'metadata': {
                'generated_date': datetime.now().isoformat(),
                'source_records': len(data),
                'columns': list(data.columns),
                'data_types': data.dtypes.to_dict()
            },
            'samples': []
        }
        
        # Generate training samples
        for idx, row in data.iterrows():
            sample = {
                'id': f"ict_sample_{idx:06d}",
                'content': row.to_dict(),
                'features': {}
            }
            
            # Extract features based on data types
            for col, value in row.items():
                if pd.isna(value):
                    continue
                
                if isinstance(value, str):
                    # Text features
                    sample['features'][f"{col}_length"] = len(str(value))
                    sample['features'][f"{col}_word_count"] = len(str(value).split())
                elif isinstance(value, (int, float)):
                    # Numeric features
                    sample['features'][f"{col}_value"] = value
            
            training_data['samples'].append(sample)
        
        # Save training data
        training_file = self.training_dir / f"ict_training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(training_file, 'w') as f:
            json.dump(training_data, f, indent=2, default=str)
        
        self.logger.info(f"Generated {len(training_data['samples'])} training samples")
        self.logger.info(f"Training data saved to: {training_file}")
        
        return training_data
    
    def export_formats(self, data: pd.DataFrame) -> None:
        """Export data in multiple formats."""
        self.logger.info("Exporting data in multiple formats...")
        
        if data.empty:
            self.logger.warning("No data to export")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export to CSV
        csv_file = self.output_dir / f"ict_content_{timestamp}.csv"
        data.to_csv(csv_file, index=False)
        self.logger.info(f"Exported CSV: {csv_file}")
        
        # Export to JSON
        json_file = self.output_dir / f"ict_content_{timestamp}.json"
        data.to_json(json_file, orient='records', indent=2)
        self.logger.info(f"Exported JSON: {json_file}")
        
        # Export to JSONL (for LLM training)
        jsonl_file = self.output_dir / f"ict_content_{timestamp}.jsonl"
        with open(jsonl_file, 'w') as f:
            for _, row in data.iterrows():
                f.write(json.dumps(row.to_dict()) + '\n')
        self.logger.info(f"Exported JSONL: {jsonl_file}")
        
        # Export to Parquet (if available)
        try:
            parquet_file = self.output_dir / f"ict_content_{timestamp}.parquet"
            data.to_parquet(parquet_file, index=False)
            self.logger.info(f"Exported Parquet: {parquet_file}")
        except ImportError:
            self.logger.warning("Parquet export skipped (pyarrow not available)")
    
    def run_pipeline(self, data_path: Optional[str] = None) -> bool:
        """Run the complete ICT content pipeline."""
        self.logger.info("Starting ICT Content Pipeline...")
        
        try:
            # Load data
            data = self.load_data(data_path)
            
            # Preprocess data
            processed_data = self.preprocess_data(data)
            
            # Generate training data
            training_data = self.generate_training_data(processed_data)
            
            # Export in multiple formats
            self.export_formats(processed_data)
            
            self.logger.info("ICT Content Pipeline completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            return False

def main():
    """Main entry point for the ICT Content Pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ICT Content Pipeline')
    parser.add_argument('--data', type=str, help='Path to input data file')
    parser.add_argument('--config', type=str, default='config/pipeline_config.json', 
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Initialize and run pipeline
    pipeline = ICTContentPipeline(args.config)
    success = pipeline.run_pipeline(args.data)
    
    if success:
        print("✅ ICT Content Pipeline completed successfully!")
        sys.exit(0)
    else:
        print("❌ ICT Content Pipeline failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
"@

$pipeline_script | Out-File "scripts\ict_pipeline.py" -Encoding UTF8

# Step 5: Create requirements file
$requirements = @"
pandas>=1.3.0
numpy>=1.21.0
click>=8.0.0
rich>=10.0.0
pyarrow>=5.0.0
sentence-transformers>=2.0.0
transformers>=4.20.0
torch>=1.12.0
scikit-learn>=1.0.0
matplotlib>=3.5.0
seaborn>=0.11.0
"@

$requirements | Out-File "requirements.txt" -Encoding UTF8

# Step 6: Create PowerShell launcher
$launcher_script = @"
# Launch ICT Content Pipeline
# ===========================

Write-Host "Starting ICT Content Pipeline..." -ForegroundColor Cyan

# Check if Python is available
try {
    python --version | Out-Null
    Write-Host "Python found" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Run pipeline
Write-Host "Running pipeline..." -ForegroundColor Yellow
python scripts\ict_pipeline.py

Write-Host "Pipeline completed!" -ForegroundColor Green
"@

$launcher_script | Out-File "run_pipeline.ps1" -Encoding UTF8

# Step 7: Create batch launcher
$batch_launcher = @"
@echo off
echo Starting ICT Content Pipeline...
echo.

echo Checking Python...
python --version
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo.
echo Installing requirements...
pip install -r requirements.txt

echo.
echo Running pipeline...
python scripts\ict_pipeline.py

echo.
echo Pipeline completed!
pause
"@

$batch_launcher | Out-File "run_pipeline.bat" -Encoding UTF8

# Step 8: Create README
$readme = @"
# ICT Content Pipeline

AI Learning Pipeline for ICT (Information and Communication Technology) content.

## Overview

This pipeline is designed to process ICT content data and prepare it for AI/ML training. It includes:

- Data loading from multiple formats (CSV, JSON, JSONL)
- Data preprocessing and cleaning
- Feature extraction
- Training data generation
- Multiple export formats (CSV, JSON, JSONL, Parquet)

## Quick Start

### PowerShell
```powershell
.\run_pipeline.ps1
```

### Command Line
```cmd
.\run_pipeline.bat
```

### Manual
```bash
pip install -r requirements.txt
python scripts\ict_pipeline.py
```

## Configuration

Edit `config\pipeline_config.json` to modify pipeline settings.

## Data Structure

Place your ICT content data files in the `data\` directory. Supported formats:
- CSV files
- JSON files  
- JSONL files

## Output

Generated files will be placed in:
- `output\` - Processed data in multiple formats
- `training_data\` - AI training datasets
- `logs\` - Pipeline execution logs

## Features

- **Text Processing**: Automatic text cleaning and normalization
- **Feature Extraction**: Automatic feature generation from data
- **Training Data Prep**: Ready-to-use datasets for ML models
- **Multiple Formats**: Export in various formats for different use cases
- **Logging**: Comprehensive logging for debugging and monitoring

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Customization

The pipeline is designed to be easily customizable:

1. Modify `scripts\ict_pipeline.py` for custom processing logic
2. Update `config\pipeline_config.json` for configuration changes
3. Add new data sources in the `load_data()` method
4. Customize preprocessing in the `preprocess_data()` method

## Example Usage

```python
from scripts.ict_pipeline import ICTContentPipeline

# Initialize pipeline
pipeline = ICTContentPipeline()

# Run with specific data file
pipeline.run_pipeline("path/to/your/data.csv")

# Or run with data in data directory
pipeline.run_pipeline()
```
"@

$readme | Out-File "README.md" -Encoding UTF8

# Step 9: Create sample data structure
$sample_data = @"
id,title,content,category,source,date
1,Introduction to AI,Artificial Intelligence is a branch of computer science...,AI,Textbook,2024-01-15
2,Machine Learning Basics,Machine learning is a subset of AI that enables...,ML,Online Course,2024-01-16
3,Data Science Fundamentals,Data science combines statistics, programming...,Data Science,Research Paper,2024-01-17
"@

$sample_data | Out-File "data\sample_ict_data.csv" -Encoding UTF8

Write-Host "`nICT Content Pipeline setup completed successfully!" -ForegroundColor Green
Write-Host "Location: $ict_project_path" -ForegroundColor Yellow
Write-Host "`nTo get started:" -ForegroundColor Cyan
Write-Host "   cd $ict_project_path" -ForegroundColor White
Write-Host "   .\run_pipeline.ps1" -ForegroundColor White
Write-Host "`nOr run the batch file:" -ForegroundColor Cyan
Write-Host "   .\run_pipeline.bat" -ForegroundColor White
