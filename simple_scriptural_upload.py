#!/usr/bin/env python3
"""
Simple Scriptural Truth Upload with Clear Progress
==================================================
"""

import json
import time
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

def upload_with_simple_progress():
    """Upload with simple, visible progress."""
    print("🚀 Starting Scriptural Truth Upload...")
    
    # Connect to Qdrant
    client = QdrantClient(path='qdrant_data')
    collection_name = "scriptural_truth_complete"
    
    # Check current count
    try:
        info = client.get_collection(collection_name)
        current_count = info.points_count
        print(f"📊 Current items in collection: {current_count}")
    except:
        current_count = 0
        print("📊 Starting fresh upload")
    
    # Load training data
    training_path = Path("output/scriptural_truth_training.jsonl")
    if not training_path.exists():
        print("❌ Training data file not found!")
        return
    
    print("📖 Loading training data...")
    
    # Count total lines
    total_lines = 0
    with open(training_path, 'r', encoding='utf-8') as f:
        for _ in f:
            total_lines += 1
    
    print(f"📋 Total items to process: {total_lines}")
    print(f"📋 Already uploaded: {current_count}")
    print(f"📋 Remaining: {total_lines - current_count}")
    
    if current_count >= total_lines:
        print("✅ All items already uploaded!")
        return
    
    # Upload in small batches
    batch_size = 5  # Very small batches
    processed = 0
    batch_num = 0
    
    print(f"\n🔄 Starting upload in batches of {batch_size}...")
    print("=" * 50)
    
    with open(training_path, 'r', encoding='utf-8') as f:
        # Skip already uploaded items
        for _ in range(current_count):
            next(f)
        
        batch_points = []
        
        for line_num, line in enumerate(f, start=current_count):
            try:
                item = json.loads(line.strip())
                
                # Create simple embedding (384 zeros)
                embedding = [0.0] * 384
                
                point = PointStruct(
                    id=line_num + 1,
                    vector=embedding,
                    payload={
                        'id': item.get('id', f'item_{line_num}'),
                        'title': item.get('title', '')[:100],
                        'content': item.get('content', '')[:500],
                        'content_type': item.get('content_type', ''),
                        'source_url': item.get('source_url', ''),
                        'uploaded_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                )
                batch_points.append(point)
                
                # Upload when batch is full
                if len(batch_points) >= batch_size:
                    try:
                        client.upsert(
                            collection_name=collection_name,
                            points=batch_points
                        )
                        
                        batch_num += 1
                        processed += len(batch_points)
                        
                        # Show progress
                        progress = (processed / (total_lines - current_count)) * 100
                        print(f"📦 Batch {batch_num}: Uploaded {processed}/{total_lines - current_count} items ({progress:.1f}%)")
                        
                        # Clear batch
                        batch_points = []
                        
                    except Exception as e:
                        print(f"❌ Error in batch {batch_num}: {e}")
                        batch_points = []
                        continue
        
        # Upload remaining items
        if batch_points:
            try:
                client.upsert(
                    collection_name=collection_name,
                    points=batch_points
                )
                batch_num += 1
                processed += len(batch_points)
                print(f"📦 Final batch {batch_num}: Uploaded {processed}/{total_lines - current_count} items (100.0%)")
            except Exception as e:
                print(f"❌ Error in final batch: {e}")
    
    print("=" * 50)
    print(f"✅ Upload completed! Processed {processed} items in {batch_num} batches")
    
    # Show final stats
    try:
        info = client.get_collection(collection_name)
        print(f"📊 Final collection size: {info.points_count} items")
    except Exception as e:
        print(f"❌ Error getting final stats: {e}")

if __name__ == "__main__":
    upload_with_simple_progress()
