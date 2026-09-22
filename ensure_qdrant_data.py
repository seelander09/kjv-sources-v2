#!/usr/bin/env python3
"""
Ensure local Qdrant has kjv_sources collection with data.
Creates the collection and uploads from output/ CSV files if missing or empty.
Run from project root. Requires output/<Book>/<Book>.csv (from pipeline or existing data).
"""

import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]


def main():
    try:
        from src.kjv_sources.qdrant_client import create_qdrant_client
    except ImportError as e:
        print("Import error. Install deps: pip install -r requirements.txt -r api_requirements.txt")
        print(e)
        return 1

    print("Checking local Qdrant (qdrant_data)...")
    try:
        client = create_qdrant_client(use_local=True)
    except Exception as e:
        err = str(e).lower()
        if "validationerror" in err or "extra inputs" in err or "pydantic" in err:
            print("Local qdrant_data has an incompatible schema (e.g. from an older Qdrant client).")
            print("Remove or rename the folder 'qdrant_data' and run again to create a fresh database.")
        else:
            print(f"Qdrant client error: {e}")
        return 1

    # Check if collection exists and has data
    try:
        colls = client.client.get_collections()
        exists = any(c.name == client.collection_name for c in colls.collections)
    except Exception:
        exists = False

    if exists:
        try:
            info = client.client.get_collection(client.collection_name)
            count = info.points_count
            if count and count > 0:
                print(f"Collection '{client.collection_name}' exists with {count} points. Skipping upload.")
                return 0
        except Exception as e:
            print(f"Could not get collection info: {e}")

    # Create or recreate collection
    print("Creating collection (if needed)...")
    client.create_collection(force_recreate=False)

    # Find and upload CSVs
    uploaded = 0
    for book in BOOKS:
        csv_path = ROOT / "output" / book / f"{book}.csv"
        if not csv_path.exists():
            print(f"  [SKIP] {csv_path} not found")
            continue
        if client.upload_book_data(book, str(csv_path)):
            uploaded += 1

    if uploaded == 0:
        print("\nNo CSV data found under output/<Book>/<Book>.csv.")
        print("Run the pipeline first: python kjv_pipeline.py")
        return 1

    print(f"\nUploaded {uploaded} book(s). You can start the API and dashboard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
