#!/usr/bin/env python3
"""
Check Qdrant collections and their contents
"""

from qdrant_client import QdrantClient

def main():
    client = QdrantClient('localhost', port=6333)
    collections = client.get_collections()
    
    print("Available Qdrant Collections:")
    print("=" * 50)
    
    for col in collections.collections:
        print(f"\nCollection: {col.name}")
        try:
            info = client.get_collection(col.name)
            print(f"  Vectors: {info.vectors_count}")
            print(f"  Status: {info.status}")
            print(f"  Vector Size: {info.config.params.vectors.size if hasattr(info.config.params, 'vectors') else 'N/A'}")
            
            # Try to get a sample point
            try:
                points = client.scroll(col.name, limit=1)
                if points[0]:
                    print(f"  Sample point available: Yes")
                else:
                    print(f"  Sample point available: No")
            except Exception as e:
                print(f"  Sample point error: {e}")
                
        except Exception as e:
            print(f"  Error getting info: {e}")

if __name__ == "__main__":
    main()