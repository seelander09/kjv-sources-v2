#!/usr/bin/env python3
"""
Train ML Model on Torah Source Data
===================================

Trains a source classification model using confirmed Torah verse data (5,852 verses).
This model will be used to identify Torah source patterns in other biblical books.
"""

import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import re
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Source colors mapping
SOURCE_COLORS = {
    'J': '#000088',
    'E': '#008888',
    'P': '#888800',
    'D': '#000000',
    'R': '#880000'
}


@dataclass
class FeatureVector:
    """Feature vector for source classification"""
    vocabulary_features: Dict[str, float]
    theological_features: Dict[str, float]
    style_features: Dict[str, float]
    structural_features: Dict[str, float]
    combined_score: float = 0.0


class TorahFeatureExtractor:
    """Extract comprehensive features from biblical verses"""
    
    def __init__(self):
        self.vocab_patterns = self._load_vocabulary_patterns()
        self.theme_patterns = self._load_theological_themes()
        self.style_patterns = self._load_style_markers()
        self.structural_patterns = self._load_structural_patterns()
    
    def _load_vocabulary_patterns(self) -> Dict[str, Dict[str, float]]:
        """Load vocabulary patterns for each source"""
        return {
            'J': {
                'yhwh': 0.3, 'lord': 0.3, 'behold': 0.2, 'it came to pass': 0.2,
                'god walked': 0.3, 'face to face': 0.2, 'anthropomorphic': 0.2,
                'came to pass': 0.15, 'spake': 0.15, 'said': 0.1
            },
            'E': {
                'elohim': 0.25, 'angel of the lord': 0.3, 'fear': 0.2,
                'dream': 0.2, 'vision': 0.2, 'prophetic': 0.2,
                'angel': 0.25, 'fear of god': 0.2
            },
            'P': {
                'generations': 0.3, 'according to their kinds': 0.3, 'command': 0.2,
                'statute': 0.2, 'ordinance': 0.2, 'holy': 0.2, 'systematic': 0.2,
                'begat': 0.25, 'son of': 0.2, 'these are': 0.2
            },
            'D': {
                'listen': 0.2, 'guard': 0.2, 'observe': 0.2, 'do': 0.2,
                'love': 0.2, 'serve': 0.2, 'fear': 0.2, 'covenant': 0.2,
                'command': 0.15, 'hearken': 0.15, 'keep': 0.15, 'perform': 0.15
            },
            'R': {
                'now': 0.15, 'and': 0.1, 'then': 0.15, 'after': 0.15,
                'transitional': 0.2, 'harmonizing': 0.2, 'therefore': 0.1
            }
        }
    
    def _load_theological_themes(self) -> Dict[str, List[str]]:
        """Load theological theme keywords"""
        return {
            'J': ['anthropomorphic', 'god walks', 'god speaks', 'covenant', 'blessing', 'curse', 'human agency'],
            'E': ['divine communication', 'angel', 'fear of god', 'prophetic calling', 'dream', 'vision'],
            'P': ['order', 'system', 'ritual', 'holiness', 'genealogy', 'legal', 'command'],
            'D': ['law', 'covenant', 'obedience', 'land', 'history', 'command', 'serve'],
            'R': ['unity', 'continuity', 'harmonization', 'transition', 'connection']
        }
    
    def _load_style_markers(self) -> Dict[str, List[str]]:
        """Load literary style markers"""
        return {
            'J': ['said', 'spake', 'answered', 'behold'],
            'E': ['behold', 'lo', 'see', 'vision'],
            'P': ['according to', 'these are', 'generations'],
            'D': ['therefore', 'now', 'remember', 'take heed'],
            'R': ['and', 'now', 'then', 'after']
        }
    
    def _load_structural_patterns(self) -> Dict[str, List[str]]:
        """Load structural pattern indicators"""
        return {
            'P': ['genealogy', 'legal code', 'systematic list'],
            'D': ['covenant formula', 'legal instruction', 'historical review'],
            'J': ['narrative', 'dialogue', 'story'],
            'E': ['vision', 'dream', 'prophetic'],
            'R': ['transition', 'connection', 'harmonization']
        }
    
    def extract(self, verse_data: Dict[str, Any]) -> FeatureVector:
        """Extract comprehensive feature vector from verse"""
        text = verse_data.get('text', '').lower()
        
        vocab_features = self._extract_vocabulary(text)
        theme_features = self._extract_themes(text, verse_data)
        style_features = self._extract_style(text)
        structural_features = self._extract_structure(text, verse_data)
        
        combined_score = self._calculate_combined_score(
            vocab_features, theme_features, style_features, structural_features
        )
        
        return FeatureVector(
            vocabulary_features=vocab_features,
            theological_features=theme_features,
            style_features=style_features,
            structural_features=structural_features,
            combined_score=combined_score
        )
    
    def _extract_vocabulary(self, text: str) -> Dict[str, float]:
        """Extract vocabulary-based features"""
        features = {}
        
        for source, patterns in self.vocab_patterns.items():
            score = 0.0
            for word, weight in patterns.items():
                if word in text:
                    score += weight
            features[source] = min(score, 1.0)
        
        return features
    
    def _extract_themes(self, text: str, verse_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract theological theme features"""
        features = {}
        
        for source, themes in self.theme_patterns.items():
            score = 0.0
            for theme in themes:
                if theme in text:
                    score += 0.15
            features[source] = min(score, 1.0)
        
        return features
    
    def _extract_style(self, text: str) -> Dict[str, float]:
        """Extract literary style features"""
        features = {}
        
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # J Style: Narrative, dialogue-rich
        dialogue_indicators = ['"', "'", 'said', 'spake', 'answered']
        has_dialogue = any(indicator in text for indicator in dialogue_indicators)
        features['J'] = 0.5 if has_dialogue else 0.2
        features['J'] += 0.3 if avg_sentence_length < 15 else 0.1
        
        # P Style: Systematic, formulaic
        formulaic_patterns = ['according to', 'these are', 'generations']
        has_formulaic = sum(1 for pattern in formulaic_patterns if pattern in text)
        features['P'] = min(has_formulaic * 0.3, 1.0)
        features['P'] += 0.3 if avg_sentence_length > 20 else 0.1
        
        # D Style: Rhetorical
        rhetorical_markers = ['therefore', 'now', 'remember', 'take heed']
        has_rhetorical = sum(1 for marker in rhetorical_markers if marker in text)
        features['D'] = min(has_rhetorical * 0.25, 1.0)
        
        # E Style: Prophetic
        visionary_markers = ['behold', 'lo', 'see', 'vision']
        has_visionary = sum(1 for marker in visionary_markers if marker in text)
        features['E'] = min(has_visionary * 0.3, 1.0)
        
        # R Style: Transitional
        transitional_markers = ['and', 'now', 'then', 'after']
        has_transitional = sum(1 for marker in transitional_markers if marker in text)
        features['R'] = min(has_transitional * 0.2, 1.0)
        
        return features
    
    def _extract_structure(self, text: str, verse_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract structural pattern features"""
        features = {}
        
        # Genealogical structure (P indicator)
        if 'son of' in text or 'begat' in text or 'generations' in text:
            features['P'] = 0.8
        
        # Legal code structure
        if 'command' in text and ('law' in text or 'statute' in text):
            features['P'] = features.get('P', 0) + 0.3
            features['D'] = features.get('D', 0) + 0.3
        
        # Covenant formula
        if 'covenant' in text and ('god' in text or 'lord' in text):
            features['J'] = features.get('J', 0) + 0.3
            features['D'] = features.get('D', 0) + 0.3
        
        # Narrative structure
        if verse_data.get('chapter', 0) > 0:
            clauses = text.count(',') + text.count(';')
            if clauses > 2:
                features['J'] = features.get('J', 0) + 0.2
        
        return features
    
    def _calculate_combined_score(self, vocab: Dict, theme: Dict, 
                                  style: Dict, structure: Dict) -> float:
        """Calculate combined confidence score"""
        sources = ['J', 'E', 'P', 'D', 'R']
        combined_scores = {}
        
        for source in sources:
            combined_scores[source] = (
                vocab.get(source, 0) * 0.3 +
                theme.get(source, 0) * 0.3 +
                style.get(source, 0) * 0.2 +
                structure.get(source, 0) * 0.2
            )
        
        return max(combined_scores.values()) if combined_scores else 0.0


class TorahSourceModelTrainer:
    """Train source classification model on Torah data"""
    
    def __init__(self, output_dir: str = "models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.feature_extractor = TorahFeatureExtractor()
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.trained = False
    
    def load_torah_data(self) -> List[Dict[str, Any]]:
        """Load Torah verse data from Qdrant or CSV files"""
        verses = []
        
        # Try loading from CSV files first
        books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
        output_dir = Path('output')
        
        for book in books:
            csv_path = output_dir / book / f"{book}.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                for _, row in df.iterrows():
                    sources = str(row.get('sources', '')).split(';')
                    sources = [s.strip() for s in sources if s.strip()]
                    
                    if sources:
                        verses.append({
                            'book': book,
                            'chapter': int(row.get('chapter', 0)),
                            'verse': int(row.get('verse', 0)),
                            'text': str(row.get('full_text', row.get('text', ''))),
                            'sources': sources,
                            'primary_source': sources[0]
                        })
        
        print(f"✅ Loaded {len(verses)} verses from Torah books")
        return verses
    
    def prepare_training_data(self, verses: List[Dict[str, Any]]) -> tuple:
        """Prepare feature vectors and labels for training"""
        X = []
        y = []
        
        print("📊 Extracting features from verses...")
        for i, verse in enumerate(verses):
            if (i + 1) % 500 == 0:
                print(f"   Processed {i + 1}/{len(verses)} verses...")
            
            # Extract features
            features = self.feature_extractor.extract(verse)
            
            # Create feature vector
            feature_vector = self._vectorize_features(features)
            X.append(feature_vector)
            
            # Get label (primary source)
            sources = verse.get('sources', [])
            label = sources[0] if sources else 'UNKNOWN'
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"✅ Prepared {len(X)} feature vectors")
        print(f"   Feature dimensions: {X.shape[1]}")
        print(f"   Classes: {np.unique(y)}")
        
        return X, y
    
    def _vectorize_features(self, features: FeatureVector) -> np.ndarray:
        """Convert FeatureVector to numpy array"""
        vector = []
        sources = ['J', 'E', 'P', 'D', 'R']
        
        # Vocabulary features (5 features)
        for source in sources:
            vector.append(features.vocabulary_features.get(source, 0.0))
        
        # Theological features (5 features)
        for source in sources:
            vector.append(features.theological_features.get(source, 0.0))
        
        # Style features (5 features)
        for source in sources:
            vector.append(features.style_features.get(source, 0.0))
        
        # Structural features (5 features)
        for source in sources:
            vector.append(features.structural_features.get(source, 0.0))
        
        return np.array(vector)
    
    def train(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2):
        """Train the model"""
        print("\n🔬 Training model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n✅ Model training complete!")
        print(f"   Training set: {len(X_train)} verses")
        print(f"   Test set: {len(X_test)} verses")
        print(f"   Accuracy: {accuracy:.2%}")
        
        print("\n📊 Classification Report:")
        print(classification_report(y_test, y_pred))
        
        print("\n📈 Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        # Cross-validation
        print("\n🔄 Cross-validation scores:")
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        print(f"   Mean: {cv_scores.mean():.2%} (+/- {cv_scores.std() * 2:.2%})")
        
        self.trained = True
        return accuracy
    
    def save_model(self, filename: str = "torah_source_classifier.pkl"):
        """Save trained model"""
        if not self.trained:
            raise ValueError("Model must be trained before saving")
        
        model_path = self.output_dir / filename
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_extractor': self.feature_extractor,
                'version': '1.0'
            }, f)
        
        print(f"\n💾 Model saved to: {model_path}")
        return model_path
    
    def load_model(self, filename: str = "torah_source_classifier.pkl"):
        """Load trained model"""
        model_path = self.output_dir / filename
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.feature_extractor = data.get('feature_extractor', TorahFeatureExtractor())
            self.trained = True
        
        print(f"✅ Model loaded from: {model_path}")
    
    def predict(self, verse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict source for a verse"""
        if not self.trained:
            raise ValueError("Model must be trained or loaded before prediction")
        
        features = self.feature_extractor.extract(verse_data)
        feature_vector = self._vectorize_features(features)
        feature_vector_scaled = self.scaler.transform([feature_vector])
        
        # Get predictions
        predicted_class = self.model.predict(feature_vector_scaled)[0]
        probabilities = self.model.predict_proba(feature_vector_scaled)[0]
        
        # Map to source codes
        source_map = self.model.classes_
        source_probs = {
            source: float(prob) 
            for source, prob in zip(source_map, probabilities)
        }
        
        return {
            'predicted_source': predicted_class,
            'confidence': float(max(probabilities)),
            'source_probabilities': source_probs,
            'features': {
                'vocabulary': features.vocabulary_features,
                'theological': features.theological_features,
                'style': features.style_features,
                'structural': features.structural_features
            }
        }


def main():
    """Main training function"""
    print("=" * 60)
    print("Torah Source Classification Model Training")
    print("=" * 60)
    
    # Initialize trainer
    trainer = TorahSourceModelTrainer()
    
    # Load Torah data
    verses = trainer.load_torah_data()
    
    if len(verses) == 0:
        print("❌ No verse data found. Please run the pipeline first.")
        return
    
    # Prepare training data
    X, y = trainer.prepare_training_data(verses)
    
    # Train model
    accuracy = trainer.train(X, y)
    
    # Save model
    model_path = trainer.save_model()
    
    print("\n" + "=" * 60)
    print("✅ Training complete!")
    print(f"   Model accuracy: {accuracy:.2%}")
    print(f"   Model saved to: {model_path}")
    print("=" * 60)
    
    # Test prediction
    print("\n🧪 Testing prediction on sample verse...")
    sample_verse = verses[0]
    prediction = trainer.predict(sample_verse)
    print(f"   Verse: {sample_verse['book']} {sample_verse['chapter']}:{sample_verse['verse']}")
    print(f"   Actual source: {sample_verse['primary_source']}")
    print(f"   Predicted source: {prediction['predicted_source']}")
    print(f"   Confidence: {prediction['confidence']:.2%}")


if __name__ == "__main__":
    main()

