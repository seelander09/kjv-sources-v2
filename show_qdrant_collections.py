#!/usr/bin/env python3
"""
Show Qdrant Collections Information
"""

from qdrant_client import QdrantClient
from pathlib import Path
import json

def show_collections():
    print("🔍 Qdrant Collections Information")
    print("=" * 50)
    
    qdrant_path = Path("qdrant_data")
    if not qdrant_path.exists():
        print("❌ Qdrant data directory not found")
        return
    
    try:
        # Connect to Qdrant
        client = QdrantClient(path=str(qdrant_path))
        
        # Get collections
        collections = client.get_collections()
        
        if not collections.collections:
            print("📭 No collections found")
            return
        
        print(f"📊 Found {len(collections.collections)} collections:")
        print()
        
        for collection in collections.collections:
            try:
                info = client.get_collection(collection.name)
                
                print(f"📚 Collection: {collection.name}")
                print(f"   • Points: {info.points_count:,}")
                print(f"   • Vectors: {info.vectors_count:,}")
                print(f"   • Status: {info.status}")
                print(f"   • Vector Size: {info.config.params.vectors.size}")
                print(f"   • Distance: {info.config.params.vectors.distance}")
                
                # Get a sample point
                try:
                    sample = client.scroll(collection_name=collection.name, limit=1)[0]
                    if sample:
                        point = sample[0]
                        print(f"   • Sample Payload Keys: {list(point.payload.keys()) if point.payload else 'None'}")
                except Exception as e:
                    print(f"   • Sample Error: {e}")
                
                print()
                
            except Exception as e:
                print(f"❌ Error getting info for {collection.name}: {e}")
                print()
    
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")

def show_web_ui_instructions():
    print("\n🌐 Qdrant Web UI Access Instructions")
    print("=" * 50)
    print("To access Qdrant's built-in web UI with visualization:")
    print()
    print("1. 🐳 Start Qdrant with Docker:")
    print("   docker run -d --name qdrant-ui -p 6333:6333 -p 6334:6334 \\")
    print("     -v \"$(pwd)/qdrant_data:/qdrant/storage\" \\")
    print("     qdrant/qdrant:latest")
    print()
    print("2. 🌐 Open your browser and go to:")
    print("   http://localhost:6333/dashboard")
    print()
    print("3. 📊 Visualize your collections:")
    print("   • Select a collection from the list")
    print("   • Click 'VISUALIZE' to create 2D projections")
    print("   • Use UMAP/t-SNE for clustering visualization")
    print("   • Color-code by payload attributes")
    print()
    print("4. 🔍 Features available:")
    print("   • Interactive vector visualization")
    print("   • Payload-based color coding")
    print("   • Clustering and outlier detection")
    print("   • Point inspection with tooltips")
    print()
    print("💡 Note: The Docker container needs read-write access to your data")
    print("💡 Your collections will be available once the container starts")

if __name__ == "__main__":
    show_collections()
    show_web_ui_instructions()
