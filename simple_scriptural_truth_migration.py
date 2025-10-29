#!/usr/bin/env python3
"""
Simple Scriptural Truth Migration - Downloads and processes content
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import re

# Web scraping
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# AI and vector database
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

print("🚀 Starting Simple Scriptural Truth Migration")
print("=" * 50)

# Setup
base_url = "https://scriptural-truth.com/"
output_dir = Path("scriptural_truth_data")
output_dir.mkdir(exist_ok=True)

# Initialize AI model
print("🧠 Loading AI model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ AI model loaded")

# Initialize Qdrant (create new collection)
print("🗄️ Setting up Qdrant...")
try:
    qdrant_client = QdrantClient(path="qdrant_data")
    collection_name = "scriptural_truth"
    
    # Create collection if it doesn't exist
    try:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=384,  # all-MiniLM-L6-v2 dimension
                distance=Distance.COSINE
            )
        )
        print(f"✅ Created collection '{collection_name}'")
    except Exception as e:
        print(f"ℹ️ Collection '{collection_name}' already exists")
    
except Exception as e:
    print(f"❌ Qdrant setup failed: {e}")
    exit(1)

print("✅ Qdrant setup complete")

# Simple page discovery
print("🔍 Discovering pages...")
discovered_urls = set()
to_process = [base_url]

while to_process:
    current_url = to_process.pop(0)
    
    if current_url in discovered_urls:
        continue
    
    try:
        print(f"📄 Processing: {current_url}")
        response = requests.get(current_url, timeout=10)
        response.raise_for_status()
        
        discovered_urls.add(current_url)
        
        # Parse HTML and find links
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all internal links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            
            # Only process internal links
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                # Skip multi-language documents
                if any(lang in full_url.lower() for lang in ['russian', 'german', 'afrikaan', 'arabic', 'hindi', 'japanese', 'spanish', 'french', 'chinese', 'korean']):
                    continue
                # Skip PDF_Other_Languages directory entirely
                if 'pdf_other_languages' in full_url.lower():
                    continue
                    
                if full_url not in discovered_urls and full_url not in to_process:
                    to_process.append(full_url)
        
        time.sleep(0.5)  # Be respectful to the server
        
    except Exception as e:
        print(f"❌ Failed to process {current_url}: {e}")
        continue

print(f"✅ Discovered {len(discovered_urls)} pages")

# Process content
print("📝 Processing content...")
content_items = []
processed_count = 0

for url in discovered_urls:
    try:
        print(f"📄 Processing content: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title = title.get_text().strip() if title else urlparse(url).path
        
        # Extract main content
        content = ""
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if main_content:
            content = main_content.get_text(separator='\n', strip=True)
        else:
            body = soup.find('body')
            if body:
                content = body.get_text(separator='\n', strip=True)
        
        # Clean up content
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = content.strip()
        
        if not content or len(content) < 100:
            continue
        
        # Determine content type
        content_type = "article"
        if url.endswith('.mp3') or 'mp3' in url.lower():
            content_type = "mp3"
        elif url.endswith('.pdf') or 'pdf' in url.lower():
            content_type = "pdf"
        elif url.endswith('.mp4') or 'video' in url.lower():
            content_type = "video"
        
        # Create content item
        content_item = {
            "id": hashlib.md5(url.encode()).hexdigest()[:12],
            "title": title,
            "url": url,
            "content_type": content_type,
            "content": content,
            "word_count": len(content.split()),
            "character_count": len(content),
            "created_at": datetime.now().isoformat(),
            "file_size": len(response.content),
            "checksum": hashlib.md5(content.encode()).hexdigest()
        }
        
        content_items.append(content_item)
        processed_count += 1
        
        print(f"✅ Processed {processed_count} items")
        
        time.sleep(0.5)  # Be respectful to the server
        
    except Exception as e:
        print(f"❌ Failed to process {url}: {e}")
        continue

print(f"✅ Processed {len(content_items)} content items")

# Save processed data
print("💾 Saving processed data...")
with open(output_dir / "scriptural_truth_content.json", 'w', encoding='utf-8') as f:
    json.dump(content_items, f, indent=2, ensure_ascii=False)

print("✅ Data saved to scriptural_truth_data/scriptural_truth_content.json")

# Create embeddings and store in Qdrant
print("🧠 Creating embeddings and storing in Qdrant...")
stored_count = 0

for i, item in enumerate(content_items):
    try:
        print(f"📊 Processing item {i+1}/{len(content_items)}: {item['title'][:50]}...")
        
        # Create embedding
        text = f"{item['title']}\n{item['content'][:8000]}"
        embedding = embedding_model.encode(text).tolist()
        
        # Store in Qdrant
        point = PointStruct(
            id=hash(item['id']),
            vector=embedding,
            payload=item
        )
        
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[point]
        )
        
        stored_count += 1
        print(f"✅ Stored {stored_count} items in Qdrant")
        
    except Exception as e:
        print(f"❌ Failed to store item {i+1}: {e}")
        continue

print(f"🎉 Migration complete! Stored {stored_count} items in Qdrant")
print(f"📁 Data saved in: {output_dir.absolute()}")
print("🚀 Ready for Elysia integration!")
