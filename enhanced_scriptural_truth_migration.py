#!/usr/bin/env python3
"""
Enhanced Scriptural Truth Migration with Advanced Resume Capability
Downloads and processes content with robust error handling, progress display, and user controls
"""

import os
import json
import time
import requests
import signal
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import re
import threading
import queue

# Web scraping
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# AI and vector database
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

class MigrationManager:
    def __init__(self):
        self.base_url = "https://scriptural-truth.com/"
        self.output_dir = Path("scriptural_truth_data")
        self.output_dir.mkdir(exist_ok=True)
        
        # Progress files
        self.progress_file = self.output_dir / "migration_progress.json"
        self.discovered_urls_file = self.output_dir / "discovered_urls.json"
        self.processed_items_file = self.output_dir / "processed_items.json"
        self.error_log_file = self.output_dir / "migration_errors.json"
        
        # State
        self.progress = {
            "discovered_urls": set(),
            "to_process": [self.base_url],
            "processed_items": [],
            "stored_count": 0,
            "phase": "discovery",
            "start_time": datetime.now().isoformat(),
            "last_updated": None,
            "errors": []
        }
        
        # Control flags
        self.should_stop = False
        self.pause_requested = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Progress display
        self.progress_queue = queue.Queue()
        self.progress_thread = None
        
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully"""
        print(f"\n🛑 Received signal {signum}. Saving progress and shutting down gracefully...")
        self.should_stop = True
        self.save_progress()
        print("✅ Progress saved. You can resume later by running the script again.")
        sys.exit(0)
    
    def load_progress(self):
        """Load previous progress if available"""
        print("📂 Checking for previous progress...")
        
        if self.discovered_urls_file.exists():
            try:
                with open(self.discovered_urls_file, 'r') as f:
                    self.progress["discovered_urls"] = set(json.load(f))
                print(f"✅ Loaded {len(self.progress['discovered_urls'])} previously discovered URLs")
            except Exception as e:
                print(f"⚠️ Error loading discovered URLs: {e}")
        
        if self.processed_items_file.exists():
            try:
                with open(self.processed_items_file, 'r') as f:
                    self.progress["processed_items"] = json.load(f)
                print(f"✅ Loaded {len(self.progress['processed_items'])} previously processed items")
            except Exception as e:
                print(f"⚠️ Error loading processed items: {e}")
        
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    saved_progress = json.load(f)
                    self.progress["stored_count"] = saved_progress.get("stored_count", 0)
                    self.progress["phase"] = saved_progress.get("phase", "discovery")
                    self.progress["start_time"] = saved_progress.get("start_time", datetime.now().isoformat())
                print(f"✅ Resuming from phase: {self.progress['phase']}")
            except Exception as e:
                print(f"⚠️ Error loading progress: {e}")
        
        if self.error_log_file.exists():
            try:
                with open(self.error_log_file, 'r') as f:
                    self.progress["errors"] = json.load(f)
                print(f"⚠️ Loaded {len(self.progress['errors'])} previous errors")
            except Exception as e:
                print(f"⚠️ Error loading error log: {e}")
    
    def save_progress(self):
        """Save current progress"""
        try:
            # Save discovered URLs
            with open(self.discovered_urls_file, 'w') as f:
                json.dump(list(self.progress["discovered_urls"]), f)
            
            # Save processed items
            with open(self.processed_items_file, 'w') as f:
                json.dump(self.progress["processed_items"], f)
            
            # Save overall progress
            self.progress["last_updated"] = datetime.now().isoformat()
            with open(self.progress_file, 'w') as f:
                json.dump({
                    "stored_count": self.progress["stored_count"],
                    "phase": self.progress["phase"],
                    "start_time": self.progress["start_time"],
                    "last_updated": self.progress["last_updated"],
                    "total_discovered": len(self.progress["discovered_urls"]),
                    "total_processed": len(self.progress["processed_items"])
                }, f, indent=2)
            
            # Save error log
            with open(self.error_log_file, 'w') as f:
                json.dump(self.progress["errors"], f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving progress: {e}")
    
    def log_error(self, url: str, error: str, phase: str):
        """Log an error for later review"""
        error_entry = {
            "url": url,
            "error": str(error),
            "phase": phase,
            "timestamp": datetime.now().isoformat()
        }
        self.progress["errors"].append(error_entry)
    
    def display_progress(self):
        """Display current progress"""
        phase = self.progress["phase"]
        discovered = len(self.progress["discovered_urls"])
        processed = len(self.progress["processed_items"])
        stored = self.progress["stored_count"]
        
        print(f"\n📊 Progress Update:")
        print(f"   Phase: {phase}")
        print(f"   URLs Discovered: {discovered}")
        print(f"   Items Processed: {processed}")
        print(f"   Items Stored: {stored}")
        print(f"   Errors: {len(self.progress['errors'])}")
        
        if self.progress["start_time"]:
            start_time = datetime.fromisoformat(self.progress["start_time"])
            elapsed = datetime.now() - start_time
            print(f"   Elapsed Time: {elapsed}")
    
    def run_migration(self):
        """Run the complete migration process"""
        print("🚀 Starting Enhanced Scriptural Truth Migration")
        print("=" * 60)
        print("💡 Press Ctrl+C to gracefully stop and save progress")
        print("=" * 60)
        
        # Load previous progress
        self.load_progress()
        
        # Initialize AI model
        print("\n🧠 Loading AI model...")
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ AI model loaded")
        except Exception as e:
            print(f"❌ Failed to load AI model: {e}")
            return False
        
        # Initialize Qdrant
        print("\n🗄️ Setting up Qdrant...")
        try:
            self.qdrant_client = QdrantClient(path="qdrant_data")
            self.collection_name = "scriptural_truth"
            
            # Create collection if it doesn't exist
            try:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # all-MiniLM-L6-v2 dimension
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Created collection '{self.collection_name}'")
            except Exception as e:
                print(f"ℹ️ Collection '{self.collection_name}' already exists")
                
        except Exception as e:
            print(f"❌ Qdrant setup failed: {e}")
            return False
        
        print("✅ Qdrant setup complete")
        
        # Run phases
        try:
            if self.progress["phase"] in ["discovery"]:
                self._run_discovery_phase()
            
            if not self.should_stop and self.progress["phase"] in ["processing", "embedding"]:
                self._run_processing_phase()
            
            if not self.should_stop and self.progress["phase"] in ["embedding"]:
                self._run_embedding_phase()
            
            if not self.should_stop:
                self._cleanup_on_completion()
                print("\n🎉 Migration completed successfully!")
                return True
            else:
                print("\n⏸️ Migration paused. Progress saved.")
                return False
                
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            self.log_error("MIGRATION", str(e), "GENERAL")
            self.save_progress()
            return False
    
    def _run_discovery_phase(self):
        """Run the URL discovery phase"""
        print("\n🔍 Phase 1: Discovering pages...")
        discovered_urls = self.progress["discovered_urls"]
        to_process = self.progress["to_process"]
        
        while to_process and not self.should_stop:
            current_url = to_process.pop(0)
            
            if current_url in discovered_urls:
                continue
            
            try:
                print(f"📄 Discovering: {current_url}")
                response = requests.get(current_url, timeout=10)
                response.raise_for_status()
                
                discovered_urls.add(current_url)
                
                # Parse HTML and find links
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all internal links
                new_links = 0
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(current_url, href)
                    
                    # Only process internal links
                    if urlparse(full_url).netloc == urlparse(self.base_url).netloc:
                        # Skip multi-language documents
                        if any(lang in full_url.lower() for lang in ['russian', 'german', 'afrikaan', 'arabic', 'hindi', 'japanese', 'spanish', 'french', 'chinese', 'korean']):
                            continue
                        # Skip PDF_Other_Languages directory entirely
                        if 'pdf_other_languages' in full_url.lower():
                            continue
                            
                        if full_url not in discovered_urls and full_url not in to_process:
                            to_process.append(full_url)
                            new_links += 1
                
                print(f"   ✅ Found {new_links} new links")
                
                # Update progress
                self.progress["discovered_urls"] = discovered_urls
                self.progress["to_process"] = to_process
                self.save_progress()
                
                # Display progress every 10 URLs
                if len(discovered_urls) % 10 == 0:
                    self.display_progress()
                
                time.sleep(0.5)  # Be respectful to the server
                
            except Exception as e:
                print(f"❌ Failed to process {current_url}: {e}")
                self.log_error(current_url, str(e), "discovery")
                continue
        
        print(f"✅ Discovery complete! Found {len(discovered_urls)} URLs")
        self.progress["phase"] = "processing"
        self.save_progress()
    
    def _run_processing_phase(self):
        """Run the content processing phase"""
        print("\n📝 Phase 2: Processing content...")
        content_items = self.progress["processed_items"]
        discovered_urls = self.progress["discovered_urls"]
        
        # Find URLs that haven't been processed yet
        processed_urls = {item["url"] for item in content_items}
        urls_to_process = [url for url in discovered_urls if url not in processed_urls]
        
        print(f"📊 Processing {len(urls_to_process)} remaining URLs...")
        
        for i, url in enumerate(urls_to_process):
            if self.should_stop:
                break
                
            try:
                print(f"📄 Processing {i+1}/{len(urls_to_process)}: {url}")
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
                    print(f"   ⚠️ Skipping (insufficient content)")
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
                self.progress["processed_items"] = content_items
                self.save_progress()
                
                print(f"   ✅ Processed ({len(content_items)} total)")
                
                # Display progress every 5 items
                if len(content_items) % 5 == 0:
                    self.display_progress()
                
                time.sleep(0.5)  # Be respectful to the server
                
            except Exception as e:
                print(f"❌ Failed to process {url}: {e}")
                self.log_error(url, str(e), "processing")
                continue
        
        print(f"✅ Processing complete! Processed {len(content_items)} items")
        
        # Save final processed data
        print("💾 Saving processed data...")
        with open(self.output_dir / "scriptural_truth_content.json", 'w', encoding='utf-8') as f:
            json.dump(content_items, f, indent=2, ensure_ascii=False)
        
        print("✅ Data saved to scriptural_truth_data/scriptural_truth_content.json")
        self.progress["phase"] = "embedding"
        self.save_progress()
    
    def _run_embedding_phase(self):
        """Run the embedding and storage phase"""
        print("\n🧠 Phase 3: Creating embeddings and storing in Qdrant...")
        content_items = self.progress["processed_items"]
        stored_count = self.progress["stored_count"]
        
        # Check which items are already stored
        try:
            existing_points = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=10000
            )[0]
            existing_ids = {point.id for point in existing_points}
            print(f"📊 Found {len(existing_ids)} existing items in Qdrant")
        except:
            existing_ids = set()
        
        for i, item in enumerate(content_items):
            if self.should_stop:
                break
                
            item_id = hash(item['id'])
            
            # Skip if already stored
            if item_id in existing_ids:
                continue
                
            try:
                print(f"📊 Embedding {i+1}/{len(content_items)}: {item['title'][:50]}...")
                
                # Create embedding
                text = f"{item['title']}\n{item['content'][:8000]}"
                embedding = self.embedding_model.encode(text).tolist()
                
                # Store in Qdrant
                point = PointStruct(
                    id=item_id,
                    vector=embedding,
                    payload=item
                )
                
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
                
                stored_count += 1
                
                # Update progress
                self.progress["stored_count"] = stored_count
                self.save_progress()
                
                print(f"   ✅ Stored ({stored_count} total)")
                
                # Display progress every 3 items
                if stored_count % 3 == 0:
                    self.display_progress()
                
            except Exception as e:
                print(f"❌ Failed to store item {i+1}: {e}")
                self.log_error(item['url'], str(e), "embedding")
                continue
        
        print(f"✅ Embedding complete! Stored {stored_count} items in Qdrant")
    
    def _cleanup_on_completion(self):
        """Clean up progress files on successful completion"""
        try:
            self.progress_file.unlink()
            self.discovered_urls_file.unlink()
            self.processed_items_file.unlink()
            print("🧹 Cleaned up progress files")
        except:
            pass

def main():
    """Main entry point"""
    migration = MigrationManager()
    success = migration.run_migration()
    
    if success:
        print(f"\n🎉 Migration completed successfully!")
        print(f"📁 Data saved in: {migration.output_dir.absolute()}")
        print("🚀 Ready for Elysia integration!")
    else:
        print(f"\n⏸️ Migration paused or failed.")
        print("💡 Run the script again to resume from where it left off.")
        if migration.progress["errors"]:
            print(f"⚠️ Check {migration.error_log_file} for error details.")

if __name__ == "__main__":
    main()
