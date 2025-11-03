#!/usr/bin/env python3
"""
Bible Expansion Framework
==========================

Framework for expanding source analysis beyond the Pentateuch to all 66 books.
Supports multiple source attribution methods and gradual expansion.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import pickle
from datetime import datetime

# Import the feature extractor and model from training script
try:
    from train_torah_source_model import TorahFeatureExtractor, TorahSourceModelTrainer
except ImportError:
    print("Warning: Could not import training modules. Some features may be unavailable.")


@dataclass
class ExpandedVerseData:
    """Extended verse data structure for full Bible"""
    verse_id: str
    book: str
    chapter: int
    verse: int
    text: str
    sources: List[str]
    source_confidence: float
    source_attribution_method: str
    source_confidence_scores: Dict[str, float]
    torah_source_patterns: Optional[Dict[str, float]] = None
    nt_references: Optional[List[str]] = None
    torah_allusions: Optional[List[str]] = None
    source_evolution: Optional[Dict[str, Any]] = None
    parsing_version: str = "2.0"
    attribution_date: Optional[str] = None
    validation_status: str = "pending"


class BibleExpansionFramework:
    """Framework for expanding to all 66 books"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.output_dir = Path(self.config.get('output_dir', 'output'))
        self.models_dir = Path(self.config.get('models_dir', 'models'))
        self.models_dir.mkdir(exist_ok=True)
        
        # Load components
        self.feature_extractor = TorahFeatureExtractor() if 'TorahFeatureExtractor' in globals() else None
        self.model_trainer = None
        self._load_models()
    
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load framework configuration"""
        default_config = {
            'output_dir': 'output',
            'models_dir': 'models',
            'source_attribution_methods': ['ml_classification', 'pattern_match', 'heuristic'],
            'confidence_threshold': 0.7,
            'enable_cross_reference': True,
            'enable_torah_pattern_matching': True
        }
        
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _load_models(self):
        """Load trained models"""
        model_path = self.models_dir / 'torah_source_classifier.pkl'
        if model_path.exists() and 'TorahSourceModelTrainer' in globals():
            try:
                self.model_trainer = TorahSourceModelTrainer()
                self.model_trainer.load_model()
                print("✅ Loaded trained source classification model")
            except Exception as e:
                print(f"⚠️  Could not load model: {e}")
    
    def get_bible_books(self) -> Dict[str, Dict[str, Any]]:
        """Get all 66 books of the Bible with metadata"""
        return {
            # Old Testament - Torah (5 books) - Already done
            'Genesis': {'testament': 'OT', 'category': 'Torah', 'verses': 1533, 'status': 'complete'},
            'Exodus': {'testament': 'OT', 'category': 'Torah', 'verses': 1213, 'status': 'complete'},
            'Leviticus': {'testament': 'OT', 'category': 'Torah', 'verses': 859, 'status': 'complete'},
            'Numbers': {'testament': 'OT', 'category': 'Torah', 'verses': 1288, 'status': 'complete'},
            'Deuteronomy': {'testament': 'OT', 'category': 'Torah', 'verses': 959, 'status': 'complete'},
            
            # Old Testament - Historical Books (12 books)
            'Joshua': {'testament': 'OT', 'category': 'Historical', 'verses': 658, 'status': 'pending'},
            'Judges': {'testament': 'OT', 'category': 'Historical', 'verses': 618, 'status': 'pending'},
            'Ruth': {'testament': 'OT', 'category': 'Historical', 'verses': 85, 'status': 'pending'},
            '1 Samuel': {'testament': 'OT', 'category': 'Historical', 'verses': 810, 'status': 'pending'},
            '2 Samuel': {'testament': 'OT', 'category': 'Historical', 'verses': 695, 'status': 'pending'},
            '1 Kings': {'testament': 'OT', 'category': 'Historical', 'verses': 816, 'status': 'pending'},
            '2 Kings': {'testament': 'OT', 'category': 'Historical', 'verses': 719, 'status': 'pending'},
            '1 Chronicles': {'testament': 'OT', 'category': 'Historical', 'verses': 942, 'status': 'pending'},
            '2 Chronicles': {'testament': 'OT', 'category': 'Historical', 'verses': 822, 'status': 'pending'},
            'Ezra': {'testament': 'OT', 'category': 'Historical', 'verses': 280, 'status': 'pending'},
            'Nehemiah': {'testament': 'OT', 'category': 'Historical', 'verses': 406, 'status': 'pending'},
            'Esther': {'testament': 'OT', 'category': 'Historical', 'verses': 167, 'status': 'pending'},
            
            # Add more books as needed...
        }
    
    def process_book(self, book_name: str, source_file: Path, 
                    source_type: str = 'plain_text') -> List[ExpandedVerseData]:
        """
        Process a biblical book and attribute sources.
        
        Args:
            book_name: Name of the book
            source_file: Path to source file
            source_type: Type of source file ('plain_text', 'structured', 'xml')
        
        Returns:
            List of ExpandedVerseData objects
        """
        print(f"\n📖 Processing {book_name}...")
        
        # Parse book (this would call the extended parser)
        verses = self._parse_book(source_file, book_name, source_type)
        
        # Attribute sources
        expanded_verses = []
        for verse in verses:
            expanded_verse = self._attribute_sources(verse, book_name)
            expanded_verses.append(expanded_verse)
        
        # Save results
        self._save_book_results(book_name, expanded_verses)
        
        print(f"✅ Processed {len(expanded_verses)} verses from {book_name}")
        return expanded_verses
    
    def _parse_book(self, source_file: Path, book_name: str, 
                    source_type: str) -> List[Dict[str, Any]]:
        """Parse book from source file"""
        # This would integrate with ExtendedBibleParser
        # For now, return empty list as placeholder
        return []
    
    def _attribute_sources(self, verse_data: Dict[str, Any], 
                          book_name: str) -> ExpandedVerseData:
        """Attribute sources using multiple methods"""
        verse_ref = f"{book_name} {verse_data.get('chapter', 0)}:{verse_data.get('verse', 0)}"
        
        # Try ML classification first
        if self.model_trainer and self.model_trainer.trained:
            try:
                ml_result = self.model_trainer.predict(verse_data)
                if ml_result['confidence'] >= self.config['confidence_threshold']:
                    return ExpandedVerseData(
                        verse_id=f"{book_name}_{verse_data.get('chapter', 0)}_{verse_data.get('verse', 0)}",
                        book=book_name,
                        chapter=verse_data.get('chapter', 0),
                        verse=verse_data.get('verse', 0),
                        text=verse_data.get('text', ''),
                        sources=[ml_result['predicted_source']],
                        source_confidence=ml_result['confidence'],
                        source_attribution_method='ml_classification',
                        source_confidence_scores=ml_result['source_probabilities'],
                        torah_source_patterns=ml_result.get('features', {}),
                        attribution_date=datetime.now().isoformat()
                    )
            except Exception as e:
                print(f"⚠️  ML classification failed: {e}")
        
        # Fallback to pattern matching
        if self.feature_extractor:
            features = self.feature_extractor.extract(verse_data)
            best_source = max(features.vocabulary_features.items(), 
                            key=lambda x: x[1])[0] if features.vocabulary_features else 'UNKNOWN'
            confidence = features.vocabulary_features.get(best_source, 0.0)
            
            return ExpandedVerseData(
                verse_id=f"{book_name}_{verse_data.get('chapter', 0)}_{verse_data.get('verse', 0)}",
                book=book_name,
                chapter=verse_data.get('chapter', 0),
                verse=verse_data.get('verse', 0),
                text=verse_data.get('text', ''),
                sources=[best_source] if confidence > 0.3 else ['UNKNOWN'],
                source_confidence=confidence,
                source_attribution_method='pattern_match',
                source_confidence_scores={k: v for k, v in features.vocabulary_features.items()},
                torah_source_patterns={
                    'vocabulary': features.vocabulary_features,
                    'theological': features.theological_features,
                    'style': features.style_features,
                    'structural': features.structural_features
                },
                attribution_date=datetime.now().isoformat()
            )
        
        # Default fallback
        return ExpandedVerseData(
            verse_id=f"{book_name}_{verse_data.get('chapter', 0)}_{verse_data.get('verse', 0)}",
            book=book_name,
            chapter=verse_data.get('chapter', 0),
            verse=verse_data.get('verse', 0),
            text=verse_data.get('text', ''),
            sources=['UNKNOWN'],
            source_confidence=0.0,
            source_attribution_method='none',
            source_confidence_scores={},
            attribution_date=datetime.now().isoformat()
        )
    
    def _save_book_results(self, book_name: str, verses: List[ExpandedVerseData]):
        """Save processed book results"""
        book_output_dir = self.output_dir / book_name
        book_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as CSV
        df_data = []
        for verse in verses:
            df_data.append(asdict(verse))
        
        df = pd.DataFrame(df_data)
        csv_path = book_output_dir / f"{book_name}.csv"
        df.to_csv(csv_path, index=False)
        
        # Save as JSON
        json_path = book_output_dir / f"{book_name}_expanded.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(v) for v in verses], f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved results to {csv_path} and {json_path}")
    
    def get_expansion_status(self) -> Dict[str, Any]:
        """Get status of Bible expansion"""
        books = self.get_bible_books()
        status = {
            'total_books': len(books),
            'completed': 0,
            'pending': 0,
            'total_verses': 0,
            'completed_verses': 0,
            'by_category': {}
        }
        
        for book, info in books.items():
            status['total_verses'] += info.get('verses', 0)
            if info.get('status') == 'complete':
                status['completed'] += 1
                status['completed_verses'] += info.get('verses', 0)
            else:
                status['pending'] += 1
            
            category = info.get('category', 'Unknown')
            if category not in status['by_category']:
                status['by_category'][category] = {'completed': 0, 'pending': 0}
            
            if info.get('status') == 'complete':
                status['by_category'][category]['completed'] += 1
            else:
                status['by_category'][category]['pending'] += 1
        
        return status


def main():
    """Main function for expansion framework"""
    print("=" * 60)
    print("Bible Expansion Framework")
    print("=" * 60)
    
    framework = BibleExpansionFramework()
    
    # Show expansion status
    status = framework.get_expansion_status()
    print(f"\n📊 Expansion Status:")
    print(f"   Total books: {status['total_books']}")
    print(f"   Completed: {status['completed']}")
    print(f"   Pending: {status['pending']}")
    print(f"   Total verses: {status['total_verses']:,}")
    print(f"   Completed verses: {status['completed_verses']:,}")
    print(f"   Progress: {status['completed_verses']/status['total_verses']*100:.1f}%")
    
    print(f"\n📚 By Category:")
    for category, counts in status['by_category'].items():
        print(f"   {category}: {counts['completed']} completed, {counts['pending']} pending")


if __name__ == "__main__":
    main()

