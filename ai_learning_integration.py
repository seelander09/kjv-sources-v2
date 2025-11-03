#!/usr/bin/env python3
"""
AI Learning System Integration
==============================

Integrates the AI learning system with the existing KJV Sources pipeline.
Enables pattern recognition, comparative analysis, and continuous learning.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Import components
try:
    from train_torah_source_model import TorahFeatureExtractor, TorahSourceModelTrainer
    from expand_bible_framework import BibleExpansionFramework, ExpandedVerseData
    from src.kjv_sources.qdrant_client import KJVQdrantClient, create_qdrant_client
except ImportError as e:
    print(f"Warning: Could not import some components: {e}")


@dataclass
class PatternMatch:
    """Represents a pattern match between Torah and other books"""
    torah_reference: str
    comparison_reference: str
    source: str
    pattern_name: str
    similarity: float
    confidence: float
    feature_matches: Dict[str, float]
    discovered_date: str


@dataclass
class ComparisonReport:
    """Report comparing Torah sources with other books"""
    torah_source: str
    comparison_book: str
    total_matches: int
    pattern_matches: List[PatternMatch]
    average_similarity: float
    theological_continuity: Dict[str, float]
    source_influence_score: float
    generated_date: str


class AILearningIntegration:
    """Main integration class for AI learning system"""
    
    def __init__(self):
        self.output_dir = Path('output/ai_analysis')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.feature_extractor = TorahFeatureExtractor() if 'TorahFeatureExtractor' in globals() else None
        self.model_trainer = None
        self.expansion_framework = None
        self.qdrant_client = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components"""
        print("🔧 Initializing AI Learning System components...")
        
        # Load model trainer
        if 'TorahSourceModelTrainer' in globals():
            try:
                self.model_trainer = TorahSourceModelTrainer()
                model_path = Path('models/torah_source_classifier.pkl')
                if model_path.exists():
                    self.model_trainer.load_model()
                    print("   ✅ Loaded trained source classification model")
                else:
                    print("   ⚠️  Model not found. Train model first using train_torah_source_model.py")
            except Exception as e:
                print(f"   ⚠️  Could not load model: {e}")
        
        # Initialize expansion framework
        if 'BibleExpansionFramework' in globals():
            try:
                self.expansion_framework = BibleExpansionFramework()
                print("   ✅ Initialized Bible expansion framework")
            except Exception as e:
                print(f"   ⚠️  Could not initialize framework: {e}")
        
        # Initialize Qdrant client
        try:
            self.qdrant_client = create_qdrant_client(use_local=True)
            print("   ✅ Connected to Qdrant vector database")
        except Exception as e:
            print(f"   ⚠️  Could not connect to Qdrant: {e}")
        
        print("✅ Component initialization complete\n")
    
    def identify_torah_patterns_in_book(self, book_name: str, 
                                        threshold: float = 0.7) -> List[PatternMatch]:
        """
        Identify Torah source patterns in any biblical book.
        
        Args:
            book_name: Name of book to analyze
            threshold: Minimum similarity threshold
        
        Returns:
            List of pattern matches
        """
        print(f"🔍 Identifying Torah patterns in {book_name}...")
        
        if not self.model_trainer or not self.model_trainer.trained:
            print("❌ Model not trained. Please train model first.")
            return []
        
        if not self.qdrant_client:
            print("❌ Qdrant client not available.")
            return []
        
        # Get verses from book
        try:
            results = self.qdrant_client.client.scroll(
                collection_name=self.qdrant_client.collection_name,
                limit=10000,
                with_payload=True
            )[0]
            
            book_verses = [
                r for r in results 
                if r.payload.get('book', '').lower() == book_name.lower()
            ]
        except Exception as e:
            print(f"❌ Error loading verses: {e}")
            return []
        
        if not book_verses:
            print(f"⚠️  No verses found for {book_name}")
            return []
        
        # Get Torah source examples for comparison
        torah_examples = self._get_torah_source_examples()
        
        matches = []
        for verse_result in book_verses:
            verse_data = {
                'book': verse_result.payload.get('book', ''),
                'chapter': verse_result.payload.get('chapter', 0),
                'verse': verse_result.payload.get('verse', 0),
                'text': verse_result.payload.get('text', ''),
                'sources': verse_result.payload.get('sources', '')
            }
            
            # Extract features
            if self.feature_extractor:
                verse_features = self.feature_extractor.extract(verse_data)
                
                # Compare with Torah patterns
                for source, examples in torah_examples.items():
                    for torah_example in examples:
                        similarity = self._calculate_similarity(
                            verse_features, torah_example['features']
                        )
                        
                        if similarity >= threshold:
                            matches.append(PatternMatch(
                                torah_reference=torah_example['reference'],
                                comparison_reference=f"{book_name} {verse_data['chapter']}:{verse_data['verse']}",
                                source=source,
                                pattern_name=f"{source}_pattern",
                                similarity=similarity,
                                confidence=similarity,
                                feature_matches={
                                    'vocabulary': verse_features.vocabulary_features.get(source, 0),
                                    'theological': verse_features.theological_features.get(source, 0),
                                    'style': verse_features.style_features.get(source, 0),
                                    'structural': verse_features.structural_features.get(source, 0)
                                },
                                discovered_date=datetime.now().isoformat()
                            ))
        
        print(f"✅ Found {len(matches)} pattern matches in {book_name}")
        return matches
    
    def _get_torah_source_examples(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get example verses from each Torah source"""
        if not self.qdrant_client:
            return {}
        
        examples = {}
        sources = ['J', 'E', 'P', 'D', 'R']
        torah_books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
        
        try:
            results = self.qdrant_client.client.scroll(
                collection_name=self.qdrant_client.collection_name,
                limit=10000,
                with_payload=True
            )[0]
            
            for source in sources:
                source_verses = [
                    r for r in results
                    if r.payload.get('book') in torah_books and
                    source in str(r.payload.get('sources', ''))
                ][:10]  # Get 10 examples per source
                
                examples[source] = []
                for verse_result in source_verses:
                    verse_data = {
                        'book': verse_result.payload.get('book', ''),
                        'chapter': verse_result.payload.get('chapter', 0),
                        'verse': verse_result.payload.get('verse', 0),
                        'text': verse_result.payload.get('text', ''),
                        'sources': verse_result.payload.get('sources', '')
                    }
                    
                    if self.feature_extractor:
                        features = self.feature_extractor.extract(verse_data)
                        examples[source].append({
                            'reference': f"{verse_data['book']} {verse_data['chapter']}:{verse_data['verse']}",
                            'verse_data': verse_data,
                            'features': features
                        })
        except Exception as e:
            print(f"⚠️  Error getting Torah examples: {e}")
        
        return examples
    
    def _calculate_similarity(self, features1, features2) -> float:
        """Calculate similarity between two feature vectors"""
        if not isinstance(features1, type(features2)):
            return 0.0
        
        # Weighted similarity
        weights = {
            'vocabulary': 0.3,
            'theological': 0.3,
            'style': 0.2,
            'structural': 0.2
        }
        
        similarity = 0.0
        
        # Vocabulary similarity
        vocab_sim = self._dict_similarity(
            features1.vocabulary_features,
            features2.vocabulary_features
        )
        similarity += vocab_sim * weights['vocabulary']
        
        # Theological similarity
        theme_sim = self._dict_similarity(
            features1.theological_features,
            features2.theological_features
        )
        similarity += theme_sim * weights['theological']
        
        # Style similarity
        style_sim = self._dict_similarity(
            features1.style_features,
            features2.style_features
        )
        similarity += style_sim * weights['style']
        
        # Structural similarity
        struct_sim = self._dict_similarity(
            features1.structural_features,
            features2.structural_features
        )
        similarity += struct_sim * weights['structural']
        
        return similarity
    
    def _dict_similarity(self, dict1: Dict, dict2: Dict) -> float:
        """Calculate similarity between two dictionaries"""
        keys = set(dict1.keys()) | set(dict2.keys())
        if not keys:
            return 0.0
        
        sum_sq_diff = sum((dict1.get(k, 0) - dict2.get(k, 0))**2 for k in keys)
        return 1.0 / (1.0 + sum_sq_diff)
    
    def compare_torah_with_book(self, torah_source: str, 
                                comparison_book: str) -> ComparisonReport:
        """
        Compare how a Torah source appears in another book.
        
        Args:
            torah_source: Source code (J, E, P, D, R)
            comparison_book: Book name to compare with
        
        Returns:
            ComparisonReport with analysis results
        """
        print(f"📊 Comparing {torah_source} source with {comparison_book}...")
        
        # Get pattern matches
        matches = self.identify_torah_patterns_in_book(comparison_book, threshold=0.6)
        source_matches = [m for m in matches if m.source == torah_source]
        
        # Calculate statistics
        avg_similarity = sum(m.similarity for m in source_matches) / len(source_matches) if source_matches else 0.0
        
        # Calculate theological continuity
        theological_continuity = {}
        for match in source_matches:
            for theme, score in match.feature_matches.items():
                if theme == 'theological':
                    theological_continuity[torah_source] = theological_continuity.get(torah_source, 0) + score
        
        # Normalize
        if theological_continuity:
            max_score = max(theological_continuity.values())
            theological_continuity = {k: v/max_score if max_score > 0 else 0 
                                    for k, v in theological_continuity.items()}
        
        # Calculate source influence score
        influence_score = avg_similarity * (len(source_matches) / 100.0)  # Normalize by expected matches
        
        report = ComparisonReport(
            torah_source=torah_source,
            comparison_book=comparison_book,
            total_matches=len(source_matches),
            pattern_matches=source_matches,
            average_similarity=avg_similarity,
            theological_continuity=theological_continuity,
            source_influence_score=influence_score,
            generated_date=datetime.now().isoformat()
        )
        
        # Save report
        self._save_comparison_report(report)
        
        print(f"✅ Comparison complete: {len(source_matches)} matches found")
        return report
    
    def _save_comparison_report(self, report: ComparisonReport):
        """Save comparison report to file"""
        report_path = self.output_dir / f"comparison_{report.torah_source}_{report.comparison_book}.json"
        
        report_dict = asdict(report)
        # Convert PatternMatch objects to dicts
        report_dict['pattern_matches'] = [asdict(m) for m in report.pattern_matches]
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved comparison report to {report_path}")
    
    def generate_discovery_report(self) -> Dict[str, Any]:
        """Generate a comprehensive discovery report"""
        print("\n📋 Generating discovery report...")
        
        # Get all pattern matches across books
        all_matches = []
        books_to_analyze = ['Joshua', 'Judges', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings']
        
        for book in books_to_analyze:
            matches = self.identify_torah_patterns_in_book(book, threshold=0.7)
            all_matches.extend(matches)
        
        # Analyze by source
        source_analysis = {}
        for source in ['J', 'E', 'P', 'D', 'R']:
            source_matches = [m for m in all_matches if m.source == source]
            source_analysis[source] = {
                'total_matches': len(source_matches),
                'average_similarity': sum(m.similarity for m in source_matches) / len(source_matches) if source_matches else 0,
                'books_with_matches': len(set(m.comparison_reference.split()[0] for m in source_matches))
            }
        
        report = {
            'generated_date': datetime.now().isoformat(),
            'total_pattern_matches': len(all_matches),
            'source_analysis': source_analysis,
            'matches_by_book': {
                book: len([m for m in all_matches if book in m.comparison_reference])
                for book in books_to_analyze
            }
        }
        
        # Save report
        report_path = self.output_dir / 'discovery_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved discovery report to {report_path}")
        return report


def main():
    """Main function"""
    print("=" * 60)
    print("AI Learning System Integration")
    print("=" * 60)
    
    integration = AILearningIntegration()
    
    # Example: Compare P source with Chronicles
    print("\n" + "=" * 60)
    print("Example: Comparing P (Priestly) source with 1 Chronicles")
    print("=" * 60)
    
    try:
        report = integration.compare_torah_with_book('P', '1 Chronicles')
        print(f"\n📊 Results:")
        print(f"   Total matches: {report.total_matches}")
        print(f"   Average similarity: {report.average_similarity:.2%}")
        print(f"   Source influence score: {report.source_influence_score:.2f}")
    except Exception as e:
        print(f"⚠️  Could not generate comparison: {e}")
        print("   Make sure Qdrant has data and model is trained")
    
    # Generate discovery report
    print("\n" + "=" * 60)
    print("Generating Discovery Report")
    print("=" * 60)
    
    try:
        discovery_report = integration.generate_discovery_report()
        print(f"\n📊 Discovery Report Summary:")
        print(f"   Total pattern matches: {discovery_report['total_pattern_matches']}")
        print(f"\n   By Source:")
        for source, analysis in discovery_report['source_analysis'].items():
            print(f"     {source}: {analysis['total_matches']} matches, "
                  f"{analysis['average_similarity']:.2%} avg similarity")
    except Exception as e:
        print(f"⚠️  Could not generate discovery report: {e}")


if __name__ == "__main__":
    main()

