#!/usr/bin/env python3
"""
Research Validation Pipeline for KJV Sources Project
==================================================

This module integrates real-time scholarly research validation with the existing
parsing pipeline to ensure source attributions are validated against current
academic scholarship.

Features:
- Real-time source validation during parsing
- Integration with existing parse_wikitext.py pipeline
- Automated research gathering for source validation
- Enhanced confidence scoring with scholarly consensus
- Research-informed source attribution corrections
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Import existing parsing components
import sys
sys.path.append(str(Path(__file__).parent))

# Import research tool
from duckduckgo_research_tool import DuckDuckGoResearchTool, SourceValidation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidatedVerse:
    """Enhanced verse data with research validation"""
    book: str
    chapter: int
    verse: int
    text: str
    sources: Dict[str, str]  # source_id -> text
    original_confidence: float
    research_validation: Optional[SourceValidation]
    validated_confidence: float
    validation_status: str  # 'validated', 'disputed', 'needs_review', 'error'
    research_notes: List[str]
    timestamp: str

@dataclass
class ValidationReport:
    """Report of validation results for a book or batch"""
    book: str
    total_verses: int
    validated_verses: int
    disputed_verses: int
    error_verses: int
    average_confidence: float
    validation_summary: Dict[str, int]
    recommendations: List[str]
    timestamp: str

class ResearchValidationPipeline:
    """Main validation pipeline for biblical source attributions"""
    
    def __init__(self, research_output_dir: str = "research_output"):
        self.research_output_dir = Path(research_output_dir)
        self.research_output_dir.mkdir(exist_ok=True)
        
        self.research_tool = DuckDuckGoResearchTool(str(research_output_dir))
        
        # Validation settings
        self.auto_validate = True
        self.validation_threshold = 0.7  # Minimum confidence for auto-validation
        self.research_cache_duration = 24  # hours
        self.max_concurrent_validations = 5
        
        # Validation cache
        self.validation_cache = {}
        
        # Statistics
        self.validation_stats = {
            'total_validated': 0,
            'disputed_found': 0,
            'errors_encountered': 0,
            'cache_hits': 0
        }

    async def validate_parsed_verses(self, verses_data: List[Dict[str, Any]], 
                                   book: str = "Unknown") -> List[ValidatedVerse]:
        """
        Validate a list of parsed verses against current scholarship
        
        Args:
            verses_data: List of verse data from parsing pipeline
            book: Biblical book name
            
        Returns:
            List of ValidatedVerse objects with research validation
        """
        try:
            logger.info(f"Starting validation for {len(verses_data)} verses in {book}")
            
            validated_verses = []
            
            # Process verses in batches to avoid overwhelming the research API
            batch_size = self.max_concurrent_validations
            for i in range(0, len(verses_data), batch_size):
                batch = verses_data[i:i + batch_size]
                batch_results = await self._validate_verse_batch(batch, book)
                validated_verses.extend(batch_results)
                
                # Log progress
                logger.info(f"Validated batch {i//batch_size + 1}/{(len(verses_data) + batch_size - 1)//batch_size}")
            
            # Update statistics
            self.validation_stats['total_validated'] += len(validated_verses)
            
            logger.info(f"Validation completed for {book}: {len(validated_verses)} verses processed")
            return validated_verses
            
        except Exception as e:
            logger.error(f"Error validating verses for {book}: {e}")
            return []

    async def _validate_verse_batch(self, verses_batch: List[Dict[str, Any]], 
                                  book: str) -> List[ValidatedVerse]:
        """
        Validate a batch of verses concurrently
        
        Args:
            verses_batch: Batch of verse data
            book: Biblical book name
            
        Returns:
            List of ValidatedVerse objects
        """
        try:
            # Create validation tasks
            validation_tasks = []
            for verse_data in verses_batch:
                task = self._validate_single_verse(verse_data, book)
                validation_tasks.append(task)
            
            # Execute validations concurrently
            validated_verses = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Filter out exceptions and log errors
            valid_results = []
            for i, result in enumerate(validated_verses):
                if isinstance(result, Exception):
                    logger.error(f"Validation error for verse {i}: {result}")
                    self.validation_stats['errors_encountered'] += 1
                else:
                    valid_results.append(result)
            
            return valid_results
            
        except Exception as e:
            logger.error(f"Error validating verse batch: {e}")
            return []

    async def _validate_single_verse(self, verse_data: Dict[str, Any], 
                                   book: str) -> ValidatedVerse:
        """
        Validate a single verse against current scholarship
        
        Args:
            verse_data: Single verse data from parsing pipeline
            book: Biblical book name
            
        Returns:
            ValidatedVerse object
        """
        try:
            # Extract verse information
            verse_ref = f"{book} {verse_data.get('chapter', 1)}:{verse_data.get('verse', 1)}"
            sources = verse_data.get('sources', {})
            original_confidence = verse_data.get('confidence', 0.0)
            
            # Check cache first
            cache_key = f"{book}_{verse_data.get('chapter', 1)}_{verse_data.get('verse', 1)}"
            if cache_key in self.validation_cache:
                cached_validation = self.validation_cache[cache_key]
                if self._is_cache_valid(cached_validation['timestamp']):
                    self.validation_stats['cache_hits'] += 1
                    return self._create_validated_verse(verse_data, cached_validation['validation'], book)
            
            # Validate each source in the verse
            source_validations = []
            research_notes = []
            validation_status = "validated"
            validated_confidence = original_confidence
            
            for source_id, source_text in sources.items():
                if source_id in ['J', 'E', 'P', 'D', 'R']:
                    validation = await self.research_tool.validate_source_attribution(source_id, verse_ref)
                    source_validations.append(validation)
                    
                    # Analyze validation results
                    if validation.validation_status == "disputed":
                        validation_status = "disputed"
                        research_notes.append(f"{source_id} source attribution is disputed in current scholarship")
                        self.validation_stats['disputed_found'] += 1
                    elif validation.validation_status == "outdated":
                        validation_status = "needs_review"
                        research_notes.append(f"{source_id} source attribution may be outdated")
                    elif validation.validation_status == "new_evidence":
                        research_notes.append(f"New evidence supports {source_id} source attribution")
                    
                    # Adjust confidence based on scholarly consensus
                    if validation.scholarly_consensus < 0.5:
                        validated_confidence *= 0.8  # Reduce confidence for disputed sources
                    elif validation.scholarly_consensus > 0.8:
                        validated_confidence *= 1.1  # Increase confidence for well-supported sources
                        validated_confidence = min(validated_confidence, 1.0)  # Cap at 1.0
            
            # Create combined validation result
            combined_validation = self._combine_source_validations(source_validations, verse_ref)
            
            # Cache the validation result
            self.validation_cache[cache_key] = {
                'validation': combined_validation,
                'timestamp': datetime.now().isoformat()
            }
            
            return self._create_validated_verse(verse_data, combined_validation, book, 
                                              validation_status, research_notes, validated_confidence)
            
        except Exception as e:
            logger.error(f"Error validating single verse: {e}")
            self.validation_stats['errors_encountered'] += 1
            return self._create_validated_verse(verse_data, None, book, "error", [str(e)], 0.0)

    def _combine_source_validations(self, source_validations: List[SourceValidation], 
                                  verse_ref: str) -> SourceValidation:
        """
        Combine multiple source validations into a single result
        
        Args:
            source_validations: List of individual source validations
            verse_ref: Verse reference
            
        Returns:
            Combined SourceValidation object
        """
        if not source_validations:
            return SourceValidation(
                source_identifier="Multiple",
                verse_reference=verse_ref,
                validation_status="no_data",
                scholarly_consensus=0.5,
                supporting_sources=[],
                conflicting_sources=[],
                last_updated=datetime.now().isoformat()
            )
        
        # Combine supporting and conflicting sources
        all_supporting = []
        all_conflicting = []
        
        for validation in source_validations:
            all_supporting.extend(validation.supporting_sources)
            all_conflicting.extend(validation.conflicting_sources)
        
        # Calculate combined consensus
        if source_validations:
            combined_consensus = sum(v.scholarly_consensus for v in source_validations) / len(source_validations)
        else:
            combined_consensus = 0.5
        
        # Determine combined status
        statuses = [v.validation_status for v in source_validations]
        if "disputed" in statuses:
            combined_status = "disputed"
        elif "outdated" in statuses:
            combined_status = "needs_review"
        elif "confirmed" in statuses:
            combined_status = "confirmed"
        else:
            combined_status = "mixed"
        
        return SourceValidation(
            source_identifier="Multiple",
            verse_reference=verse_ref,
            validation_status=combined_status,
            scholarly_consensus=combined_consensus,
            supporting_sources=all_supporting,
            conflicting_sources=all_conflicting,
            last_updated=datetime.now().isoformat()
        )

    def _create_validated_verse(self, verse_data: Dict[str, Any], validation: Optional[SourceValidation],
                              book: str, status: str = "validated", notes: List[str] = None,
                              confidence: float = None) -> ValidatedVerse:
        """
        Create a ValidatedVerse object from verse data and validation results
        
        Args:
            verse_data: Original verse data
            validation: Research validation results
            book: Biblical book name
            status: Validation status
            notes: Research notes
            confidence: Validated confidence score
            
        Returns:
            ValidatedVerse object
        """
        if notes is None:
            notes = []
        if confidence is None:
            confidence = verse_data.get('confidence', 0.0)
        
        return ValidatedVerse(
            book=book,
            chapter=verse_data.get('chapter', 1),
            verse=verse_data.get('verse', 1),
            text=verse_data.get('text', ''),
            sources=verse_data.get('sources', {}),
            original_confidence=verse_data.get('confidence', 0.0),
            research_validation=validation,
            validated_confidence=confidence,
            validation_status=status,
            research_notes=notes,
            timestamp=datetime.now().isoformat()
        )

    def _is_cache_valid(self, timestamp: str) -> bool:
        """Check if cached validation is still valid"""
        try:
            cache_time = datetime.fromisoformat(timestamp)
            current_time = datetime.now()
            hours_diff = (current_time - cache_time).total_seconds() / 3600
            return hours_diff < self.research_cache_duration
        except:
            return False

    def generate_validation_report(self, validated_verses: List[ValidatedVerse], 
                                 book: str) -> ValidationReport:
        """
        Generate a validation report for validated verses
        
        Args:
            validated_verses: List of validated verses
            book: Biblical book name
            
        Returns:
            ValidationReport object
        """
        try:
            total_verses = len(validated_verses)
            validated_count = sum(1 for v in validated_verses if v.validation_status == "validated")
            disputed_count = sum(1 for v in validated_verses if v.validation_status == "disputed")
            error_count = sum(1 for v in validated_verses if v.validation_status == "error")
            
            # Calculate average confidence
            if validated_verses:
                average_confidence = sum(v.validated_confidence for v in validated_verses) / len(validated_verses)
            else:
                average_confidence = 0.0
            
            # Create validation summary
            validation_summary = {
                'validated': validated_count,
                'disputed': disputed_count,
                'needs_review': sum(1 for v in validated_verses if v.validation_status == "needs_review"),
                'error': error_count
            }
            
            # Generate recommendations
            recommendations = []
            if disputed_count > 0:
                recommendations.append(f"Review {disputed_count} disputed source attributions")
            if error_count > 0:
                recommendations.append(f"Investigate {error_count} validation errors")
            if average_confidence < 0.7:
                recommendations.append("Consider additional research for low-confidence attributions")
            
            return ValidationReport(
                book=book,
                total_verses=total_verses,
                validated_verses=validated_count,
                disputed_verses=disputed_count,
                error_verses=error_count,
                average_confidence=average_confidence,
                validation_summary=validation_summary,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error generating validation report: {e}")
            return ValidationReport(
                book=book,
                total_verses=0,
                validated_verses=0,
                disputed_verses=0,
                error_verses=1,
                average_confidence=0.0,
                validation_summary={},
                recommendations=[f"Error generating report: {str(e)}"],
                timestamp=datetime.now().isoformat()
            )

    def save_validation_results(self, validated_verses: List[ValidatedVerse], 
                              report: ValidationReport, filename: str = None) -> Tuple[Path, Path]:
        """
        Save validation results and report to files
        
        Args:
            validated_verses: List of validated verses
            report: Validation report
            filename: Optional filename prefix
            
        Returns:
            Tuple of (verses_file_path, report_file_path)
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"validation_{report.book}_{timestamp}"
            
            # Save validated verses
            verses_file = self.research_output_dir / f"{filename}_verses.json"
            serializable_verses = []
            for verse in validated_verses:
                serializable_verse = {
                    'book': verse.book,
                    'chapter': verse.chapter,
                    'verse': verse.verse,
                    'text': verse.text,
                    'sources': verse.sources,
                    'original_confidence': verse.original_confidence,
                    'research_validation': asdict(verse.research_validation) if verse.research_validation else None,
                    'validated_confidence': verse.validated_confidence,
                    'validation_status': verse.validation_status,
                    'research_notes': verse.research_notes,
                    'timestamp': verse.timestamp
                }
                serializable_verses.append(serializable_verse)
            
            with open(verses_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_verses, f, indent=2, ensure_ascii=False)
            
            # Save validation report
            report_file = self.research_output_dir / f"{filename}_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(report), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Validation results saved to: {verses_file}")
            logger.info(f"Validation report saved to: {report_file}")
            
            return verses_file, report_file
            
        except Exception as e:
            logger.error(f"Error saving validation results: {e}")
            return None, None

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get current validation statistics"""
        return {
            'statistics': self.validation_stats.copy(),
            'cache_size': len(self.validation_cache),
            'cache_duration_hours': self.research_cache_duration,
            'validation_threshold': self.validation_threshold
        }

async def main():
    """Main function for testing the validation pipeline"""
    pipeline = ResearchValidationPipeline()
    
    # Test with sample verse data
    sample_verses = [
        {
            'book': 'Genesis',
            'chapter': 1,
            'verse': 1,
            'text': 'In the beginning God created the heaven and the earth.',
            'sources': {'J': 'In the beginning God created the heaven and the earth.'},
            'confidence': 0.85
        },
        {
            'book': 'Genesis',
            'chapter': 1,
            'verse': 2,
            'text': 'And the earth was without form, and void; and darkness was upon the face of the deep.',
            'sources': {'P': 'And the earth was without form, and void; and darkness was upon the face of the deep.'},
            'confidence': 0.75
        }
    ]
    
    print("Testing validation pipeline...")
    validated_verses = await pipeline.validate_parsed_verses(sample_verses, "Genesis")
    
    print(f"Validated {len(validated_verses)} verses")
    
    # Generate report
    report = pipeline.generate_validation_report(validated_verses, "Genesis")
    print(f"Validation report: {report.validated_verses}/{report.total_verses} validated")
    print(f"Average confidence: {report.average_confidence:.2f}")
    
    # Save results
    verses_file, report_file = pipeline.save_validation_results(validated_verses, report)
    if verses_file and report_file:
        print(f"Results saved to: {verses_file}")
        print(f"Report saved to: {report_file}")
    
    # Show statistics
    stats = pipeline.get_validation_statistics()
    print(f"Validation statistics: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
