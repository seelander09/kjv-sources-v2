#!/usr/bin/env python3
"""
Analyze SQLite files to understand Qdrant data structure
"""

import sqlite3
import json
import os
from pathlib import Path

def analyze_sqlite_file(db_path):
    """Analyze a SQLite file to understand its structure"""
    print(f"\n🔍 Analyzing: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ File not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Tables: {[table[0] for table in tables]}")
        
        # Analyze each table
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print(f"   Columns: {[col[1] for col in columns]}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   Rows: {count}")
            
            # Show sample data (first few rows)
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_rows = cursor.fetchall()
                print(f"   Sample data:")
                for i, row in enumerate(sample_rows):
                    print(f"     Row {i+1}: {row[:3]}...")  # Show first 3 columns
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing {db_path}: {e}")

def main():
    """Main analysis function"""
    print("🔍 Analyzing Qdrant SQLite data files...")
    
    # Check local files
    qdrant_path = Path("qdrant_data/collection")
    if qdrant_path.exists():
        print(f"\n📁 Local files in {qdrant_path}:")
        for collection_dir in qdrant_path.iterdir():
            if collection_dir.is_dir():
                sqlite_file = collection_dir / "storage.sqlite"
                if sqlite_file.exists():
                    analyze_sqlite_file(str(sqlite_file))
    
    # Check container files
    print(f"\n🐳 Container files:")
    collections = ["kjv_sources", "nbcot_test_files", "scriptural_truth"]
    for collection in collections:
        container_path = f"/qdrant/storage/collection/{collection}/storage.sqlite"
        print(f"   {collection}: {container_path}")

if __name__ == "__main__":
    main()
