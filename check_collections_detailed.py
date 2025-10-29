#!/usr/bin/env python3
"""
Detailed collection analysis
"""

from qdrant_client import QdrantClient

def main():
    client = QdrantClient('localhost', port=6333)
    collections = client.get_collections()
    
    print("Detailed Collection Analysis:")
    print("=" * 50)
    
    for col in collections.collections:
        print(f"\nCollection: {col.name}")
        try:
            info = client.get_collection(col.name)
            print(f"  Vectors: {info.vectors_count}")
            print(f"  Status: {info.status}")
            print(f"  Config: {info.config}")
            
            # Try to get a sample point to see the structure
            try:
                points = client.scroll(col.name, limit=1)
                if points[0]:
                    print(f"  Sample point structure:")
                    point = points[0][0]
                    print(f"    ID: {point.id}")
                    print(f"    Payload keys: {list(point.payload.keys()) if point.payload else 'No payload'}")
                    if point.payload:
                        for key, value in point.payload.items():
                            if isinstance(value, str) and len(value) > 100:
                                print(f"    {key}: {value[:100]}...")
                            else:
                                print(f"    {key}: {value}")
                else:
                    print(f"  No sample points available")
            except Exception as e:
                print(f"  Error getting sample: {e}")
                
        except Exception as e:
            print(f"  Error getting info: {e}")

if __name__ == "__main__":
    main()
