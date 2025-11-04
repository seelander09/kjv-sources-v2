#!/usr/bin/env python3
"""
Mathematical Stylometric Profiler for Documentary Hypothesis Sources

This script creates purely mathematical profiles for each Documentary Hypothesis source (J, E, P, R)
based on word frequency distributions, n-gram patterns, and statistical measures of language usage.

Key Features:
- Word frequency analysis (unigrams, bigrams, trigrams)
- Function word signatures
- Syntactic pattern analysis
- Mathematical distance metrics (KL divergence, JS distance, cosine similarity)
- Comparison of BOM authors using statistical similarity

Mathematical Approach:
- No semantic embeddings (pure statistics)
- Reproducible quantitative measurements
- Stylometric fingerprinting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Counter as CounterType
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import os
import re
import json
from pathlib import Path
from math import log, sqrt
from itertools import islice

# KJV-specific function words (most common in biblical text)
KJV_FUNCTION_WORDS = [
    'the', 'and', 'of', 'to', 'in', 'that', 'it', 'with', 'as', 'he', 'was', 'for',
    'on', 'are', 'by', 'had', 'you', 'not', 'be', 'his', 'they', 'this', 'have',
    'from', 'or', 'one', 'all', 'will', 'there', 'said', 'who', 'each', 'which',
    'their', 'time', 'if', 'them', 'no', 'so', 'when', 'what', 'out', 'up',
    'then', 'made', 'about', 'did', 'these', 'would', 'her', 'can', 'only',
    'some', 'could', 'other', 'into', 'than', 'were', 'now', 'him', 'people'
]

# KJV archaic/specific words
KJV_ARCHAIC_WORDS = [
    'thou', 'thee', 'thy', 'thine', 'thou', 'doth', 'hast', 'hath', 'shalt',
    'wilt', 'art', 'wert', 'behold', 'lo', 'unto', 'hither', 'thither',
    'whither', 'hence', 'thence', 'whence', 'wherefore', 'therefore',
    'nevertheless', 'moreover', 'furthermore', 'likewise', 'also'
]

# Punctuation marks to analyze
PUNCTUATION_MARKS = '.,;:!?()[]{}"\'—–'

class MathematicalStylometricProfiler:
    """Create mathematical profiles for sources using statistical analysis."""

    def __init__(self, qdrant_url: str = "http://localhost:6333", collection_name: str = "kjv_sources"):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.client = QdrantClient(url=qdrant_url)

        # Create results directory
        self.results_dir = Path("mathematical_stylometric_results")
        self.results_dir.mkdir(exist_ok=True)

        # Initialize profiles
        self.source_profiles = {}
        self.source_texts = {}

    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for statistical analysis."""
        if not text or not isinstance(text, str):
            return []

        # Convert to lowercase
        text = text.lower()

        # Remove punctuation but keep word boundaries
        text = re.sub(r'[^\w\s]', ' ', text)

        # Split into words and filter
        words = text.split()
        words = [w for w in words if w and len(w) > 0]

        return words

    def extract_source_texts(self, source: str, max_verses: int = 2000) -> List[str]:
        """Extract all text segments attributed to a specific source."""
        print(f"🔍 Extracting {source} source texts from Torah...")

        texts = []

        try:
            # Scroll through Torah verses attributed to this source
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="book_category", match=MatchValue(value="torah")),
                        FieldCondition(key="sources", match=MatchValue(value=source))
                    ]
                ),
                limit=max_verses,  # Limit for computational efficiency
                with_payload=True
            )[0]

            for result in results:
                # Get the full text for verses attributed to this source
                text = result.payload.get("full_text", "").strip()

                if text and len(text) > 10:  # Filter very short texts
                    texts.append(text)

            print(f"✅ Extracted {len(texts)} text segments for {source} source")
            self.source_texts[source] = texts

        except Exception as e:
            print(f"❌ Error extracting {source} source texts: {e}")
            return []

        return texts

    def create_word_frequency_profile(self, texts: List[str]) -> Dict[str, Any]:
        """Create word frequency profile for a source."""
        print("📊 Creating word frequency profile...")

        # Combine all texts
        combined_text = ' '.join(texts)

        # Preprocess
        all_words = self.preprocess_text(combined_text)
        total_words = len(all_words)

        if total_words == 0:
            return {}

        # Word frequency distribution
        word_freq = Counter(all_words)
        word_freq_dist = {word: count/total_words for word, count in word_freq.items()}

        # Most common words (top 100)
        most_common = dict(word_freq.most_common(100))

        # Vocabulary statistics
        vocab_size = len(word_freq)
        type_token_ratio = vocab_size / total_words if total_words > 0 else 0

        # Hapax legomena (words appearing only once)
        hapax_count = sum(1 for count in word_freq.values() if count == 1)
        hapax_ratio = hapax_count / vocab_size if vocab_size > 0 else 0

        # Word length distribution
        word_lengths = [len(word) for word in all_words]
        avg_word_length = np.mean(word_lengths)
        word_length_std = np.std(word_lengths)

        # Function word profile
        function_word_freq = {word: word_freq_dist.get(word, 0) for word in KJV_FUNCTION_WORDS}
        function_word_total = sum(function_word_freq.values())

        # Archaic word usage
        archaic_freq = {word: word_freq_dist.get(word, 0) for word in KJV_ARCHAIC_WORDS}
        archaic_total = sum(archaic_freq.values())

        return {
            "word_frequency": word_freq_dist,
            "most_common_words": most_common,
            "vocabulary_stats": {
                "vocab_size": vocab_size,
                "total_words": total_words,
                "type_token_ratio": type_token_ratio,
                "hapax_count": hapax_count,
                "hapax_ratio": hapax_ratio
            },
            "word_length_stats": {
                "avg_word_length": avg_word_length,
                "word_length_std": word_length_std,
                "word_lengths": word_lengths[:1000]  # Sample for analysis
            },
            "function_words": function_word_freq,
            "function_word_ratio": function_word_total,
            "archaic_words": archaic_freq,
            "archaic_ratio": archaic_total
        }

    def create_ngram_profile(self, texts: List[str], n: int = 2) -> Dict[str, float]:
        """Create n-gram frequency profile."""
        print(f"🔤 Creating {n}-gram frequency profile...")

        ngram_counter = Counter()

        for text in texts:
            words = self.preprocess_text(text)
            if len(words) >= n:
                # Generate n-grams
                ngrams = [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]
                ngram_counter.update(ngrams)

        # Convert to frequency distribution
        total_ngrams = sum(ngram_counter.values())
        ngram_freq = {ngram: count/total_ngrams for ngram, count in ngram_counter.items()}

        # Return top 200 n-grams
        return dict(ngram_counter.most_common(200))

    def create_syntactic_profile(self, texts: List[str]) -> Dict[str, Any]:
        """Create syntactic pattern profile."""
        print("📝 Creating syntactic pattern profile...")

        # Sentence analysis
        sentences = []
        for text in texts:
            # Split on sentence endings (KJV uses semicolons extensively)
            text_sentences = re.split(r'[.;:!?]+', text)
            sentences.extend([s.strip() for s in text_sentences if s.strip()])

        # Sentence length statistics
        sentence_lengths = [len(sent.split()) for sent in sentences if sent]
        avg_sentence_length = np.mean(sentence_lengths) if sentence_lengths else 0
        sentence_length_std = np.std(sentence_lengths) if sentence_lengths else 0

        # Punctuation analysis
        combined_text = ' '.join(texts)
        punctuation_freq = Counter()
        for char in combined_text:
            if char in PUNCTUATION_MARKS:
                punctuation_freq[char] += 1

        total_chars = len(combined_text)
        punctuation_dist = {char: count/total_chars for char, count in punctuation_freq.items()}

        # Capitalization patterns (KJV uses many capitals for divine names, etc.)
        capital_words = [word for text in texts for word in text.split() if word and word[0].isupper()]
        capital_ratio = len(capital_words) / sum(len(text.split()) for text in texts) if texts else 0

        return {
            "sentence_stats": {
                "avg_sentence_length": avg_sentence_length,
                "sentence_length_std": sentence_length_std,
                "total_sentences": len(sentences)
            },
            "punctuation_dist": punctuation_dist,
            "capitalization_ratio": capital_ratio,
            "sentence_lengths": sentence_lengths[:500]  # Sample
        }

    def create_source_profile(self, source: str) -> Dict[str, Any]:
        """Create complete mathematical profile for a source."""
        print(f"🧮 Creating complete mathematical profile for {source} source...")

        # Extract texts
        texts = self.extract_source_texts(source)
        if not texts:
            return {}

        # Create all profile components
        word_profile = self.create_word_frequency_profile(texts)
        bigram_profile = self.create_ngram_profile(texts, n=2)
        trigram_profile = self.create_ngram_profile(texts, n=3)
        syntactic_profile = self.create_syntactic_profile(texts)

        # Combine into complete profile
        profile = {
            "source": source,
            "total_texts": len(texts),
            "word_profile": word_profile,
            "bigram_profile": bigram_profile,
            "trigram_profile": trigram_profile,
            "syntactic_profile": syntactic_profile,
            "metadata": {
                "creation_timestamp": pd.Timestamp.now().isoformat(),
                "profile_type": "mathematical_stylometric"
            }
        }

        self.source_profiles[source] = profile
        print(f"✅ Created mathematical profile for {source} source")
        return profile

    def kullback_leibler_divergence(self, p: Dict[str, float], q: Dict[str, float]) -> float:
        """Calculate KL divergence between two probability distributions."""
        # Only consider words present in both distributions
        common_keys = set(p.keys()) & set(q.keys())

        if not common_keys:
            return float('inf')

        kl_sum = 0.0
        for key in common_keys:
            if p[key] > 0 and q[key] > 0:
                kl_sum += p[key] * log(p[key] / q[key])

        return kl_sum

    def jensen_shannon_distance(self, p: Dict[str, float], q: Dict[str, float]) -> float:
        """Calculate Jensen-Shannon distance (symmetric KL divergence)."""
        # Create combined distribution
        all_keys = set(p.keys()) | set(q.keys())
        m = {}

        for key in all_keys:
            m[key] = (p.get(key, 0) + q.get(key, 0)) / 2

        # Calculate JS distance
        kl_pm = self.kullback_leibler_divergence(p, m)
        kl_qm = self.kullback_leibler_divergence(q, m)

        return (kl_pm + kl_qm) / 2

    def cosine_similarity_freq(self, p: Dict[str, float], q: Dict[str, float]) -> float:
        """Calculate cosine similarity for frequency distributions."""
        # Get common keys
        common_keys = set(p.keys()) & set(q.keys())

        if not common_keys:
            return 0.0

        # Calculate dot product and magnitudes
        dot_product = sum(p[key] * q[key] for key in common_keys)
        p_magnitude = sqrt(sum(val**2 for val in p.values()))
        q_magnitude = sqrt(sum(val**2 for val in q.values()))

        if p_magnitude == 0 or q_magnitude == 0:
            return 0.0

        return dot_product / (p_magnitude * q_magnitude)

    def compare_profiles(self, profile1: Dict[str, Any], profile2: Dict[str, Any]) -> Dict[str, float]:
        """Compare two mathematical profiles using multiple distance metrics."""
        similarities = {}

        # Word frequency comparison
        if "word_profile" in profile1 and "word_profile" in profile2:
            p_freq = profile1["word_profile"].get("word_frequency", {})
            q_freq = profile2["word_profile"].get("word_frequency", {})

            similarities["word_freq_cosine"] = self.cosine_similarity_freq(p_freq, q_freq)
            similarities["word_freq_js_distance"] = self.jensen_shannon_distance(p_freq, q_freq)

        # Function word comparison
        if "word_profile" in profile1 and "word_profile" in profile2:
            p_func = profile1["word_profile"].get("function_words", {})
            q_func = profile2["word_profile"].get("function_words", {})

            similarities["function_words_cosine"] = self.cosine_similarity_freq(p_func, q_func)
            similarities["function_words_js_distance"] = self.jensen_shannon_distance(p_func, q_func)

        # Archaic word comparison
        if "word_profile" in profile1 and "word_profile" in profile2:
            p_archaic = profile1["word_profile"].get("archaic_words", {})
            q_archaic = profile2["word_profile"].get("archaic_words", {})

            similarities["archaic_words_cosine"] = self.cosine_similarity_freq(p_archaic, q_archaic)

        # Syntactic comparison (sentence length)
        if "syntactic_profile" in profile1 and "syntactic_profile" in profile2:
            p_sent_len = profile1["syntactic_profile"]["sentence_stats"]["avg_sentence_length"]
            q_sent_len = profile2["syntactic_profile"]["sentence_stats"]["avg_sentence_length"]

            # Normalize sentence length difference
            max_sent_len = max(abs(p_sent_len), abs(q_sent_len), 1)
            similarities["sentence_length_similarity"] = 1 - abs(p_sent_len - q_sent_len) / max_sent_len

        return similarities

    def extract_bom_author_profile(self, author: str) -> Dict[str, Any]:
        """Extract mathematical profile for a BOM author."""
        print(f"📖 Extracting mathematical profile for BOM author: {author}")

        texts = []

        try:
            # Get all verses by this author
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="book_category", match=MatchValue(value="book_of_mormon")),
                        FieldCondition(key="author", match=MatchValue(value=author))
                    ]
                ),
                limit=5000,  # Get substantial sample
                with_payload=True
            )[0]

            for result in results:
                text = result.payload.get("full_text", "").strip()
                if text:
                    texts.append(text)

        except Exception as e:
            print(f"❌ Error extracting {author} texts: {e}")
            return {}

        if not texts:
            return {}

        # Create mathematical profile using same methods as sources
        word_profile = self.create_word_frequency_profile(texts)
        bigram_profile = self.create_ngram_profile(texts, n=2)
        syntactic_profile = self.create_syntactic_profile(texts)

        return {
            "author": author,
            "total_texts": len(texts),
            "word_profile": word_profile,
            "bigram_profile": bigram_profile,
            "syntactic_profile": syntactic_profile,
            "metadata": {
                "corpus": "book_of_mormon",
                "creation_timestamp": pd.Timestamp.now().isoformat(),
                "profile_type": "mathematical_stylometric"
            }
        }

    def create_similarity_matrix(self, source_profiles: Dict[str, Dict],
                               bom_profiles: Dict[str, Dict]) -> pd.DataFrame:
        """Create similarity matrix between sources and BOM authors."""
        print("📊 Creating similarity matrix...")

        results = []

        for source_name, source_profile in source_profiles.items():
            for author_name, author_profile in bom_profiles.items():
                similarities = self.compare_profiles(source_profile, author_profile)

                result = {
                    "source": source_name,
                    "bom_author": author_name,
                    "word_freq_cosine": similarities.get("word_freq_cosine", 0),
                    "word_freq_js_distance": similarities.get("word_freq_js_distance", 0),
                    "function_words_cosine": similarities.get("function_words_cosine", 0),
                    "function_words_js_distance": similarities.get("function_words_js_distance", 0),
                    "archaic_words_cosine": similarities.get("archaic_words_cosine", 0),
                    "sentence_length_similarity": similarities.get("sentence_length_similarity", 0)
                }

                # Calculate composite similarity score
                weights = {
                    "word_freq_cosine": 0.3,
                    "function_words_cosine": 0.3,
                    "archaic_words_cosine": 0.2,
                    "sentence_length_similarity": 0.2
                }

                composite_score = sum(
                    result[metric] * weight for metric, weight in weights.items()
                    if metric in result and not np.isnan(result[metric])
                )

                result["composite_similarity"] = composite_score
                results.append(result)

        return pd.DataFrame(results)

    def create_similarity_heatmap(self, similarity_df: pd.DataFrame):
        """Create heatmap visualization of similarities."""
        print("🎨 Creating similarity heatmap...")

        # Pivot for heatmap
        heatmap_data = similarity_df.pivot(
            index="bom_author",
            columns="source",
            values="composite_similarity"
        )

        # Create heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt=".3f",
            cmap="YlOrRd",
            cbar_kws={'label': 'Composite Similarity Score'},
            vmin=0,
            vmax=1
        )

        plt.title("Mathematical Stylometric Similarity: Torah Sources vs BOM Authors", fontsize=14, pad=20)
        plt.xlabel("Torah Source", fontsize=12)
        plt.ylabel("BOM Author", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Save heatmap
        plt.savefig(self.results_dir / "mathematical_stylometric_similarity_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()

        print("✅ Saved mathematical similarity heatmap")

    def generate_mathematical_report(self, similarity_df: pd.DataFrame,
                                   source_profiles: Dict[str, Dict],
                                   bom_profiles: Dict[str, Dict]) -> str:
        """Generate comprehensive mathematical analysis report."""
        report = "# Mathematical Stylometric Profiling Report\n\n"
        report += "## Executive Summary\n\n"
        report += "This analysis creates purely mathematical profiles for each Documentary Hypothesis source "
        report += "based on word frequency distributions, n-gram patterns, and statistical measures of language usage. "
        report += "No semantic embeddings are used - only quantitative statistical patterns.\n\n"

        # Source profiles summary
        report += "## Source Profiles Summary\n\n"
        for source, profile in source_profiles.items():
            if profile:
                vocab_stats = profile["word_profile"]["vocabulary_stats"]
                report += f"### {source} Source\n"
                report += f"- Texts analyzed: {profile['total_texts']}\n"
                report += f"- Total words: {vocab_stats['total_words']:,}\n"
                report += f"- Vocabulary size: {vocab_stats['vocab_size']:,}\n"
                report += f"- Type-token ratio: {vocab_stats['type_token_ratio']:.3f}\n"
                report += f"- Function word ratio: {profile['word_profile']['function_word_ratio']:.3f}\n"
                report += f"- Archaic word ratio: {profile['word_profile']['archaic_ratio']:.3f}\n\n"

        # Top similarities
        report += "## Top Mathematical Similarities\n\n"

        # Sort by composite similarity
        top_similarities = similarity_df.nlargest(20, "composite_similarity")

        for _, row in top_similarities.iterrows():
            report += f"### {row['source']} Source ↔ {row['bom_author']}\n"
            report += f"- Composite similarity: {row['composite_similarity']:.3f}\n"
            report += f"- Word frequency cosine: {row['word_freq_cosine']:.3f}\n"
            report += f"- Function words cosine: {row['function_words_cosine']:.3f}\n"
            report += f"- Archaic words cosine: {row['archaic_words_cosine']:.3f}\n"
            report += f"- Sentence length similarity: {row['sentence_length_similarity']:.3f}\n\n"

        # Mathematical methodology
        report += "## Mathematical Methodology\n\n"
        report += "### Distance Metrics Used:\n"
        report += "1. **Cosine Similarity**: Measures angle between frequency vectors\n"
        report += "2. **Jensen-Shannon Distance**: Symmetric KL divergence for probability distributions\n"
        report += "3. **Sentence Length Similarity**: Normalized difference in average sentence lengths\n\n"

        report += "### Features Analyzed:\n"
        report += "- Word frequency distributions (unigrams)\n"
        report += "- Function word usage patterns\n"
        report += "- Archaic KJV word frequencies\n"
        report += "- Bigram and trigram patterns\n"
        report += "- Syntactic patterns (sentence length, punctuation)\n"
        report += "- Capitalization patterns\n\n"

        return report

    def run_complete_mathematical_analysis(self):
        """Run the complete mathematical stylometric analysis."""
        print("🔢 Starting Complete Mathematical Stylometric Analysis")
        print("=" * 70)

        # Create source profiles
        source_profiles = {}
        sources = ["J", "E", "P", "R"]

        for source in sources:
            profile = self.create_source_profile(source)
            if profile:
                source_profiles[source] = profile

        if not source_profiles:
            print("❌ No source profiles could be created")
            return

        # Extract BOM author profiles
        bom_authors = ["Nephi", "Jacob", "Enos", "Jarom", "Omni", "Amaleki", "King Benjamin",
                      "Mosiah", "Alma", "Helaman", "Mormon", "Moroni"]

        bom_profiles = {}
        for author in bom_authors:
            profile = self.extract_bom_author_profile(author)
            if profile:
                bom_profiles[author] = profile

        # Create similarity matrix
        similarity_df = self.create_similarity_matrix(source_profiles, bom_profiles)

        # Create visualizations
        self.create_similarity_heatmap(similarity_df)

        # Generate report
        print("\n📝 Generating mathematical analysis report...")
        report = self.generate_mathematical_report(similarity_df, source_profiles, bom_profiles)

        # Save results
        report_path = self.results_dir / "mathematical_stylometric_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        # Save raw data (with tuple key handling for JSON)
        def convert_tuples(obj):
            """Convert tuple keys to string keys for JSON serialization."""
            if isinstance(obj, dict):
                return {str(k) if isinstance(k, tuple) else k: convert_tuples(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_tuples(item) for item in obj]
            else:
                return obj

        results_data = {
            "source_profiles": convert_tuples(source_profiles),
            "bom_profiles": convert_tuples(bom_profiles),
            "similarity_matrix": similarity_df.to_dict('records'),
            "metadata": {
                "analysis_date": pd.Timestamp.now().isoformat(),
                "methodology": "mathematical_stylometric",
                "distance_metrics": ["cosine_similarity", "js_distance", "sentence_length_similarity"],
                "features_analyzed": ["word_freq", "function_words", "archaic_words", "syntactic_patterns"]
            }
        }

        data_path = self.results_dir / "mathematical_stylometric_results.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, default=str)

        print("✅ Complete mathematical analysis finished!")
        print(f"📊 Results saved to: {self.results_dir}")
        print(f"📋 Full report: {report_path}")
        print(f"🔢 Raw data: {data_path}")

        # Print key findings
        print("\n🎯 Key Mathematical Findings:")
        top_matches = similarity_df.nlargest(5, "composite_similarity")
        for _, row in top_matches.iterrows():
            print(".3f"
                  ".3f")

        return results_data


def main():
    """Main execution function."""
    profiler = MathematicalStylometricProfiler()
    results = profiler.run_complete_mathematical_analysis()

    if results:
        print("\n🔬 Mathematical Stylometric Analysis Complete!")
        print("This provides purely statistical, reproducible measurements")
        print("of linguistic patterns without semantic interpretation.")


if __name__ == "__main__":
    main()
