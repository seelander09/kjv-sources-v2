#!/usr/bin/env python3
"""
Quick geographical pattern search - works with existing collections
"""

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime

def quick_search():
    print("=== QUICK GEOGRAPHICAL PATTERN SEARCH ===")
    
    # Connect to local Qdrant
    client = QdrantClient(path='qdrant_data')
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Check what collections we have
    collections = client.get_collections()
    print(f"\nAvailable collections: {[col.name for col in collections.collections]}")
    
    # Search patterns
    patterns = [
        "north south east west directions",
        "mount sinai directions",
        "jordan river directions", 
        "red sea directions",
        "canaan land directions"
    ]
    
    results = []
    
    for pattern in patterns:
        print(f"\nSearching: {pattern}")
        query_embedding = model.encode([pattern])[0].tolist()
        
        # Try each collection
        for col in collections.collections:
            try:
                search_results = client.query_points(
                    collection_name=col.name,
                    query=query_embedding,
                    limit=5,
                    score_threshold=0.3,
                    with_payload=True
                )
                
                for result in search_results.points:
                    payload = result.payload
                    verse_data = {
                        'score': result.score,
                        'reference': f"{payload.get('book', 'Unknown')} {payload.get('chapter', '?')}:{payload.get('verse', '?')}",
                        'source': payload.get('source', 'Unknown'),
                        'text': payload.get('text', '')[:100],
                        'pattern': pattern,
                        'collection': col.name
                    }
                    results.append(verse_data)
                    
            except Exception as e:
                print(f"  Error with {col.name}: {e}")
    
    # Show results
    print(f"\n=== FOUND {len(results)} RESULTS ===")
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. {result['reference']} ({result['source']}) - {result['text']}...")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quick_geographical_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    quick_search()
