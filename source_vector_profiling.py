#!/usr/bin/env python3
"""
Source Vector Profiling for Documentary Hypothesis Sources

This script creates vector profiles for each Documentary Hypothesis source (J, E, P, R)
from the Torah and finds similar sections/authors in the Book of Mormon.

Key Features:
- Extract all verses attributed to each Torah source
- Create representative embeddings for J/E/P/R sources
- Find BOM sections with similar vector profiles
- Analyze which BOM authors match which source styles
- Generate visualizations and reports

Sources in Documentary Hypothesis:
- J (Jahwist): Anthropomorphic God, southern perspective, narrative focus
- E (Elohist): More transcendent God, northern perspective, prophetic focus
- P (Priestly): Ritual and legal emphasis, genealogies, cultic details
- R (Redactor): Editorial combinations, harmonizing sources
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import os
from pathlib import Path
import json

# Documentary Hypothesis Source Definitions
SOURCE_DEFINITIONS = {
    "J": {
        "name": "Jahwist (J)",
        "description": "Anthropomorphic God depictions, southern/Judah perspective, narrative focus",
        "characteristics": ["anthropomorphic", "personal", "storytelling", "southern"],
        "color": "#000088"  # Navy Blue
    },
    "E": {
        "name": "Elohist (E)",
        "description": "More transcendent God, northern/Israel perspective, prophetic focus",
        "characteristics": ["transcendent", "northern", "prophetic", "moral"],
        "color": "#008888"  # Teal
    },
    "P": {
        "name": "Priestly (P)",
        "description": "Ritual and legal emphasis, genealogies, cultic and priestly details",
        "characteristics": ["ritual", "legal", "genealogical", "cultic"],
        "color": "#888800"  # Olive Yellow
    },
    "R": {
        "name": "Redactor (R)",
        "description": "Editorial combinations, harmonizing different sources",
        "characteristics": ["editorial", "harmonizing", "composite", "synthetic"],
        "color": "#880000"  # Maroon Red
    }
}

class SourceVectorProfiler:
    """Create and compare vector profiles for Documentary Hypothesis sources."""

    def __init__(self, qdrant_url: str = "http://localhost:6333", collection_name: str = "kjv_sources"):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.client = QdrantClient(url=qdrant_url)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.source_embeddings = {}
        self.results_dir = Path("source_profiling_results")
        self.results_dir.mkdir(exist_ok=True)

    def extract_source_passages(self, source: str, max_passages: int = 1000) -> List[str]:
        """Extract all passages attributed to a specific source from Torah."""
        print(f"🔍 Extracting passages for {SOURCE_DEFINITIONS[source]['name']} source...")

        passages = []

        try:
            # Scroll through all Torah verses
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="book_category", match=MatchValue(value="torah")),
                        FieldCondition(key="sources", match=MatchValue(value=source))
                    ]
                ),
                limit=10000,  # Get all verses for this source
                with_payload=True
            )[0]

            for result in results:
                text = result.payload.get("full_text", "").strip()
                if text:
                    passages.append(text)

            # Limit passages for computational efficiency
            passages = passages[:max_passages]
            print(f"✅ Found {len(passages)} passages for {source} source")

        except Exception as e:
            print(f"❌ Error extracting {source} source passages: {e}")
            return []

        return passages

    def create_source_profile(self, source: str) -> Optional[np.ndarray]:
        """Create a representative embedding profile for a source."""
        passages = self.extract_source_passages(source)

        if not passages:
            print(f"⚠️  No passages found for {source} source")
            return None

        print(f"🧮 Creating embedding profile for {SOURCE_DEFINITIONS[source]['name']}...")

        # Generate embeddings for all passages
        embeddings = []
        for passage in tqdm(passages, desc=f"Embedding {source} source"):
            try:
                embedding = self.model.encode(passage)
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error embedding passage for {source}: {e}")
                continue

        if not embeddings:
            return None

        # Create representative profile (average embedding)
        source_profile = np.mean(embeddings, axis=0)
        self.source_embeddings[source] = source_profile

        print(f"✅ Created {source} source profile from {len(embeddings)} passages")
        return source_profile

    def find_similar_bom_sections(self, source_profile: np.ndarray, source: str,
                                similarity_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """Find BOM sections similar to a Torah source profile."""
        print(f"🔎 Finding BOM sections similar to {SOURCE_DEFINITIONS[source]['name']}...")

        similar_sections = []

        try:
            # Get all BOM verses
            bom_results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="book_category", match=MatchValue(value="book_of_mormon"))
                    ]
                ),
                limit=10000,
                with_payload=True
            )[0]

            # Calculate similarities
            bom_embeddings = []
            bom_payloads = []

            print("📊 Computing similarities...")
            for result in tqdm(bom_results, desc="Processing BOM verses"):
                text = result.payload.get("full_text", "").strip()
                if text:
                    try:
                        embedding = self.model.encode(text)
                        bom_embeddings.append(embedding)
                        bom_payloads.append(result.payload)
                    except Exception as e:
                        continue

            if bom_embeddings:
                # Compute cosine similarities
                similarities = cosine_similarity([source_profile], bom_embeddings)[0]

                # Find similar passages above threshold
                for i, similarity in enumerate(similarities):
                    if similarity >= similarity_threshold:
                        payload = bom_payloads[i]
                        similar_sections.append({
                            "similarity": float(similarity),
                            "reference": payload.get("canonical_reference", ""),
                            "book": payload.get("book", ""),
                            "chapter": payload.get("chapter", ""),
                            "verse": payload.get("verse", ""),
                            "text": payload.get("full_text", ""),
                            "author": payload.get("author", ""),
                            "literary_style": payload.get("literary_style", "")
                        })

            # Sort by similarity (highest first)
            similar_sections.sort(key=lambda x: x["similarity"], reverse=True)

            print(f"✅ Found {len(similar_sections)} BOM passages similar to {source} source")

        except Exception as e:
            print(f"❌ Error finding similar BOM sections: {e}")

        return similar_sections[:200]  # Limit for analysis

    def analyze_bom_authors_by_source(self, source: str, similar_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze which BOM authors match each source style."""
        print(f"📈 Analyzing BOM author patterns for {SOURCE_DEFINITIONS[source]['name']}...")

        # Group by author
        author_stats = {}
        author_passages = {}

        for section in similar_sections:
            author = section.get("author", "Unknown")
            similarity = section["similarity"]

            if author not in author_stats:
                author_stats[author] = {
                    "count": 0,
                    "avg_similarity": 0.0,
                    "max_similarity": 0.0,
                    "total_similarity": 0.0
                }
                author_passages[author] = []

            author_stats[author]["count"] += 1
            author_stats[author]["total_similarity"] += similarity
            author_stats[author]["max_similarity"] = max(author_stats[author]["max_similarity"], similarity)
            author_passages[author].append(section)

        # Calculate averages
        for author in author_stats:
            author_stats[author]["avg_similarity"] = author_stats[author]["total_similarity"] / author_stats[author]["count"]

        # Sort authors by average similarity
        sorted_authors = sorted(author_stats.items(), key=lambda x: x[1]["avg_similarity"], reverse=True)

        return {
            "top_authors": sorted_authors[:10],  # Top 10 authors
            "author_details": author_passages
        }

    def create_source_comparison_heatmap(self, source_similarities: Dict[str, List[Dict[str, Any]]]):
        """Create a heatmap showing source similarities across BOM authors."""
        print("🎨 Creating source comparison heatmap...")

        # Get all unique authors
        all_authors = set()
        for source, sections in source_similarities.items():
            for section in sections:
                author = section.get("author", "Unknown")
                all_authors.add(author)

        authors = sorted(list(all_authors))
        sources = list(SOURCE_DEFINITIONS.keys())

        # Create similarity matrix
        similarity_matrix = np.zeros((len(authors), len(sources)))

        for i, author in enumerate(authors):
            for j, source in enumerate(sources):
                # Average similarity for this author-source combination
                author_sections = [s for s in source_similarities[source] if s.get("author") == author]
                if author_sections:
                    avg_similarity = np.mean([s["similarity"] for s in author_sections])
                    similarity_matrix[i, j] = avg_similarity

        # Create heatmap
        plt.figure(figsize=(12, 10))
        sns.heatmap(
            similarity_matrix,
            annot=True,
            fmt=".2f",
            xticklabels=[SOURCE_DEFINITIONS[s]["name"] for s in sources],
            yticklabels=authors,
            cmap="YlOrRd",
            cbar_kws={'label': 'Average Similarity Score'}
        )

        plt.title("BOM Author Similarity to Torah Source Styles", fontsize=16, pad=20)
        plt.xlabel("Torah Source", fontsize=12)
        plt.ylabel("BOM Author", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Save heatmap
        plt.savefig(self.results_dir / "source_author_similarity_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()

        print("✅ Saved source comparison heatmap")

    def generate_source_profile_report(self, source: str, similar_sections: List[Dict[str, Any]],
                                    author_analysis: Dict[str, Any]) -> str:
        """Generate a detailed report for a source profile."""
        report = f"""
# {SOURCE_DEFINITIONS[source]["name"]} Source Profile Analysis

## Source Characteristics
{SOURCE_DEFINITIONS[source]["description"]}

**Key Traits:** {", ".join(SOURCE_DEFINITIONS[source]["characteristics"])}

## Torah Data
- **Passages Analyzed:** {len(self.extract_source_passages(source))}
- **Source Color:** {SOURCE_DEFINITIONS[source]["color"]}

## BOM Similarity Analysis
Found {len(similar_sections)} BOM passages with similarity ≥ 0.6

### Top BOM Authors Matching {source} Style
"""

        for author, stats in author_analysis["top_authors"][:5]:
            report += f"""
- **{author}**: Average similarity {stats['avg_similarity']:.3f}
  - Passages: {stats['count']}
  - Max similarity: {stats['max_similarity']:.3f}
"""

        report += f"""

### Representative Examples
"""
        for i, section in enumerate(similar_sections[:3]):
            report += f"""
**{i+1}. {section['reference']}** (Similarity: {section['similarity']:.3f})
*{section.get('author', 'Unknown')} - {section.get('literary_style', 'Unknown')}*
"{section['text'][:200]}..."
"""

        return report

    def run_complete_analysis(self):
        """Run the complete source profiling analysis."""
        print("🚀 Starting Complete Source Vector Profiling Analysis")
        print("=" * 70)

        # Create source profiles
        source_profiles = {}
        for source in SOURCE_DEFINITIONS.keys():
            profile = self.create_source_profile(source)
            if profile is not None:
                source_profiles[source] = profile

        if not source_profiles:
            print("❌ No source profiles could be created")
            return

        # Find similar BOM sections for each source
        source_similarities = {}
        author_analyses = {}

        for source, profile in source_profiles.items():
            print(f"\n🔍 Analyzing {SOURCE_DEFINITIONS[source]['name']} similarities...")
            similar_sections = self.find_similar_bom_sections(profile, source)
            source_similarities[source] = similar_sections

            # Analyze author patterns
            author_analysis = self.analyze_bom_authors_by_source(source, similar_sections)
            author_analyses[source] = author_analysis

        # Create visualizations
        self.create_source_comparison_heatmap(source_similarities)

        # Generate comprehensive report
        print("\n📝 Generating comprehensive report...")

        full_report = "# Source Vector Profiling: Torah Sources vs Book of Mormon\n\n"
        full_report += "## Executive Summary\n\n"
        full_report += "This analysis creates vector profiles for each Documentary Hypothesis source (J, E, P, R) "
        full_report += "and identifies similar sections in the Book of Mormon. By comparing semantic embeddings, "
        full_report += "we can discover which BOM authors and sections match the literary and theological styles "
        full_report += "of ancient biblical sources.\n\n"

        # Add individual source reports
        for source in SOURCE_DEFINITIONS.keys():
            if source in source_similarities:
                report = self.generate_source_profile_report(
                    source,
                    source_similarities[source],
                    author_analyses[source]
                )
                full_report += report + "\n\n"

        # Save results
        report_path = self.results_dir / "source_profiling_complete_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(full_report)

        # Save raw data for further analysis
        results_data = {
            "source_definitions": SOURCE_DEFINITIONS,
            "source_similarities": source_similarities,
            "author_analyses": author_analyses,
            "metadata": {
                "analysis_date": pd.Timestamp.now().isoformat(),
                "embedding_model": "all-MiniLM-L6-v2",
                "similarity_threshold": 0.6,
                "max_passages_per_source": 1000
            }
        }

        data_path = self.results_dir / "source_profiling_results.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, default=str)

        print("✅ Complete analysis finished!")
        print(f"📊 Results saved to: {self.results_dir}")
        print(f"📋 Full report: {report_path}")
        print(f"🔢 Raw data: {data_path}")

        return results_data


def main():
    """Main execution function."""
    profiler = SourceVectorProfiler()
    results = profiler.run_complete_analysis()

    if results:
        print("\n🎯 Key Findings:")

        # Print top author matches for each source
        for source in SOURCE_DEFINITIONS.keys():
            if source in results["author_analyses"]:
                top_authors = results["author_analyses"][source]["top_authors"][:3]
                if top_authors:
                    author, stats = top_authors[0]
                    print(f"• {SOURCE_DEFINITIONS[source]['name']} → {author} "
                         f"(avg similarity: {stats['avg_similarity']:.3f})")


if __name__ == "__main__":
    main()
