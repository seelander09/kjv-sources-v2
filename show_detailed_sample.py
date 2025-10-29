#!/usr/bin/env python3
"""
Show detailed sample from The Book of Jubilees
"""

import json

def show_detailed_sample():
    # Load the processed content
    with open('output/scriptural_truth_debug_content.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find The Book of Jubilees
    jubilees = None
    for item in data:
        if 'JUBILEES' in item['title'].upper() and item['content_type'] == 'pdf':
            jubilees = item
            break
    
    if not jubilees:
        print("❌ The Book of Jubilees not found")
        return
    
    print("📚 THE BOOK OF JUBILEES - Detailed Sample")
    print("=" * 60)
    print(f"Title: {jubilees['title']}")
    print(f"Total Length: {len(jubilees['content']):,} characters")
    print(f"File: {jubilees['file_path']}")
    print(f"Word Count: {jubilees['metadata']['word_count']:,} words")
    
    content = jubilees['content']
    
    print("\n📝 BEGINNING OF THE BOOK:")
    print("-" * 60)
    print(content[:1000])
    print("-" * 60)
    
    print("\n📝 MIDDLE SECTION (characters 10000-11000):")
    print("-" * 60)
    print(content[10000:11000])
    print("-" * 60)
    
    print("\n📝 END OF THE BOOK:")
    print("-" * 60)
    print(content[-500:])
    print("-" * 60)
    
    # Show some statistics
    print(f"\n📊 CONTENT STATISTICS:")
    print(f"  Total Characters: {len(content):,}")
    print(f"  Total Words: {jubilees['metadata']['word_count']:,}")
    print(f"  Average Word Length: {len(content) / jubilees['metadata']['word_count']:.1f} characters")
    print(f"  File Size: {jubilees['file_size']:,} bytes")
    print(f"  Processing Date: {jubilees['processed_at']}")

if __name__ == "__main__":
    show_detailed_sample()
