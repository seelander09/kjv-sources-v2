#!/usr/bin/env python3
"""
Simple Pattern Search for KJV Sources
Searches for biblical patterns directly in the CSV data using semantic similarity
"""

import os
import json
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Sentence transformers for creating semantic vectors
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Sentence transformers not available. Install with: pip install sentence-transformers")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PatternResult:
    """Represents a pattern search result"""
    verse_reference: str
    verse_text: str
    pattern_match: str
    similarity_score: float
    sources: List[str]
    book: str
    chapter: int
    verse: int

class SimplePatternSearcher:
    """Simple pattern searcher for biblical text patterns using CSV data"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        
        # Initialize embedding model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        else:
            self.embedding_model = None
        
        # Load all verse data
        self.all_verses = self.load_all_verses()
    
    def load_all_verses(self) -> List[Dict[str, Any]]:
        """Load all verses from CSV files"""
        all_verses = []
        books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
        
        for book in books:
            csv_path = self.output_dir / book / f"{book}.csv"
            if csv_path.exists():
                try:
                    df = pd.read_csv(csv_path)
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
                except Exception as e:
                    logger.error(f"Error loading {book}: {e}")
        
        logger.info(f"Loaded {len(all_verses)} verses total")
        return all_verses
    
    def create_pattern_vector(self, pattern_description: str) -> Optional[List[float]]:
        """Create a semantic vector representation of a pattern"""
        if not self.embedding_model:
            logger.warning("Embedding model not available")
            return None
        
        try:
            # Create embedding for the pattern description
            embedding = self.embedding_model.encode(pattern_description)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error creating pattern vector: {e}")
            return None
    
    def search_similar_patterns(self, pattern_description: str, limit: int = 20) -> List[PatternResult]:
        """Search for verses with similar patterns using semantic similarity"""
        if not self.embedding_model:
            return self.text_based_search(pattern_description, limit)
        
        try:
            # Create pattern embedding
            pattern_embedding = self.embedding_model.encode(pattern_description)
            
            # Calculate similarities
            similarities = []
            for verse in self.all_verses:
                verse_embedding = self.embedding_model.encode(verse['text'])
                similarity = self.cosine_similarity(pattern_embedding, verse_embedding)
                
                pattern_result = PatternResult(
                    verse_reference=verse['reference'],
                    verse_text=verse['text'],
                    pattern_match=pattern_description,
                    similarity_score=similarity,
                    sources=verse['sources'],
                    book=verse['book'],
                    chapter=verse['chapter'],
                    verse=verse['verse']
                )
                similarities.append(pattern_result)
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x.similarity_score, reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Error in semantic pattern search: {e}")
            return []
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def text_based_search(self, pattern_description: str, limit: int = 20) -> List[PatternResult]:
        """Fallback text-based search when embeddings are not available"""
        # Extract key words from pattern description
        keywords = re.findall(r'\b\w+\b', pattern_description.lower())
        
        results = []
        for verse in self.all_verses:
            verse_text_lower = verse['text'].lower()
            score = 0
            
            # Count keyword matches
            for keyword in keywords:
                if keyword in verse_text_lower:
                    score += 1
            
            if score > 0:
                # Normalize score
                normalized_score = score / len(keywords)
                
                pattern_result = PatternResult(
                    verse_reference=verse['reference'],
                    verse_text=verse['text'],
                    pattern_match=pattern_description,
                    similarity_score=normalized_score,
                    sources=verse['sources'],
                    book=verse['book'],
                    chapter=verse['chapter'],
                    verse=verse['verse']
                )
                results.append(pattern_result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    def search_listen_guard_do_pattern(self, limit: int = 20) -> List[PatternResult]:
        """Search for the specific 'listen, guard, do' pattern"""
        pattern_descriptions = [
            "listen hear hearken then guard keep observe then do perform obey",
            "divine command sequence: hear, keep, do",
            "covenant obedience pattern: listen, guard, do",
            "biblical command structure: hear, observe, perform",
            "deuteronomic formula: hearken, keep, do"
        ]
        
        all_results = []
        for description in pattern_descriptions:
            results = self.search_similar_patterns(description, limit)
            all_results.extend(results)
        
        # Remove duplicates and sort by score
        unique_results = {}
        for result in all_results:
            key = result.verse_reference
            if key not in unique_results or result.similarity_score > unique_results[key].similarity_score:
                unique_results[key] = result
        
        return sorted(unique_results.values(), key=lambda x: x.similarity_score, reverse=True)[:limit]
    
    def search_sequential_verb_patterns(self, limit: int = 20) -> List[PatternResult]:
        """Search for other sequential verb patterns"""
        pattern_descriptions = [
            "command obey serve love fear",
            "walk keep observe establish",
            "swear serve cleave avouch",
            "love serve fear keep",
            "observe keep do perform",
            "command establish keep walk",
            "fear serve love keep"
        ]
        
        all_results = []
        for description in pattern_descriptions:
            results = self.search_similar_patterns(description, limit)
            all_results.extend(results)
        
        # Remove duplicates and sort by score
        unique_results = {}
        for result in all_results:
            key = result.verse_reference
            if key not in unique_results or result.similarity_score > unique_results[key].similarity_score:
                unique_results[key] = result
        
        return sorted(unique_results.values(), key=lambda x: x.similarity_score, reverse=True)[:limit]
    
    def search_covenant_patterns(self, limit: int = 20) -> List[PatternResult]:
        """Search for covenant-related patterns"""
        pattern_descriptions = [
            "covenant agreement promise oath",
            "blessing curse conditional promise",
            "if you obey then blessing",
            "covenant renewal ceremony",
            "swear serve love keep"
        ]
        
        all_results = []
        for description in pattern_descriptions:
            results = self.search_similar_patterns(description, limit)
            all_results.extend(results)
        
        # Remove duplicates and sort by score
        unique_results = {}
        for result in all_results:
            key = result.verse_reference
            if key not in unique_results or result.similarity_score > unique_results[key].similarity_score:
                unique_results[key] = result
        
        return sorted(unique_results.values(), key=lambda x: x.similarity_score, reverse=True)[:limit]
    
    def analyze_pattern_frequency(self, results: List[PatternResult]) -> Dict[str, Any]:
        """Analyze the frequency and distribution of patterns"""
        analysis = {
            "total_results": len(results),
            "books": {},
            "sources": {},
            "score_distribution": {
                "high": 0,  # > 0.8
                "medium": 0,  # 0.6-0.8
                "low": 0  # < 0.6
            },
            "pattern_types": {}
        }
        
        for result in results:
            # Book distribution
            book = result.book
            analysis["books"][book] = analysis["books"].get(book, 0) + 1
            
            # Source distribution
            for source in result.sources:
                analysis["sources"][source] = analysis["sources"].get(source, 0) + 1
            
            # Score distribution
            if result.similarity_score > 0.8:
                analysis["score_distribution"]["high"] += 1
            elif result.similarity_score > 0.6:
                analysis["score_distribution"]["medium"] += 1
            else:
                analysis["score_distribution"]["low"] += 1
        
        return analysis
    
    def display_results(self, results: List[PatternResult], title: str = "Pattern Search Results"):
        """Display pattern search results"""
        print(f"\n{title}")
        print("=" * 60)
        
        if not results:
            print("No results found.")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. [{result.similarity_score:.3f}] {result.verse_reference}")
            print(f"   Sources: {', '.join(result.sources)}")
            print(f"   Text: {result.verse_text[:100]}...")
            print(f"   Pattern: {result.pattern_match}")
        
        # Display analysis
        analysis = self.analyze_pattern_frequency(results)
        print(f"\n📊 Pattern Analysis:")
        print(f"   Total Results: {analysis['total_results']}")
        print(f"   Books: {analysis['books']}")
        print(f"   Sources: {analysis['sources']}")
        print(f"   Score Distribution: {analysis['score_distribution']}")
    
    def save_results(self, results: List[PatternResult], filename: str):
        """Save results to JSON file"""
        output_data = []
        for result in results:
            output_data.append({
                "verse_reference": result.verse_reference,
                "verse_text": result.verse_text,
                "pattern_match": result.pattern_match,
                "similarity_score": result.similarity_score,
                "sources": result.sources,
                "book": result.book,
                "chapter": result.chapter,
                "verse": result.verse
            })
        
        output_path = Path(filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")

def main():
    """Main function to run simple pattern search"""
    print("🔍 Simple Pattern Search for KJV Sources")
    print("=" * 50)
    
    # Initialize searcher
    searcher = SimplePatternSearcher()
    
    # Search for "listen, guard, do" pattern
    print("\n1. Searching for 'Listen, Guard, Do' pattern...")
    listen_guard_do_results = searcher.search_listen_guard_do_pattern(limit=15)
    searcher.display_results(listen_guard_do_results, "Listen, Guard, Do Pattern Results")
    searcher.save_results(listen_guard_do_results, "listen_guard_do_pattern_results.json")
    
    # Search for other sequential verb patterns
    print("\n2. Searching for other sequential verb patterns...")
    sequential_verb_results = searcher.search_sequential_verb_patterns(limit=15)
    searcher.display_results(sequential_verb_results, "Sequential Verb Pattern Results")
    searcher.save_results(sequential_verb_results, "sequential_verb_pattern_results.json")
    
    # Search for covenant patterns
    print("\n3. Searching for covenant patterns...")
    covenant_results = searcher.search_covenant_patterns(limit=15)
    searcher.display_results(covenant_results, "Covenant Pattern Results")
    searcher.save_results(covenant_results, "covenant_pattern_results.json")
    
    print(f"\n🎯 Pattern search complete!")
    print(f"📁 Results saved to JSON files")

if __name__ == "__main__":
    main()
