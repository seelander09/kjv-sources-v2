#!/usr/bin/env python3
"""
Integrate Additional Documents with Elysia
=========================================

This script integrates the AdditionalDocuments collection with your
existing Elysia configuration, making new documents available for
AI analysis through the conversational interface.
"""

import json
import weaviate
from pathlib import Path

def check_additional_documents_collection():
    """Check if AdditionalDocuments collection exists and has data"""
    try:
        client = weaviate.connect_to_local(host='localhost', port=8080)
        
        # Check if collection exists
        try:
            collection = client.collections.get("AdditionalDocuments")
            result = collection.aggregate.over_all(total_count=True)
            count = result.total_count
            
            print(f"✅ AdditionalDocuments collection found with {count} documents")
            
            # Get sample document
            if count > 0:
                sample = collection.query.fetch_objects(limit=1)
                if sample.objects:
                    doc = sample.objects[0]
                    print(f"📄 Sample document: {doc.properties.get('title', 'No title')}")
                    print(f"   Type: {doc.properties.get('content_type', 'Unknown')}")
                    print(f"   Topics: {doc.properties.get('topics', [])}")
                    print(f"   Biblical References: {doc.properties.get('biblical_references', [])}")
            
            client.close()
            return True, count
            
        except Exception as e:
            print(f"❌ AdditionalDocuments collection not found: {e}")
            client.close()
            return False, 0
            
    except Exception as e:
        print(f"❌ Failed to connect to Weaviate: {e}")
        return False, 0

def update_elysia_config():
    """Update Elysia configuration to include AdditionalDocuments collection"""
    
    # Load existing configuration
    config_file = "elysia_documentary_hypothesis_config.json"
    if not Path(config_file).exists():
        print(f"❌ Configuration file {config_file} not found")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Add AdditionalDocuments collection
        additional_collection = {
            "name": "AdditionalDocuments",
            "description": "Additional documents for biblical research and analysis",
            "weaviate_collection": "AdditionalDocuments",
            "search_fields": ["content", "title", "topics", "biblical_references"],
            "filter_fields": ["content_type", "topics", "source_attributions", "language"],
            "metadata_fields": ["word_count", "character_count", "created_at", "processed_at", "file_size"]
        }
        
        # Add to collections if not already present
        if "collections" not in config:
            config["collections"] = []
        
        # Check if already exists
        collection_names = [col["name"] for col in config["collections"]]
        if "AdditionalDocuments" not in collection_names:
            config["collections"].append(additional_collection)
            print("✅ Added AdditionalDocuments to Elysia configuration")
        else:
            print("ℹ️ AdditionalDocuments already in Elysia configuration")
        
        # Add new tools for additional documents
        additional_tools = [
            {
                "name": "search_additional_documents",
                "description": "Search through additional uploaded documents for specific topics or content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for document content, topics, or biblical references"
                        },
                        "content_type": {
                            "type": "string",
                            "description": "Filter by document type (pdf, docx, txt, md, html, rtf)"
                        },
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by topics (creation, covenant, law, sacrifice, etc.)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "analyze_document_content",
                "description": "Analyze the content of a specific uploaded document",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_title": {
                            "type": "string",
                            "description": "Title or identifier of the document to analyze"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["summary", "theological_analysis", "biblical_references", "source_attribution"],
                            "description": "Type of analysis to perform on the document"
                        }
                    },
                    "required": ["document_title", "analysis_type"]
                }
            },
            {
                "name": "compare_documents",
                "description": "Compare multiple uploaded documents on specific topics or themes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_titles": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of document titles to compare"
                        },
                        "comparison_focus": {
                            "type": "string",
                            "description": "Focus of comparison (theological themes, biblical references, source attributions, etc.)"
                        }
                    },
                    "required": ["document_titles", "comparison_focus"]
                }
            },
            {
                "name": "get_document_statistics",
                "description": "Get statistics and overview of all uploaded documents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "statistics_type": {
                            "type": "string",
                            "enum": ["overview", "by_topic", "by_type", "by_source_attribution"],
                            "description": "Type of statistics to generate"
                        }
                    }
                }
            }
        ]
        
        # Add tools if not already present
        if "tools" not in config:
            config["tools"] = []
        
        existing_tool_names = [tool["name"] for tool in config["tools"]]
        for tool in additional_tools:
            if tool["name"] not in existing_tool_names:
                config["tools"].append(tool)
                print(f"✅ Added tool: {tool['name']}")
        
        # Update agent description to mention additional documents
        if "agent_description" in config:
            config["agent_description"] += " You also have access to additional uploaded documents for comprehensive biblical research and analysis."
        
        # Save updated configuration
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated Elysia configuration: {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update Elysia configuration: {e}")
        return False

def create_document_functions():
    """Create Python functions for document analysis"""
    
    functions_content = '''#!/usr/bin/env python3
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
'''
    
    with open("additional_document_functions.py", 'w', encoding='utf-8') as f:
        f.write(functions_content)
    
    print("✅ Created additional_document_functions.py")

def main():
    """Main integration function"""
    print("🔗 Integrating Additional Documents with Elysia")
    print("=" * 50)
    
    # Check if collection exists
    collection_exists, doc_count = check_additional_documents_collection()
    
    if not collection_exists:
        print("❌ AdditionalDocuments collection not found")
        print("💡 Run the document ingestion pipeline first to create the collection")
        return
    
    if doc_count == 0:
        print("⚠️ AdditionalDocuments collection is empty")
        print("💡 Add documents to new_documents folder and run the pipeline")
        return
    
    # Update Elysia configuration
    if update_elysia_config():
        print("✅ Elysia configuration updated successfully")
    else:
        print("❌ Failed to update Elysia configuration")
        return
    
    # Create document analysis functions
    create_document_functions()
    
    print("\n🎉 Additional Documents Integration Complete!")
    print("=" * 50)
    print(f"📊 {doc_count} documents are now available in Elysia")
    print("\n🔍 New capabilities available:")
    print("  • Search through uploaded documents")
    print("  • Analyze specific document content")
    print("  • Compare multiple documents")
    print("  • Get document statistics and overview")
    print("\n💡 Example queries for Elysia:")
    print("  'Search my uploaded documents for creation theology'")
    print("  'Analyze the content of [document title]'")
    print("  'Compare the theological themes in my research papers'")
    print("  'Show me statistics about all my uploaded documents'")
    print("\n🚀 Restart Elysia to access the new capabilities:")
    print("  .\\start_elysia_documentary_research.ps1")

if __name__ == "__main__":
    main()
