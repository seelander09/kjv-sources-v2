# DuckDuckGo MCP Integration Setup Guide
## KJV Sources Project

This guide explains how to set up and use the DuckDuckGo MCP server integration with your KJV Sources project for enhanced biblical scholarship and real-time research capabilities.

## 🚀 Quick Start

### 1. Activate DuckDuckGo MCP in Docker Desktop

1. Open Docker Desktop
2. Navigate to the MCP toolkit section
3. Enable the DuckDuckGo MCP server
4. Configure authentication if required
5. Test the connection

### 2. Test the Integration

```powershell
# Test the research tool
python duckduckgo_research_tool.py

# Test the validation pipeline
python research_validation_pipeline.py

# Test the enhanced LightRAG integration
python enhanced_lightrag_research.py
```

### 3. Run Your First Research Query

```powershell
# Research documentary hypothesis for Genesis
.\research_automation.ps1 -Action research -Book Genesis

# Validate J source attributions
.\research_automation.ps1 -Action validate -Source J -Book Genesis

# Run comprehensive research
.\research_automation.ps1 -Action research -Book Exodus -Report
```

## 📁 New Files Created

### Core Research Components

- **`duckduckgo_research_tool.py`** - Main research tool for scholarly queries
- **`research_validation_pipeline.py`** - Real-time source validation pipeline
- **`enhanced_lightrag_research.py`** - Enhanced LightRAG with research integration

### PowerShell Automation Scripts

- **`research_automation.ps1`** - Automated research and validation scripts
- **`integrate_research_pipeline.ps1`** - Full pipeline integration script

### Documentation

- **`DUCKDUCKGO_MCP_SETUP_GUIDE.md`** - This setup guide

## 🔧 Configuration

### Research Tool Settings

```python
# In duckduckgo_research_tool.py
class DuckDuckGoResearchTool:
    def __init__(self, output_dir: str = "research_output"):
        # Configure output directory
        # Set research categories
        # Define source validation queries
```

### Validation Pipeline Settings

```python
# In research_validation_pipeline.py
class ResearchValidationPipeline:
    def __init__(self, research_output_dir: str = "research_output"):
        # Configure validation settings
        self.auto_validate = True
        self.validation_threshold = 0.7
        self.research_cache_duration = 24  # hours
```

## 📊 Usage Examples

### 1. Basic Research Queries

```powershell
# Search for scholarly articles
.\research_automation.ps1 -Action search -Source "documentary hypothesis"

# Research specific book
.\research_automation.ps1 -Action research -Book Genesis

# Validate source attributions
.\research_automation.ps1 -Action validate -Source J -Book Genesis
```

### 2. Enhanced LightRAG Queries

```python
# In Python
from enhanced_lightrag_research import EnhancedLightRAGResearch

enhanced_lightrag = EnhancedLightRAGResearch()

# Enhanced query with research context
result = await enhanced_lightrag.enhanced_query("source:J")
print(f"Confidence: {result.confidence_score}")
print(f"Research context: {len(result.research_context)} items")
```

### 3. Validation Pipeline Integration

```python
# In Python
from research_validation_pipeline import ResearchValidationPipeline

pipeline = ResearchValidationPipeline()

# Validate parsed verses
validated_verses = await pipeline.validate_parsed_verses(verses_data, "Genesis")

# Generate validation report
report = pipeline.generate_validation_report(validated_verses, "Genesis")
```

## 🔄 Integration with Existing Pipeline

### 1. Full Pipeline Integration

```powershell
# Run complete integration pipeline
.\integrate_research_pipeline.ps1 -Action integrate -FullPipeline -Book Genesis

# Run individual components
.\integrate_research_pipeline.ps1 -Action parse -Book Exodus
.\integrate_research_pipeline.ps1 -Action validate -Book Exodus
.\integrate_research_pipeline.ps1 -Action research -Book Exodus
```

### 2. Enhanced Parsing with Validation

```powershell
# Parse with automatic validation
.\integrate_research_pipeline.ps1 -Action integrate -Validate -Book Genesis

# Parse with research enhancement
.\integrate_research_pipeline.ps1 -Action integrate -Research -Book Exodus
```

## 📈 Research Categories

### Documentary Hypothesis Sources

- **J (Jahwist)**: Early narrative source, anthropomorphic God
- **E (Elohist)**: Northern source, divine communication
- **P (Priestly)**: Ritual source, systematic organization
- **D (Deuteronomist)**: Deuteronomy-focused source
- **R (Redactor)**: Editorial additions and harmonization

### Research Query Types

1. **Source Validation**: Validate specific source attributions
2. **Scholarly Research**: Find current academic papers
3. **Cross-Reference**: Verify against multiple sources
4. **Recent Developments**: Track new research findings

## 🎯 Key Features

### Real-Time Research Integration

- **Current Scholarship**: Access to latest academic research
- **Source Validation**: Verify attributions against current consensus
- **Cross-Reference**: Multiple source verification
- **Confidence Scoring**: Enhanced confidence with scholarly consensus

### Enhanced LightRAG Capabilities

- **Research Context**: Real-time scholarly context in responses
- **Source Validation**: Automatic validation during queries
- **Enhanced Responses**: Research-informed answer generation
- **Confidence Metrics**: Improved confidence scoring

### Validation Pipeline

- **Automated Validation**: Real-time source validation
- **Research Integration**: Current scholarship validation
- **Confidence Adjustment**: Dynamic confidence scoring
- **Validation Reports**: Comprehensive validation summaries

## 📊 Output Files

### Research Output Directory

```
research_output/
├── research_results_Genesis_20240101_120000.json
├── validation_Genesis_20240101_120000_verses.json
├── validation_Genesis_20240101_120000_report.json
├── enhanced_query_results_20240101_120000.json
└── integration_summary_20240101_120000.json
```

### File Types

- **Research Results**: Scholarly research findings
- **Validation Results**: Source validation data
- **Validation Reports**: Summary reports with recommendations
- **Enhanced Queries**: Research-enhanced query results
- **Integration Summaries**: Pipeline integration status

## 🔍 Troubleshooting

### Common Issues

1. **DuckDuckGo MCP Not Responding**
   - Check Docker Desktop MCP toolkit status
   - Verify DuckDuckGo MCP server is enabled
   - Test connection with simple query

2. **Research Queries Failing**
   - Check internet connection
   - Verify research tool configuration
   - Review error logs in `logs/research_automation.log`

3. **Validation Pipeline Errors**
   - Ensure parsed data is available
   - Check validation pipeline configuration
   - Review validation statistics

### Debug Commands

```powershell
# Check prerequisites
.\integrate_research_pipeline.ps1 -Action integrate

# Test individual components
python duckduckgo_research_tool.py
python research_validation_pipeline.py
python enhanced_lightrag_research.py

# View logs
Get-Content logs\research_automation.log -Tail 50
Get-Content logs\integration.log -Tail 50
```

## 📚 Advanced Usage

### Custom Research Queries

```python
# Custom research queries
research_tool = DuckDuckGoResearchTool()

# Search for specific topics
results = await research_tool.search_scholarly_resources("biblical archaeology Genesis")

# Validate specific sources
validation = await research_tool.validate_source_attribution("J", "Genesis 1:1")
```

### Integration with Existing Systems

```python
# Integrate with existing parse_wikitext.py
from research_validation_pipeline import ResearchValidationPipeline

# After parsing, validate results
pipeline = ResearchValidationPipeline()
validated_verses = await pipeline.validate_parsed_verses(parsed_verses, "Genesis")
```

### Enhanced LightRAG Integration

```python
# Use enhanced LightRAG for queries
from enhanced_lightrag_research import EnhancedLightRAGResearch

enhanced_lightrag = EnhancedLightRAGResearch()

# Enhanced query with research
result = await enhanced_lightrag.enhanced_query("source:J", include_research=True)
```

## 🎉 Benefits

### For Biblical Scholarship

- **Current Research**: Access to latest academic findings
- **Source Validation**: Verify attributions against current consensus
- **Enhanced Accuracy**: Research-informed source identification
- **Academic Credibility**: Current scholarly validation

### For Your Project

- **Enhanced Pipeline**: Research-integrated parsing and analysis
- **Real-Time Validation**: Current scholarship validation
- **Improved Confidence**: Research-informed confidence scoring
- **Academic Integration**: Seamless scholarly research integration

### For Research Workflow

- **Automated Research**: Automated scholarly research gathering
- **Validation Reports**: Comprehensive validation summaries
- **Research Context**: Real-time research context in responses
- **Enhanced Queries**: Research-enhanced query capabilities

## 🚀 Next Steps

1. **Test the Integration**: Run the test commands above
2. **Explore Research Features**: Try different research queries
3. **Integrate with Your Workflow**: Use the validation pipeline
4. **Enhance Your Analysis**: Leverage research-enhanced queries
5. **Share Your Findings**: Use the research reports for collaboration

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the log files in the `logs/` directory
3. Test individual components separately
4. Verify Docker Desktop MCP toolkit configuration

The DuckDuckGo MCP integration transforms your KJV Sources project into a dynamic, research-informed biblical scholarship platform that stays current with academic developments!
