#!/usr/bin/env python3
"""
Simple Torah upload script with clear progress output
"""

import os
import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("=" * 60)
    print("TORAH UPLOAD TO QDRANT")
    print("=" * 60)
    
    # Check what data files we have
    output_dir = Path("output")
    books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    
    print("\n1. CHECKING DATA FILES:")
    print("-" * 30)
    
    available_books = []
    for book in books:
        csv_path = output_dir / book / f"{book}.csv"
        if csv_path.exists():
            size_mb = csv_path.stat().st_size / (1024 * 1024)
            print(f"✓ {book}: {size_mb:.2f} MB - READY")
            available_books.append(book)
        else:
            print(f"✗ {book}: MISSING")
    
    if not available_books:
        print("\n❌ NO DATA FILES FOUND!")
        print("Run the parser first to generate the CSV files.")
        return
    
    print(f"\nFound {len(available_books)} books ready for upload.")
    
    # Try to import the Qdrant client
    print("\n2. INITIALIZING QDRANT CLIENT:")
    print("-" * 30)
    
    try:
        from kjv_sources.qdrant_client import KJVQdrantClient
        print("✓ Qdrant client imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return
    
    try:
        client = KJVQdrantClient()
        print("✓ Qdrant client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return
    
    # Upload each book
    print(f"\n3. UPLOADING {len(available_books)} BOOKS:")
    print("-" * 30)
    
    successful = []
    failed = []
    
    for i, book in enumerate(available_books, 1):
        print(f"\n[{i}/{len(available_books)}] Uploading {book}...")
        
        csv_path = output_dir / book / f"{book}.csv"
        
        try:
            print(f"  - File: {csv_path}")
            print(f"  - Size: {csv_path.stat().st_size / (1024*1024):.2f} MB")
            print(f"  - Status: Starting upload...")
            
            start_time = time.time()
            success = client.upload_book_data(book, str(csv_path))
            elapsed = time.time() - start_time
            
            if success:
                print(f"  - Result: ✅ SUCCESS ({elapsed:.1f}s)")
                successful.append(book)
            else:
                print(f"  - Result: ❌ FAILED")
                failed.append(book)
                
        except Exception as e:
            print(f"  - Result: ❌ ERROR - {e}")
            failed.append(book)
    
    # Final summary
    print("\n" + "=" * 60)
    print("UPLOAD SUMMARY:")
    print("=" * 60)
    
    print(f"✅ Successful: {len(successful)}")
    for book in successful:
        print(f"   - {book}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for book in failed:
            print(f"   - {book}")
    
    # Show collection stats
    if successful:
        print(f"\n📊 COLLECTION STATISTICS:")
        try:
            stats = client.get_collection_stats()
            if stats:
                print(f"   Total verses: {stats.get('total_points', 0)}")
                print(f"   Vector size: {stats.get('vector_size', 0)}")
                print(f"   Status: {stats.get('status', 'Unknown')}")
        except Exception as e:
            print(f"   Could not get stats: {e}")
    
    print("\n🎉 UPLOAD COMPLETED!")
    print("You can now search across the entire Torah for geographical patterns.")

if __name__ == "__main__":
    main()
