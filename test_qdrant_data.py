#!/usr/bin/env python3
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import json

client = QdrantClient(url='http://localhost:6333')

# Get collection info
info = client.get_collection('kjv_sources')
print(f"\nCollection: kjv_sources")
print(f"Total points: {info.points_count}")

# Get first 5 verses
results = client.scroll('kjv_sources', limit=5, with_payload=True)[0]

print("\nFirst 5 verses:")
for i, r in enumerate(results):
    payload = r.payload
    print(f"\n{i+1}. {payload.get('canonical_reference', 'N/A')}")
    print(f"   Text: {payload.get('full_text', '')[:60]}...")
    print(f"   Book: {payload.get('book', 'N/A')}")
    print(f"   Book Category: '{payload.get('book_category', 'NOT SET')}'")
    print(f"   Author: {payload.get('author', 'N/A')}")

# Test filter for Torah
print("\n\nTesting Torah filter:")
torah_results = client.scroll(
    'kjv_sources',
    scroll_filter=Filter(
        must=[FieldCondition(key="book_category", match=MatchValue(value="torah"))]
    ),
    limit=3,
    with_payload=True
)[0]
print(f"Found {len(torah_results)} Torah verses")

# Test filter for BOM
print("\nTesting Book of Mormon filter:")
bom_results = client.scroll(
    'kjv_sources',
    scroll_filter=Filter(
        must=[FieldCondition(key="book_category", match=MatchValue(value="book_of_mormon"))]
    ),
    limit=3,
    with_payload=True
)[0]
print(f"Found {len(bom_results)} BOM verses")

