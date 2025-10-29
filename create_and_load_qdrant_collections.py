#!/usr/bin/env python3
"""
Create Qdrant collections and load biblical verse data
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

def create_collection(client, collection_name, vector_size=384):
    """Create a new collection in Qdrant"""
    try:
        # Check if collection exists
        collections = client.get_collections()
        existing_collections = [col.name for col in collections.collections]
        
        if collection_name in existing_collections:
            print(f"Collection '{collection_name}' already exists")
            return True
        
        # Create collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        print(f"✅ Created collection '{collection_name}'")
        return True
        
    except Exception as e:
        print(f"❌ Error creating collection '{collection_name}': {e}")
        return False

def load_biblical_data_from_jsonl(client, collection_name, jsonl_file_path):
    """Load biblical data from JSONL file into Qdrant"""
    try:
        print(f"📖 Loading biblical data from {jsonl_file_path}...")
        
        # Load the embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        points = []
        with open(jsonl_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        data = json.loads(line)
                        
                        # Create embedding from the text
                        text = data.get('text', '')
                        embedding = model.encode(text)
                        
                        # Create point with integer ID
                        point = PointStruct(
                            id=line_num,  # Use line number as integer ID
                            vector=embedding.tolist(),
                            payload={
                                'text': text,
                                'reference': data.get('metadata', {}).get('reference', ''),
                                'book': data.get('metadata', {}).get('book', ''),
                                'chapter': data.get('metadata', {}).get('chapter', ''),
                                'verse': data.get('metadata', {}).get('verse', ''),
                                'source': data.get('metadata', {}).get('source', ''),
                                'sub_source': data.get('metadata', {}).get('sub_source', ''),
                                'word_count': data.get('metadata', {}).get('word_count', 0),
                                'color_code': data.get('metadata', {}).get('color_code', ''),
                                'document_type': data.get('metadata', {}).get('document_type', ''),
                                'parsing_date': data.get('metadata', {}).get('parsing_date', '')
                            }
                        )
                        points.append(point)
                        
                        if line_num % 100 == 0:
                            print(f"   Processed {line_num} verses...")
                            
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️  Error parsing line {line_num}: {e}")
                        continue
                    except Exception as e:
                        print(f"   ⚠️  Error processing line {line_num}: {e}")
                        continue
        
        print(f"📊 Created {len(points)} points from {jsonl_file_path}")
        
        # Upload points to Qdrant in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(points) + batch_size - 1) // batch_size
            
            print(f"   📤 Uploading batch {batch_num}/{total_batches} ({len(batch)} points)...")
            
            try:
                client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                print(f"   ✅ Batch {batch_num} uploaded successfully")
            except Exception as e:
                print(f"   ❌ Error uploading batch {batch_num}: {e}")
                return False
        
        print(f"✅ Successfully loaded {len(points)} biblical verses into '{collection_name}'")
        return True
        
    except Exception as e:
        print(f"❌ Error loading biblical data: {e}")
        return False

def main():
    print("🚀 Creating Qdrant collections and loading biblical data")
    print("=" * 60)
    
    # Connect to Qdrant
    try:
        client = QdrantClient('localhost', port=6333)
        print("✅ Connected to Qdrant successfully")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return
    
    # Create collections
    collections_to_create = [
        "kjv_biblical_verses",
        "kjv_deuteronomy_verses"
    ]
    
    for collection_name in collections_to_create:
        create_collection(client, collection_name)
    
    # Load biblical data
    jsonl_files = [
        {
            "file": "output/deuteronomist_vector_docs.jsonl",
            "collection": "kjv_deuteronomy_verses"
        }
    ]
    
    for file_info in jsonl_files:
        file_path = Path(file_info["file"])
        collection_name = file_info["collection"]
        
        if file_path.exists():
            load_biblical_data_from_jsonl(client, collection_name, file_path)
        else:
            print(f"❌ File not found: {file_path}")
    
    # Check final status
    print("\n📊 Final collection status:")
    collections = client.get_collections()
    for col in collections.collections:
        try:
            info = client.get_collection(col.name)
            print(f"  {col.name}: {info.vectors_count} vectors")
        except Exception as e:
            print(f"  {col.name}: Error getting info - {e}")
    
    print("\n🎉 Setup completed!")
    print("🌐 You can now view your data at: http://localhost:6333/dashboard")

if __name__ == "__main__":
    main()
