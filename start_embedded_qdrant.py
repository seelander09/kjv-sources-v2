from qdrant_client import QdrantClient
import time

client = QdrantClient(path='qdrant_data')
print('Qdrant server started on http://127.0.0.1:6333')
print('Collections:')
try:
    cols = client.get_collections()
    for coll in cols.collections:
        info = client.get_collection(coll.name)
        print(f' - {coll.name}: {info.points_count} points')
except Exception as exc:
    print(f'Failed to list collections: {exc}')

print('Press Ctrl+C to stop.')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
