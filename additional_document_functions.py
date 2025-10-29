#!/usr/bin/env python3
"""
Additional Document Analysis Functions for Elysia
===============================================

These functions provide analysis capabilities for additional uploaded documents.
"""

import weaviate
import json
from typing import List, Dict, Any, Optional

def search_additional_documents(query: str, content_type: str = None, topics: List[str] = None) -> Dict[str, Any]:
    """Search through additional uploaded documents"""
    try:
        client = weaviate.connect_to_local(host='localhost', port=8080)
        collection = client.collections.get("AdditionalDocuments")
        
        # Build search query
        where_filter = None
        if content_type or topics:
            conditions = []
            if content_type:
                conditions.append({
                    "path": ["content_type"],
                    "operator": "Equal",
                    "valueText": content_type
                })
            if topics:
                conditions.append({
                    "path": ["topics"],
                    "operator": "ContainsAny",
                    "valueText": topics
                })
            
            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {
                    "path": ["content_type"],
                    "operator": "And",
                    "operands": conditions
                }
        
        # Perform search
        result = collection.query.fetch_objects(
            where=where_filter,
            limit=20
        )
        
        documents = []
        for obj in result.objects:
            documents.append({
                "title": obj.properties.get("title", ""),
                "content_type": obj.properties.get("content_type", ""),
                "content_preview": obj.properties.get("content", "")[:500] + "...",
                "topics": obj.properties.get("topics", []),
                "biblical_references": obj.properties.get("biblical_references", []),
                "source_attributions": obj.properties.get("source_attributions", []),
                "word_count": obj.properties.get("word_count", 0),
                "created_at": obj.properties.get("created_at", "")
            })
        
        client.close()
        
        return {
            "query": query,
            "total_found": len(documents),
            "documents": documents
        }
        
    except Exception as e:
        return {"error": str(e)}

def analyze_document_content(document_title: str, analysis_type: str) -> Dict[str, Any]:
    """Analyze specific document content"""
    try:
        client = weaviate.connect_to_local(host='localhost', port=8080)
        collection = client.collections.get("AdditionalDocuments")
        
        # Find document by title
        result = collection.query.fetch_objects(
            where={
                "path": ["title"],
                "operator": "Like",
                "valueText": f"*{document_title}*"
            },
            limit=1
        )
        
        if not result.objects:
            return {"error": f"Document '{document_title}' not found"}
        
        doc = result.objects[0]
        
        analysis = {
            "document_title": doc.properties.get("title", ""),
            "analysis_type": analysis_type,
            "content_type": doc.properties.get("content_type", ""),
            "word_count": doc.properties.get("word_count", 0),
            "topics": doc.properties.get("topics", []),
            "biblical_references": doc.properties.get("biblical_references", []),
            "source_attributions": doc.properties.get("source_attributions", [])
        }
        
        if analysis_type == "summary":
            content = doc.properties.get("content", "")
            analysis["summary"] = content[:1000] + "..." if len(content) > 1000 else content
        elif analysis_type == "theological_analysis":
            analysis["theological_themes"] = doc.properties.get("topics", [])
            analysis["biblical_connections"] = doc.properties.get("biblical_references", [])
        elif analysis_type == "biblical_references":
            analysis["references"] = doc.properties.get("biblical_references", [])
        elif analysis_type == "source_attribution":
            analysis["source_attributions"] = doc.properties.get("source_attributions", [])
        
        client.close()
        return analysis
        
    except Exception as e:
        return {"error": str(e)}

def compare_documents(document_titles: List[str], comparison_focus: str) -> Dict[str, Any]:
    """Compare multiple documents"""
    try:
        client = weaviate.connect_to_local(host='localhost', port=8080)
        collection = client.collections.get("AdditionalDocuments")
        
        documents = []
        for title in document_titles:
            result = collection.query.fetch_objects(
                where={
                    "path": ["title"],
                    "operator": "Like",
                    "valueText": f"*{title}*"
                },
                limit=1
            )
            
            if result.objects:
                doc = result.objects[0]
                documents.append({
                    "title": doc.properties.get("title", ""),
                    "content_type": doc.properties.get("content_type", ""),
                    "topics": doc.properties.get("topics", []),
                    "biblical_references": doc.properties.get("biblical_references", []),
                    "source_attributions": doc.properties.get("source_attributions", []),
                    "word_count": doc.properties.get("word_count", 0)
                })
        
        if not documents:
            return {"error": "No documents found for comparison"}
        
        comparison = {
            "comparison_focus": comparison_focus,
            "documents_compared": len(documents),
            "documents": documents
        }
        
        # Add comparison analysis based on focus
        if comparison_focus == "theological_themes":
            all_topics = set()
            for doc in documents:
                all_topics.update(doc["topics"])
            comparison["shared_themes"] = list(all_topics)
        elif comparison_focus == "biblical_references":
            all_refs = set()
            for doc in documents:
                all_refs.update(doc["biblical_references"])
            comparison["shared_references"] = list(all_refs)
        elif comparison_focus == "source_attribution":
            all_sources = set()
            for doc in documents:
                all_sources.update(doc["source_attributions"])
            comparison["shared_sources"] = list(all_sources)
        
        client.close()
        return comparison
        
    except Exception as e:
        return {"error": str(e)}

def get_document_statistics(statistics_type: str = "overview") -> Dict[str, Any]:
    """Get statistics about uploaded documents"""
    try:
        client = weaviate.connect_to_local(host='localhost', port=8080)
        collection = client.collections.get("AdditionalDocuments")
        
        # Get all documents
        result = collection.query.fetch_objects(limit=1000)
        
        if not result.objects:
            return {"error": "No documents found"}
        
        stats = {
            "statistics_type": statistics_type,
            "total_documents": len(result.objects)
        }
        
        if statistics_type == "overview":
            content_types = {}
            total_words = 0
            all_topics = set()
            all_refs = set()
            
            for obj in result.objects:
                content_type = obj.properties.get("content_type", "unknown")
                content_types[content_type] = content_types.get(content_type, 0) + 1
                total_words += obj.properties.get("word_count", 0)
                all_topics.update(obj.properties.get("topics", []))
                all_refs.update(obj.properties.get("biblical_references", []))
            
            stats.update({
                "content_types": content_types,
                "total_words": total_words,
                "unique_topics": len(all_topics),
                "unique_biblical_references": len(all_refs),
                "topics": list(all_topics),
                "biblical_references": list(all_refs)
            })
        
        elif statistics_type == "by_topic":
            topic_counts = {}
            for obj in result.objects:
                topics = obj.properties.get("topics", [])
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            stats["topic_distribution"] = topic_counts
        
        elif statistics_type == "by_type":
            type_counts = {}
            for obj in result.objects:
                content_type = obj.properties.get("content_type", "unknown")
                type_counts[content_type] = type_counts.get(content_type, 0) + 1
            stats["type_distribution"] = type_counts
        
        client.close()
        return stats
        
    except Exception as e:
        return {"error": str(e)}
