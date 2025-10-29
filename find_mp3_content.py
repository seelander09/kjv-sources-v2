#!/usr/bin/env python3
"""
Find the MP3 content about "Good Things Come in Threes"
"""

import json

def search_scriptural_truth_files():
    """Search the scriptural truth files for the MP3 content"""
    
    # Try to read the scriptural truth content file
    try:
        with open('output/scriptural_truth_content.json', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Search for the MP3 title
        if "Good Things Come in Threes" in content:
            print("✅ Found 'Good Things Come in Threes' in scriptural_truth_content.json")
            
            # Try to find the specific content
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "Good Things Come in Threes" in line:
                    print(f"Found at line {i}: {line[:100]}...")
                    # Show context around this line
                    start = max(0, i-5)
                    end = min(len(lines), i+10)
                    print("\nContext:")
                    for j in range(start, end):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}{j}: {lines[j][:150]}...")
                    break
        else:
            print("❌ 'Good Things Come in Threes' not found in scriptural_truth_content.json")
            
    except FileNotFoundError:
        print("❌ scriptural_truth_content.json not found")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
    
    # Also try the training data
    try:
        with open('output/scriptural_truth_training.jsonl', 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if "Good Things Come in Threes" in line:
                    print(f"✅ Found in training data at line {line_num}")
                    data = json.loads(line)
                    print(f"Title: {data.get('title', 'No title')}")
                    print(f"Content preview: {data.get('text', '')[:300]}...")
                    break
    except FileNotFoundError:
        print("❌ scriptural_truth_training.jsonl not found")
    except Exception as e:
        print(f"❌ Error reading training file: {e}")

if __name__ == "__main__":
    print("Searching for 'Good Things Come in Threes' MP3 content...")
    print("=" * 60)
    search_scriptural_truth_files()
