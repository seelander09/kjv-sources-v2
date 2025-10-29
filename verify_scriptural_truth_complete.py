#!/usr/bin/env python3
"""
Verify Scriptural Truth Complete Pipeline Results
"""

import json
from qdrant_client import QdrantClient

def verify_results():
    print('📊 Scriptural Truth Complete Pipeline Results:')
    print('=' * 50)
    
    # Load the summary
    with open('output/scriptural_truth_complete_summary.json', 'r') as f:
        summary = json.load(f)
    
    print(f'✅ Total items processed: {summary["total_items"]}')
    print(f'✅ Items stored in Qdrant: {summary["stored_in_qdrant"]}')
    print(f'❌ Failed storage: {summary["failed_storage"]}')
    print(f'🗄️ Collection name: {summary["collection_name"]}')
    print(f'🧠 Embedding model: {summary["embedding_model"]}')
    print(f'📏 Vector dimension: {summary["vector_dimension"]}')
    print(f'📝 Total content length: {summary["total_content_length"]:,} characters')
    print(f'⏰ Processed at: {summary["processed_at"]}')
    
    # Test Qdrant connection
    try:
        client = QdrantClient(host='localhost', port=6333)
        collection_info = client.get_collection('scriptural_truth_complete')
        print(f'\n🗄️ Qdrant Collection Status:')
        print(f'   Points count: {collection_info.points_count}')
        print(f'   Vector size: {collection_info.config.params.vectors.size}')
        print(f'   Distance metric: {collection_info.config.params.vectors.distance}')
        print('✅ Qdrant collection is ready for queries!')
        
        # Test a simple search
        print('\n🔍 Testing search functionality...')
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        query = 'Book of Jubilees'
        query_embedding = model.encode(query).tolist()
        
        results = client.search(
            collection_name='scriptural_truth_complete',
            query_vector=query_embedding,
            limit=3
        )
        
        print(f'✅ Search test successful! Found {len(results)} results for "{query}"')
        for i, result in enumerate(results, 1):
            title = result.payload.get('title', 'Unknown')
            score = result.score
            print(f'   {i}. {title} (score: {score:.3f})')
            
    except Exception as e:
        print(f'❌ Qdrant connection error: {e}')

if __name__ == "__main__":
    verify_results()
