#!/usr/bin/env python3
"""
Enhanced LightRAG Research Integration
====================================

This module integrates real-time scholarly research with the existing LightRAG system
for enhanced biblical text analysis and documentary hypothesis research.

Features:
- Real-time research integration with LightRAG queries
- Enhanced entity-relation reasoning with current scholarship
- Dynamic source validation during queries
- Research-informed response generation
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Import the research tool
from duckduckgo_research_tool import DuckDuckGoResearchTool, ResearchResult, SourceValidation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedQueryResult:
    """Enhanced query result with research integration"""
    original_query: str
    lightrag_results: List[Dict[str, Any]]
    research_context: List[ResearchResult]
    source_validations: List[SourceValidation]
    enhanced_response: str
    confidence_score: float
    timestamp: str

class EnhancedLightRAGResearch:
    """Enhanced LightRAG system with real-time research integration"""
    
    def __init__(self, lightrag_data_dir: str = "lightrag_data", research_output_dir: str = "research_output"):
        self.lightrag_data_dir = Path(lightrag_data_dir)
        self.research_output_dir = Path(research_output_dir)
        self.research_tool = DuckDuckGoResearchTool(str(research_output_dir))
        
        # Research integration settings
        self.research_enabled = True
        self.auto_validate_sources = True
        self.include_research_context = True
        self.max_research_results = 5
        
        # Cache for research results
        self.research_cache = {}
        self.cache_duration_hours = 24

    async def enhanced_query(self, query: str, include_research: bool = True) -> EnhancedQueryResult:
        """
        Perform enhanced query with research integration
        
        Args:
            query: User query string
            include_research: Whether to include real-time research
            
        Returns:
            EnhancedQueryResult with research context
        """
        try:
            logger.info(f"Processing enhanced query: {query}")
            
            # Get LightRAG results (placeholder - would integrate with actual LightRAG)
            lightrag_results = await self._get_lightrag_results(query)
            
            # Initialize research components
            research_context = []
            source_validations = []
            enhanced_response = ""
            confidence_score = 0.0
            
            if include_research and self.research_enabled:
                # Get research context
                research_context = await self._get_research_context(query)
                
                # Validate sources if auto-validation is enabled
                if self.auto_validate_sources:
                    source_validations = await self._validate_sources_in_query(query, lightrag_results)
                
                # Generate enhanced response
                enhanced_response = await self._generate_enhanced_response(
                    query, lightrag_results, research_context, source_validations
                )
                
                # Calculate confidence score
                confidence_score = self._calculate_confidence_score(
                    lightrag_results, research_context, source_validations
                )
            
            result = EnhancedQueryResult(
                original_query=query,
                lightrag_results=lightrag_results,
                research_context=research_context,
                source_validations=source_validations,
                enhanced_response=enhanced_response,
                confidence_score=confidence_score,
                timestamp=datetime.now().isoformat()
            )
            
            # Cache the result
            self._cache_result(query, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced query: {e}")
            return EnhancedQueryResult(
                original_query=query,
                lightrag_results=[],
                research_context=[],
                source_validations=[],
                enhanced_response=f"Error processing query: {str(e)}",
                confidence_score=0.0,
                timestamp=datetime.now().isoformat()
            )

    async def _get_lightrag_results(self, query: str) -> List[Dict[str, Any]]:
        """
        Get results from LightRAG system (placeholder implementation)
        
        Args:
            query: User query
            
        Returns:
            List of LightRAG results
        """
        # This would integrate with the actual LightRAG system
        # For now, return placeholder results
        logger.info(f"Getting LightRAG results for: {query}")
        
        # Simulate LightRAG results
        results = []
        if "source:J" in query.lower():
            results.append({
                "type": "verse",
                "book": "Genesis",
                "chapter": 1,
                "verse": 1,
                "text": "In the beginning God created the heaven and the earth.",
                "source": "J",
                "confidence": 0.85,
                "metadata": {
                    "source_type": "jahwist",
                    "characteristics": ["anthropomorphic God", "vivid storytelling"]
                }
            })
        elif "source:E" in query.lower():
            results.append({
                "type": "verse",
                "book": "Genesis",
                "chapter": 1,
                "verse": 1,
                "text": "In the beginning God created the heaven and the earth.",
                "source": "E",
                "confidence": 0.75,
                "metadata": {
                    "source_type": "elohist",
                    "characteristics": ["divine communication", "prophetic emphasis"]
                }
            })
        
        return results

    async def _get_research_context(self, query: str) -> List[ResearchResult]:
        """
        Get research context for the query
        
        Args:
            query: User query
            
        Returns:
            List of relevant research results
        """
        try:
            # Check cache first
            cache_key = f"research_{hash(query)}"
            if cache_key in self.research_cache:
                cached_result = self.research_cache[cache_key]
                if self._is_cache_valid(cached_result['timestamp']):
                    logger.info("Using cached research results")
                    return cached_result['results']
            
            # Generate research queries based on the user query
            research_queries = self._generate_research_queries(query)
            
            all_results = []
            for research_query in research_queries:
                results = await self.research_tool.search_scholarly_resources(
                    research_query, self.max_research_results
                )
                all_results.extend(results)
            
            # Cache the results
            self.research_cache[cache_key] = {
                'results': all_results,
                'timestamp': datetime.now().isoformat()
            }
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error getting research context: {e}")
            return []

    def _generate_research_queries(self, query: str) -> List[str]:
        """
        Generate research queries based on user query
        
        Args:
            query: User query
            
        Returns:
            List of research query strings
        """
        queries = []
        
        # Extract source information
        if "source:J" in query.lower() or "jahwist" in query.lower():
            queries.extend([
                "jahwist source documentary hypothesis",
                "J source biblical criticism",
                "early narrative source pentateuch"
            ])
        
        if "source:E" in query.lower() or "elohist" in query.lower():
            queries.extend([
                "elohist source documentary hypothesis",
                "E source biblical criticism",
                "northern source pentateuch"
            ])
        
        if "source:P" in query.lower() or "priestly" in query.lower():
            queries.extend([
                "priestly source documentary hypothesis",
                "P source biblical criticism",
                "ritual source pentateuch"
            ])
        
        if "source:D" in query.lower() or "deuteronomist" in query.lower():
            queries.extend([
                "deuteronomist source documentary hypothesis",
                "D source biblical criticism",
                "deuteronomy source pentateuch"
            ])
        
        if "source:R" in query.lower() or "redactor" in query.lower():
            queries.extend([
                "redactor source documentary hypothesis",
                "R source biblical criticism",
                "editorial additions pentateuch"
            ])
        
        # Extract book information
        books = ["genesis", "exodus", "leviticus", "numbers", "deuteronomy"]
        for book in books:
            if book in query.lower():
                queries.append(f"documentary hypothesis {book}")
                queries.append(f"biblical source criticism {book}")
                break
        
        # If no specific queries generated, use general ones
        if not queries:
            queries = [
                "documentary hypothesis biblical criticism",
                "pentateuch source analysis",
                "biblical text criticism"
            ]
        
        return queries

    async def _validate_sources_in_query(self, query: str, lightrag_results: List[Dict[str, Any]]) -> List[SourceValidation]:
        """
        Validate sources mentioned in the query and results
        
        Args:
            query: User query
            lightrag_results: Results from LightRAG
            
        Returns:
            List of source validations
        """
        validations = []
        
        try:
            # Extract sources from query
            sources_in_query = self._extract_sources_from_query(query)
            
            # Extract sources from results
            sources_in_results = set()
            for result in lightrag_results:
                if 'source' in result:
                    sources_in_results.add(result['source'])
            
            # Combine all sources
            all_sources = sources_in_query.union(sources_in_results)
            
            # Validate each source
            for source in all_sources:
                # Get verse reference from results if available
                verse_ref = "General"
                for result in lightrag_results:
                    if result.get('source') == source:
                        book = result.get('book', 'Genesis')
                        chapter = result.get('chapter', 1)
                        verse = result.get('verse', 1)
                        verse_ref = f"{book} {chapter}:{verse}"
                        break
                
                validation = await self.research_tool.validate_source_attribution(source, verse_ref)
                validations.append(validation)
            
            return validations
            
        except Exception as e:
            logger.error(f"Error validating sources: {e}")
            return []

    def _extract_sources_from_query(self, query: str) -> set:
        """Extract source identifiers from query"""
        sources = set()
        query_lower = query.lower()
        
        if "source:J" in query_lower or "jahwist" in query_lower:
            sources.add("J")
        if "source:E" in query_lower or "elohist" in query_lower:
            sources.add("E")
        if "source:P" in query_lower or "priestly" in query_lower:
            sources.add("P")
        if "source:D" in query_lower or "deuteronomist" in query_lower:
            sources.add("D")
        if "source:R" in query_lower or "redactor" in query_lower:
            sources.add("R")
        
        return sources

    async def _generate_enhanced_response(self, query: str, lightrag_results: List[Dict[str, Any]], 
                                        research_context: List[ResearchResult], 
                                        source_validations: List[SourceValidation]) -> str:
        """
        Generate enhanced response with research context
        
        Args:
            query: Original user query
            lightrag_results: Results from LightRAG
            research_context: Research results
            source_validations: Source validation results
            
        Returns:
            Enhanced response string
        """
        try:
            response_parts = []
            
            # Start with LightRAG results summary
            if lightrag_results:
                response_parts.append("## Biblical Text Analysis Results")
                response_parts.append("")
                
                for result in lightrag_results:
                    book = result.get('book', 'Unknown')
                    chapter = result.get('chapter', 'Unknown')
                    verse = result.get('verse', 'Unknown')
                    text = result.get('text', 'No text available')
                    source = result.get('source', 'Unknown')
                    confidence = result.get('confidence', 0.0)
                    
                    response_parts.append(f"**{book} {chapter}:{verse}** ({source} source, confidence: {confidence:.2f})")
                    response_parts.append(f"> {text}")
                    response_parts.append("")
            
            # Add research context
            if research_context and self.include_research_context:
                response_parts.append("## Current Scholarly Research")
                response_parts.append("")
                
                for i, research in enumerate(research_context[:3], 1):
                    response_parts.append(f"{i}. **{research.title}**")
                    response_parts.append(f"   {research.snippet}")
                    response_parts.append(f"   *Relevance: {research.relevance_score:.2f}*")
                    response_parts.append("")
            
            # Add source validation information
            if source_validations:
                response_parts.append("## Source Validation")
                response_parts.append("")
                
                for validation in source_validations:
                    status = validation.validation_status
                    consensus = validation.scholarly_consensus
                    source_id = validation.source_identifier
                    
                    response_parts.append(f"**{source_id} Source**: {status.title()} (Consensus: {consensus:.2f})")
                    
                    if validation.supporting_sources:
                        response_parts.append(f"  - Supporting sources: {len(validation.supporting_sources)}")
                    if validation.conflicting_sources:
                        response_parts.append(f"  - Conflicting sources: {len(validation.conflicting_sources)}")
                    response_parts.append("")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error generating enhanced response: {e}")
            return f"Error generating enhanced response: {str(e)}"

    def _calculate_confidence_score(self, lightrag_results: List[Dict[str, Any]], 
                                  research_context: List[ResearchResult], 
                                  source_validations: List[SourceValidation]) -> float:
        """
        Calculate overall confidence score for the enhanced response
        
        Args:
            lightrag_results: Results from LightRAG
            research_context: Research results
            source_validations: Source validation results
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            scores = []
            
            # LightRAG confidence scores
            if lightrag_results:
                lightrag_confidence = sum(r.get('confidence', 0.0) for r in lightrag_results) / len(lightrag_results)
                scores.append(lightrag_confidence)
            
            # Research context relevance scores
            if research_context:
                research_confidence = sum(r.relevance_score for r in research_context) / len(research_context)
                scores.append(research_confidence)
            
            # Source validation consensus scores
            if source_validations:
                validation_confidence = sum(v.scholarly_consensus for v in source_validations) / len(source_validations)
                scores.append(validation_confidence)
            
            # Calculate weighted average
            if scores:
                return sum(scores) / len(scores)
            else:
                return 0.5  # Neutral confidence if no data
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0

    def _cache_result(self, query: str, result: EnhancedQueryResult):
        """Cache query result"""
        cache_key = f"enhanced_{hash(query)}"
        self.research_cache[cache_key] = {
            'result': result,
            'timestamp': datetime.now().isoformat()
        }

    def _is_cache_valid(self, timestamp: str) -> bool:
        """Check if cached result is still valid"""
        try:
            cache_time = datetime.fromisoformat(timestamp)
            current_time = datetime.now()
            hours_diff = (current_time - cache_time).total_seconds() / 3600
            return hours_diff < self.cache_duration_hours
        except:
            return False

    def save_enhanced_results(self, results: List[EnhancedQueryResult], filename: str = None) -> Path:
        """
        Save enhanced query results to JSON file
        
        Args:
            results: List of enhanced query results
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_query_results_{timestamp}.json"
        
        filepath = self.research_output_dir / filename
        
        # Convert results to serializable format
        serializable_results = []
        for result in results:
            serializable_result = {
                'original_query': result.original_query,
                'lightrag_results': result.lightrag_results,
                'research_context': [asdict(r) for r in result.research_context],
                'source_validations': [asdict(v) for v in result.source_validations],
                'enhanced_response': result.enhanced_response,
                'confidence_score': result.confidence_score,
                'timestamp': result.timestamp
            }
            serializable_results.append(serializable_result)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Enhanced results saved to: {filepath}")
        return filepath

async def main():
    """Main function for testing enhanced LightRAG research"""
    enhanced_lightrag = EnhancedLightRAGResearch()
    
    # Test queries
    test_queries = [
        "source:J",
        "source:E",
        "documentary hypothesis Genesis",
        "priestly source analysis"
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        result = await enhanced_lightrag.enhanced_query(query)
        results.append(result)
        
        print(f"Confidence score: {result.confidence_score:.2f}")
        print(f"Research context items: {len(result.research_context)}")
        print(f"Source validations: {len(result.source_validations)}")
        print(f"Enhanced response length: {len(result.enhanced_response)} characters")
    
    # Save results
    filepath = enhanced_lightrag.save_enhanced_results(results)
    print(f"\nResults saved to: {filepath}")

if __name__ == "__main__":
    asyncio.run(main())
