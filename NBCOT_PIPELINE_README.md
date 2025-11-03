# NBCOT Test Files Pipeline
============================

This pipeline processes NBCOT (National Board for Certification in Occupational Therapy) test files and adds them to a vector database for AI learning and retrieval. This is kept separate from the main KJV Sources project.

## Overview

The NBCOT pipeline extracts text from PDF documents containing occupational therapy study materials and creates semantic embeddings that can be used for:
- AI-powered question answering
- Document similarity search
- Content recommendation
- Study material analysis

## Files Included

- `nbcot_pipeline.py` - Main processing script
- `run_nbcot_pipeline.ps1` - PowerShell runner script
- `nbcot_requirements.txt` - Python dependencies
- `query_nbcot_database.py` - Query tool for the vector database
- `NBCOT_PIPELINE_README.md` - This documentation

## Prerequisites

1. **Python 3.8+** installed
2. **Qdrant vector database** running (Docker recommended)
3. **NBCOT Test files** folder with PDF documents

## Setup

### 1. Install Dependencies

```powershell
# Install Python dependencies
pip install -r nbcot_requirements.txt

# Or use the PowerShell script
.\run_nbcot_pipeline.ps1 -InstallDependencies
```

### 2. Start Qdrant Database

```powershell
# Using Docker (recommended)
docker run -p 6333:6333 qdrant/qdrant

# Or check if Qdrant is already running
.\run_nbcot_pipeline.ps1 -CheckQdrant
```

### 3. Prepare NBCOT Files

Ensure your `NBCOT Test files` folder contains the PDF documents you want to process.

## Usage

### Quick Start

```powershell
# Run the complete pipeline (install dependencies, check Qdrant, process files)
.\run_nbcot_pipeline.ps1 -All
```

### Step-by-Step

```powershell
# 1. Check status
.\run_nbcot_pipeline.ps1

# 2. Install dependencies (if needed)
.\run_nbcot_pipeline.ps1 -InstallDependencies

# 3. Check Qdrant connection
.\run_nbcot_pipeline.ps1 -CheckQdrant

# 4. Run the pipeline
.\run_nbcot_pipeline.ps1 -RunPipeline
```

### Query the Database

```powershell
# Interactive query tool
python query_nbcot_database.py

# Quick search
python query_nbcot_database.py "pediatric occupational therapy interventions"
```

## Pipeline Features

### Text Extraction
- Supports both PyPDF2 and pdfplumber for PDF processing
- Handles large PDF files efficiently
- Preserves page structure and formatting
- Extracts text from complex layouts

### Text Chunking
- Splits documents into overlapping chunks (1000 words with 200 word overlap)
- Maintains context across chunk boundaries
- Optimized for semantic search

### Vector Embeddings
- Uses `all-MiniLM-L6-v2` model for embeddings
- 384-dimensional vectors
- Cosine similarity for matching
- Fast and accurate semantic search

### Database Storage
- Qdrant vector database for efficient storage
- Separate collection: `nbcot_documents`
- Metadata preservation (filename, chunk index, etc.)
- Scalable for large document collections

## Output Files

The pipeline creates several output files in the `nbcot_output/` folder:

- `{filename}_extracted.txt` - Raw extracted text from each document
- `{filename}_chunks.json` - Chunked text with metadata
- `nbcot_processing_summary.json` - Complete processing summary
- `nbcot_pipeline.log` - Detailed processing log

## Query Examples

### Basic Search
```python
# Search for specific topics
python query_nbcot_database.py "sensory integration therapy"
python query_nbcot_database.py "ADL assessment tools"
python query_nbcot_database.py "mental health occupational therapy"
```

### Interactive Mode
```python
python query_nbcot_database.py
# Then choose from menu options:
# 1. Search documents
# 2. List all documents  
# 3. Search within specific document
# 4. Show collection info
```

## Configuration

### Customizing Chunk Size
Edit `nbcot_pipeline.py` and modify the `chunk_size` and `overlap` parameters:

```python
chunks = self.chunk_text(text, chunk_size=1500, overlap=300)
```

### Different Embedding Model
Change the model in the `NBCOTProcessor` class:

```python
self.model = SentenceTransformer('all-mpnet-base-v2')  # Larger, more accurate
```

### Custom Collection Name
Modify the collection name when initializing:

```python
processor = NBCOTProcessor(collection_name="my_nbcot_docs")
```

## Troubleshooting

### Common Issues

1. **Qdrant not running**
   ```powershell
   # Start Qdrant
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. **Missing dependencies**
   ```powershell
   pip install PyPDF2 sentence-transformers qdrant-client
   ```

3. **Large PDF files taking too long**
   - The pipeline processes files sequentially
   - Large files (>100MB) may take several minutes
   - Check the log file for progress

4. **Memory issues**
   - Reduce chunk size in the pipeline
   - Process files one at a time
   - Ensure sufficient RAM (4GB+ recommended)

### Log Files

Check `nbcot_pipeline.log` for detailed error messages and processing information.

## Integration with AI Systems

The vector database can be integrated with:

- **ChatGPT/Claude** - Use as RAG (Retrieval-Augmented Generation) source
- **Custom AI applications** - Direct API access to Qdrant
- **Study assistants** - Question-answering systems
- **Content recommendation** - Similar document suggestions

## Security and Privacy

- All processing is done locally
- No data is sent to external services
- Vector embeddings are stored in your local Qdrant instance
- Original PDF files remain unchanged

## Performance

- **Processing speed**: ~1-2 MB/minute for PDF files
- **Memory usage**: ~500MB for typical processing
- **Storage**: ~10-20% of original PDF size for vectors
- **Query speed**: <100ms for typical searches

## Support

For issues or questions:
1. Check the log files in `nbcot_output/`
2. Verify Qdrant is running on port 6333
3. Ensure all dependencies are installed
4. Check that NBCOT files are accessible

## License

This pipeline is part of the KJV Sources project and follows the same licensing terms.
