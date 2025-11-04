#!/usr/bin/env python3
"""
Upload Book of Mormon to Qdrant Vector Database
===============================================

Generates sentence-transformer embeddings for all Book of Mormon verses
and uploads them to the existing Qdrant collection alongside Torah data.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from tqdm import tqdm


def load_bom_verses(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Load Book of Mormon verses from JSONL file"""
    verses = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                verses.append(json.loads(line))
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
    collection_name: str = "kjv_biblical_verses",
    qdrant_url: str = "http://localhost:6333"
):
    """Upload verses with embeddings to Qdrant"""
    print(f"[INFO] Connecting to Qdrant at {qdrant_url}")
    client = QdrantClient(url=qdrant_url)
    
    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    if collection_name not in collection_names:
        print(f"[WARNING] Collection '{collection_name}' does not exist.")
        print("[INFO] Creating new collection...")
        from qdrant_client.models import Distance, VectorParams
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
    
    # Get current collection info
    collection_info = client.get_collection(collection_name)
    starting_count = collection_info.points_count
    print(f"[INFO] Collection currently has {starting_count} points")
    
    # Prepare points
    points = []
    for idx, (verse, embedding) in enumerate(zip(verses, embeddings)):
        # Calculate unique ID (offset from Torah verses)
        point_id = starting_count + idx + 1
        
        # Prepare payload
        payload = {
            "reference": verse["canonical_reference"],
            "canonical_reference": verse["canonical_reference"],
            "full_text": verse["full_text"],
            "book": verse["book"],
            "chapter": verse["chapter"],
            "verse": verse["verse"],
            "book_category": verse["book_category"],
            "author": verse.get("author", ""),
            "literary_style": verse.get("literary_style", ""),
            "isaiah_parallel": verse.get("isaiah_parallel"),
            "christ_reference": verse.get("christ_reference", False),
            "canonical_order": verse.get("canonical_order", 0),
            # Additional fields for compatibility
            "primary_source": verse.get("author", ""),  # Map author to primary_source
            "sources": verse.get("author", ""),  # Single author
            "is_doublet": False,  # Will be identified later
            "doublet_names": [],
            "doublet_themes": [],
            "doublet_categories": []
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
    
    parser = argparse.ArgumentParser(description="Upload Book of Mormon to Qdrant")
    parser.add_argument(
        "--input",
        default="output/book_of_mormon.jsonl",
        help="Input JSONL file with parsed verses"
    )
    parser.add_argument(
        "--collection",
        default="kjv_biblical_verses",
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
    print("Book of Mormon → Qdrant Upload")
    print(f"{'='*60}\n")
    
    verses = load_bom_verses(Path(args.input))
    print(f"[INFO] Loaded {len(verses)} verses")
    
    # Generate embeddings
    embeddings = generate_embeddings(verses, args.model)
    print(f"[INFO] Generated {len(embeddings)} embeddings")
    
    # Upload to Qdrant
    upload_to_qdrant(verses, embeddings, args.collection, args.qdrant_url)
    
    print(f"\n{'='*60}")
    print("✓ Book of Mormon successfully added to vector database!")
    print(f"{'='*60}\n")
    print("You can now query Book of Mormon verses using:")
    print("  - API endpoints")
    print("  - Semantic search")
    print("  - Comparative analysis with Torah")


if __name__ == "__main__":
    main()

