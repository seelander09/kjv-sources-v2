# Extended Parser Architecture for Full Bible

## Overview

This document outlines the architecture for extending the KJV Sources parser to handle all 66 books of the Bible, moving beyond the current Pentateuch-only (Genesis-Deuteronomy) implementation.

## Current Architecture

### Existing Parser (`parse_wikitext.py`)

The current parser is designed for:
- **Input Format**: Wikitext files with color-coded source markers
- **Books Supported**: Genesis, Exodus, Leviticus, Numbers, Deuteronomy
- **Source Attribution**: Direct from color codes in wikitext
- **Output Formats**: CSV, JSONL (training data), HTML previews

### Key Components

```python
# Current parser structure
COLOR_TO_SOURCE = {
    "#888800": "P",  # Priestly source
    "#000088": "J",  # Jahwist source
    "#008888": "E",  # Elohist source
    "#880000": "R",  # Redactor
    "#000000": "D",  # Deuteronomist source
}

def parse_wikitext_file(file_path):
    """Parse wikitext file to extract verses with sources"""
    # Current implementation
```

## Extended Architecture Design

### Core Parser Class

```python
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import json

@dataclass
class VerseData:
    """Extended verse data structure"""
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


class ExtendedBibleParser:
    """Parser for all 66 books of the Bible"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize parser with configuration.
        
        Args:
            config_path: Path to parser configuration file
        """
        self.config = self._load_config(config_path)
        self.torah_patterns = self._load_torah_source_patterns()
        self.ml_classifier = self._load_source_classifier()
        self.heuristic_rules = self._load_heuristic_rules()
        self.scholar_annotations = self._load_scholar_annotations()
        
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load parser configuration"""
        default_config = {
            "supported_formats": ["wikitext", "plain_text", "structured", "xml"],
            "source_attribution_methods": ["direct_annotation", "ml_classification", 
                                          "pattern_match", "heuristic"],
            "confidence_threshold": 0.7,
            "enable_cross_reference": True,
            "enable_torah_pattern_matching": True
        }
        
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _load_torah_source_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Load confirmed Torah source patterns for pattern matching.
        
        Returns:
            Dictionary mapping source codes to pattern dictionaries
        """
        patterns_path = Path("data/torah_source_patterns.json")
        if patterns_path.exists():
            with open(patterns_path, 'r') as f:
                return json.load(f)
        return self._generate_default_patterns()
    
    def _load_source_classifier(self):
        """Load ML model for source classification"""
        # Placeholder for ML model loading
        # Will be implemented with trained models
        return None
    
    def _load_heuristic_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load heuristic rules for source attribution"""
        rules_path = Path("data/heuristic_rules.json")
        if rules_path.exists():
            with open(rules_path, 'r') as f:
                return json.load(f)
        return self._generate_default_heuristics()
    
    def _load_scholar_annotations(self) -> Dict[str, Dict[str, Any]]:
        """Load scholar annotations for source attribution"""
        annotations_path = Path("data/scholar_annotations.json")
        if annotations_path.exists():
            with open(annotations_path, 'r') as f:
                return json.load(f)
        return {}
    
    def parse_book(self, book_name: str, source_type: str = "wikitext", 
                   file_path: Optional[Path] = None) -> List[VerseData]:
        """
        Parse any biblical book.
        
        Args:
            book_name: Name of biblical book (e.g., "Joshua", "Psalms")
            source_type: Format type ('wikitext', 'plain_text', 'structured', 'xml')
            file_path: Optional path to source file
            
        Returns:
            List of VerseData objects
        """
        # Determine file path if not provided
        if not file_path:
            file_path = self._find_book_file(book_name, source_type)
        
        # Route to appropriate parser
        if source_type == "wikitext":
            return self._parse_wikitext(file_path, book_name)
        elif source_type == "plain_text":
            return self._parse_plain_text(file_path, book_name)
        elif source_type == "structured":
            return self._parse_structured(file_path, book_name)
        elif source_type == "xml":
            return self._parse_xml(file_path, book_name)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    def attribute_sources(self, verse_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attribute sources using multiple methods.
        
        Uses priority order:
        1. Direct annotation (highest priority)
        2. Scholar annotations
        3. ML classification
        4. Pattern matching
        5. Heuristic rules (lowest priority)
        
        Returns:
            Dictionary with source attribution results
        """
        verse_ref = f"{verse_data['book']} {verse_data['chapter']}:{verse_data['verse']}"
        
        # Method 1: Check for direct annotation
        if verse_ref in self.scholar_annotations:
            annotation = self.scholar_annotations[verse_ref]
            return {
                "sources": annotation.get("sources", []),
                "source_confidence": annotation.get("confidence", 1.0),
                "source_attribution_method": "direct_annotation",
                "source_confidence_scores": annotation.get("confidence_scores", {}),
                "annotation_source": annotation.get("scholar", "unknown")
            }
        
        # Method 2: ML Classification
        if self.ml_classifier:
            ml_result = self._classify_with_ml(verse_data)
            if ml_result["confidence"] >= self.config["confidence_threshold"]:
                return {
                    "sources": ml_result["sources"],
                    "source_confidence": ml_result["confidence"],
                    "source_attribution_method": "ml_classification",
                    "source_confidence_scores": ml_result["confidence_scores"]
                }
        
        # Method 3: Pattern Matching
        pattern_result = self._match_torah_patterns(verse_data)
        if pattern_result["confidence"] >= self.config["confidence_threshold"]:
            return {
                "sources": pattern_result["sources"],
                "source_confidence": pattern_result["confidence"],
                "source_attribution_method": "pattern_match",
                "source_confidence_scores": pattern_result["confidence_scores"],
                "torah_source_patterns": pattern_result["pattern_matches"]
            }
        
        # Method 4: Heuristic Rules
        heuristic_result = self._apply_heuristics(verse_data)
        return {
            "sources": heuristic_result["sources"],
            "source_confidence": heuristic_result["confidence"],
            "source_attribution_method": "heuristic",
            "source_confidence_scores": heuristic_result["confidence_scores"]
        }
    
    def _classify_with_ml(self, verse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify verse using ML model"""
        # Placeholder for ML classification
        # Will extract features and run through trained model
        return {
            "sources": [],
            "confidence": 0.0,
            "confidence_scores": {}
        }
    
    def _match_torah_patterns(self, verse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Match verse against known Torah source patterns"""
        text = verse_data.get("text", "").lower()
        best_matches = {}
        
        for source, patterns in self.torah_patterns.items():
            score = 0.0
            matches = []
            
            # Check vocabulary patterns
            vocab_patterns = patterns.get("vocabulary", [])
            for pattern in vocab_patterns:
                if pattern in text:
                    score += 0.2
                    matches.append(f"vocab:{pattern}")
            
            # Check theological themes
            theme_patterns = patterns.get("themes", [])
            for theme in theme_patterns:
                if theme in text:
                    score += 0.15
                    matches.append(f"theme:{theme}")
            
            # Check style markers
            style_markers = patterns.get("style", [])
            for marker in style_markers:
                if marker in text:
                    score += 0.1
                    matches.append(f"style:{marker}")
            
            if score > 0:
                best_matches[source] = {
                    "score": min(score, 1.0),
                    "matches": matches
                }
        
        # Determine primary source
        if best_matches:
            primary_source = max(best_matches.items(), key=lambda x: x[1]["score"])
            return {
                "sources": [primary_source[0]],
                "confidence": primary_source[1]["score"],
                "confidence_scores": {k: v["score"] for k, v in best_matches.items()},
                "pattern_matches": best_matches
            }
        
        return {
            "sources": [],
            "confidence": 0.0,
            "confidence_scores": {},
            "pattern_matches": {}
        }
    
    def _apply_heuristics(self, verse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply heuristic rules for source attribution"""
        text = verse_data.get("text", "")
        sources = []
        confidence_scores = {}
        
        for rule in self.heuristic_rules.get("rules", []):
            if self._evaluate_rule(rule, verse_data):
                source = rule.get("source")
                if source not in sources:
                    sources.append(source)
                confidence_scores[source] = rule.get("confidence", 0.5)
        
        return {
            "sources": sources if sources else ["UNKNOWN"],
            "confidence": max(confidence_scores.values()) if confidence_scores else 0.3,
            "confidence_scores": confidence_scores
        }
    
    def _evaluate_rule(self, rule: Dict[str, Any], verse_data: Dict[str, Any]) -> bool:
        """Evaluate a single heuristic rule"""
        rule_type = rule.get("type")
        conditions = rule.get("conditions", [])
        
        if rule_type == "vocabulary":
            text = verse_data.get("text", "").lower()
            return any(condition in text for condition in conditions)
        
        elif rule_type == "structure":
            # Check structural patterns
            return False  # Placeholder
        
        elif rule_type == "theological_theme":
            # Check theological themes
            return False  # Placeholder
        
        return False
    
    def _parse_wikitext(self, file_path: Path, book_name: str) -> List[VerseData]:
        """Parse wikitext format (reuses existing logic)"""
        # Reuse existing parse_wikitext_file logic
        verses = []
        # ... existing parsing logic ...
        return verses
    
    def _parse_plain_text(self, file_path: Path, book_name: str) -> List[VerseData]:
        """Parse plain text format"""
        verses = []
        # Implementation for plain text parsing
        return verses
    
    def _parse_structured(self, file_path: Path, book_name: str) -> List[VerseData]:
        """Parse structured format (JSON, CSV, etc.)"""
        verses = []
        # Implementation for structured parsing
        return verses
    
    def _parse_xml(self, file_path: Path, book_name: str) -> List[VerseData]:
        """Parse XML format"""
        verses = []
        # Implementation for XML parsing
        return verses
```

## Source Attribution Methods

### Method 1: ML-Based Attribution

**Purpose**: Use machine learning models trained on Torah patterns to classify verses

**Implementation**:
```python
class SourceClassificationModel:
    """ML model for source classification"""
    
    def __init__(self, model_path: Path):
        self.model = self._load_model(model_path)
        self.feature_extractor = TorahFeatureExtractor()
    
    def classify(self, verse_data: Dict[str, Any]) -> Dict[str, float]:
        """Classify verse and return source probabilities"""
        features = self.feature_extractor.extract(verse_data)
        probabilities = self.model.predict_proba([features])[0]
        return {
            "J": probabilities[0],
            "E": probabilities[1],
            "P": probabilities[2],
            "D": probabilities[3],
            "R": probabilities[4]
        }
```

### Method 2: Pattern Matching

**Purpose**: Match verses against known Torah source patterns

**Pattern Types**:
- Vocabulary patterns (e.g., "YHWH" vs "Elohim")
- Theological themes (e.g., anthropomorphic vs transcendent)
- Literary style markers (e.g., formulaic vs narrative)
- Structural patterns (e.g., genealogies, legal codes)

### Method 3: Heuristic Rules

**Purpose**: Rule-based system for clear indicators

**Rule Examples**:
```json
{
  "rules": [
    {
      "type": "vocabulary",
      "source": "P",
      "conditions": ["generations", "according to their kinds", "command"],
      "confidence": 0.8
    },
    {
      "type": "structure",
      "source": "P",
      "conditions": ["genealogy", "legal_code"],
      "confidence": 0.9
    }
  ]
}
```

### Method 4: Scholar Annotation

**Purpose**: Manual annotations from biblical scholars

**Format**:
```json
{
  "Genesis 1:1": {
    "sources": ["P"],
    "confidence": 0.95,
    "confidence_scores": {"P": 0.95, "J": 0.02, "E": 0.01, "D": 0.01, "R": 0.01},
    "scholar": "Dr. Scholar Name",
    "date": "2025-01-15",
    "notes": "Clear P source with systematic creation account"
  }
}
```

## Data Schema Extensions

### Extended Verse Schema

```python
{
    "verse_id": "Joshua_1_1",
    "book": "Joshua",
    "chapter": 1,
    "verse": 1,
    "text": "Now after the death of Moses...",
    
    # Source attribution
    "sources": ["D"],
    "source_confidence": 0.85,
    "source_attribution_method": "ml_classification",
    "source_confidence_scores": {
        "J": 0.05,
        "E": 0.03,
        "P": 0.02,
        "D": 0.85,
        "R": 0.05
    },
    
    # Torah pattern connections
    "torah_source_patterns": {
        "vocabulary_similarity": {"D": 0.88},
        "theological_theme_match": {"D": 0.82},
        "literary_style_match": {"D": 0.90}
    },
    
    # Cross-testament analysis
    "nt_references": ["Hebrews 11:30"],
    "torah_allusions": ["Deuteronomy 31:1-8"],
    "source_evolution": {
        "influenced_by": ["Deuteronomy"],
        "influences": ["Judges", "1 Samuel"]
    },
    
    # Metadata
    "parsing_version": "2.0",
    "attribution_date": "2025-01-15",
    "validation_status": "pending"
}
```

## Implementation Phases

### Phase 1: Historical Books (Joshua - Chronicles)

**Timeline**: Months 1-3

**Focus**:
- Extend parser for historical narrative structure
- Develop D source (Deuteronomistic History) detection
- Identify P source patterns in Chronicles
- Create source attribution heuristics

### Phase 2: Wisdom Literature (Job - Song of Songs)

**Timeline**: Months 4-6

**Focus**:
- Specialized parser for poetic structures
- Theme-based source attribution
- Cross-reference with Torah theological patterns

### Phase 3: Prophetic Literature (Isaiah - Malachi)

**Timeline**: Months 7-9

**Focus**:
- Prophetic voice pattern identification
- Theological connection mapping
- Redaction layer analysis

### Phase 4: New Testament (Matthew - Revelation)

**Timeline**: Months 10-12

**Focus**:
- NT-specific source attribution model
- Torah quotation/allusion identification
- Theological theme mapping
- Comparative analysis framework

## Next Steps

1. **Create Configuration System**: Design and implement parser configuration
2. **Build Pattern Database**: Create comprehensive Torah pattern database
3. **Develop ML Models**: Train source classification models on Torah data
4. **Implement Heuristic Rules**: Create rule-based attribution system
5. **Scholar Annotation Interface**: Build interface for manual annotations
6. **Test with Sample Books**: Validate approach with selected books
7. **Full Bible Rollout**: Extend to all 66 books

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Status**: Design Phase

