#!/usr/bin/env python3
"""
Start Qdrant Web GUI and show collections
"""

from qdrant_client import QdrantClient
import webbrowser
import time
import subprocess
import sys

def start_qdrant_gui():
    print('🚀 Starting Qdrant Web GUI...')
    print('=' * 40)

    # Check if Qdrant server is running
    try:
        client = QdrantClient(host='localhost', port=6333)
        collections = client.get_collections()
        print(f'✅ Qdrant server is running on localhost:6333')
        print(f'📊 Found {len(collections.collections)} collections:')
        
        for collection in collections.collections:
            info = client.get_collection(collection.name)
            print(f'   📁 {collection.name}: {info.points_count} points')
        
        print(f'\n🌐 Opening Qdrant Web GUI...')
        print(f'   URL: http://localhost:6333/dashboard')
        
        # Open the web GUI
        webbrowser.open('http://localhost:6333/dashboard')
        
        print(f'\n✅ Qdrant Web GUI should now be open in your browser!')
        print(f'   If it didn\'t open automatically, go to: http://localhost:6333/dashboard')
        
    except Exception as e:
        print(f'❌ Error connecting to Qdrant: {e}')
        print(f'\n🔧 Let\'s try to start Qdrant server...')
        
        try:
            # Try to start Qdrant server
            subprocess.Popen(['qdrant', '--config-path', 'qdrant_config.yaml'], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
            print(f'✅ Qdrant server starting...')
            print(f'   Please wait a moment and then go to: http://localhost:6333/dashboard')
        except:
            print(f'❌ Could not start Qdrant server automatically')
            print(f'   Please start Qdrant manually or check if it\'s installed')

if __name__ == "__main__":
    start_qdrant_gui()

