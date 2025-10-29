#!/usr/bin/env python3
"""
Targeted Pattern Analysis for KJV Sources
Analyzes specific verses we've already identified with the "listen, guard, do" pattern
"""

import os
import json
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PatternAnalysis:
    """Represents analysis of a specific pattern"""
    verse_reference: str
    verse_text: str
    pattern_type: str
    verbs_found: List[str]
    sequence_order: str
    sources: List[str]
    book: str
    chapter: int
    verse: int
    context: str

class TargetedPatternAnalyzer:
    """Targeted analyzer for specific biblical patterns"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        
        # Known "listen, guard, do" patterns from our earlier search
        self.known_patterns = {
            "listen_guard_do": [
                "Deuteronomy 4:6",
                "Deuteronomy 5:1", 
                "Deuteronomy 6:3",
                "Deuteronomy 8:1",
                "Deuteronomy 12:28",
                "Deuteronomy 15:5",
                "Deuteronomy 28:1",
                "Deuteronomy 28:13"
            ],
            "observe_keep_do": [
                "Deuteronomy 5:32",
                "Deuteronomy 6:25",
                "Deuteronomy 8:1",
                "Deuteronomy 12:28",
                "Deuteronomy 12:32",
                "Deuteronomy 15:5",
                "Deuteronomy 24:8",
                "Deuteronomy 28:1",
                "Deuteronomy 28:13"
            ],
            "command_observe_do": [
                "Deuteronomy 5:32",
                "Deuteronomy 6:25",
                "Deuteronomy 8:1",
                "Deuteronomy 12:28",
                "Deuteronomy 12:32",
                "Deuteronomy 15:5",
                "Deuteronomy 24:8",
                "Deuteronomy 28:1",
                "Deuteronomy 28:13"
            ]
        }
    
    def load_verse_data(self, book: str) -> pd.DataFrame:
        """Load verse data from CSV file"""
        csv_path = self.output_dir / book / f"{book}.csv"
        if csv_path.exists():
            return pd.read_csv(csv_path)
        return pd.DataFrame()
    
    def find_verse_by_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        """Find a specific verse by reference"""
        # Parse reference
        match = re.match(r"(\w+)\s+(\d+):(\d+)", reference)
        if not match:
            return None
        
        book, chapter, verse = match.groups()
        book, chapter, verse = book, int(chapter), int(verse)
        
        # Load book data
        df = self.load_verse_data(book)
        if df.empty:
            return None
        
        # Find the verse
        verse_data = df[(df['chapter'] == chapter) & (df['verse'] == verse)]
        if verse_data.empty:
            return None
        
        row = verse_data.iloc[0]
        return {
            'reference': row['canonical_reference'],
            'text': row['full_text'],
            'book': book,
            'chapter': chapter,
            'verse': verse,
            'sources': row['sources'].split(';') if pd.notna(row['sources']) else [],
            'primary_source': row['primary_source']
        }
    
    def analyze_verse_pattern(self, verse_data: Dict[str, Any], pattern_type: str) -> PatternAnalysis:
        """Analyze a specific verse for patterns"""
        text = verse_data['text'].lower()
        
        # Define verb patterns
        verb_patterns = {
            "listen_guard_do": {
                "listen": ["hear", "hearken", "listen"],
                "guard": ["keep", "observe", "guard"],
                "do": ["do", "perform", "obey"]
            },
            "observe_keep_do": {
                "observe": ["observe", "keep", "guard"],
                "keep": ["keep", "observe", "guard"],
                "do": ["do", "perform", "obey"]
            },
            "command_observe_do": {
                "command": ["command", "commanded"],
                "observe": ["observe", "keep", "guard"],
                "do": ["do", "perform", "obey"]
            }
        }
        
        if pattern_type not in verb_patterns:
            return None
        
        pattern = verb_patterns[pattern_type]
        verbs_found = []
        sequence_order = []
        
        # Find verbs in text
        for category, verbs in pattern.items():
            for verb in verbs:
                if verb in text:
                    verbs_found.append(verb)
                    sequence_order.append(category)
                    break
        
        # Determine context
        context = self.extract_context(verse_data['text'])
        
        return PatternAnalysis(
            verse_reference=verse_data['reference'],
            verse_text=verse_data['text'],
            pattern_type=pattern_type,
            verbs_found=verbs_found,
            sequence_order=" -> ".join(sequence_order),
            sources=verse_data['sources'],
            book=verse_data['book'],
            chapter=verse_data['chapter'],
            verse=verse_data['verse'],
            context=context
        )
    
    def extract_context(self, text: str) -> str:
        """Extract contextual information from verse text"""
        context_indicators = []
        
        if "lord" in text.lower():
            context_indicators.append("Divine command")
        if "covenant" in text.lower():
            context_indicators.append("Covenant context")
        if "blessing" in text.lower() or "curse" in text.lower():
            context_indicators.append("Blessing/curse")
        if "if" in text.lower():
            context_indicators.append("Conditional")
        if "commandment" in text.lower():
            context_indicators.append("Commandment")
        
        return "; ".join(context_indicators) if context_indicators else "General"
    
    def analyze_all_patterns(self) -> Dict[str, List[PatternAnalysis]]:
        """Analyze all known patterns"""
        results = {}
        
        for pattern_type, references in self.known_patterns.items():
            pattern_results = []
            
            for reference in references:
                verse_data = self.find_verse_by_reference(reference)
                if verse_data:
                    analysis = self.analyze_verse_pattern(verse_data, pattern_type)
                    if analysis:
                        pattern_results.append(analysis)
            
            results[pattern_type] = pattern_results
        
        return results
    
    def find_similar_patterns(self) -> List[PatternAnalysis]:
        """Find other verses with similar sequential verb patterns"""
        all_verses = []
        books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
        
        # Load all verses
        for book in books:
            df = self.load_verse_data(book)
            if not df.empty:
                for _, row in df.iterrows():
                    verse_data = {
                        'reference': row['canonical_reference'],
                        'text': row['full_text'],
                        'book': book,
                        'chapter': row['chapter'],
                        'verse': row['verse'],
                        'sources': row['sources'].split(';') if pd.notna(row['sources']) else [],
                        'primary_source': row['primary_source']
                    }
                    all_verses.append(verse_data)
        
        # Search for other sequential patterns
        similar_patterns = []
        
        # Define other sequential patterns to look for
        other_patterns = {
            "love_serve_fear": ["love", "serve", "fear"],
            "walk_keep_obey": ["walk", "keep", "obey"],
            "swear_serve_cleave": ["swear", "serve", "cleave"],
            "command_establish_keep": ["command", "establish", "keep"],
            "fear_serve_love": ["fear", "serve", "love"]
        }
        
        for verse_data in all_verses:
            text = verse_data['text'].lower()
            
            for pattern_name, verbs in other_patterns.items():
                found_verbs = []
                for verb in verbs:
                    if verb in text:
                        found_verbs.append(verb)
                
                # If we found at least 2 verbs from the pattern
                if len(found_verbs) >= 2:
                    analysis = PatternAnalysis(
                        verse_reference=verse_data['reference'],
                        verse_text=verse_data['text'],
                        pattern_type=pattern_name,
                        verbs_found=found_verbs,
                        sequence_order=" -> ".join(found_verbs),
                        sources=verse_data['sources'],
                        book=verse_data['book'],
                        chapter=verse_data['chapter'],
                        verse=verse_data['verse'],
                        context=self.extract_context(verse_data['text'])
                    )
                    similar_patterns.append(analysis)
        
        return similar_patterns
    
    def display_analysis(self, results: Dict[str, List[PatternAnalysis]]):
        """Display pattern analysis results"""
        print("🔍 Targeted Pattern Analysis for KJV Sources")
        print("=" * 60)
        
        for pattern_type, analyses in results.items():
            print(f"\n📋 {pattern_type.replace('_', ' ').title()} Pattern")
            print("-" * 40)
            
            if not analyses:
                print("No verses found for this pattern.")
                continue
            
            for i, analysis in enumerate(analyses, 1):
                print(f"\n{i}. {analysis.verse_reference}")
                print(f"   Sources: {', '.join(analysis.sources)}")
                print(f"   Verbs: {', '.join(analysis.verbs_found)}")
                print(f"   Sequence: {analysis.sequence_order}")
                print(f"   Context: {analysis.context}")
                print(f"   Text: {analysis.verse_text[:80]}...")
    
    def display_similar_patterns(self, similar_patterns: List[PatternAnalysis]):
        """Display similar patterns found"""
        print(f"\n🔍 Other Sequential Verb Patterns Found")
        print("=" * 60)
        
        if not similar_patterns:
            print("No similar patterns found.")
            return
        
        # Group by pattern type
        pattern_groups = {}
        for analysis in similar_patterns:
            if analysis.pattern_type not in pattern_groups:
                pattern_groups[analysis.pattern_type] = []
            pattern_groups[analysis.pattern_type].append(analysis)
        
        for pattern_type, analyses in pattern_groups.items():
            print(f"\n📋 {pattern_type.replace('_', ' ').title()} Pattern ({len(analyses)} instances)")
            print("-" * 40)
            
            for i, analysis in enumerate(analyses[:5], 1):  # Show first 5
                print(f"\n{i}. {analysis.verse_reference}")
                print(f"   Sources: {', '.join(analysis.sources)}")
                print(f"   Verbs: {', '.join(analysis.verbs_found)}")
                print(f"   Context: {analysis.context}")
                print(f"   Text: {analysis.verse_text[:60]}...")
            
            if len(analyses) > 5:
                print(f"\n   ... and {len(analyses) - 5} more instances")
    
    def save_analysis(self, results: Dict[str, List[PatternAnalysis]], similar_patterns: List[PatternAnalysis]):
        """Save analysis results to JSON"""
        output_data = {
            "known_patterns": {},
            "similar_patterns": []
        }
        
        # Convert known patterns
        for pattern_type, analyses in results.items():
            output_data["known_patterns"][pattern_type] = []
            for analysis in analyses:
                output_data["known_patterns"][pattern_type].append({
                    "verse_reference": analysis.verse_reference,
                    "verse_text": analysis.verse_text,
                    "pattern_type": analysis.pattern_type,
                    "verbs_found": analysis.verbs_found,
                    "sequence_order": analysis.sequence_order,
                    "sources": analysis.sources,
                    "book": analysis.book,
                    "chapter": analysis.chapter,
                    "verse": analysis.verse,
                    "context": analysis.context
                })
        
        # Convert similar patterns
        for analysis in similar_patterns:
            output_data["similar_patterns"].append({
                "verse_reference": analysis.verse_reference,
                "verse_text": analysis.verse_text,
                "pattern_type": analysis.pattern_type,
                "verbs_found": analysis.verbs_found,
                "sequence_order": analysis.sequence_order,
                "sources": analysis.sources,
                "book": analysis.book,
                "chapter": analysis.chapter,
                "verse": analysis.verse,
                "context": analysis.context
            })
        
        # Save to file
        with open("targeted_pattern_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info("Analysis results saved to targeted_pattern_analysis.json")

def main():
    """Main function to run targeted pattern analysis"""
    print("🔍 Targeted Pattern Analysis for KJV Sources")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = TargetedPatternAnalyzer()
    
    # Analyze known patterns
    print("\n1. Analyzing known 'Listen, Guard, Do' patterns...")
    results = analyzer.analyze_all_patterns()
    analyzer.display_analysis(results)
    
    # Find similar patterns
    print("\n2. Searching for other sequential verb patterns...")
    similar_patterns = analyzer.find_similar_patterns()
    analyzer.display_similar_patterns(similar_patterns)
    
    # Save results
    analyzer.save_analysis(results, similar_patterns)
    
    print(f"\n🎯 Analysis complete!")
    print(f"📁 Results saved to targeted_pattern_analysis.json")

if __name__ == "__main__":
    main()
