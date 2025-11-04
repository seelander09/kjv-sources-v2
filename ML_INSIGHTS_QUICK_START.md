# ML Insights Dashboard - Quick Start Guide

## 🚀 Access the Dashboard

**URL**: `http://localhost:8080/ml-insights.html`

---

## 🎯 What You'll See

### 4 Powerful Visualizations:

1. **Top Left**: **Semantic Embedding Space** (t-SNE/UMAP)
   - 481 doublet verses projected into 2D
   - Color = Source (J=Navy, E=Teal, P=Olive, R=Maroon)
   - Shows semantic clusters and relationships

2. **Top Right**: **Similarity Network** (Force-Directed Graph)
   - 10 doublet groups as nodes
   - Edges = Semantic similarity
   - Drag to rearrange, click to select

3. **Bottom**: **Parallel Coordinates** (Multi-Dimensional Features)
   - 12 feature dimensions per doublet
   - Each line = one doublet event
   - Shows source "fingerprints"

---

## 🎮 Controls

### Main Controls Bar:
- **Projection Method**: Toggle between t-SNE and UMAP
- **Similarity Threshold**: Adjust network edge sensitivity (0.5-0.9)
- **Refresh All**: Reload all visualizations
- **Selected**: Shows currently selected doublet

### Per-Visualization Controls:
- **Reset Zoom**: (Embedding chart) Return to default view
- **Restart Layout**: (Network) Re-run force simulation

---

## 💡 How to Explore

### Discover Semantic Clusters:
1. Look at **Embedding Space** (top left)
2. Notice color groupings (sources cluster!)
3. Zoom into interesting regions
4. Click points to see details

### Find Related Stories:
1. View **Network Graph** (top right)
2. Look for thick edges (high similarity)
3. Notice communities (grouped doublets)
4. Click nodes to select across all views

### Identify Source Patterns:
1. View **Parallel Coordinates** (bottom)
2. Look at source % columns (J%, E%, P%, R%)
3. Find high J% + low P% = J narrative style
4. High P% + low J% = Priestly/legal style

---

## 🔍 What to Look For

### In Embedding Space:
- **Clusters**: Do J passages cluster separately from P?
- **Outliers**: Unusual passages far from others
- **Gradients**: Smooth transitions between sources?

### In Network Graph:
- **Communities**: Which doublets are tightly connected?
- **Bridge Nodes**: Stories connecting different traditions
- **Isolated Nodes**: Unique doublets with few similarities

### In Parallel Coordinates:
- **Patterns**: Lines that follow similar paths = similar features
- **Correlations**: Do high J% always have high J_vocab?
- **Outliers**: Lines that deviate from patterns

---

## 📊 Example Discoveries

### Discovery 1: J vs P Separation
**Observation**: In embedding space, navy dots (J) cluster in one region, olive dots (P) in another.

**Meaning**: J's narrative style is semantically distinct from P's priestly style. This supports the Documentary Hypothesis!

### Discovery 2: Creation-Flood-Covenant Triangle
**Observation**: In network graph, "Creation Stories", "Flood Narrative", and "Abrahamic Covenant" form tight triangle.

**Meaning**: These three major theological events share strong thematic and narrative similarities.

### Discovery 3: Source Fingerprints
**Observation**: In parallel coordinates, J-dominant passages have high J_vocab scores.

**Meaning**: Vocabulary features successfully identify source authorship!

---

## 🎓 Academic Use Cases

### For Research Papers:
1. **Export visualizations** (screenshot)
2. **Cite quantitative evidence** (similarity scores, cluster analysis)
3. **Show multi-dimensional analysis** (parallel coordinates)

### For Teaching:
1. **Interactive demonstration** of Documentary Hypothesis
2. **Visual proof** that sources are distinct
3. **Exploration activity** for students

### For Discovery:
1. **Find outliers** (passages that don't fit patterns)
2. **Test hypotheses** (do certain themes cluster?)
3. **Generate questions** for further research

---

## 🔗 Navigation

From ML Insights to:
- **Bird's Eye View**: Overview statistics and charts
- **Source Timeline**: Chronological doublet view
- **Verse Explorer**: Verse-by-verse browser

From other pages to ML Insights:
- Look for "🧠 ML Insights" button in navigation

---

## ⚡ Pro Tips

1. **Start with t-SNE**: More stable for first exploration
2. **Try UMAP**: Often reveals different structure
3. **Adjust threshold**: Lower = more network edges (0.6-0.7 good start)
4. **Use linked selection**: Click in one view, see in others
5. **Zoom and pan**: Embedding chart is fully interactive
6. **Drag nodes**: Rearrange network for better visibility

---

## 🐛 Troubleshooting

### "Error loading embedding projection"
- **Cause**: API server not running
- **Fix**: Check if `http://localhost:8001` is accessible

### "UMAP not installed"
- **Cause**: Optional dependency not installed
- **Fix**: Use t-SNE method instead (always available)

### Network nodes overlap
- **Fix**: Click "Restart Layout" or drag nodes apart

### Can't see all parallel coordinate lines
- **Fix**: Scroll down or zoom out browser window

---

## 📈 Next Steps

After exploring ML Insights:

1. **Drill down**: Click doublets to see in Verse Explorer
2. **Compare sources**: Use filters in Bird's Eye View
3. **Analyze patterns**: Document discoveries
4. **Export findings**: Screenshot visualizations

---

## 🎉 You're Ready!

Open `http://localhost:8080/ml-insights.html` and start exploring the Documentary Hypothesis through machine learning! 🚀

---

*For detailed technical information, see `ML_INSIGHTS_IMPLEMENTATION_SUMMARY.md`*

