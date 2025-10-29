#!/usr/bin/env python3
"""
Search Scriptural Truth content for specific topics
"""

import weaviate

def search_scriptural_truth(query_term):
    """Search Scriptural Truth collection for specific terms"""
    try:
        client = weaviate.connect_to_local(host='localhost', port=8080)
        collection = client.collections.get('ScripturalTruth')
        
        # Search for documents containing the query term
        result = collection.query.fetch_objects(
            where={
                'path': ['content'],
                'operator': 'Like',
                'valueText': f'*{query_term}*'
            },
            limit=10
        )
        
        print(f"Found {len(result.objects)} documents mentioning '{query_term}':")
        print("=" * 60)
        
        for i, obj in enumerate(result.objects, 1):
            title = obj.properties.get('title', 'No title')
            content = obj.properties.get('content', '')
            
            # Find the relevant section
            content_lower = content.lower()
            query_lower = query_term.lower()
            
            if query_lower in content_lower:
                # Find the context around the query term
                start_idx = content_lower.find(query_lower)
                context_start = max(0, start_idx - 200)
                context_end = min(len(content), start_idx + len(query_term) + 200)
                context = content[context_start:context_end]
                
                print(f"\n{i}. Title: {title}")
                print(f"   Context: ...{context}...")
                print("-" * 40)
        
        client.close()
        return len(result.objects)
        
    except Exception as e:
        print(f"Error searching Scriptural Truth: {e}")
        return 0

if __name__ == "__main__":
    # Search for "good things come in three" and related terms
    search_terms = [
        "good things come in three",
        "number three",
        "significance of three",
        "three good things"
    ]
    
    for term in search_terms:
        print(f"\nSearching for: '{term}'")
        count = search_scriptural_truth(term)
        if count == 0:
            print("No results found.")
        print("\n" + "="*80)
