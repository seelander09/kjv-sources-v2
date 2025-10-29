#!/usr/bin/env python3
"""
Show sample content from Scriptural Truth processing
"""

import json
from pathlib import Path

def show_sample_content():
    # Load the processed content
    with open('output/scriptural_truth_debug_content.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("📚 Scriptural Truth Content Samples")
    print("=" * 50)
    
    # Find PDF items with substantial content
    pdf_items = [item for item in data if item['content_type'] == 'pdf' and len(item['content']) > 1000]
    print(f"\n📄 Found {len(pdf_items)} PDF items with substantial content")
    
    if pdf_items:
        # Show first PDF sample
        sample = pdf_items[0]
        print(f"\n🔍 SAMPLE 1: {sample['title']}")
        print(f"📊 Content Length: {len(sample['content']):,} characters")
        print(f"📁 File: {sample['file_path']}")
        print("\n📝 Content Preview (first 800 characters):")
        print("-" * 60)
        print(sample['content'][:800] + "..." if len(sample['content']) > 800 else sample['content'])
        print("-" * 60)
    
    # Find HTML items with substantial content
    html_items = [item for item in data if item['content_type'] == 'webpage' and len(item['content']) > 500]
    print(f"\n🌐 Found {len(html_items)} HTML items with substantial content")
    
    if html_items:
        # Show first HTML sample
        sample = html_items[0]
        print(f"\n🔍 SAMPLE 2: {sample['title']}")
        print(f"📊 Content Length: {len(sample['content']):,} characters")
        print(f"📁 File: {sample['file_path']}")
        print("\n📝 Content Preview (first 600 characters):")
        print("-" * 60)
        print(sample['content'][:600] + "..." if len(sample['content']) > 600 else sample['content'])
        print("-" * 60)
    
    # Show content type breakdown
    print(f"\n📊 CONTENT TYPE BREAKDOWN:")
    content_types = {}
    for item in data:
        content_type = item['content_type']
        if content_type not in content_types:
            content_types[content_type] = {'count': 0, 'total_chars': 0}
        content_types[content_type]['count'] += 1
        content_types[content_type]['total_chars'] += len(item['content'])
    
    for content_type, stats in content_types.items():
        avg_chars = stats['total_chars'] // stats['count'] if stats['count'] > 0 else 0
        print(f"  {content_type.upper()}: {stats['count']} items, {stats['total_chars']:,} total chars, {avg_chars:,} avg chars")
    
    # Show largest content items
    print(f"\n🏆 LARGEST CONTENT ITEMS:")
    sorted_items = sorted(data, key=lambda x: len(x['content']), reverse=True)[:5]
    for i, item in enumerate(sorted_items, 1):
        print(f"  {i}. {item['title']} ({item['content_type']}) - {len(item['content']):,} characters")

if __name__ == "__main__":
    show_sample_content()
