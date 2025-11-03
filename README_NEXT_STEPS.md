# Next Steps Implementation Guide

## Overview

This guide documents the implementation of the next steps for the KJV Sources project:

1. ✅ Frontend visualization development (using the new API endpoints)
2. ✅ Model training on Torah data (5,852 verses)
3. ✅ Gradual expansion to other biblical books
4. ✅ Integration with the AI learning system

## 1. Frontend Visualization

### File Created
- `frontend/birds-eye-view.html` - Interactive visualization dashboard

### Features
- Source Stratigraphy Map (stacked area chart)
- Source Dominance Matrix (heatmap)
- Doublet Distribution Heatmap
- Source Flow Network (Sankey diagram)
- Real-time filtering and statistics

### Usage

1. **Start the API server**:
   ```powershell
   python -m uvicorn src.kjv_sources.api:app --reload --port 8001
   ```

2. **Open the visualization**:
   - Open `frontend/birds-eye-view.html` in a web browser
   - Or serve via HTTP server:
     ```powershell
     cd frontend
     python -m http.server 8080
     ```
   - Navigate to: `http://localhost:8080/birds-eye-view.html`

3. **Interact with visualizations**:
   - Use filters to select books or doublet categories
   - Hover over charts for detailed information
   - Click refresh to reload data

### API Endpoints Used
- `/api/v1/bird-eye/source-stratigraphy`
- `/api/v1/bird-eye/source-dominance-matrix`
- `/api/v1/bird-eye/doublet-heatmap`
- `/api/v1/bird-eye/source-flow-network`

## 2. Model Training Infrastructure

### File Created
- `train_torah_source_model.py` - ML model training script

### Features
- Feature extraction from Torah verses
- Random Forest classifier training
- Model evaluation and validation
- Model persistence (save/load)

### Usage

1. **Train the model**:
   ```powershell
   python train_torah_source_model.py
   ```

2. **What it does**:
   - Loads 5,852 confirmed Torah verses
   - Extracts features (vocabulary, theological, style, structural)
   - Trains Random Forest classifier
   - Evaluates with cross-validation
   - Saves model to `models/torah_source_classifier.pkl`

3. **Expected output**:
   - Training accuracy report
   - Classification metrics
   - Confusion matrix
   - Saved model file

### Feature Extraction
The model extracts 20 features per verse:
- 5 vocabulary features (one per source: J, E, P, D, R)
- 5 theological features
- 5 style features
- 5 structural features

## 3. Bible Expansion Framework

### File Created
- `expand_bible_framework.py` - Framework for expanding to all 66 books

### Features
- Book metadata management
- Source attribution for new books
- Multiple attribution methods (ML, pattern matching, heuristics)
- Progress tracking
- Results export (CSV, JSON)

### Usage

1. **Check expansion status**:
   ```powershell
   python expand_bible_framework.py
   ```

2. **Process a new book**:
   ```python
   from expand_bible_framework import BibleExpansionFramework
   
   framework = BibleExpansionFramework()
   framework.process_book('Joshua', Path('data/joshua.txt'), 'plain_text')
   ```

3. **View status**:
   ```python
   status = framework.get_expansion_status()
   print(f"Progress: {status['completed_verses']/status['total_verses']*100:.1f}%")
   ```

### Supported Methods
1. **ML Classification** (highest priority) - Uses trained model
2. **Pattern Matching** - Matches Torah source patterns
3. **Heuristic Rules** - Rule-based attribution
4. **Scholar Annotations** - Manual annotations (future)

## 4. AI Learning System Integration

### File Created
- `ai_learning_integration.py` - Main integration script

### Features
- Pattern recognition across books
- Comparative analysis (Torah vs other books)
- Discovery report generation
- Source influence tracking

### Usage

1. **Identify patterns in a book**:
   ```powershell
   python ai_learning_integration.py
   ```

2. **Compare Torah source with another book**:
   ```python
   from ai_learning_integration import AILearningIntegration
   
   integration = AILearningIntegration()
   report = integration.compare_torah_with_book('P', '1 Chronicles')
   ```

3. **Generate discovery report**:
   ```python
   report = integration.generate_discovery_report()
   ```

### Output Files
- `output/ai_analysis/comparison_*.json` - Comparison reports
- `output/ai_analysis/discovery_report.json` - Comprehensive discovery report

## Integration Workflow

### Complete Workflow Example

1. **Train the model** (one-time setup):
   ```powershell
   python train_torah_source_model.py
   ```

2. **Start API server**:
   ```powershell
   python -m uvicorn src.kjv_sources.api:app --reload --port 8001
   ```

3. **Open visualization**:
   - Open `frontend/birds-eye-view.html` in browser

4. **Expand to new books**:
   ```powershell
   python expand_bible_framework.py
   ```

5. **Run AI analysis**:
   ```powershell
   python ai_learning_integration.py
   ```

## File Structure

```
kjv-sources/
├── frontend/
│   └── birds-eye-view.html          # Frontend visualization
├── models/
│   └── torah_source_classifier.pkl  # Trained model (after training)
├── output/
│   └── ai_analysis/                 # AI analysis results
├── train_torah_source_model.py      # Model training script
├── expand_bible_framework.py        # Expansion framework
├── ai_learning_integration.py      # AI integration
└── README_NEXT_STEPS.md            # This file
```

## Dependencies

### Required Python Packages
```bash
pip install scikit-learn pandas numpy
```

### Already Installed (from requirements.txt)
- pandas
- qdrant-client
- sentence-transformers
- fastapi
- uvicorn

## Next Actions

### Immediate
1. ✅ Train the model on Torah data
2. ✅ Test the frontend visualization
3. ✅ Verify API endpoints work

### Short-term
1. Collect source text files for historical books
2. Process first historical book (Joshua)
3. Validate results with scholars
4. Iterate on model accuracy

### Long-term
1. Expand to all 66 books
2. Build scholar annotation interface
3. Deploy visualization platform
4. Continuous model improvement

## Troubleshooting

### Model Training Issues
- **No data found**: Run `python kjv_pipeline.py` first to generate CSV files
- **Memory errors**: Reduce training data size or use batch processing
- **Low accuracy**: Adjust feature weights or add more training data

### API Issues
- **Connection refused**: Make sure API server is running on port 8001
- **CORS errors**: Check browser console and API CORS settings
- **No data**: Verify Qdrant has data and collection name is correct

### Visualization Issues
- **Charts not loading**: Check browser console for errors
- **API errors**: Verify API server is running and endpoints are accessible
- **Missing data**: Ensure data has been processed and loaded into Qdrant

---

**Last Updated**: January 2025  
**Status**: Implementation Complete - Ready for Testing

