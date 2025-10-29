#!/usr/bin/env python3
"""
Import vector data from SQLite files to Qdrant collections
"""

import sqlite3
import pickle
import requests
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

def deserialize_point(data: bytes):
    """Deserialize a pickled Qdrant PointStruct"""
    try:
        return pickle.loads(data)
    except Exception as e:
        print(f"❌ Error deserializing point: {e}")
        return None

def extract_points_from_sqlite(db_path: str, collection_name: str, limit: int = None) -> List[Dict[str, Any]]:
    """Extract points from SQLite database"""
    print(f"🔍 Extracting points from {collection_name}...")
    
    points = []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM points")
        total_count = cursor.fetchone()[0]
        print(f"📊 Found {total_count} points in {collection_name}")
        
        # Extract points
        query = "SELECT * FROM points"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for i, row in enumerate(rows):
            if i % 100 == 0:
                print(f"   Processing point {i+1}/{len(rows)}...")
            
            # Deserialize the point data
            point_data = deserialize_point(row[1])  # row[1] is the pickled data
            
            if point_data:
                # Convert to Qdrant API format
                point = {
                    "id": point_data.id,
                    "vector": point_data.vector,
                    "payload": point_data.payload
                }
                points.append(point)
        
        conn.close()
        print(f"✅ Extracted {len(points)} points from {collection_name}")
        return points
        
    except Exception as e:
        print(f"❌ Error extracting from {collection_name}: {e}")
        return []

def upload_points_to_qdrant(collection_name: str, points: List[Dict[str, Any]], batch_size: int = 100):
    """Upload points to Qdrant collection"""
    print(f"📤 Uploading {len(points)} points to {collection_name}...")
    
    base_url = "http://localhost:6333"
    
    # Upload in batches
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(points) + batch_size - 1) // batch_size
        
        print(f"   Uploading batch {batch_num}/{total_batches} ({len(batch)} points)...")
        
        try:
            response = requests.put(
                f"{base_url}/collections/{collection_name}/points",
                json={"points": batch},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"   ✅ Batch {batch_num} uploaded successfully")
            else:
                print(f"   ❌ Batch {batch_num} failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error uploading batch {batch_num}: {e}")
            return False
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    print(f"✅ All points uploaded to {collection_name}")
    return True

def check_collection_status(collection_name: str):
    """Check the status of a collection"""
    try:
        response = requests.get(f"http://localhost:6333/collections/{collection_name}")
        if response.status_code == 200:
            data = response.json()
            points_count = data.get('result', {}).get('points_count', 0)
            print(f"📊 {collection_name}: {points_count} points")
            return points_count
        else:
            print(f"❌ Error checking {collection_name}: {response.status_code}")
            return 0
    except Exception as e:
        print(f"❌ Error checking {collection_name}: {e}")
        return 0

def main():
    """Main import function"""
    print("🚀 Starting Qdrant data import...")
    
    # Collection configurations
    collections = {
        "kjv_sources": {
            "db_path": "qdrant_data/collection/kjv_sources/storage.sqlite",
            "limit": 100  # Start with 100 points for testing
        },
        "nbcot_test_files": {
            "db_path": "qdrant_data/collection/nbcot_test_files/storage.sqlite", 
            "limit": 50
        },
        "scriptural_truth": {
            "db_path": "qdrant_data/collection/scriptural_truth/storage.sqlite",
            "limit": 50
        }
    }
    
    # Check initial status
    print("\n📊 Initial collection status:")
    for collection_name in collections.keys():
        check_collection_status(collection_name)
    
    # Import data for each collection
    for collection_name, config in collections.items():
        print(f"\n🔄 Processing {collection_name}...")
        
        db_path = config["db_path"]
        limit = config.get("limit")
        
        if not Path(db_path).exists():
            print(f"❌ Database file not found: {db_path}")
            continue
        
        # Extract points
        points = extract_points_from_sqlite(db_path, collection_name, limit)
        
        if not points:
            print(f"❌ No points extracted from {collection_name}")
            continue
        
        # Upload points
        success = upload_points_to_qdrant(collection_name, points)
        
        if success:
            print(f"✅ {collection_name} import completed")
        else:
            print(f"❌ {collection_name} import failed")
    
    # Check final status
    print("\n📊 Final collection status:")
    for collection_name in collections.keys():
        check_collection_status(collection_name)
    
    print("\n🎉 Import process completed!")
    print("🌐 You can now view your data at: http://localhost:6333/dashboard")

if __name__ == "__main__":
    main()
