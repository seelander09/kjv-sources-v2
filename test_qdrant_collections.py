#!/usr/bin/env python3
"""
Test Qdrant Collections via API
Tests the Qdrant collections without loading the entire database into memory
"""

import requests
import json
from datetime import datetime

def test_qdrant_api():
    """Test Qdrant API and collections"""
    print("🔍 Testing Qdrant Collections via API")
    print("=" * 50)
    
    base_url = "http://localhost:6333"
    
    try:
        # Test basic connectivity
        print("🔌 Testing Qdrant connectivity...")
        response = requests.get(f"{base_url}/collections", timeout=10)
        
        if response.status_code == 200:
            print("✅ Qdrant API is accessible")
            
            data = response.json()
            collections = data.get('result', {}).get('collections', [])
            
            if not collections:
                print("📭 No collections found")
                return
            
            print(f"📊 Found {len(collections)} collections:")
            print()
            
            # Get detailed info for each collection
            for collection in collections:
                collection_name = collection['name']
                print(f"📚 Collection: {collection_name}")
                
                try:
                    # Get collection info
                    info_response = requests.get(f"{base_url}/collections/{collection_name}", timeout=10)
                    if info_response.status_code == 200:
                        info = info_response.json()['result']
                        
                        print(f"   • Points: {info.get('points_count', 0):,}")
                        print(f"   • Vectors: {info.get('vectors_count', 0):,}")
                        print(f"   • Status: {info.get('status', 'unknown')}")
                        
                        config = info.get('config', {}).get('params', {}).get('vectors', {})
                        if config:
                            print(f"   • Vector Size: {config.get('size', 'unknown')}")
                            print(f"   • Distance: {config.get('distance', 'unknown')}")
                        
                        # Get a sample point
                        try:
                            sample_response = requests.post(
                                f"{base_url}/collections/{collection_name}/points/scroll",
                                json={"limit": 1},
                                timeout=10
                            )
                            
                            if sample_response.status_code == 200:
                                sample_data = sample_response.json()
                                points = sample_data.get('result', {}).get('points', [])
                                
                                if points:
                                    point = points[0]
                                    payload_keys = list(point.get('payload', {}).keys())
                                    print(f"   • Sample Payload Keys: {payload_keys[:5]}{'...' if len(payload_keys) > 5 else ''}")
                                else:
                                    print("   • No sample points available")
                            else:
                                print(f"   • Sample Error: HTTP {sample_response.status_code}")
                                
                        except Exception as e:
                            print(f"   • Sample Error: {e}")
                        
                    else:
                        print(f"   ❌ Error getting info: HTTP {info_response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                
                print()
            
            # Test search functionality
            print("🔍 Testing search functionality...")
            if collections:
                test_collection = collections[0]['name']
                print(f"   Testing search on collection: {test_collection}")
                
                try:
                    # Test a simple search
                    search_response = requests.post(
                        f"{base_url}/collections/{test_collection}/points/search",
                        json={
                            "vector": [0.1] * 384,  # Dummy vector
                            "limit": 3
                        },
                        timeout=10
                    )
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        results = search_data.get('result', [])
                        print(f"   ✅ Search successful: {len(results)} results")
                    else:
                        print(f"   ❌ Search failed: HTTP {search_response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Search error: {e}")
            
        else:
            print(f"❌ Qdrant API error: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Qdrant API")
        print("   Make sure Qdrant is running on http://localhost:6333")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_web_ui_info():
    """Show web UI access information"""
    print("\n🌐 Qdrant Web UI Access")
    print("=" * 30)
    print("📊 Dashboard: http://localhost:6333/dashboard")
    print("🔍 Collections: http://localhost:6333/collections")
    print("📚 API Docs: http://localhost:6333/docs")
    print()
    print("💡 To visualize collections:")
    print("   1. Go to http://localhost:6333/dashboard")
    print("   2. Select a collection")
    print("   3. Click 'VISUALIZE' for 2D projections")
    print("   4. Use UMAP/t-SNE for clustering visualization")

def main():
    """Main function"""
    test_qdrant_api()
    show_web_ui_info()

if __name__ == "__main__":
    main()
