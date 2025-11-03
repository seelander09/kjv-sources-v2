# KJV Sources Project

A sophisticated biblical text analysis platform focused on the Documentary Hypothesis in the King James Version of the Bible. This project parses color-coded wikitext files to extract and analyze different source traditions (J, E, P, D, R) and provides multiple data formats for LLM training and scholarly research.

## 📋 Project Overview

The KJV Sources project implements the Documentary Hypothesis methodology, which identifies different source traditions within the Pentateuch (first five books of the Bible). The project:

- **Parses** color-coded wikitext files from Wikiversity
- **Extracts** source attributions (J, E, P, D, R) from biblical text
- **Analyzes** multi-source verses and redaction patterns
- **Generates** LLM training datasets and scholarly exports
- **Provides** a FastAPI server for semantic search and analysis
- **Offers** command-line tools for data exploration

## 🎨 Documentary Hypothesis Sources

The project analyzes five main source traditions with specific color mappings:

| Source | Color | Hex Code | Description |
|--------|-------|----------|-------------|
| **J** (Jahwist) | Navy Blue | `#000088` | Early narrative source with anthropomorphic God |
| **E** (Elohist) | Teal | `#008888` | Northern narrative source with prophetic emphasis |
| **P** (Priestly) | Olive Yellow | `#888800` | Priestly/liturgical source with systematic organization |
| **D** (Deuteronomist) | Black | `#000000` | Deuteronomy-focused source |
| **R** (Redactor) | Maroon Red | `#880000` | Editorial additions and harmonizing elements |

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional, for vector database services)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/kjv-sources.git
   cd kjv-sources
   ```

2. **Install dependencies:**
   ```bash
   # Main dependencies
   pip install -r requirements.txt
   
   # API dependencies (if using FastAPI server)
   pip install -r api_requirements.txt
   
   # LightRAG dependencies (if using LightRAG)
   pip install -r lightrag_requirements.txt
   ```

3. **Run the pipeline:**
   ```bash
   # Windows
   python kjv_pipeline.py
   
   # Or use the CLI
   python kjv_cli.py view genesis
   ```

## 📚 Available Books

The pipeline currently supports the first five books of the Bible (Pentateuch):

- **Genesis** - Creation and early history
- **Exodus** - Israel's deliverance and law
- **Leviticus** - Priestly laws and rituals
- **Numbers** - Wilderness journey and census
- **Deuteronomy** - Moses' final speeches

## 🔧 Usage

### Command-Line Interface

The project includes a rich CLI for viewing and analyzing data:

```bash
# View verses with rich formatting
python kjv_cli.py view genesis

# View specific chapter
python kjv_cli.py view genesis --chapter 1

# View only multi-source verses
python kjv_cli.py view genesis --show-multi

# Filter by source
python kjv_cli.py view genesis --source P

# Export CSV
python kjv_cli.py export-csv genesis --format llm

# Show statistics
python kjv_cli.py stats genesis
```

### FastAPI Server

Start the API server for semantic search and visualization endpoints:

```bash
# Start the server
python -m uvicorn src.kjv_sources.api:app --reload --port 8001

# Or use Docker Compose
docker-compose --profile qdrant --profile api up
```

The API provides endpoints for:
- Semantic search in biblical text
- Source analysis and statistics
- Geographic pattern analysis
- Doublet detection and visualization
- Documentary hypothesis timeline data

See `RAG_API_GUIDE.md` for detailed API documentation.

### Vector Database Setup

The project uses Qdrant for semantic search. To set up:

1. **Start Qdrant:**
   ```bash
   docker-compose --profile qdrant up -d
   ```

2. **Ingest data:**
   ```bash
   python lightrag_ingestion.py
   ```

## 📁 Project Structure

```
kjv-sources/
├── src/kjv_sources/          # Main Python package
│   ├── __init__.py
│   ├── api.py                 # FastAPI server
│   ├── cli.py                 # CLI interface
│   ├── enhanced_cli.py        # Enhanced CLI features
│   ├── qdrant_client.py       # Qdrant client wrapper
│   ├── parsers/               # Parsing modules
│   └── data/                   # Data models
├── tests/                     # Test suite
├── wiki_markdown/             # Source wikitext files (local, gitignored)
├── output/                    # Generated outputs (local, gitignored)
├── qdrant_data/              # Vector database (local, gitignored)
├── lightrag_data/            # LightRAG data (local, gitignored)
├── parse_wikitext.py         # Core parsing logic
├── kjv_pipeline.py           # Main pipeline orchestrator
├── kjv_cli.py                # CLI launcher
├── lightrag_ingestion.py     # Vector DB ingestion
├── requirements.txt           # Main dependencies
├── api_requirements.txt      # API dependencies
├── lightrag_requirements.txt # LightRAG dependencies
├── docker-compose.yml        # Docker services
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## 🗄️ Local Data Directories

The following directories contain large data files and are excluded from Git (see `.gitignore`):

- `wiki_markdown/` - Source wikitext files (~3.9 MB)
- `output/` - Generated outputs (~88 GB)
- `qdrant_data/` - Qdrant vector database (~9.6 GB)
- `lightrag_data/` - LightRAG vector database
- `scriptural_truth_data/` - Additional source data
- `processed_documents/` - Processed document data

These directories should remain local and are not pushed to GitHub. The pipeline will generate them when you run the data processing scripts.

## 🛠️ Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

The project follows PEP 8 style guidelines and uses type hints. See `.cursorrules` for detailed coding standards.

### Adding New Features

1. Create a feature branch
2. Add tests for new functionality
3. Update documentation
4. Submit a pull request

## 📊 Output Formats

The pipeline generates multiple data formats:

### CSV Exports
- **Simple CSV**: Basic verse data with source codes
- **LLM-Optimized CSV**: Enhanced features for machine learning

### Training Datasets (JSONL)
- **Instruction Fine-tuning**: Prompt-response pairs
- **Source Classification**: Labeled text data
- **Sequence Labeling**: Token-level source labels
- **Analysis Data**: Complex source analysis examples

### HTML Previews
- Color-coded verse displays
- Source visualization
- Statistical summaries

## 🔍 Technical Details

### Core Technologies
- **Python 3.8+** - Primary language
- **FastAPI** - Web API framework
- **Qdrant** - Vector database for RAG
- **LightRAG** - Advanced retrieval system
- **Rich** - Terminal UI library
- **Click** - CLI framework
- **Pandas** - Data manipulation
- **Sentence Transformers** - Embedding models

### Parsing Logic

The parser (`parse_wikitext.py`) extracts color-coded segments from Wikiversity wikitext format and maps them to source traditions. It handles:
- Multi-source verses
- Redaction indicators
- Source percentages
- Text segmentation

### Vector Database

The project uses Qdrant for semantic search, storing:
- Verse embeddings
- Source metadata
- Geographic references
- Document relationships

## 📖 Documentation

- `PIPELINE_README.md` - Detailed pipeline documentation
- `RAG_API_GUIDE.md` - API usage guide
- `QDRANT_GUIDE.md` - Qdrant setup and usage
- `LIGHTRAG_GUIDE.md` - LightRAG integration

## 🤝 Contributing

This project is designed for:
- **Biblical scholars** and researchers
- **LLM developers** working on religious text models
- **Digital humanities** projects
- **Theological education** and training

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

This project is based on the Documentary Hypothesis research methodology and uses color-coded source data from Wikiversity.

## 📞 Support

For questions or issues, please:
- Check the documentation in the `docs/` directory
- Review existing GitHub issues
- Create a new issue with detailed information

---

**Note**: This project focuses on scholarly analysis and does not make theological claims. The Documentary Hypothesis is one of several academic approaches to understanding the composition of the Pentateuch.
