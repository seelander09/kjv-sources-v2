#!/usr/bin/env python3
"""
Show HTML content samples
"""

import json

def show_html_samples():
    # Load the processed content
    with open('output/scriptural_truth_debug_content.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find HTML items with substantial content
    html_items = [item for item in data if item['content_type'] == 'webpage' and len(item['content']) > 5000]
    
    print("🌐 HTML CONTENT SAMPLES")
    print("=" * 50)
    print(f"Found {len(html_items)} HTML items with substantial content")
    
    # Show first 3 HTML samples
    for i, sample in enumerate(html_items[:3], 1):
        print(f"\n📄 SAMPLE {i}: {sample['title']}")
        print(f"📊 Length: {len(sample['content']):,} characters")
        print(f"📁 File: {sample['file_path']}")
        print("\n📝 Content Preview (first 600 characters):")
        print("-" * 50)
        content_preview = sample['content'][:600] + "..." if len(sample['content']) > 600 else sample['content']
        print(content_preview)
        print("-" * 50)
    
    # Show content type summary
    print(f"\n📊 SUMMARY OF ALL CONTENT:")
    total_chars = sum(len(item['content']) for item in data)
    total_words = sum(item['metadata']['word_count'] for item in data)
    
    print(f"  Total Items: {len(data)}")
    print(f"  Total Characters: {total_chars:,}")
    print(f"  Total Words: {total_words:,}")
    print(f"  Average Item Length: {total_chars // len(data):,} characters")
    print(f"  Average Word Length: {total_chars / total_words:.1f} characters")

if __name__ == "__main__":
    show_html_samples()
