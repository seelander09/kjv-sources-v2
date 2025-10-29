# Document Ingestion Pipeline for KJV Sources Project

## 🎯 Overview

The Document Ingestion Pipeline allows you to easily add new documents to your KJV Sources project for AI analysis. Simply drop documents into the `new_documents` folder and run the pipeline to automatically process and integrate them into your research system.

## 🚀 Quick Start

### 1. Setup the Pipeline
```powershell
python setup_document_pipeline.py
```

### 2. Add Documents
- Drop any supported documents into the `new_documents` folder
- Supported formats: PDF, DOCX, TXT, MD, HTML, RTF

### 3. Run the Pipeline
```powershell
python document_ingestion_pipeline.py
```
Or use the convenient runner:
```powershell
.\run_document_pipeline.ps1
```

### 4. Access in Elysia
Your documents are now available for AI analysis through Elysia!

## 📁 Directory Structure

```
kjv-sources/
├── new_documents/              # Drop new documents here
│   ├── README.md              # Usage instructions
│   └── processed/             # Processed files archive
├── processed_documents/        # Processing logs and metadata
│   ├── processed_documents.json
│   ├── processing_stats.json
│   ├── training_data.jsonl
│   └── archive/               # Content backup
├── document_ingestion_pipeline.py
├── setup_document_pipeline.py
├── integrate_additional_documents.py
└── run_document_pipeline.ps1
```

## 🔧 What the Pipeline Does

### 1. **Document Discovery**
- Scans the `new_documents` folder for supported file types
- Identifies PDF, DOCX, TXT, MD, HTML, and RTF files

### 2. **Text Extraction**
- **PDF**: Extracts text from all pages
- **DOCX**: Processes Word documents
- **HTML**: Removes markup and extracts clean text
- **TXT/MD/RTF**: Reads plain text content

### 3. **Intelligent Analysis**
- **Biblical References**: Automatically identifies verses like "Genesis 1:1", "Exodus 2:3-5"
- **Source Attributions**: Detects Documentary Hypothesis sources (J, E, P, D, R)
- **Topic Extraction**: Identifies theological themes (creation, covenant, law, etc.)
- **Metadata Generation**: Word counts, file sizes, timestamps, checksums

### 4. **AI Processing**
- **Embeddings**: Creates semantic vectors for intelligent search
- **Vector Storage**: Stores in Weaviate for AI analysis
- **Training Data**: Generates JSONL format for LLM training

### 5. **Integration**
- **Elysia Integration**: Makes documents available through conversational AI
- **Archive Management**: Moves processed files to archive
- **Logging**: Comprehensive processing logs

## 📊 Supported File Types

| Format | Extension | Use Case | Processing |
|--------|-----------|----------|------------|
| **PDF** | `.pdf` | Academic papers, books | Text extraction from all pages |
| **Word** | `.docx` | Research papers, manuscripts | Paragraph-by-paragraph processing |
| **Text** | `.txt` | Plain text documents | Direct text reading |
| **Markdown** | `.md` | Documentation, notes | Markdown-aware processing |
| **HTML** | `.html`, `.htm` | Web pages, articles | Clean text extraction |
| **Rich Text** | `.rtf` | Formatted documents | RTF parsing |

## 🔍 AI Analysis Capabilities

Once processed, your documents are available in Elysia with these capabilities:

### **Document Search**
- "Search my uploaded documents for creation theology"
- "Find documents that discuss covenant themes"
- "Show me papers about the Documentary Hypothesis"

### **Content Analysis**
- "Analyze the theological content of [document title]"
- "What biblical references are in my research papers?"
- "Summarize the main themes in [document]"

### **Comparative Analysis**
- "Compare the theological perspectives in my uploaded documents"
- "How do different authors approach the J source?"
- "What are the common themes across my research papers?"

### **Statistical Overview**
- "Show me statistics about all my uploaded documents"
- "What topics are most common in my research?"
- "How many biblical references do I have across all documents?"

## 🛠️ Configuration Options

The pipeline can be configured via `document_pipeline_config.json`:

```json
{
  "pipeline_settings": {
    "input_directory": "new_documents",
    "output_directory": "processed_documents",
    "archive_processed_files": true,
    "create_embeddings": true,
    "store_in_weaviate": true,
    "supported_formats": [".pdf", ".docx", ".txt", ".md", ".html", ".htm", ".rtf"],
    "min_content_length": 50,
    "max_content_length": 10000,
    "embedding_model": "all-MiniLM-L6-v2",
    "weaviate_collection": "AdditionalDocuments"
  }
}
```

## 📈 Processing Statistics

The pipeline provides detailed statistics:

- **Total Files**: Number of documents discovered
- **Processed Files**: Successfully processed documents
- **Failed Files**: Documents with processing errors
- **Content Types**: Breakdown by file format
- **Total Content**: Character count across all documents
- **Topics**: Extracted theological themes
- **Biblical References**: Identified verse references
- **Source Attributions**: Documentary Hypothesis sources

## 🔧 Troubleshooting

### **Common Issues**

1. **Large Files**: Very large documents may take longer to process
   - **Solution**: The pipeline processes in batches and shows progress

2. **Encoding Issues**: Some documents may have encoding problems
   - **Solution**: The pipeline uses error-tolerant encoding

3. **Empty Content**: Very short documents (< 50 characters) are skipped
   - **Solution**: Check document content and ensure it's substantial

4. **Duplicate Detection**: Documents with identical content are detected
   - **Solution**: The pipeline generates checksums to identify duplicates

### **Logs and Debugging**

- **Processing Log**: `document_ingestion.log` contains detailed logs
- **Statistics**: `processed_documents/processing_stats.json` has processing metrics
- **Metadata**: `processed_documents/processed_documents.json` contains all document metadata

## 🎯 Best Practices

### **File Organization**
1. **Use Descriptive Filenames**: Include author, title, or topic
2. **Clean Documents**: Remove headers/footers that aren't content
3. **Batch Processing**: Add multiple related documents together
4. **Check Results**: Review the processing summary for any issues

### **Content Quality**
1. **Substantial Content**: Ensure documents have meaningful content (> 50 characters)
2. **Clean Text**: Remove unnecessary formatting or metadata
3. **Consistent Naming**: Use consistent naming conventions
4. **Related Documents**: Group related research papers together

## 🔄 Workflow Integration

### **Research Workflow**
1. **Collect Documents**: Gather research papers, commentaries, manuscripts
2. **Add to Pipeline**: Drop documents into `new_documents` folder
3. **Process**: Run the ingestion pipeline
4. **Analyze**: Use Elysia to analyze and compare documents
5. **Archive**: Processed files are automatically archived

### **Academic Workflow**
1. **Literature Review**: Add academic papers and books
2. **Research Notes**: Include your own analysis and notes
3. **Comparative Study**: Use AI to compare different sources
4. **Citation Analysis**: Track biblical references across sources
5. **Thematic Analysis**: Identify common theological themes

## 🚀 Advanced Features

### **Custom Analysis**
- **Topic Extraction**: Automatically identifies theological themes
- **Biblical Reference Detection**: Finds verse citations
- **Source Attribution**: Detects Documentary Hypothesis sources
- **Semantic Search**: AI-powered content discovery

### **Integration Capabilities**
- **Elysia Integration**: Conversational AI interface
- **Weaviate Storage**: Vector database for semantic search
- **Training Data**: Generates LLM training datasets
- **API Access**: Programmatic access to processed content

## 📚 Example Use Cases

### **Academic Research**
- Process academic papers on biblical studies
- Compare different scholarly perspectives
- Track citations and references across sources
- Generate comprehensive literature reviews

### **Theological Study**
- Add commentary manuscripts
- Analyze theological themes across sources
- Compare different denominational perspectives
- Study historical theological development

### **Personal Study**
- Process personal study notes
- Add sermon manuscripts
- Include devotional materials
- Create comprehensive study resources

## 🔮 Future Enhancements

The pipeline is designed to be extensible:

- **Additional Formats**: Support for more document types
- **Language Detection**: Automatic language identification
- **Advanced NLP**: More sophisticated text analysis
- **Visual Content**: Support for images and diagrams
- **Collaborative Features**: Multi-user document sharing

## 📞 Support

For issues or questions:

1. **Check Logs**: Review `document_ingestion.log` for error details
2. **Verify Setup**: Ensure Weaviate is running and accessible
3. **Test Documents**: Try with simple text files first
4. **Configuration**: Check `document_pipeline_config.json` settings

## 🎉 Getting Started

Ready to add your documents? Here's your quick start:

1. **Setup**: `python setup_document_pipeline.py`
2. **Add Documents**: Drop files into `new_documents/`
3. **Process**: `python document_ingestion_pipeline.py`
4. **Analyze**: Ask Elysia about your documents!

Your documents will be ready for advanced AI analysis in minutes! 🚀
