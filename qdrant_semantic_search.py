#!/usr/bin/env python3
"""
Semantic Pattern Search using Qdrant Vector Database
Find biblical verses with patterns similar to "listen, guard, do" sequences
"""

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import json
import numpy as np

def create_pattern_embeddings():
    """Create embeddings for pattern descriptions"""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Primary "listen, guard, do" patterns
    primary_patterns = [
        "listen hear hearken then guard keep observe then do perform obey",
        "divine command sequence: hear, keep, do",
        "covenant obedience pattern: listen, guard, do",
        "biblical command structure: hear, observe, perform",
        "deuteronomic formula: hearken, keep, do"
    ]
    
    # Additional sequential verb patterns
    additional_patterns = [
        "command obey serve love fear",
        "walk keep observe establish",
        "swear serve cleave avouch",
        "love serve fear keep",
        "observe keep do perform"
    ]
    
    all_patterns = primary_patterns + additional_patterns
    pattern_embeddings = model.encode(all_patterns)
    
    return model, all_patterns, pattern_embeddings

def search_qdrant_collections(client, pattern_embeddings, patterns, collection_name, top_k=20):
    """Search Qdrant collections for semantic patterns"""
    results = {}
    
    try:
        # Get collection info
        collection_info = client.get_collection(collection_name)
        print(f"Searching collection: {collection_name}")
        print(f"Vectors count: {collection_info.vectors_count}")
        
        if collection_info.vectors_count == 0:
            print(f"  No vectors found in {collection_name}")
            return {}
        
        # Search for each pattern
        for i, pattern in enumerate(patterns):
            print(f"\nSearching for pattern: '{pattern}'")
            
            try:
                # Perform vector search
                search_results = client.search(
                    collection_name=collection_name,
                    query_vector=pattern_embeddings[i].tolist(),
                    limit=top_k,
                    with_payload=True
                )
                
                pattern_results = []
                for result in search_results:
                    if result.score > 0.3:  # Only include results with reasonable similarity
                        result_data = {
                            'pattern': pattern,
                            'similarity_score': float(result.score),
                            'payload': result.payload,
                            'id': result.id
                        }
                        pattern_results.append(result_data)
                
                results[pattern] = pattern_results
                print(f"  Found {len(pattern_results)} verses with similarity > 0.3")
                
                # Show top 3 results
                for j, result in enumerate(pattern_results[:3]):
                    payload = result['payload']
                    text = payload.get('text', payload.get('content', 'No text available'))[:100]
                    reference = payload.get('reference', payload.get('verse_reference', 'No reference'))
                    source = payload.get('source', 'Unknown source')
                    print(f"    {j+1}. {reference} (Source: {source}) - Score: {result['similarity_score']:.3f}")
                    print(f"       Text: {text}...")
                    
            except Exception as e:
                print(f"  Error searching pattern '{pattern}': {e}")
                results[pattern] = []
    
    except Exception as e:
        print(f"Error accessing collection {collection_name}: {e}")
        return {}
    
    return results

def main():
    print("Semantic Pattern Search using Qdrant Vector Database")
    print("=" * 60)
    
    # Connect to Qdrant
    try:
        client = QdrantClient('localhost', port=6333)
        print("Connected to Qdrant successfully")
    except Exception as e:
        print(f"Failed to connect to Qdrant: {e}")
        return
    
    # Get available collections
    try:
        collections = client.get_collections()
        print(f"\nAvailable collections: {[col.name for col in collections.collections]}")
        
        # Focus on biblical verse collections
        biblical_collections = [col for col in collections.collections if 'kjv' in col.name.lower() or 'biblical' in col.name.lower()]
        if biblical_collections:
            print(f"Biblical verse collections: {[col.name for col in biblical_collections]}")
        else:
            print("No biblical verse collections found")
    except Exception as e:
        print(f"Failed to get collections: {e}")
        return
    
    # Create pattern embeddings
    print("\nCreating pattern embeddings...")
    model, patterns, pattern_embeddings = create_pattern_embeddings()
    print(f"Created embeddings for {len(patterns)} patterns")
    
    # Search each collection, focusing on biblical verse collections
    all_results = {}
    
    # Filter to biblical verse collections
    collections_to_search = [col for col in collections.collections if 'kjv' in col.name.lower() or 'biblical' in col.name.lower()]
    
    if not collections_to_search:
        print("No biblical verse collections found to search")
        return
    
    for collection in collections_to_search:
        collection_name = collection.name
        print(f"\n{'='*60}")
        print(f"Searching collection: {collection_name}")
        print(f"{'='*60}")
        
        collection_results = search_qdrant_collections(
            client, pattern_embeddings, patterns, collection_name
        )
        
        if collection_results:
            all_results[collection_name] = collection_results
    
    # Save results
    if all_results:
        output_file = "qdrant_semantic_pattern_search_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {output_file}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SEARCH SUMMARY")
        print("=" * 60)
        
        total_found = 0
        for collection_name, collection_results in all_results.items():
            collection_total = sum(len(verses) for verses in collection_results.values())
            total_found += collection_total
            print(f"\nCollection: {collection_name}")
            print(f"  Total verses found: {collection_total}")
            
            # Most effective patterns in this collection
            pattern_effectiveness = [(pattern, len(verses)) for pattern, verses in collection_results.items()]
            pattern_effectiveness.sort(key=lambda x: x[1], reverse=True)
            
            print("  Most effective patterns:")
            for pattern, count in pattern_effectiveness[:3]:
                print(f"    - {pattern}: {count} verses")
        
        print(f"\nOverall total verses found: {total_found}")
    else:
        print("\nNo results found in any collection.")

if __name__ == "__main__":
    main()
