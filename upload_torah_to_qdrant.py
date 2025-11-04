#!/usr/bin/env python3
"""
Upload Torah to Qdrant Vector Database
=======================================

Generates sentence-transformer embeddings for all Torah verses
and uploads them to the Qdrant collection alongside Book of Mormon.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from tqdm import tqdm


def load_torah_verses() -> List[Dict[str, Any]]:
    """Load Torah verses from CSV files"""
    verses = []
    books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
    output_dir = Path("output")
    
    for book in books:
        csv_path = output_dir / book / f"{book}.csv"
        if csv_path.exists():
            print(f"[INFO] Loading {book}...")
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Add book_category field
                    row['book_category'] = 'torah'
                    verses.append(row)
        else:
            print(f"[WARNING] {csv_path} not found, skipping")
    
    return verses


def generate_embeddings(verses: List[Dict[str, Any]], model_name: str = 'all-MiniLM-L6-v2') -> List[List[float]]:
    """Generate embeddings for all verses"""
    print(f"[INFO] Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    print(f"[INFO] Generating embeddings for {len(verses)} verses...")
    texts = [verse['full_text'] for verse in verses]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    
    return embeddings.tolist()


def upload_to_qdrant(
    verses: List[Dict[str, Any]], 
    embeddings: List[List[float]],
    collection_name: str = "kjv_sources",
    qdrant_url: str = "http://localhost:6333"
):
    """Upload verses with embeddings to Qdrant"""
    print(f"[INFO] Connecting to Qdrant at {qdrant_url}")
    client = QdrantClient(url=qdrant_url)
    
    # Get current collection info
    collection_info = client.get_collection(collection_name)
    starting_count = collection_info.points_count
    print(f"[INFO] Collection currently has {starting_count} points")
    
    # Prepare points
    points = []
    for idx, (verse, embedding) in enumerate(zip(verses, embeddings)):
        # Calculate unique ID (start after existing BOM verses)
        point_id = starting_count + idx + 1
        
        # Prepare payload
        payload = {
            "reference": verse["canonical_reference"],
            "canonical_reference": verse["canonical_reference"],
            "full_text": verse["full_text"],
            "book": verse["book"],
            "chapter": int(verse["chapter"]),
            "verse": int(verse["verse"]),
            "book_category": "torah",
            "sources": verse.get("sources", ""),
            "primary_source": verse.get("primary_source", ""),
            "is_doublet": verse.get("is_doublet", "").lower() == "true" if verse.get("is_doublet") else False,
            "doublet_names": verse.get("doublet_names", "").split(";") if verse.get("doublet_names") else [],
            "doublet_themes": verse.get("doublet_themes", "").split(";") if verse.get("doublet_themes") else [],
            "doublet_categories": verse.get("doublet_categories", "").split(";") if verse.get("doublet_categories") else [],
            # Compatibility fields for BOM comparison
            "author": verse.get("primary_source", ""),
            "literary_style": "",
            "isaiah_parallel": None,
            "christ_reference": False
        }
        
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        )
        points.append(point)
    
    # Upload in batches
    batch_size = 100
    print(f"[INFO] Uploading {len(points)} points in batches of {batch_size}...")
    
    for i in tqdm(range(0, len(points), batch_size), desc="Uploading"):
        batch = points[i:i+batch_size]
        client.upsert(
            collection_name=collection_name,
            points=batch
        )
    
    # Verify upload
    final_info = client.get_collection(collection_name)
    final_count = final_info.points_count
    print(f"[SUCCESS] Upload complete!")
    print(f"[INFO] Collection now has {final_count} points (added {final_count - starting_count})")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload Torah to Qdrant")
    parser.add_argument(
        "--collection",
        default="kjv_sources",
        help="Qdrant collection name"
    )
    parser.add_argument(
        "--qdrant-url",
        default="http://localhost:6333",
        help="Qdrant server URL"
    )
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model name"
    )
    
    args = parser.parse_args()
    
    # Load verses
    print(f"\n{'='*60}")
    print("Torah → Qdrant Upload")
    print(f"{'='*60}\n")
    
    verses = load_torah_verses()
    print(f"[INFO] Loaded {len(verses)} Torah verses")
    
    # Generate embeddings
    embeddings = generate_embeddings(verses, args.model)
    print(f"[INFO] Generated {len(embeddings)} embeddings")
    
    # Upload to Qdrant
    upload_to_qdrant(verses, embeddings, args.collection, args.qdrant_url)
    
    print(f"\n{'='*60}")
    print("✓ Torah successfully added to vector database!")
    print(f"{'='*60}\n")
    print("Full corpus now available for comparative analysis!")


if __name__ == "__main__":
    main()

