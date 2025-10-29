# Qdrant Vector Database Semantic Pattern Search Prompt

Use this prompt with any AI agent to perform semantic pattern searches on the KJV Sources Qdrant vector database.

## System Context
You are working with a sophisticated biblical text analysis project that uses Qdrant vector database for semantic pattern recognition. The database contains biblical verses with Documentary Hypothesis source attribution (J, E, P, D, R sources) and semantic embeddings.

## Available Collections
- **kjv_deuteronomy_verses**: 685 Deuteronomy verses with embeddings
- **kjv_biblical_verses**: Additional biblical text collections
- **scriptural_truth_***: Scriptural Truth website content

## Technical Setup
- **Qdrant Server**: localhost:6333
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Similarity Metric**: Cosine similarity
- **Threshold**: 0.3 (adjustable)

## Search Instructions

### 1. Basic Semantic Pattern Search
```
Perform a semantic pattern search on the KJV Sources Qdrant database for the following pattern: "[YOUR_PATTERN_HERE]"

Requirements:
- Use the qdrant_semantic_search.py script approach
- Search the kjv_deuteronomy_verses collection
- Return top 20 results with similarity > 0.3
- Include verse text, reference, source attribution, and similarity score
- Save results to JSON file

Pattern examples:
- "listen hear hearken then guard keep observe then do perform obey"
- "covenant obedience pattern: listen, guard, do"
- "divine command sequence: hear, keep, do"
- "love serve fear keep"
- "command obey serve love fear"
```

### 2. Advanced Pattern Analysis
```
Perform a comprehensive semantic pattern analysis on the KJV Sources Qdrant database:

Search for these patterns:
1. "[PRIMARY_PATTERN]"
2. "[SECONDARY_PATTERN]"
3. "[TERTIARY_PATTERN]"

Requirements:
- Use sentence transformers to create pattern embeddings
- Search kjv_deuteronomy_verses collection
- Return top 20 results per pattern
- Analyze source distribution (D, J, E, P, R)
- Identify theological themes
- Compare pattern effectiveness
- Generate summary statistics
- Save detailed results to JSON
```

### 3. Documentary Hypothesis Source Analysis
```
Perform a semantic search focusing on Documentary Hypothesis source patterns:

Search for: "[PATTERN]"

Requirements:
- Search kjv_deuteronomy_verses collection
- Filter results by source attribution (D, J, E, P, R)
- Analyze source-specific language patterns
- Identify theological differences between sources
- Compare Deuteronomic (D) vs other sources
- Generate source distribution analysis
- Include sub-source analysis (Dtr1, Dtr2, Core)
```

### 4. Custom Pattern Discovery
```
Discover new semantic patterns in the KJV Sources Qdrant database:

Task: Find verses with patterns similar to "[SEED_PATTERN]"

Requirements:
- Use semantic similarity to find related patterns
- Expand search beyond exact matches
- Identify theological themes
- Analyze verb sequences
- Find covenant language patterns
- Discover command structures
- Generate pattern taxonomy
```

## Technical Implementation Guide

### Required Scripts
1. **qdrant_semantic_search.py** - Main search script
2. **create_and_load_qdrant_collections.py** - Data loading script

### Key Functions to Use
```python
# Connect to Qdrant
client = QdrantClient('localhost', port=6333)

# Create pattern embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
pattern_embedding = model.encode("your pattern here")

# Search collection
results = client.search(
    collection_name="kjv_deuteronomy_verses",
    query_vector=pattern_embedding.tolist(),
    limit=20,
    with_payload=True
)
```

### Result Analysis Template
```
For each pattern found:
1. Similarity Score (0.0-1.0)
2. Verse Reference (Book Chapter:Verse)
3. Source Attribution (D/J/E/P/R)
4. Sub-source (if available)
5. Verse Text (first 100 characters)
6. Theological Theme
7. Pattern Type (command/obedience/covenant/etc.)
```

## Example Searches

### Covenant Language
```
Search for: "covenant oath promise swear establish"
Expected results: Covenant-making language, divine promises
```

### Obedience Commands
```
Search for: "obey observe keep do perform follow"
Expected results: Command structures, obedience patterns
```

### Divine Names
```
Search for: "LORD God YHWH Elohim Adonai"
Expected results: Source-specific divine name usage
```

### Creation Patterns
```
Search for: "create make form establish beginning"
Expected results: Creation narratives, cosmogony
```

## Output Format
```json
{
  "pattern": "your search pattern",
  "total_results": 20,
  "results": [
    {
      "similarity_score": 0.575,
      "verse_reference": "Deuteronomy 18:1",
      "source": "D",
      "sub_source": "Dtr2",
      "text": "When thou shalt hearken to the voice of the LORD...",
      "theological_theme": "divine_command",
      "pattern_type": "obedience_sequence"
    }
  ],
  "source_distribution": {
    "D": 15,
    "J": 3,
    "E": 2
  },
  "analysis": "Brief theological analysis of findings"
}
```

## Advanced Features

### Multi-Collection Search
- Search across multiple collections
- Compare results between collections
- Generate cross-collection analysis

### Pattern Evolution
- Track pattern development across sources
- Analyze chronological patterns
- Identify redaction layers

### Semantic Clustering
- Group similar patterns
- Identify pattern families
- Create pattern taxonomies

## Troubleshooting

### Common Issues
1. **No results found**: Lower similarity threshold to 0.2
2. **Collection not found**: Check collection names in Qdrant
3. **Connection errors**: Verify Qdrant server is running on localhost:6333

### Performance Tips
1. Use batch processing for large searches
2. Cache embeddings for repeated patterns
3. Filter by source for faster results

## Success Metrics
- **High similarity scores** (>0.4) indicate strong pattern matches
- **Source clustering** confirms Documentary Hypothesis patterns
- **Theological coherence** validates semantic understanding
- **Pattern consistency** across similar searches

## Next Steps
1. Run the semantic search
2. Analyze results for theological insights
3. Compare with traditional text search methods
4. Document new pattern discoveries
5. Expand to other biblical books

---

**Remember**: The power of this approach lies in semantic understanding, not exact word matches. The vector database captures meaning and theological concepts that simple text search cannot find.
