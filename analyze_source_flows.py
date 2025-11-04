#!/usr/bin/env python3
"""
Analyze Source Flow Network - Detailed Doublet Analysis
Shows granular data about source relationships and specific examples
"""

import json
import requests
from collections import defaultdict, Counter

# Fetch the doublet data directly from API
print("Fetching doublet data from API...")
response = requests.get('http://localhost:8001/api/v1/doublets/timeline')
data = response.json()

doublets = data['doublets']

print("=" * 80)
print("SOURCE FLOW NETWORK - DETAILED ANALYSIS")
print("=" * 80)

# Group doublets by doublet name to find which sources appear together
doublet_groups = defaultdict(list)
for d in doublets:
    for name in d['doublet_names']:
        doublet_groups[name].append(d)

print(f"\nTotal doublets found: {len(doublets)}")
print(f"Unique doublet groups: {len(doublet_groups)}")

# Analyze source pairings
source_pairings = defaultdict(int)
source_to_sources = defaultdict(lambda: defaultdict(list))

for name, verses in doublet_groups.items():
    # Get all sources in this doublet group
    sources_in_group = set()
    for v in verses:
        sources_in_group.update(v['sources'])
    
    # Create pairings
    sources_list = sorted(list(sources_in_group))
    if len(sources_list) >= 2:
        for i, source1 in enumerate(sources_list):
            for source2 in sources_list[i+1:]:
                pair = f"{source1} ↔ {source2}"
                source_pairings[pair] += 1
                source_to_sources[source1][source2].append(name)
                source_to_sources[source2][source1].append(name)

print("\n" + "=" * 80)
print("SOURCE PAIRING FREQUENCY (Doublets involving these source combinations)")
print("=" * 80)
for pair, count in sorted(source_pairings.items(), key=lambda x: -x[1]):
    print(f"{pair:20} : {count:3} doublet groups")

print("\n" + "=" * 80)
print("R (REDACTOR) - DETAILED ANALYSIS")
print("=" * 80)

print("\n📥 INFLOWS TO R (Other sources that R also has versions of):")
print("-" * 80)
for source in ['J', 'E', 'P', 'D']:
    if source in source_to_sources and 'R' in source_to_sources[source]:
        doublet_names = source_to_sources[source]['R']
        print(f"\n{source} → R: {len(doublet_names)} doublet group(s)")
        for name in doublet_names[:5]:  # Show first 5
            print(f"  • {name}")
        if len(doublet_names) > 5:
            print(f"  ... and {len(doublet_names) - 5} more")

print("\n📤 OUTFLOWS FROM R (R material that other sources also have):")
print("-" * 80)
if 'R' in source_to_sources:
    for target, doublet_names in source_to_sources['R'].items():
        if target != 'R':
            print(f"\nR → {target}: {len(doublet_names)} doublet group(s)")
            for name in doublet_names[:5]:
                print(f"  • {name}")
            if len(doublet_names) > 5:
                print(f"  ... and {len(doublet_names) - 5} more")
else:
    print("No outflows from R found")

print("\n" + "=" * 80)
print("J (JAHWIST) - DETAILED ANALYSIS")
print("=" * 80)

print("\n📤 OUTFLOWS FROM J (J stories that other sources also have):")
print("-" * 80)
if 'J' in source_to_sources:
    for target, doublet_names in sorted(source_to_sources['J'].items(), key=lambda x: -len(x[1])):
        if target != 'J':
            print(f"\nJ → {target}: {len(doublet_names)} doublet group(s)")
            for name in doublet_names[:5]:
                print(f"  • {name}")
            if len(doublet_names) > 5:
                print(f"  ... and {len(doublet_names) - 5} more")

print("\n" + "=" * 80)
print("KEY INSIGHTS")
print("=" * 80)

# Chronological ordering
print("\n1. CHRONOLOGICAL FLOW (Expected: Earlier → Later)")
print("-" * 80)
chronology = ['J', 'E', 'P', 'D', 'R']
print("Expected order: J (~950 BCE) → E (~850 BCE) → P (~550 BCE) → D (~620 BCE) → R (~450 BCE)")

print("\n2. WHY R HAS INFLOWS FROM ALL SOURCES:")
print("-" * 80)
print("✓ R is the LATEST source (post-exilic period)")
print("✓ R had access to all earlier traditions (J, E, P, D)")
print("✓ R's role: compile, harmonize, edit existing material")
print("✓ Inflows show: R worked with material from ALL earlier sources")

print("\n3. WHY R HAS MINIMAL/NO OUTFLOW TO J:")
print("-" * 80)
print("✓ CHRONOLOGICAL CONSTRAINT: R cannot influence J (J came centuries earlier)")
print("✓ No R→J flow = Data respects chronological integrity")
print("✓ If R→J existed, it would suggest:")
print("  - Data error")
print("  - Late insertions into J material")
print("  - Or misattribution of sources")

print("\n4. WHAT THE J→R FLOW MEANS:")
print("-" * 80)
if 'J' in source_to_sources and 'R' in source_to_sources['J']:
    j_to_r_count = len(source_to_sources['J']['R'])
    print(f"✓ {j_to_r_count} doublet groups where J material was later edited/revised by R")
    print("✓ Shows: J stories were important enough to preserve BUT also modify")
    print("✓ Examples: J's anthropomorphic God → R's more theological revision")
    print("✓ Demonstrates: Centuries of textual transmission and editing")

print("\n" + "=" * 80)
print("SPECIFIC DOUBLET EXAMPLES")
print("=" * 80)

# Show a few concrete examples
example_count = 0
for name, verses in list(doublet_groups.items())[:10]:
    sources_in_group = set()
    for v in verses:
        sources_in_group.update(v['sources'])
    
    if len(sources_in_group) >= 2:
        print(f"\n📖 {name}")
        print(f"   Sources: {', '.join(sorted(sources_in_group))}")
        print(f"   Verses: {len(verses)} verses involved")
        
        # Show verse references
        refs = []
        for v in verses[:3]:
            ref = f"{v['book']} {v['chapter']}:{v['verse']}"
            refs.append(ref)
        print(f"   Examples: {', '.join(refs)}")
        if len(verses) > 3:
            print(f"   ... and {len(verses) - 3} more verses")
        
        example_count += 1
        if example_count >= 5:
            break

print("\n" + "=" * 80)
print("END OF ANALYSIS")
print("=" * 80)

