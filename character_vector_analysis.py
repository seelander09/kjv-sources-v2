#!/usr/bin/env python3
"""
Character Vector Analysis: Torah vs Book of Mormon
==================================================

Analyzes semantic similarities between characters in the Torah and Book of Mormon
by comparing their vector embeddings based on how they're portrayed in the texts.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from tqdm import tqdm
import pandas as pd


# Character definitions - both major and peripheral
TORAH_CHARACTERS = {
    # Major characters
    "Moses": ["moses", "moses'", "moses's"],
    "Abraham": ["abraham", "abram"],
    "Isaac": ["isaac"],
    "Jacob": ["jacob", "israel"],
    "Joseph": ["joseph"],
    "Aaron": ["aaron"],
    "Miriam": ["miriam"],
    "Joshua": ["joshua"],
    "Noah": ["noah"],
    "Adam": ["adam"],
    "Eve": ["eve"],

    # Peripheral characters
    "Sarah": ["sarah", "sarah's"],
    "Rebekah": ["rebekah"],
    "Rachel": ["rachel"],
    "Leah": ["leah"],
    "Laban": ["laban"],
    "Pharaoh": ["pharaoh", "pharaoh's"],
    "Potiphar": ["potiphar"],
    "Reuben": ["reuben"],
    "Simeon": ["simeon"],
    "Levi": ["levi"],
    "Judah": ["judah"],
    "Dan": ["dan"],
    "Naphtali": ["naphtali"],
    "Gad": ["gad"],
    "Asher": ["asher"],
    "Issachar": ["issachar"],
    "Zebulun": ["zebulun"],
    "Benjamin": ["benjamin"],
    "Korah": ["korah"],
    "Dathan": ["dathan"],
    "Abiram": ["abiram"],
    "Cain": ["cain"],
    "Abel": ["abel"],
    "Seth": ["seth"],
    "Enosh": ["enosh"],
    "Enoch": ["enoch"]
}

BOM_CHARACTERS = {
    # Major characters
    "Nephi": ["nephi", "nephi's"],
    "Lehi": ["lehi", "lehi's"],
    "Laman": ["laman"],
    "Lemuel": ["lemuel"],
    "Sam": ["sam"],
    "Alma": ["alma"],
    "Helaman": ["helaman"],
    "Mormon": ["mormon"],
    "Moroni": ["moroni"],
    "Jesus": ["jesus", "christ", "savior"],
    "God": ["god", "lord", "father"],

    # Peripheral characters
    "Sariah": ["sariah"],
    "Ishmael": ["ishmael"],
    "Zoram": ["zoram"],
    "King Noah": ["noah", "king noah"],
    "Abinadi": ["abinadi"],
    "Ammon": ["ammon"],
    "Zeniff": ["zeniff"],
    "Limhi": ["limhi"],
    "Mosiah": ["mosiah"],
    "Benjamin": ["benjamin"],  # Note: Also in Torah
    "Zenock": ["zenock"],
    "Zenos": ["zenos"],
    "Ezias": ["ezias"],
    "Isaiah": ["isaiah"],  # Quoted prophet
    "Ether": ["ether"],
    "Jared": ["jared"],
    "Mahonri": ["mahonri"],
    "Coriantor": ["coriantor"],
    "Com": ["com"],
    "Shiblom": ["shiblom"],
    "Coriantumr": ["coriantumr"]
}


class CharacterVectorAnalyzer:
    """Analyze semantic similarities between biblical characters using vector embeddings."""

    def __init__(self, qdrant_url: str = "http://localhost:6333", collection_name: str = "kjv_sources"):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.client = QdrantClient(url=qdrant_url)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.character_embeddings = {}

    def extract_character_passages(self, character_name: str, search_terms: List[str],
                                 book_category: str, max_passages: int = 50) -> List[str]:
        """Extract passages mentioning a character using proper text search."""
        passages = []

        for term in search_terms:
            try:
                # Use scroll to get ALL verses, then filter for the term
                # This is inefficient but necessary since Qdrant text search is limited
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

                # Filter passages that contain the search term as a whole word
                for result in results:
                    text = result.payload.get("full_text", "").lower()
                    # Check for whole word matches to avoid false positives
                    term_lower = term.lower()
                    if self._contains_word(text, term_lower):
                        passages.append(result.payload.get("full_text", ""))

                if len(passages) >= max_passages:
                    break  # Found enough passages

            except Exception as e:
                print(f"Error searching for {character_name} with term '{term}': {e}")
                continue

        # Remove duplicates and limit
        unique_passages = list(set(passages))[:max_passages]
        print(f"Found {len(unique_passages)} passages for {character_name} ({book_category})")
        return unique_passages

    def _contains_word(self, text: str, word: str) -> bool:
        """Check if text contains word as a whole word (not part of another word)."""
        import re
        # Use word boundaries to ensure whole word matches
        pattern = r'\b' + re.escape(word) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def get_character_embedding(self, character_name: str, search_terms: List[str],
                              book_category: str) -> Optional[np.ndarray]:
        """Get aggregated embedding for a character."""
        passages = self.extract_character_passages(character_name, search_terms, book_category)

        if not passages:
            print(f"No passages found for {character_name}")
            return None

        # Generate embeddings for all passages
        embeddings = []
        for passage in tqdm(passages, desc=f"Embedding {character_name}"):
            try:
                embedding = self.model.encode(passage)
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error embedding passage for {character_name}: {e}")
                continue

        if not embeddings:
            return None

        # Return average embedding
        avg_embedding = np.mean(embeddings, axis=0)
        return avg_embedding

    def analyze_all_characters(self):
        """Analyze all characters from both corpora."""
        print("🔍 Analyzing Character Vectors")
        print("=" * 60)

        # Analyze Torah characters
        print("\n📖 Analyzing Torah Characters...")
        for char_name, search_terms in TORAH_CHARACTERS.items():
            embedding = self.get_character_embedding(char_name, search_terms, "torah")
            if embedding is not None:
                self.character_embeddings[f"{char_name} (Torah)"] = embedding

        # Analyze BOM characters
        print("\n📚 Analyzing Book of Mormon Characters...")
        for char_name, search_terms in BOM_CHARACTERS.items():
            embedding = self.get_character_embedding(char_name, search_terms, "book_of_mormon")
            if embedding is not None:
                self.character_embeddings[f"{char_name} (BOM)"] = embedding

        print(f"\n✅ Successfully analyzed {len(self.character_embeddings)} characters")

    def compute_similarity_matrix(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """Compute cosine similarity between all character pairs."""
        characters = list(self.character_embeddings.keys())
        n_chars = len(characters)

        # Initialize similarity matrix
        similarity_matrix = np.zeros((n_chars, n_chars))

        # Compute pairwise similarities
        for i in range(n_chars):
            for j in range(n_chars):
                if i == j:
                    similarity_matrix[i, j] = 1.0  # Self-similarity
                else:
                    vec1 = self.character_embeddings[characters[i]]
                    vec2 = self.character_embeddings[characters[j]]
                    similarity = cosine_similarity([vec1], [vec2])[0][0]
                    similarity_matrix[i, j] = similarity

        # Create DataFrame
        df = pd.DataFrame(
            similarity_matrix,
            index=characters,
            columns=characters
        )

        return df, similarity_matrix

    def find_most_similar_pairs(self, similarity_df: pd.DataFrame, top_n: int = 10) -> List[Tuple[str, str, float]]:
        """Find the most similar character pairs."""
        pairs = []

        # Only consider cross-corpus pairs (Torah vs BOM)
        torah_chars = [c for c in similarity_df.index if "(Torah)" in c]
        bom_chars = [c for c in similarity_df.index if "(BOM)" in c]

        for torah_char in torah_chars:
            for bom_char in bom_chars:
                similarity = similarity_df.loc[torah_char, bom_char]
                pairs.append((torah_char, bom_char, similarity))

        # Sort by similarity (descending)
        pairs.sort(key=lambda x: x[2], reverse=True)

        return pairs[:top_n]

    def visualize_similarity_heatmap(self, similarity_df: pd.DataFrame, output_path: str = "character_similarity_heatmap.png"):
        """Create a heatmap visualization of character similarities."""
        plt.figure(figsize=(16, 14))

        # Create mask for upper triangle
        mask = np.triu(np.ones_like(similarity_df, dtype=bool))

        # Create heatmap
        sns.heatmap(
            similarity_df,
            mask=mask,
            annot=False,
            cmap='RdYlBu_r',
            center=0.5,
            square=True,
            cbar_kws={'shrink': 0.8, 'label': 'Cosine Similarity'}
        )

        plt.title('Character Vector Similarities: Torah vs Book of Mormon', fontsize=16, pad=20)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"📊 Heatmap saved to {output_path}")

    def create_cross_corpus_analysis(self, similarity_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze similarities between Torah and BOM characters."""
        analysis = {
            "most_similar_pairs": [],
            "torah_character_clusters": {},
            "bom_character_clusters": {},
            "interesting_findings": []
        }

        # Find most similar cross-corpus pairs
        similar_pairs = self.find_most_similar_pairs(similarity_df, top_n=20)
        analysis["most_similar_pairs"] = similar_pairs

        # Analyze character roles/types
        torah_chars = {k: v for k, v in self.character_embeddings.items() if "(Torah)" in k}
        bom_chars = {k: v for k, v in self.character_embeddings.items() if "(BOM)" in k}

        # Group by similarity patterns
        analysis["interesting_findings"] = self._analyze_character_patterns(similar_pairs)

        return analysis

    def _analyze_character_patterns(self, similar_pairs: List[Tuple[str, str, float]]) -> List[str]:
        """Analyze patterns in character similarities."""
        findings = []

        # Look for specific interesting pairs
        for torah_char, bom_char, similarity in similar_pairs:
            if similarity > 0.6:  # High similarity threshold
                # Remove corpus labels for cleaner names
                torah_name = torah_char.replace(" (Torah)", "")
                bom_name = bom_char.replace(" (BOM)", "")

                if torah_name == "Moses" and bom_name == "Nephi":
                    findings.append(f"🕊️ Moses & Nephi: {similarity:.3f} - Both prophets who receive divine calls and lead people through challenges")
                elif torah_name == "Abraham" and bom_name == "Lehi":
                    findings.append(f"🏛️ Abraham & Lehi: {similarity:.3f} - Both patriarchs who leave homeland for promised land with covenants")
                elif torah_name == "Joseph" and bom_name in ["Nephi", "Alma"]:
                    findings.append(f"👑 Joseph & {bom_name}: {similarity:.3f} - Both face betrayal but rise to leadership")
                elif torah_name in ["Cain", "Abel"] and bom_name in ["Laman", "Lemuel"]:
                    findings.append(f"👥 Cain/Abel & Laman/Lemuel: {similarity:.3f} - Both represent sibling conflict and division")
                elif torah_name == "Aaron" and bom_name == "Alma":
                    findings.append(f"⛪ Aaron & Alma: {similarity:.3f} - Both serve in priestly/religious leadership roles")

        # General findings
        if any(s > 0.65 for _, _, s in similar_pairs):
            findings.append("🔥 Strong similarities found between prophet/leaders across texts")

        if len([s for _, _, s in similar_pairs if s > 0.5]) > 5:
            findings.append("📚 Significant overlap in character archetypes between ancient Near Eastern and American texts")

        return findings

    def export_results(self, similarity_df: pd.DataFrame, analysis: Dict[str, Any],
                      output_dir: str = "character_analysis_results"):
        """Export analysis results to files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # Export similarity matrix
        similarity_df.to_csv(output_dir / "character_similarity_matrix.csv")

        # Export most similar pairs
        pairs_data = []
        for torah_char, bom_char, similarity in analysis["most_similar_pairs"]:
            pairs_data.append({
                "torah_character": torah_char,
                "bom_character": bom_char,
                "similarity": round(similarity, 4)
            })

        pd.DataFrame(pairs_data).to_csv(output_dir / "most_similar_pairs.csv", index=False)

        # Export analysis summary
        with open(output_dir / "analysis_summary.json", 'w') as f:
            json.dump({
                "total_characters_analyzed": len(self.character_embeddings),
                "torah_characters": len([k for k in self.character_embeddings.keys() if "(Torah)" in k]),
                "bom_characters": len([k for k in self.character_embeddings.keys() if "(BOM)" in k]),
                "most_similar_pairs": analysis["most_similar_pairs"][:10],  # Top 10
                "interesting_findings": analysis["interesting_findings"]
            }, f, indent=2)

        print(f"📁 Results exported to {output_dir}/")


def main():
    """Main analysis execution."""
    print("🎭 Character Vector Analysis: Torah vs Book of Mormon")
    print("=" * 70)

    analyzer = CharacterVectorAnalyzer()

    # Analyze all characters
    analyzer.analyze_all_characters()

    # Compute similarities
    print("\n🔢 Computing similarity matrix...")
    similarity_df, similarity_matrix = analyzer.compute_similarity_matrix()

    # Create cross-corpus analysis
    print("\n🔍 Analyzing cross-corpus patterns...")
    analysis = analyzer.create_cross_corpus_analysis(similarity_df)

    # Visualize results
    print("\n📊 Creating visualizations...")
    analyzer.visualize_similarity_heatmap(similarity_df)

    # Export results
    analyzer.export_results(similarity_df, analysis)

    # Print summary
    print("\n" + "=" * 70)
    print("🎯 ANALYSIS COMPLETE")
    print("=" * 70)

    print("\n📊 Character Analysis Summary:")
    print(f"   • Total characters analyzed: {len(analyzer.character_embeddings)}")
    print(f"   • Torah characters: {len([k for k in analyzer.character_embeddings.keys() if '(Torah)' in k])}")
    print(f"   • BOM characters: {len([k for k in analyzer.character_embeddings.keys() if '(BOM)' in k])}")

    print("\n🔥 Most Similar Character Pairs:")
    for i, (torah_char, bom_char, similarity) in enumerate(analysis["most_similar_pairs"][:5]):
        print(f"   {i+1}. {torah_char} ↔ {bom_char}: {similarity:.3f}")

    print("\n💡 Key Findings:")
    for finding in analysis["interesting_findings"]:
        print(f"   • {finding}")

    print("\n📁 Results saved to: character_analysis_results/")


if __name__ == "__main__":
    main()

