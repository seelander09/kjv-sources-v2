# AI Learning System Architecture
## Torah Source Feature Comparison Framework

## Overview

This document describes the AI learning system designed to identify Torah source patterns (J, E, P, D, R) throughout the entire Bible, enabling comparative analysis and pattern discovery across all 66 books.

## Core Concept

The AI learning system trains models on confirmed Torah source patterns and applies them to identify similar patterns in other biblical books. This enables:

1. **Pattern Discovery**: Find instances of Torah source patterns in non-Torah books
2. **Comparative Analysis**: Compare how Torah sources appear in different contexts
3. **Theological Tracking**: Follow source themes across biblical timeline
4. **Redaction Analysis**: Identify how editors used Torah sources

## Architecture Components

### 1. Feature Extraction Framework

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re
from collections import Counter

@dataclass
class FeatureVector:
    """Comprehensive feature vector for source classification"""
    vocabulary_features: Dict[str, float]
    theological_features: Dict[str, float]
    style_features: Dict[str, float]
    structural_features: Dict[str, float]
    combined_score: float


class TorahFeatureExtractor:
    """Extract comprehensive features from biblical verses"""
    
    def __init__(self):
        self.vocab_patterns = self._load_vocabulary_patterns()
        self.theme_patterns = self._load_theological_themes()
        self.style_patterns = self._load_style_markers()
        self.structural_patterns = self._load_structural_patterns()
    
    def extract(self, verse_data: Dict[str, Any]) -> FeatureVector:
        """
        Extract comprehensive feature vector from verse.
        
        Args:
            verse_data: Dictionary containing verse information
            
        Returns:
            FeatureVector with all extracted features
        """
        text = verse_data.get("text", "").lower()
        
        vocab_features = self._extract_vocabulary(text)
        theme_features = self._extract_themes(text, verse_data)
        style_features = self._extract_style(text)
        structural_features = self._extract_structure(text, verse_data)
        
        return FeatureVector(
            vocabulary_features=vocab_features,
            theological_features=theme_features,
            style_features=style_features,
            structural_features=structural_features,
            combined_score=self._calculate_combined_score(
                vocab_features, theme_features, style_features, structural_features
            )
        )
    
    def _extract_vocabulary(self, text: str) -> Dict[str, float]:
        """Extract vocabulary-based features"""
        features = {}
        
        # J Source Vocabulary
        j_indicators = {
            "yhwh": 0.3, "lord": 0.3, "behold": 0.2, "it came to pass": 0.2,
            "god walked": 0.3, "face to face": 0.2, "anthropomorphic": 0.2
        }
        j_score = sum(score for word, score in j_indicators.items() if word in text)
        features["J"] = min(j_score, 1.0)
        
        # E Source Vocabulary
        e_indicators = {
            "elohim": 0.25, "angel of the lord": 0.3, "fear": 0.2,
            "dream": 0.2, "vision": 0.2, "prophetic": 0.2
        }
        e_score = sum(score for word, score in e_indicators.items() if word in text)
        features["E"] = min(e_score, 1.0)
        
        # P Source Vocabulary
        p_indicators = {
            "generations": 0.3, "according to their kinds": 0.3, "command": 0.2,
            "statute": 0.2, "ordinance": 0.2, "holy": 0.2, "systematic": 0.2
        }
        p_score = sum(score for word, score in p_indicators.items() if word in text)
        features["P"] = min(p_score, 1.0)
        
        # D Source Vocabulary
        d_indicators = {
            "listen": 0.2, "guard": 0.2, "observe": 0.2, "do": 0.2,
            "love": 0.2, "serve": 0.2, "fear": 0.2, "covenant": 0.2,
            "command": 0.15, "hearken": 0.15
        }
        d_score = sum(score for word, score in d_indicators.items() if word in text)
        features["D"] = min(d_score, 1.0)
        
        # R Source Vocabulary
        r_indicators = {
            "now": 0.15, "and": 0.1, "then": 0.15, "after": 0.15,
            "transitional": 0.2, "harmonizing": 0.2
        }
        r_score = sum(score for word, score in r_indicators.items() if word in text)
        features["R"] = min(r_score, 1.0)
        
        return features
    
    def _extract_themes(self, text: str, verse_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract theological theme features"""
        features = {}
        
        # J Themes: Anthropomorphic God, covenant, blessing/curse
        j_themes = {
            "anthropomorphic": 0.3, "god walks": 0.3, "god speaks": 0.2,
            "covenant": 0.2, "blessing": 0.2, "curse": 0.2, "human agency": 0.2
        }
        features["J"] = sum(score for theme, score in j_themes.items() if theme in text)
        
        # E Themes: Divine communication, fear of God, prophetic
        e_themes = {
            "divine communication": 0.3, "angel": 0.3, "fear of god": 0.3,
            "prophetic calling": 0.3, "dream": 0.2, "vision": 0.2
        }
        features["E"] = sum(score for theme, score in e_themes.items() if theme in text)
        
        # P Themes: Order, system, ritual, holiness
        p_themes = {
            "order": 0.3, "system": 0.3, "ritual": 0.3, "holiness": 0.3,
            "genealogy": 0.3, "legal": 0.2, "command": 0.2
        }
        features["P"] = sum(score for theme, score in p_themes.items() if theme in text)
        
        # D Themes: Law, covenant, obedience, land
        d_themes = {
            "law": 0.3, "covenant": 0.3, "obedience": 0.3, "land": 0.3,
            "history": 0.2, "command": 0.2, "serve": 0.2
        }
        features["D"] = sum(score for theme, score in d_themes.items() if theme in text)
        
        # R Themes: Unity, continuity, harmonization
        r_themes = {
            "unity": 0.3, "continuity": 0.3, "harmonization": 0.3,
            "transition": 0.2, "connection": 0.2
        }
        features["R"] = sum(score for theme, score in r_themes.items() if theme in text)
        
        # Normalize scores
        for key in features:
            features[key] = min(features[key], 1.0)
        
        return features
    
    def _extract_style(self, text: str) -> Dict[str, float]:
        """Extract literary style features"""
        features = {}
        
        # Sentence complexity
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # J Style: Narrative, dialogue-rich
        dialogue_indicators = ['"', "'", 'said', 'spake', 'answered']
        has_dialogue = any(indicator in text for indicator in dialogue_indicators)
        features["J"] = 0.5 if has_dialogue else 0.2
        features["J"] += 0.3 if avg_sentence_length < 15 else 0.1
        
        # P Style: Systematic, formulaic, repetitive
        formulaic_patterns = ["according to", "these are", "generations"]
        has_formulaic = sum(1 for pattern in formulaic_patterns if pattern in text)
        features["P"] = min(has_formulaic * 0.3, 1.0)
        features["P"] += 0.3 if avg_sentence_length > 20 else 0.1
        
        # D Style: Rhetorical, hortatory
        rhetorical_markers = ["therefore", "now", "remember", "take heed"]
        has_rhetorical = sum(1 for marker in rhetorical_markers if marker in text)
        features["D"] = min(has_rhetorical * 0.25, 1.0)
        
        # E Style: Prophetic, visionary
        visionary_markers = ["behold", "lo", "see", "vision"]
        has_visionary = sum(1 for marker in visionary_markers if marker in text)
        features["E"] = min(has_visionary * 0.3, 1.0)
        
        # R Style: Transitional
        transitional_markers = ["and", "now", "then", "after"]
        has_transitional = sum(1 for marker in transitional_markers if marker in text)
        features["R"] = min(has_transitional * 0.2, 1.0)
        
        return features
    
    def _extract_structure(self, text: str, verse_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract structural pattern features"""
        features = {}
        
        # Check for genealogical structure (P indicator)
        if "son of" in text or "begat" in text or "generations" in text:
            features["P"] = 0.8
        
        # Check for legal code structure (P/D indicator)
        if "command" in text and ("law" in text or "statute" in text):
            features["P"] = features.get("P", 0) + 0.3
            features["D"] = features.get("D", 0) + 0.3
        
        # Check for covenant formula (J/D indicator)
        if "covenant" in text and ("god" in text or "lord" in text):
            features["J"] = features.get("J", 0) + 0.3
            features["D"] = features.get("D", 0) + 0.3
        
        # Check for narrative structure (J indicator)
        if verse_data.get("chapter", 0) > 0 and verse_data.get("verse", 0) > 0:
            # Narrative verses typically have multiple clauses
            clauses = text.count(',') + text.count(';')
            if clauses > 2:
                features["J"] = features.get("J", 0) + 0.2
        
        return features
    
    def _calculate_combined_score(self, vocab: Dict, theme: Dict, 
                                  style: Dict, structure: Dict) -> float:
        """Calculate combined confidence score"""
        sources = ["J", "E", "P", "D", "R"]
        combined_scores = {}
        
        for source in sources:
            combined_scores[source] = (
                vocab.get(source, 0) * 0.3 +
                theme.get(source, 0) * 0.3 +
                style.get(source, 0) * 0.2 +
                structure.get(source, 0) * 0.2
            )
        
        return max(combined_scores.values()) if combined_scores else 0.0
```

### 2. Source Classification Model

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import pickle
import numpy as np

class SourceClassificationModel:
    """ML model for classifying verses by source"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_extractor = TorahFeatureExtractor()
        
        if model_path:
            self.load_model(model_path)
        else:
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
    
    def train(self, training_data: List[Dict[str, Any]]):
        """
        Train model on confirmed Torah source data.
        
        Args:
            training_data: List of verse data with confirmed sources
        """
        X = []
        y = []
        
        for verse in training_data:
            # Extract features
            features = self.feature_extractor.extract(verse)
            
            # Create feature vector
            feature_vector = self._vectorize_features(features)
            X.append(feature_vector)
            
            # Get label (primary source)
            sources = verse.get("sources", [])
            label = sources[0] if sources else "UNKNOWN"
            y.append(label)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        print("Classification Report:")
        print(classification_report(y_test, y_pred))
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
    
    def predict(self, verse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict source for a verse"""
        features = self.feature_extractor.extract(verse_data)
        feature_vector = self._vectorize_features(features)
        
        # Get predictions
        probabilities = self.model.predict_proba([feature_vector])[0]
        predicted_class = self.model.predict([feature_vector])[0]
        
        # Map to source codes
        source_map = self.model.classes_
        source_probs = {
            source: float(prob) 
            for source, prob in zip(source_map, probabilities)
        }
        
        return {
            "predicted_source": predicted_class,
            "confidence": float(max(probabilities)),
            "source_probabilities": source_probs
        }
    
    def _vectorize_features(self, features: FeatureVector) -> np.ndarray:
        """Convert FeatureVector to numpy array"""
        vector = []
        
        # Vocabulary features
        for source in ["J", "E", "P", "D", "R"]:
            vector.append(features.vocabulary_features.get(source, 0.0))
        
        # Theological features
        for source in ["J", "E", "P", "D", "R"]:
            vector.append(features.theological_features.get(source, 0.0))
        
        # Style features
        for source in ["J", "E", "P", "D", "R"]:
            vector.append(features.style_features.get(source, 0.0))
        
        # Structural features
        for source in ["J", "E", "P", "D", "R"]:
            vector.append(features.structural_features.get(source, 0.0))
        
        return np.array(vector)
    
    def save_model(self, file_path: str):
        """Save trained model to file"""
        with open(file_path, 'wb') as f:
            pickle.dump(self.model, f)
    
    def load_model(self, file_path: str):
        """Load model from file"""
        with open(file_path, 'rb') as f:
            self.model = pickle.load(f)
```

### 3. Pattern Recognition Model

```python
class PatternMatchingModel:
    """Identify Torah source patterns in non-Torah books"""
    
    def __init__(self):
        self.torah_patterns = self._load_torah_patterns()
        self.feature_extractor = TorahFeatureExtractor()
    
    def identify_patterns(self, verse_data: Dict[str, Any], 
                         threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Identify Torah source patterns in verse.
        
        Args:
            verse_data: Verse data to analyze
            threshold: Minimum confidence threshold
            
        Returns:
            List of pattern matches
        """
        verse_features = self.feature_extractor.extract(verse_data)
        matches = []
        
        for source, patterns in self.torah_patterns.items():
            for pattern_name, pattern_features in patterns.items():
                similarity = self._calculate_similarity(
                    verse_features, pattern_features
                )
                
                if similarity >= threshold:
                    matches.append({
                        "source": source,
                        "pattern": pattern_name,
                        "similarity": similarity,
                        "confidence": similarity
                    })
        
        return sorted(matches, key=lambda x: x["similarity"], reverse=True)
    
    def _calculate_similarity(self, verse_features: FeatureVector, 
                              pattern_features: FeatureVector) -> float:
        """Calculate similarity between verse and pattern"""
        # Weighted cosine similarity
        weights = {
            "vocabulary": 0.3,
            "theological": 0.3,
            "style": 0.2,
            "structural": 0.2
        }
        
        similarity = 0.0
        
        # Vocabulary similarity
        vocab_sim = self._dict_similarity(
            verse_features.vocabulary_features,
            pattern_features.vocabulary_features
        )
        similarity += vocab_sim * weights["vocabulary"]
        
        # Theological similarity
        theme_sim = self._dict_similarity(
            verse_features.theological_features,
            pattern_features.theological_features
        )
        similarity += theme_sim * weights["theological"]
        
        # Style similarity
        style_sim = self._dict_similarity(
            verse_features.style_features,
            pattern_features.style_features
        )
        similarity += style_sim * weights["style"]
        
        # Structural similarity
        struct_sim = self._dict_similarity(
            verse_features.structural_features,
            pattern_features.structural_features
        )
        similarity += struct_sim * weights["structural"]
        
        return similarity
    
    def _dict_similarity(self, dict1: Dict, dict2: Dict) -> float:
        """Calculate similarity between two dictionaries"""
        keys = set(dict1.keys()) | set(dict2.keys())
        if not keys:
            return 0.0
        
        sum_sq_diff = sum((dict1.get(k, 0) - dict2.get(k, 0))**2 for k in keys)
        return 1.0 / (1.0 + sum_sq_diff)
```

### 4. Comparative Analysis Model

```python
class ComparativeAnalysisModel:
    """Compare Torah sources with other biblical books"""
    
    def __init__(self):
        self.feature_extractor = TorahFeatureExtractor()
    
    def compare(self, torah_verse: Dict[str, Any], 
                comparison_verse: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare Torah verse with verse from another book.
        
        Args:
            torah_verse: Verse from Torah
            comparison_verse: Verse from comparison book
            
        Returns:
            Comparison report
        """
        torah_features = self.feature_extractor.extract(torah_verse)
        comparison_features = self.feature_extractor.extract(comparison_verse)
        
        similarities = self._calculate_feature_similarities(
            torah_features, comparison_features
        )
        
        differences = self._identify_differences(
            torah_features, comparison_features
        )
        
        return {
            "torah_reference": f"{torah_verse['book']} {torah_verse['chapter']}:{torah_verse['verse']}",
            "comparison_reference": f"{comparison_verse['book']} {comparison_verse['chapter']}:{comparison_verse['verse']}",
            "similarities": similarities,
            "differences": differences,
            "overall_similarity": sum(similarities.values()) / len(similarities),
            "source_match": self._determine_source_match(torah_verse, comparison_verse)
        }
    
    def _calculate_feature_similarities(self, torah_features: FeatureVector,
                                        comparison_features: FeatureVector) -> Dict[str, float]:
        """Calculate similarity for each feature type"""
        return {
            "vocabulary": self._dict_similarity(
                torah_features.vocabulary_features,
                comparison_features.vocabulary_features
            ),
            "theological": self._dict_similarity(
                torah_features.theological_features,
                comparison_features.theological_features
            ),
            "style": self._dict_similarity(
                torah_features.style_features,
                comparison_features.style_features
            ),
            "structural": self._dict_similarity(
                torah_features.structural_features,
                comparison_features.structural_features
            )
        }
    
    def _identify_differences(self, torah_features: FeatureVector,
                            comparison_features: FeatureVector) -> Dict[str, List[str]]:
        """Identify key differences between verses"""
        differences = {
            "vocabulary": [],
            "theological": [],
            "style": [],
            "structural": []
        }
        
        # Compare vocabulary
        for source in ["J", "E", "P", "D", "R"]:
            torah_score = torah_features.vocabulary_features.get(source, 0)
            comp_score = comparison_features.vocabulary_features.get(source, 0)
            if abs(torah_score - comp_score) > 0.3:
                differences["vocabulary"].append(
                    f"{source}: {torah_score:.2f} vs {comp_score:.2f}"
                )
        
        return differences
    
    def _determine_source_match(self, torah_verse: Dict, comparison_verse: Dict) -> bool:
        """Determine if verses match in source attribution"""
        torah_sources = set(torah_verse.get("sources", []))
        comp_sources = set(comparison_verse.get("sources", []))
        return len(torah_sources & comp_sources) > 0
```

## Main AI Learning System

```python
class TorahSourceAILearner:
    """Main AI system for learning Torah source patterns"""
    
    def __init__(self):
        self.feature_extractor = TorahFeatureExtractor()
        self.source_classifier = SourceClassificationModel()
        self.pattern_matcher = PatternMatchingModel()
        self.comparative_analyzer = ComparativeAnalysisModel()
    
    def train_on_torah_data(self, torah_verses: List[Dict[str, Any]]):
        """Train models on confirmed Torah source data"""
        print("Training source classification model...")
        self.source_classifier.train(torah_verses)
        print("Training complete!")
    
    def identify_patterns_in_book(self, book_name: str, 
                                   threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Identify Torah source patterns in any biblical book"""
        # Load verses from book
        # Extract features for each verse
        # Compare with Torah source patterns
        # Return matches with confidence scores
        pass
    
    def compare_torah_with_book(self, torah_source: str, 
                                comparison_book: str) -> Dict[str, Any]:
        """Compare how Torah source appears in another book"""
        # Get Torah source examples
        # Get comparison book verses
        # Extract features from both
        # Compute similarity and differences
        # Generate comparison report
        pass
```

## Training Data Generation

### Data Collection

1. **Torah Ground Truth**: 5,852 verses with confirmed sources
2. **Scholar Annotations**: Manual annotations for key passages
3. **Pattern Examples**: Curated examples of source patterns
4. **Comparative Examples**: Paired examples (Torah + other books)

### Data Augmentation

- Paraphrase generation (same meaning, different words)
- Synonym replacement (maintain source features)
- Style transfer (adapt source style to different contexts)
- Negative examples (non-source patterns)

## Implementation Roadmap

### Phase 1: Feature Extraction (Months 1-2)
- Implement feature extraction framework
- Create pattern databases
- Validate feature extraction accuracy

### Phase 2: Model Training (Months 3-4)
- Train source classification models
- Validate on Torah test set
- Optimize model performance

### Phase 3: Pattern Recognition (Months 5-6)
- Implement pattern matching system
- Test on sample non-Torah books
- Refine pattern matching algorithms

### Phase 4: Comparative Analysis (Months 7-8)
- Build comparative analysis tools
- Generate comparison reports
- Validate with scholars

### Phase 5: Full Integration (Months 9-12)
- Integrate with full Bible parser
- Deploy to production
- Continuous learning system

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Status**: Design Phase

