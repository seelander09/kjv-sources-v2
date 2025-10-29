#!/usr/bin/env python3
"""
Complete Scriptural Truth Pipeline
Creates embeddings and stores content in Qdrant for Elysia integration
"""

import json
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

def complete_scriptural_truth_pipeline():
    console.print('🚀 Complete Scriptural Truth Pipeline', style='bold cyan')
    console.print('=' * 50)
    
    # Load the processed content
    console.print('📂 Loading processed content...', style='blue')
    with open('output/scriptural_truth_debug_content.json', 'r', encoding='utf-8') as f:
        content_items = json.load(f)
    
    console.print(f'✅ Loaded {len(content_items)} content items', style='green')
    
    # Setup embedding model
    console.print('🧠 Setting up embedding model...', style='blue')
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    console.print('✅ Embedding model ready', style='green')
    
    # Setup Qdrant
    console.print('🗄️ Setting up Qdrant...', style='blue')
    try:
        qdrant_client = QdrantClient(host='localhost', port=6333)
        qdrant_client.get_collections()  # Test connection
        console.print('✅ Connected to Qdrant server', style='green')
    except:
        console.print('⚠️ Qdrant server not available, using local storage', style='yellow')
        qdrant_client = QdrantClient(path='qdrant_data_scriptural_truth_complete')
    
    # Create collection
    collection_name = 'scriptural_truth_complete'
    try:
        qdrant_client.get_collection(collection_name)
        console.print(f'✅ Collection {collection_name} already exists', style='green')
    except:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        console.print(f'✅ Created collection {collection_name}', style='green')
    
    # Create embeddings and store in Qdrant
    console.print('🔄 Creating embeddings and storing in Qdrant...', style='blue')
    
    stored_count = 0
    failed_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        BarColumn(),
        TextColumn('[progress.percentage]{task.percentage:>3.0f}%'),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task('Processing items...', total=len(content_items))
        
        for i, item in enumerate(content_items):
            try:
                # Create embedding
                text = f"{item['title']}\n{item['content'][:8000]}"  # Limit content length
                embedding = embedding_model.encode(text).tolist()
                
                # Create point
                point = PointStruct(
                    id=abs(hash(item['id'])) % (2**63 - 1),
                    vector=embedding,
                    payload={
                        'id': item['id'],
                        'title': item['title'],
                        'content_type': item['content_type'],
                        'content': item['content'][:8000],  # Limit for storage
                        'source_url': item.get('source_url', ''),
                        'file_path': item.get('file_path', ''),
                        'file_size': item.get('file_size', 0),
                        'created_at': item.get('created_at', ''),
                        'processed_at': item.get('processed_at', '')
                    }
                )
                
                # Store in Qdrant
                qdrant_client.upsert(
                    collection_name=collection_name,
                    points=[point]
                )
                
                stored_count += 1
                
                # Progress update every 50 items
                if (i + 1) % 50 == 0:
                    console.print(f'📦 Stored {i + 1}/{len(content_items)} items...', style='blue')
                
                progress.update(task, advance=1)
                
            except Exception as e:
                console.print(f'❌ Failed to store item {i + 1}: {e}', style='red')
                failed_count += 1
                progress.update(task, advance=1)
    
    # Save final results
    console.print('💾 Saving final results...', style='blue')
    
    final_summary = {
        'total_items': len(content_items),
        'stored_in_qdrant': stored_count,
        'failed_storage': failed_count,
        'collection_name': collection_name,
        'embedding_model': 'all-MiniLM-L6-v2',
        'vector_dimension': 384,
        'total_content_length': sum(len(item['content']) for item in content_items),
        'processed_at': '2025-09-12T01:45:00.000000'
    }
    
    with open('output/scriptural_truth_complete_summary.json', 'w', encoding='utf-8') as f:
        json.dump(final_summary, f, indent=2, ensure_ascii=False)
    
    console.print('✅ Final summary saved', style='green')
    
    # Display completion summary
    console.print('\n🎉 Scriptural Truth Complete Pipeline Finished!', style='bold green')
    console.print(f'📊 Results:', style='cyan')
    console.print(f'  ✅ Items stored in Qdrant: {stored_count}', style='green')
    console.print(f'  ❌ Failed storage: {failed_count}', style='red')
    console.print(f'  🗄️ Collection: {collection_name}', style='blue')
    console.print(f'  🧠 Embedding model: all-MiniLM-L6-v2', style='blue')
    console.print(f'  📁 Summary saved: output/scriptural_truth_complete_summary.json', style='blue')
    
    console.print('\n🚀 Scriptural Truth content is now ready for Elysia integration!', style='bold green')

if __name__ == "__main__":
    complete_scriptural_truth_pipeline()
