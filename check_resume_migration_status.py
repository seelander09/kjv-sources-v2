#!/usr/bin/env python3
"""
Check status of Scriptural Truth migration with resume capability
"""

import json
from pathlib import Path
from datetime import datetime

def check_migration_status():
    print("🔍 Scriptural Truth Migration Status (Resume Version)")
    print("=" * 60)
    
    output_dir = Path("scriptural_truth_data")
    
    if not output_dir.exists():
        print("❌ No migration data directory found")
        return
    
    # Check progress file
    progress_file = output_dir / "migration_progress.json"
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            print(f"📊 Current Phase: {progress.get('phase', 'unknown')}")
            print(f"📊 Items Stored: {progress.get('stored_count', 0)}")
            print(f"📊 Last Updated: {progress.get('last_updated', 'unknown')}")
        except Exception as e:
            print(f"❌ Error reading progress file: {e}")
    else:
        print("❌ No progress file found - migration may not be running")
    
    # Check discovered URLs
    discovered_file = output_dir / "discovered_urls.json"
    if discovered_file.exists():
        try:
            with open(discovered_file, 'r') as f:
                urls = json.load(f)
            print(f"📊 Discovered URLs: {len(urls)}")
        except Exception as e:
            print(f"❌ Error reading discovered URLs: {e}")
    else:
        print("❌ No discovered URLs file found")
    
    # Check processed items
    processed_file = output_dir / "processed_items.json"
    if processed_file.exists():
        try:
            with open(processed_file, 'r') as f:
                items = json.load(f)
            print(f"📊 Processed Items: {len(items)}")
        except Exception as e:
            print(f"❌ Error reading processed items: {e}")
    else:
        print("❌ No processed items file found")
    
    # Check final output
    final_file = output_dir / "scriptural_truth_content.json"
    if final_file.exists():
        try:
            with open(final_file, 'r') as f:
                content = json.load(f)
            print(f"📊 Final Content Items: {len(content)}")
        except Exception as e:
            print(f"❌ Error reading final content: {e}")
    else:
        print("❌ No final content file found")
    
    print("\n📁 Files in migration directory:")
    for file in output_dir.iterdir():
        if file.is_file():
            size = file.stat().st_size
            modified = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  📄 {file.name} ({size:,} bytes, modified: {modified})")

if __name__ == "__main__":
    check_migration_status()
