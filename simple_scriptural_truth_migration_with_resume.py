#!/usr/bin/env python3
"""
Simple Scriptural Truth Migration with Resume Capability
Downloads and processes content with ability to resume from interruptions
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

print("🚀 Starting Simple Scriptural Truth Migration with Resume")
print("=" * 60)

# Setup
base_url = "https://scriptural-truth.com/"
output_dir = Path("scriptural_truth_data")
output_dir.mkdir(exist_ok=True)

# Resume state files
progress_file = output_dir / "migration_progress.json"
discovered_urls_file = output_dir / "discovered_urls.json"
processed_items_file = output_dir / "processed_items.json"

def load_progress():
    """Load previous progress if available"""
    progress = {
        "discovered_urls": set(),
        "to_process": [base_url],
        "processed_items": [],
        "stored_count": 0,
        "phase": "discovery"  # discovery, processing, embedding
    }
    
    if discovered_urls_file.exists():
        try:
            with open(discovered_urls_file, 'r') as f:
                progress["discovered_urls"] = set(json.load(f))
            print(f"📂 Loaded {len(progress['discovered_urls'])} previously discovered URLs")
        except:
            pass
    
    if processed_items_file.exists():
        try:
            with open(processed_items_file, 'r') as f:
                progress["processed_items"] = json.load(f)
            print(f"📂 Loaded {len(progress['processed_items'])} previously processed items")
        except:
            pass
    
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                saved_progress = json.load(f)
                progress["stored_count"] = saved_progress.get("stored_count", 0)
                progress["phase"] = saved_progress.get("phase", "discovery")
            print(f"📂 Resuming from phase: {progress['phase']}")
        except:
            pass
    
    return progress

def save_progress(progress):
    """Save current progress"""
    # Save discovered URLs
    with open(discovered_urls_file, 'w') as f:
        json.dump(list(progress["discovered_urls"]), f)
    
    # Save processed items
    with open(processed_items_file, 'w') as f:
        json.dump(progress["processed_items"], f)
    
    # Save overall progress
    with open(progress_file, 'w') as f:
        json.dump({
            "stored_count": progress["stored_count"],
            "phase": progress["phase"],
            "last_updated": datetime.now().isoformat()
        }, f)

# Load previous progress
progress = load_progress()

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

# Phase 1: Page Discovery (if not complete)
if progress["phase"] in ["discovery"]:
    print("🔍 Discovering pages...")
    discovered_urls = progress["discovered_urls"]
    to_process = progress["to_process"]
    
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
            
            # Update progress
            progress["discovered_urls"] = discovered_urls
            progress["to_process"] = to_process
            save_progress(progress)
            
            time.sleep(0.5)  # Be respectful to the server
            
        except Exception as e:
            print(f"❌ Failed to process {current_url}: {e}")
            continue
    
    print(f"✅ Discovered {len(discovered_urls)} pages")
    progress["phase"] = "processing"
    save_progress(progress)

# Phase 2: Content Processing (if not complete)
if progress["phase"] in ["processing", "embedding"]:
    print("📝 Processing content...")
    content_items = progress["processed_items"]
    discovered_urls = progress["discovered_urls"]
    
    # Find URLs that haven't been processed yet
    processed_urls = {item["url"] for item in content_items}
    urls_to_process = [url for url in discovered_urls if url not in processed_urls]
    
    print(f"📊 Processing {len(urls_to_process)} remaining URLs...")
    
    for url in urls_to_process:
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
            
            # Update progress
            progress["processed_items"] = content_items
            save_progress(progress)
            
            print(f"✅ Processed {len(content_items)} items")
            
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
    progress["phase"] = "embedding"
    save_progress(progress)

# Phase 3: Create embeddings and store in Qdrant (if not complete)
if progress["phase"] in ["embedding"]:
    print("🧠 Creating embeddings and storing in Qdrant...")
    content_items = progress["processed_items"]
    stored_count = progress["stored_count"]
    
    # Check which items are already stored
    try:
        existing_points = qdrant_client.scroll(
            collection_name=collection_name,
            limit=10000
        )[0]
        existing_ids = {point.id for point in existing_points}
        print(f"📊 Found {len(existing_ids)} existing items in Qdrant")
    except:
        existing_ids = set()
    
    for i, item in enumerate(content_items):
        item_id = hash(item['id'])
        
        # Skip if already stored
        if item_id in existing_ids:
            continue
            
        try:
            print(f"📊 Processing item {i+1}/{len(content_items)}: {item['title'][:50]}...")
            
            # Create embedding
            text = f"{item['title']}\n{item['content'][:8000]}"
            embedding = embedding_model.encode(text).tolist()
            
            # Store in Qdrant
            point = PointStruct(
                id=item_id,
                vector=embedding,
                payload=item
            )
            
            qdrant_client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            stored_count += 1
            
            # Update progress
            progress["stored_count"] = stored_count
            save_progress(progress)
            
            print(f"✅ Stored {stored_count} items in Qdrant")
            
        except Exception as e:
            print(f"❌ Failed to store item {i+1}: {e}")
            continue

print(f"🎉 Migration complete! Stored {progress['stored_count']} items in Qdrant")
print(f"📁 Data saved in: {output_dir.absolute()}")
print("🚀 Ready for Elysia integration!")

# Clean up progress files on completion
try:
    progress_file.unlink()
    discovered_urls_file.unlink()
    processed_items_file.unlink()
    print("🧹 Cleaned up progress files")
except:
    pass
