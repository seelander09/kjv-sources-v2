#!/usr/bin/env python3
"""
Setup Document Ingestion Pipeline
================================

This script sets up the document ingestion pipeline and creates
the necessary directories and configuration files.
"""

import os
from pathlib import Path
import json

def setup_document_pipeline():
    """Setup the document ingestion pipeline"""
    print("🔧 Setting up Document Ingestion Pipeline")
    print("=" * 50)
    
    # Create directories
    directories = [
        "new_documents",
        "new_documents/processed", 
        "processed_documents",
        "processed_documents/archive"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create README for new_documents folder
    readme_content = """# New Documents Folder

## How to Use This Pipeline

1. **Add Documents**: Drop any supported documents into this folder
2. **Run Pipeline**: Execute `python document_ingestion_pipeline.py`
3. **Access in Elysia**: Your documents will be available for AI analysis

## Supported File Types

- **PDF** (.pdf) - Academic papers, books, articles
- **Word Documents** (.docx) - Research papers, manuscripts
- **Text Files** (.txt) - Plain text documents
- **Markdown** (.md) - Documentation, notes
- **HTML** (.html, .htm) - Web pages, articles
- **Rich Text** (.rtf) - Formatted documents

## What Happens During Processing

1. **Text Extraction**: Content is extracted from all supported formats
2. **Metadata Analysis**: 
   - Biblical references are automatically identified
   - Documentary Hypothesis source attributions (J, E, P, D, R) are detected
   - Topics and themes are extracted
   - Word and character counts are calculated
3. **AI Embeddings**: Content is processed for semantic search
4. **Database Storage**: Documents are stored in Weaviate for AI analysis
5. **Archive**: Original files are moved to the processed subfolder

## Example Documents to Add

- Academic papers on biblical studies
- Commentary manuscripts
- Research notes and analysis
- Historical documents
- Theological treatises
- Comparative religious texts

## Accessing Your Documents in Elysia

Once processed, you can ask Elysia questions like:
- "Analyze the content of [document title]"
- "Find documents that discuss [topic]"
- "Compare the theological perspectives in my uploaded documents"
- "Search for biblical references in my research papers"

## File Organization

- **new_documents/**: Drop new files here
- **new_documents/processed/**: Processed files are archived here
- **processed_documents/**: Contains processing logs and metadata
- **processed_documents/archive/**: Backup of all processed content

## Tips for Best Results

1. **Use Descriptive Filenames**: Include author, title, or topic in filename
2. **Clean Documents**: Remove headers/footers that aren't content
3. **Batch Processing**: Add multiple related documents together
4. **Check Results**: Review the processing summary for any issues

## Troubleshooting

- **Large Files**: Very large documents may take longer to process
- **Encoding Issues**: Some documents may have encoding problems
- **Empty Content**: Very short documents (< 50 characters) are skipped
- **Duplicate Detection**: Documents with identical content are detected

For support, check the processing logs in `document_ingestion.log`.
"""
    
    with open("new_documents/README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ Created README.md in new_documents folder")
    
    # Create batch processing script
    batch_script = """@echo off
echo Starting Document Ingestion Pipeline...
echo.

REM Activate virtual environment
call sources-env\\Scripts\\activate.bat

REM Run the pipeline
python document_ingestion_pipeline.py

echo.
echo Pipeline completed. Check the results above.
pause
"""
    
    with open("run_document_pipeline.bat", 'w', encoding='utf-8') as f:
        f.write(batch_script)
    
    print("✅ Created run_document_pipeline.bat")
    
    # Create PowerShell script
    powershell_script = """# Document Ingestion Pipeline Runner
Write-Host "Starting Document Ingestion Pipeline..." -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\\sources-env\\Scripts\\Activate.ps1"

# Run the pipeline
Write-Host "Running document ingestion pipeline..." -ForegroundColor Green
try {
    python document_ingestion_pipeline.py
    Write-Host "Pipeline completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Pipeline failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
"""
    
    with open("run_document_pipeline.ps1", 'w', encoding='utf-8') as f:
        f.write(powershell_script)
    
    print("✅ Created run_document_pipeline.ps1")
    
    # Create configuration file
    config = {
        "pipeline_settings": {
            "input_directory": "new_documents",
            "output_directory": "processed_documents",
            "archive_processed_files": True,
            "create_embeddings": True,
            "store_in_weaviate": True,
            "supported_formats": [".pdf", ".docx", ".txt", ".md", ".html", ".htm", ".rtf"],
            "min_content_length": 50,
            "max_content_length": 10000,
            "embedding_model": "all-MiniLM-L6-v2",
            "weaviate_collection": "AdditionalDocuments"
        },
        "processing_options": {
            "extract_biblical_references": True,
            "extract_source_attributions": True,
            "extract_topics": True,
            "generate_checksums": True,
            "create_training_data": True
        },
        "output_formats": {
            "json_metadata": True,
            "jsonl_training": True,
            "processing_stats": True,
            "weaviate_storage": True
        }
    }
    
    with open("document_pipeline_config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Created document_pipeline_config.json")
    
    print("\n🎉 Document Ingestion Pipeline Setup Complete!")
    print("=" * 50)
    print("📁 Created directories:")
    print("  • new_documents/ - Drop new documents here")
    print("  • new_documents/processed/ - Processed files archive")
    print("  • processed_documents/ - Processing logs and metadata")
    print("  • processed_documents/archive/ - Content backup")
    print("\n📄 Created files:")
    print("  • new_documents/README.md - Usage instructions")
    print("  • run_document_pipeline.bat - Windows batch runner")
    print("  • run_document_pipeline.ps1 - PowerShell runner")
    print("  • document_pipeline_config.json - Configuration")
    print("\n🚀 To use the pipeline:")
    print("  1. Add documents to the 'new_documents' folder")
    print("  2. Run: python document_ingestion_pipeline.py")
    print("  3. Or use: .\\run_document_pipeline.ps1")
    print("\n💡 Supported formats: PDF, DOCX, TXT, MD, HTML, RTF")
    print("📚 Documents will be available in Elysia for AI analysis")

if __name__ == "__main__":
    setup_document_pipeline()
