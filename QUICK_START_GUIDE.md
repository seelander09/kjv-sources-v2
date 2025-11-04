# Quick Start Guide - Enhanced Torah Visualizations

## Getting Started in 3 Steps

### Step 1: Start the API Server

Open PowerShell in the project directory and run:

```powershell
.\start_api_server.ps1
```

Or manually:

```powershell
$env:PYTHONPATH = "$PWD"
python -m uvicorn src.kjv_sources.api:app --reload --port 8001
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Application startup complete.
```

### Step 2: Ensure Data is Loaded

If you haven't uploaded the Torah data to Qdrant yet:

```powershell
python upload_torah_with_progress.py
```

**Expected Output:**
```
Uploading Torah Data to Qdrant
===============================
✓ Genesis - 1,533 verses uploaded
✓ Exodus - 1,213 verses uploaded
✓ Leviticus - 859 verses uploaded
✓ Numbers - 1,288 verses uploaded
✓ Deuteronomy - 959 verses uploaded

Total: 5,852 verses uploaded successfully
```

### Step 3: Open the Visualizations

**Option A: Bird's Eye View (Overview)**
```
http://localhost:8080/birds-eye-view.html
```
Or double-click: `frontend/birds-eye-view.html`

**Option B: Verse Explorer (Detailed Analysis)**
```
http://localhost:8080/verse-explorer.html
```
Or double-click: `frontend/verse-explorer.html`

## Using the Bird's Eye View

### Overview Dashboard
- **Source Stratigraphy Map**: See source distribution across all books/chapters
- **Source Dominance Matrix**: Compare which sources dominate each book
- **Doublet Heatmap**: Find chapters with doublets
- **Source Flow Network**: Visualize source relationships

### Interactive Features
1. **Click on any chart** to drill down to verse-level details
2. **Filter by book** using the dropdown
3. **Filter doublet category** to focus analysis
4. **Click "Verse Explorer"** button to switch to detailed view

### Common Use Cases
- **Research Question**: "Which chapters have the most source interweaving?"
  - Look at Source Stratigraphy Map
  - Find bars with multiple colors
  - Click to explore those chapters

- **Research Question**: "Where are creation doublets located?"
  - Filter doublet category: "creation"
  - Check Doublet Heatmap
  - Click on Genesis chapters 1-2

## Using the Verse Explorer

### Navigation
1. **Left Panel**: Click a book name to expand chapters
2. **Click a chapter number** to load verses
3. **Breadcrumb**: Navigate back to previous views

### Verse Cards
- **Click any verse** to expand/collapse details
- **Source badges** show which sources are present
- **Doublet badges** appear for parallel passages

### Doublet Analysis
1. **Click a doublet badge** to open side-by-side comparison
2. **View highlighted differences**:
   - Green = Addition
   - Red = Omission
   - Yellow = Change
3. **See source attribution** for each passage

### Filtering
1. **Select sources** (J, E, P, D, R) to show only verses with those sources
2. **Check "Doublets only"** to focus on parallel passages
3. **Text search** to find specific words/phrases
4. **Click "Apply Filters"** to see results

### Timeline View
1. **Click "Doublet Timeline"** button
2. **See all doublets** in canonical order
3. **Click any marker** to see verse details
4. **Color-coded by source** for easy identification

## Common Research Workflows

### Workflow 1: Exploring the Documentary Hypothesis

```
1. Start with Bird's Eye View
   └─> See overall patterns

2. Click Source Stratigraphy Map (e.g., Genesis chapter 1)
   └─> Opens Verse Explorer at that chapter

3. Expand verse cards to see sources
   └─> Note P (Priestly) dominance in Genesis 1

4. Click navigation to Genesis chapter 2
   └─> Note J (Jahwist) dominance in Genesis 2

5. Click doublet badge on verse
   └─> Compare creation accounts side-by-side
```

### Workflow 2: Finding Doublets

```
1. Open Bird's Eye View

2. Click Doublet Heatmap (darkest red cells)
   └─> Identifies chapters with most doublets

3. Opens Verse Explorer at that chapter

4. Check "Doublets only" filter
   └─> Shows only parallel passages

5. Click doublet badges to compare
   └─> See textual differences highlighted
```

### Workflow 3: Source Analysis

```
1. Open Verse Explorer

2. Use filters:
   - Uncheck all sources except J
   - Click "Apply Filters"

3. Browse J-only verses
   └─> Note vocabulary, themes, style

4. Repeat for E, P, D, R
   └─> Compare patterns across sources

5. Use text search for specific terms
   └─> e.g., "LORD God" (J) vs "God" (P)
```

## API Endpoints (for Advanced Users)

### Get Verses by Chapter
```bash
curl "http://localhost:8001/api/v1/verses/by-chapter?book=Genesis&chapter=1"
```

### Search Verses
```bash
curl "http://localhost:8001/api/v1/verses/search?sources=J,P&is_doublet=true"
```

### Compare Doublets
```bash
curl "http://localhost:8001/api/v1/doublets/compare?reference1=Genesis%201:1&reference2=Genesis%202:4"
```

### Get Doublet Timeline
```bash
curl "http://localhost:8001/api/v1/doublets/timeline"
```

## Troubleshooting

### Problem: Charts show "No data"
**Solution**: Make sure data is uploaded
```powershell
python upload_torah_with_progress.py
```

### Problem: API connection error
**Solution**: Check if API server is running
```powershell
# Check if port 8001 is in use
netstat -an | findstr "8001"

# If not running, start it
.\start_api_server.ps1
```

### Problem: Visualizations don't load
**Solution**: Check browser console (F12) for errors
- Ensure API is at `http://localhost:8001`
- Check CORS settings in `api.py`

### Problem: Click handlers don't work
**Solution**: 
1. Open browser console (F12)
2. Look for JavaScript errors
3. Ensure Plotly.js and D3.js are loaded

## Keyboard Shortcuts

- **Esc**: Close doublet comparison modal
- **Ctrl+F**: Focus search box
- **Enter**: Apply filters

## Browser Requirements

- **Chrome/Edge**: Fully supported
- **Firefox**: Fully supported
- **Safari**: Fully supported
- **Mobile**: Responsive design (limited features)

## Data Sources

- **Torah Books**: Genesis, Exodus, Leviticus, Numbers, Deuteronomy
- **Total Verses**: 5,852
- **Sources**: J (Jahwist), E (Elohist), P (Priestly), D (Deuteronomist), R (Redactor)

## Next Steps

1. **Explore Genesis**: Start with creation accounts (Gen 1-2)
2. **Study Doublets**: Compare flood narratives (Gen 6-9)
3. **Analyze Sources**: Filter by J or P to see stylistic differences
4. **Export Data**: Use API endpoints for research data

## Support

- **API Documentation**: `http://localhost:8001/docs`
- **Implementation Summary**: See `IMPLEMENTATION_SUMMARY.md`
- **Project Documentation**: See `README.md`

## Example Research Questions

1. **"What percentage of Genesis is J source?"**
   - Bird's Eye View → Source Dominance Matrix
   - Look at Genesis column under J row

2. **"Where do J and E sources overlap?"**
   - Verse Explorer → Filter: Check only J and E
   - Apply filters → Browse results

3. **"What are the main creation doublets?"**
   - Verse Explorer → Doublet Timeline
   - Look for creation category
   - Click markers to see verses

4. **"How does P source differ from J?"**
   - Compare verses filtered by each source
   - Note vocabulary: "God" (P) vs "LORD God" (J)
   - Note style: formal (P) vs narrative (J)

## Tips for Teaching

1. **Start with overview**: Show Bird's Eye View to class
2. **Interactive exploration**: Let students click through
3. **Doublet comparison**: Use side-by-side view for discussion
4. **Source patterns**: Filter by source to show distinctive features
5. **Timeline context**: Show doublet distribution across books

## Advanced Features

- **Deep Linking**: Share URLs with book/chapter parameters
- **Custom Queries**: Use API endpoints for research data
- **Batch Analysis**: Export data via API for statistical analysis
- **Integration**: Connect with other biblical study tools

---

**Congratulations!** You're ready to explore the Documentary Hypothesis with powerful, interactive visualizations. Happy researching! 📚

