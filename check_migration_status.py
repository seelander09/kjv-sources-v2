#!/usr/bin/env python3
"""
Check Scriptural Truth Migration Status
======================================

Quick status checker for the migration process
"""

import json
import os
from pathlib import Path
from datetime import datetime

def check_migration_status():
    """Check the current migration status"""
    
    print("🔍 Scriptural Truth Migration Status Check")
    print("=" * 50)
    
    # Check status file
    status_file = Path("migration_status.json")
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            
            print(f"📊 Migration Status: {status.get('status', 'Unknown')}")
            print(f"🕐 Started: {status.get('started', 'Unknown')}")
            print(f"📝 Current Step: {status.get('current_step', 'Unknown')}")
            print(f"📄 Pages Found: {status.get('pages_found', 0)}")
            print(f"📝 Content Items: {status.get('content_items', 0)}")
            print(f"🧠 Embeddings: {status.get('embeddings_created', 0)}")
            print(f"💾 Qdrant Points: {status.get('qdrant_points', 0)}")
            
            if status.get('errors'):
                print(f"❌ Errors: {len(status['errors'])}")
                for error in status['errors'][-3:]:  # Show last 3 errors
                    print(f"   - {error}")
            
        except Exception as e:
            print(f"❌ Error reading status file: {e}")
    else:
        print("❌ No status file found - migration may not be running")
    
    # Check log file
    log_file = Path("scriptural_truth_migration.log")
    if log_file.exists():
        print(f"\n📝 Recent Log Entries:")
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-5:]:  # Show last 5 lines
                    print(f"   {line.strip()}")
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
    else:
        print("\n❌ No log file found")
    
    # Check output directory
    output_dir = Path("scriptural_truth_data")
    if output_dir.exists():
        print(f"\n📁 Output Files:")
        for file in output_dir.iterdir():
            if file.is_file():
                size = file.stat().st_size
                print(f"   - {file.name} ({size:,} bytes)")
    else:
        print("\n❌ No output directory found")
    
    # Check Qdrant collection
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(path="qdrant_data")
        collections = client.get_collections()
        
        print(f"\n🗄️ Qdrant Collections:")
        for collection in collections.collections:
            if collection.name == "scriptural_truth":
                info = client.get_collection("scriptural_truth")
                print(f"   ✅ scriptural_truth: {info.points_count} points")
            else:
                print(f"   - {collection.name}")
                
    except Exception as e:
        print(f"\n❌ Error checking Qdrant: {e}")

if __name__ == "__main__":
    check_migration_status()
