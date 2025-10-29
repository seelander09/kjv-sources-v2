#!/usr/bin/env python3
"""
Check ScripturalTruth collection in Weaviate
"""

import weaviate

def check_scriptural_truth_collection():
    """Check the ScripturalTruth collection contents"""
    try:
        # Connect to Weaviate
        client = weaviate.connect_to_local(host='localhost', port=8080)
        print("✓ Connected to Weaviate")
        
        # Get the ScripturalTruth collection
        collection = client.collections.get('ScripturalTruth')
        print("✓ Found ScripturalTruth collection")
        
        # Check collection properties
        config = collection.config.get()
        print(f"Collection properties: {[prop.name for prop in config.properties]}")
        
        # Try to get count
        try:
            count_result = collection.aggregate.over_all(total_count=True)
            print(f"Total items in ScripturalTruth: {count_result.total_count}")
        except Exception as e:
            print(f"Could not get count: {e}")
        
        # Try to fetch some objects
        try:
            result = collection.query.fetch_objects(limit=5)
            print(f"Successfully fetched {len(result.objects)} sample items:")
            for i, obj in enumerate(result.objects):
                title = obj.properties.get('title', 'No title')
                item_id = obj.properties.get('item_id', 'No ID')
                print(f"  {i+1}. ID: {item_id}, Title: {title}")
        except Exception as e:
            print(f"Could not fetch objects: {e}")
        
        client.close()
        print("✓ Connection closed")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_scriptural_truth_collection()
