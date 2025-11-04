#!/usr/bin/env python3
"""
Semantic Category Analysis: Torah vs Book of Mormon
==================================================

Analyzes how semantic categories (directions, elements, geography, etc.)
are represented and used across both texts through vector embeddings.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from tqdm import tqdm
import pandas as pd


# SEMANTIC CATEGORY DEFINITIONS
# Each category contains related words that represent a conceptual domain

SEMANTIC_CATEGORIES = {
    # SPATIAL ORIENTATION & DIRECTION
    "cardinal_directions": {
        "words": ["north", "south", "east", "west", "northern", "southern", "eastern", "western"],
        "description": "Cardinal directions and their derivatives"
    },
    "relative_directions": {
        "words": ["before", "behind", "above", "below", "beneath", "over", "under", "across", "beyond", "through", "within"],
        "description": "Relative spatial positioning"
    },
    "vertical_orientation": {
        "words": ["up", "down", "high", "low", "heaven", "earth", "ground", "sky", "firmament"],
        "description": "Vertical positioning and cosmic layers"
    },

    # GEOGRAPHICAL FEATURES
    "mountains_heights": {
        "words": ["mountain", "mount", "hill", "valley", "rock", "stone", "cliff", "peak", "summit"],
        "description": "Elevated landforms and geological features"
    },
    "water_bodies": {
        "words": ["river", "sea", "ocean", "water", "stream", "brook", "well", "spring", "fountain", "flood"],
        "description": "Bodies of water and hydrological features"
    },
    "landscapes": {
        "words": ["land", "country", "place", "region", "border", "boundary", "coast", "shore", "island"],
        "description": "Geographical regions and territorial divisions"
    },

    # NATURAL ELEMENTS
    "fire_flame": {
        "words": ["fire", "flame", "burn", "burning", "consume", "devour", "kindle", "blaze", "smoke"],
        "description": "Fire, combustion, and related phenomena"
    },
    "earth_soil": {
        "words": ["earth", "ground", "soil", "dust", "clay", "mud", "sand", "ashes", "dirt"],
        "description": "Earth, soil, and particulate matter"
    },
    "air_wind": {
        "words": ["wind", "breath", "spirit", "air", "blow", "breathe", "whisper", "voice"],
        "description": "Air, wind, and atmospheric phenomena"
    },
    "light_darkness": {
        "words": ["light", "dark", "darkness", "night", "day", "shadow", "bright", "shine", "glow"],
        "description": "Illumination and absence of light"
    },

    # TEMPORAL CONCEPTS
    "time_periods": {
        "words": ["day", "night", "morning", "evening", "year", "month", "week", "season", "time", "hour"],
        "description": "Units and periods of time"
    },
    "temporal_sequence": {
        "words": ["first", "last", "beginning", "end", "after", "before", "then", "now", "when", "until"],
        "description": "Temporal ordering and sequence"
    },

    # DIVINE MANIFESTATIONS
    "divine_presence": {
        "words": ["glory", "presence", "majesty", "holiness", "sacred", "divine", "godly", "heavenly"],
        "description": "Divine attributes and presence"
    },
    "divine_communication": {
        "words": ["voice", "speak", "say", "word", "command", "call", "cry", "shout", "whisper"],
        "description": "Divine speech and communication"
    },
    "divine_appearance": {
        "words": ["cloud", "pillar", "throne", "angel", "cherub", "seraph", "vision", "dream"],
        "description": "Visible manifestations of the divine"
    },

    # COVENANT & RITUAL
    "covenant_terms": {
        "words": ["covenant", "promise", "oath", "swear", "vow", "pledge", "agreement", "bond"],
        "description": "Covenantal language and commitments"
    },
    "sacrificial_terms": {
        "words": ["blood", "sacrifice", "altar", "offering", "burnt", "peace", "sin", "trespass"],
        "description": "Sacrificial and ritual terminology"
    },

    # MORAL & SPIRITUAL
    "righteousness_terms": {
        "words": ["righteous", "justice", "holy", "pure", "clean", "blessed", "faithful", "true"],
        "description": "Moral and ethical qualities"
    },
    "sin_transgression": {
        "words": ["sin", "iniquity", "transgression", "wicked", "evil", "abomination", "guilt", "punishment"],
        "description": "Sin, transgression, and moral failing"
    },

    # SPECIFIC RIVER NAMES (mentioned in both texts)
    "jordan_river": {
        "words": ["jordan", "jordan river", "river jordan"],
        "description": "Jordan River references"
    },
    "other_rivers": {
        "words": ["euphrates", "tigris", "nile", "pishon", "gihon", "hiddekel", "river", "brook", "kidron"],
        "description": "Other river and watercourse names"
    }
}


class SemanticCategoryAnalyzer:
    """Analyze semantic categories across Torah and Book of Mormon."""

    def __init__(self, qdrant_url: str = "http://localhost:6333", collection_name: str = "kjv_sources"):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.client = QdrantClient(url=qdrant_url)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.category_embeddings = {}

    def extract_category_passages(self, category_name: str, word_list: List[str],
                                book_category: str, max_passages: int = 100) -> List[str]:
        """Extract passages containing words from a semantic category."""
        passages = []

        # Get all verses for the corpus
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="book_category", match=MatchValue(value=book_category))
                ]
            ),
            limit=10000,  # Get all verses for the corpus
            with_payload=True
        )[0]

        # Filter passages that contain any word from the category
        for result in results:
            text = result.payload.get("full_text", "").lower()

            # Check if any category word appears in the text (as whole word)
            for word in word_list:
                if self._contains_word(text, word.lower()):
                    passages.append(result.payload.get("full_text", ""))
                    break  # Only add each passage once

        # Limit passages to avoid noise and computation issues
        unique_passages = list(set(passages))[:max_passages]

        print(f"Found {len(unique_passages)} passages for {category_name} ({book_category})")
        return unique_passages

    def _contains_word(self, text: str, word: str) -> bool:
        """Check if text contains word as a whole word."""
        import re
        pattern = r'\b' + re.escape(word) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def get_category_embedding(self, category_name: str, word_list: List[str],
                             book_category: str) -> Optional[np.ndarray]:
        """Get aggregated embedding for a semantic category."""
        passages = self.extract_category_passages(category_name, word_list, book_category)

        if not passages:
            print(f"No passages found for {category_name} in {book_category}")
            return None

        # Generate embeddings for all passages
        embeddings = []
        for passage in tqdm(passages, desc=f"Embedding {category_name} ({book_category})"):
            try:
                embedding = self.model.encode(passage)
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error embedding passage for {category_name}: {e}")
                continue

        if not embeddings:
            return None

        # Return average embedding
        avg_embedding = np.mean(embeddings, axis=0)
        return avg_embedding

    def analyze_all_categories(self):
        """Analyze all semantic categories for both corpora."""
        print("🔍 Analyzing Semantic Categories")
        print("=" * 60)

        for category_name, category_info in SEMANTIC_CATEGORIES.items():
            word_list = category_info["words"]
            description = category_info["description"]

            print(f"\n📖 Analyzing {category_name}: {description}")

            # Analyze Torah
            torah_embedding = self.get_category_embedding(
                category_name, word_list, "torah"
            )

            # Analyze BOM
            bom_embedding = self.get_category_embedding(
                category_name, word_list, "book_of_mormon"
            )

            # Store results
            if torah_embedding is not None:
                self.category_embeddings[f"{category_name} (Torah)"] = torah_embedding
            if bom_embedding is not None:
                self.category_embeddings[f"{category_name} (BOM)"] = bom_embedding

        print(f"\n✅ Successfully analyzed {len(self.category_embeddings)} category embeddings")

    def compute_similarity_matrix(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """Compute cosine similarity between all category pairs."""
        categories = list(self.category_embeddings.keys())
        n_cats = len(categories)

        # Initialize similarity matrix
        similarity_matrix = np.zeros((n_cats, n_cats))

        # Compute pairwise similarities
        for i in range(n_cats):
            for j in range(n_cats):
                if i == j:
                    similarity_matrix[i, j] = 1.0  # Self-similarity
                else:
                    vec1 = self.category_embeddings[categories[i]]
                    vec2 = self.category_embeddings[categories[j]]
                    similarity = cosine_similarity([vec1], [vec2])[0][0]
                    similarity_matrix[i, j] = similarity

        # Create DataFrame
        df = pd.DataFrame(
            similarity_matrix,
            index=categories,
            columns=categories
        )

        return df, similarity_matrix

    def find_most_similar_category_pairs(self, similarity_df: pd.DataFrame, top_n: int = 15) -> List[Tuple[str, str, float]]:
        """Find the most similar category pairs."""
        pairs = []

        # Only consider cross-corpus pairs (Torah vs BOM)
        torah_cats = [c for c in similarity_df.index if "(Torah)" in c]
        bom_cats = [c for c in similarity_df.index if "(BOM)" in c]

        for torah_cat in torah_cats:
            for bom_cat in bom_cats:
                similarity = similarity_df.loc[torah_cat, bom_cat]
                category_name = torah_cat.replace(" (Torah)", "")
                pairs.append((torah_cat, bom_cat, similarity))

        # Sort by similarity (descending)
        pairs.sort(key=lambda x: x[2], reverse=True)

        return pairs[:top_n]

    def analyze_category_patterns(self, similarity_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in category similarities."""
        analysis = {
            "high_similarity_pairs": [],
            "category_clusters": {},
            "usage_differences": []
        }

        similar_pairs = self.find_most_similar_category_pairs(similarity_df, 20)

        # Analyze high similarity pairs
        for torah_cat, bom_cat, similarity in similar_pairs:
            if similarity > 0.75:  # High similarity threshold
                torah_name = torah_cat.replace(" (Torah)", "")
                bom_name = bom_cat.replace(" (BOM)", "")

                # Get category descriptions
                torah_desc = SEMANTIC_CATEGORIES[torah_name]["description"]
                bom_desc = SEMANTIC_CATEGORIES[bom_name]["description"]

                analysis["high_similarity_pairs"].append({
                    "torah_category": torah_name,
                    "bom_category": bom_name,
                    "similarity": round(similarity, 3),
                    "torah_description": torah_desc,
                    "bom_description": bom_desc
                })

        # Analyze category usage patterns
        analysis["usage_differences"] = self._analyze_usage_patterns(similar_pairs)

        return analysis

    def _analyze_usage_patterns(self, similar_pairs: List[Tuple[str, str, float]]) -> List[str]:
        """Analyze how categories are used differently."""
        insights = []

        # Group by similarity ranges
        high_sim = [(t, b, s) for t, b, s in similar_pairs if s > 0.8]
        med_sim = [(t, b, s) for t, b, s in similar_pairs if 0.7 <= s <= 0.8]
        low_sim = [(t, b, s) for t, b, s in similar_pairs if s < 0.7]

        if high_sim:
            insights.append(f"🔥 {len(high_sim)} category pairs show very high similarity (>0.8)")

        if med_sim:
            insights.append(f"📊 {len(med_sim)} category pairs show moderate similarity (0.7-0.8)")

        # Check for specific patterns
        direction_pairs = [p for p in similar_pairs if 'direction' in p[0].lower() or 'direction' in p[1].lower()]
        if direction_pairs and direction_pairs[0][2] > 0.75:
            insights.append("🧭 Directional/orientation language shows strong similarity")

        water_pairs = [p for p in similar_pairs if 'water' in p[0].lower() or 'river' in p[1].lower()]
        if water_pairs and water_pairs[0][2] > 0.75:
            insights.append("🌊 Water/geography terminology shows strong similarity")

        divine_pairs = [p for p in similar_pairs if 'divine' in p[0].lower() or 'divine' in p[1].lower()]
        if divine_pairs and len(divine_pairs) >= 2:
            insights.append("✨ Divine manifestation language appears in multiple similar pairs")

        return insights

    def visualize_similarity_heatmap(self, similarity_df: pd.DataFrame, output_path: str = "semantic_categories_heatmap.png"):
        """Create a heatmap visualization of category similarities."""
        plt.figure(figsize=(18, 15))

        # Create mask for upper triangle
        mask = np.triu(np.ones_like(similarity_df, dtype=bool))

        # Create heatmap
        sns.heatmap(
            similarity_df,
            mask=mask,
            annot=False,
            cmap='RdYlBu_r',
            center=0.7,
            square=True,
            cbar_kws={'shrink': 0.8, 'label': 'Cosine Similarity'}
        )

        plt.title('Semantic Category Similarities: Torah vs Book of Mormon', fontsize=16, pad=20)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"📊 Heatmap saved to {output_path}")

    def export_results(self, similarity_df: pd.DataFrame, analysis: Dict[str, Any],
                      output_dir: str = "semantic_category_analysis"):
        """Export analysis results."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # Export similarity matrix
        similarity_df.to_csv(output_dir / "category_similarity_matrix.csv")

        # Export high similarity pairs
        if analysis["high_similarity_pairs"]:
            pairs_df = pd.DataFrame(analysis["high_similarity_pairs"])
            pairs_df.to_csv(output_dir / "high_similarity_pairs.csv", index=False)

        # Export analysis summary
        with open(output_dir / "category_analysis_summary.json", 'w') as f:
            json.dump({
                "total_categories_analyzed": len(SEMANTIC_CATEGORIES),
                "embeddings_created": len(self.category_embeddings),
                "high_similarity_pairs": analysis["high_similarity_pairs"][:10],
                "usage_patterns": analysis["usage_differences"],
                "category_definitions": SEMANTIC_CATEGORIES
            }, f, indent=2)

        print(f"📁 Results exported to {output_dir}/")


def main():
    """Main analysis execution."""
    print("🔍 Semantic Category Analysis: Torah vs Book of Mormon")
    print("=" * 70)

    analyzer = SemanticCategoryAnalyzer()

    # Analyze all semantic categories
    analyzer.analyze_all_categories()

    # Compute similarities
    print("\n🔢 Computing similarity matrix...")
    similarity_df, similarity_matrix = analyzer.compute_similarity_matrix()

    # Analyze patterns
    print("\n🔍 Analyzing usage patterns...")
    analysis = analyzer.analyze_category_patterns(similarity_df)

    # Visualize results
    print("\n📊 Creating visualizations...")
    analyzer.visualize_similarity_heatmap(similarity_df)

    # Export results
    analyzer.export_results(similarity_df, analysis)

    # Print summary
    print("\n" + "=" * 70)
    print("🎯 ANALYSIS COMPLETE")
    print("=" * 70)

    print("\n📊 Semantic Category Analysis Summary:")
    print(f"   • Total categories analyzed: {len(SEMANTIC_CATEGORIES)}")
    print(f"   • Embeddings created: {len(analyzer.category_embeddings)}")
    print(f"   • High similarity pairs (>0.8): {len([p for p in analysis['high_similarity_pairs']])}")

    print("\n🔥 Most Similar Category Pairs:")
    similar_pairs = analyzer.find_most_similar_category_pairs(similarity_df, 5)
    for i, (torah_cat, bom_cat, similarity) in enumerate(similar_pairs):
        torah_name = torah_cat.replace(" (Torah)", "")
        bom_name = bom_cat.replace(" (BOM)", "")
        print(f"   {i+1}. {torah_name} ↔ {bom_name}: {similarity:.3f}")

    print("\n💡 Key Findings:")
    for insight in analysis["usage_differences"]:
        print(f"   • {insight}")

    print("\n📁 Results saved to: semantic_category_analysis/")


if __name__ == "__main__":
    main()

