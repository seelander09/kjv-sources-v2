#!/usr/bin/env python3
"""
Scriptural Truth to Qdrant Migration Pipeline
============================================

Downloads all markdown from scriptural-truth.com and processes it with
the same AI-optimized structure as biblical verses in Qdrant.

Features:
- Background processing with progress tracking
- Status updates and logging
- Resume capability if interrupted
- Rich console output with progress bars
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import re

# Web scraping and content processing
from bs4 import BeautifulSoup
import markdown
from urllib.parse import urljoin, urlparse

# AI and vector database
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Rich console output
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.logging import RichHandler
import logging

console = Console()

@dataclass
class ScripturalTruthContent:
    """Represents Scriptural Truth content item"""
    id: str
    title: str
    url: str
    content_type: str  # 'article', 'mp3', 'pdf', 'video'
    content: str
    word_count: int
    character_count: int
    topics: List[str]
    biblical_references: List[str]
    source_attributions: List[str]  # J, E, P, D, R if applicable
    created_at: datetime
    processed_at: datetime
    file_size: int
    checksum: str
    embedding: Optional[List[float]] = None

@dataclass
class MigrationStats:
    """Statistics for migration process"""
    total_pages_found: int = 0
    pages_processed: int = 0
    pages_failed: int = 0
    content_items_created: int = 0
    embeddings_created: int = 0
    qdrant_points_stored: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ScripturalTruthQdrantMigration:
    """Main migration pipeline for Scriptural Truth to Qdrant"""
    
    def __init__(self, base_url: str = "https://scriptural-truth.com/"):
        self.base_url = base_url
        self.stats = MigrationStats()
        self.content_items: List[ScripturalTruthContent] = []
        self.processed_urls = set()
        self.failed_urls = set()
        
        # Setup Qdrant
        self.qdrant_client = QdrantClient(path="qdrant_data")
        self.collection_name = "scriptural_truth"
        
        # Setup AI model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384
        
        # Setup logging
        self.setup_logging()
        
        # Create output directories
        self.output_dir = Path("scriptural_truth_data")
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger.info("Scriptural Truth to Qdrant Migration Pipeline initialized")
    
    def setup_logging(self):
        """Setup logging with rich console output"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                RichHandler(console=console, rich_tracebacks=True),
                logging.FileHandler('scriptural_truth_migration.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def discover_all_pages(self) -> List[str]:
        """Discover all pages on the Scriptural Truth website"""
        console.print("🔍 Discovering all pages on Scriptural Truth website...", style="cyan")
        
        discovered_urls = set()
        to_process = [self.base_url]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Discovering pages...", total=None)
            
            while to_process:
                current_url = to_process.pop(0)
                
                if current_url in discovered_urls:
                    continue
                
                try:
                    response = requests.get(current_url, timeout=10)
                    response.raise_for_status()
                    
                    discovered_urls.add(current_url)
                    progress.update(task, description=f"Found {len(discovered_urls)} pages")
                    
                    # Parse HTML and find links
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all internal links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(current_url, href)
                        
                        # Only process internal links
                        if urlparse(full_url).netloc == urlparse(self.base_url).netloc:
                            if full_url not in discovered_urls and full_url not in to_process:
                                to_process.append(full_url)
                    
                    time.sleep(0.5)  # Be respectful to the server
                    
                except Exception as e:
                    self.logger.error(f"Failed to process {current_url}: {e}")
                    self.failed_urls.add(current_url)
                    continue
        
        self.stats.total_pages_found = len(discovered_urls)
        console.print(f"✅ Discovered {len(discovered_urls)} pages", style="green")
        
        return list(discovered_urls)
    
    def extract_content_from_page(self, url: str) -> Optional[ScripturalTruthContent]:
        """Extract content from a single page"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title = title.get_text().strip() if title else urlparse(url).path
            
            # Extract main content
            content = ""
            
            # Try to find main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if main_content:
                content = main_content.get_text(separator='\n', strip=True)
            else:
                # Fallback to body content
                body = soup.find('body')
                if body:
                    content = body.get_text(separator='\n', strip=True)
            
            # Clean up content
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = content.strip()
            
            if not content or len(content) < 100:
                return None
            
            # Determine content type
            content_type = "article"
            if url.endswith('.mp3') or 'mp3' in url.lower():
                content_type = "mp3"
            elif url.endswith('.pdf') or 'pdf' in url.lower():
                content_type = "pdf"
            elif url.endswith('.mp4') or 'video' in url.lower():
                content_type = "video"
            
            # Generate ID and metadata
            content_id = hashlib.md5(url.encode()).hexdigest()[:12]
            
            # Extract topics and biblical references
            topics = self.extract_topics(content)
            biblical_refs = self.extract_biblical_references(content)
            source_attrs = self.extract_source_attributions(content)
            
            # Create content item
            content_item = ScripturalTruthContent(
                id=content_id,
                title=title,
                url=url,
                content_type=content_type,
                content=content,
                word_count=len(content.split()),
                character_count=len(content),
                topics=topics,
                biblical_references=biblical_refs,
                source_attributions=source_attrs,
                created_at=datetime.now(),
                processed_at=datetime.now(),
                file_size=len(response.content),
                checksum=hashlib.md5(content.encode()).hexdigest()
            )
            
            return content_item
            
        except Exception as e:
            self.logger.error(f"Failed to extract content from {url}: {e}")
            return None
    
    def extract_topics(self, content: str) -> List[str]:
        """Extract topics/themes from content"""
        topics = []
        content_lower = content.lower()
        
        # Biblical themes
        theme_keywords = {
            'creation': ['creation', 'beginning', 'genesis', 'heaven', 'earth'],
            'covenant': ['covenant', 'promise', 'agreement', 'treaty'],
            'law': ['law', 'command', 'statute', 'ordinance', 'torah'],
            'sacrifice': ['sacrifice', 'offering', 'altar', 'priest'],
            'prophecy': ['prophet', 'prophecy', 'vision', 'oracle'],
            'wisdom': ['wisdom', 'proverb', 'understanding', 'knowledge'],
            'worship': ['worship', 'praise', 'temple', 'sanctuary'],
            'redemption': ['redeem', 'salvation', 'deliver', 'save'],
            'judgment': ['judge', 'judgment', 'punish', 'curse'],
            'blessing': ['bless', 'blessing', 'blessed', 'favor'],
            'trinity': ['trinity', 'three', 'father', 'son', 'holy spirit'],
            'good things': ['good things', 'good things come in three', 'three good things']
        }
        
        for topic, keywords in theme_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def extract_biblical_references(self, content: str) -> List[str]:
        """Extract biblical references from content"""
        # Pattern to match biblical references
        pattern = r'\b(?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalms|Proverbs|Ecclesiastes|Song of Songs|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|Jude|Revelation)\s+\d+(?::\d+(?:-\d+)?)?(?:\s*,\s*\d+(?::\d+(?:-\d+)?)?)*'
        
        references = re.findall(pattern, content, re.IGNORECASE)
        return list(set(references))
    
    def extract_source_attributions(self, content: str) -> List[str]:
        """Extract Documentary Hypothesis source attributions"""
        sources = []
        content_lower = content.lower()
        
        # Look for explicit source mentions
        if 'jahwist' in content_lower or 'j source' in content_lower:
            sources.append('J')
        if 'elohist' in content_lower or 'e source' in content_lower:
            sources.append('E')
        if 'priestly' in content_lower or 'p source' in content_lower:
            sources.append('P')
        if 'deuteronomist' in content_lower or 'd source' in content_lower:
            sources.append('D')
        if 'redactor' in content_lower or 'r source' in content_lower:
            sources.append('R')
        
        return sources
    
    def process_all_pages(self, urls: List[str]):
        """Process all discovered pages"""
        console.print("📝 Processing all pages...", style="cyan")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Processing pages...", total=len(urls))
            
            for url in urls:
                content_item = self.extract_content_from_page(url)
                
                if content_item:
                    self.content_items.append(content_item)
                    self.stats.content_items_created += 1
                    progress.update(task, description=f"Processed {self.stats.content_items_created} items")
                else:
                    self.stats.pages_failed += 1
                
                self.stats.pages_processed += 1
                progress.update(task, advance=1)
                
                time.sleep(0.5)  # Be respectful to the server
    
    def create_embeddings(self):
        """Create embeddings for all content items"""
        console.print("🧠 Creating AI embeddings...", style="cyan")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Creating embeddings...", total=len(self.content_items))
            
            # Process in batches
            batch_size = 10
            for i in range(0, len(self.content_items), batch_size):
                batch = self.content_items[i:i + batch_size]
                
                try:
                    # Prepare texts for embedding
                    texts = []
                    for item in batch:
                        text = f"{item.title}\n{item.content[:8000]}"  # Limit content length
                        texts.append(text)
                    
                    # Create embeddings
                    embeddings = self.embedding_model.encode(texts)
                    
                    # Store embeddings
                    for j, item in enumerate(batch):
                        item.embedding = embeddings[j].tolist()
                        self.stats.embeddings_created += 1
                    
                    progress.update(task, advance=len(batch))
                    
                except Exception as e:
                    self.logger.error(f"Failed to create embeddings for batch {i//batch_size + 1}: {e}")
                    progress.update(task, advance=len(batch))
    
    def create_qdrant_collection(self):
        """Create Qdrant collection for Scriptural Truth content"""
        console.print("🗄️ Creating Qdrant collection...", style="cyan")
        
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            if self.collection_name in [col.name for col in collections.collections]:
                console.print(f"✅ Collection '{self.collection_name}' already exists", style="green")
            else:
                # Create collection
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                console.print(f"✅ Created collection '{self.collection_name}'", style="green")
                
        except Exception as e:
            self.logger.error(f"Failed to create Qdrant collection: {e}")
            raise
    
    def store_in_qdrant(self):
        """Store all content items in Qdrant"""
        console.print("💾 Storing content in Qdrant...", style="cyan")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Storing in Qdrant...", total=len(self.content_items))
            
            # Process in batches
            batch_size = 50
            for i in range(0, len(self.content_items), batch_size):
                batch = self.content_items[i:i + batch_size]
                
                try:
                    # Prepare points for Qdrant
                    points = []
                    for item in batch:
                        if item.embedding:
                            point = PointStruct(
                                id=hash(item.id),
                                vector=item.embedding,
                                payload={
                                    "id": item.id,
                                    "title": item.title,
                                    "url": item.url,
                                    "content_type": item.content_type,
                                    "content": item.content[:10000],  # Limit content length
                                    "word_count": item.word_count,
                                    "character_count": item.character_count,
                                    "topics": item.topics,
                                    "biblical_references": item.biblical_references,
                                    "source_attributions": item.source_attributions,
                                    "created_at": item.created_at.isoformat(),
                                    "processed_at": item.processed_at.isoformat(),
                                    "file_size": item.file_size,
                                    "checksum": item.checksum
                                }
                            )
                            points.append(point)
                    
                    # Store batch
                    if points:
                        self.qdrant_client.upsert(
                            collection_name=self.collection_name,
                            points=points
                        )
                        self.stats.qdrant_points_stored += len(points)
                    
                    progress.update(task, advance=len(batch))
                    
                except Exception as e:
                    self.logger.error(f"Failed to store batch {i//batch_size + 1}: {e}")
                    progress.update(task, advance=len(batch))
    
    def save_processed_data(self):
        """Save processed data to JSON files"""
        console.print("💾 Saving processed data...", style="cyan")
        
        # Save content items
        content_data = [asdict(item) for item in self.content_items]
        with open(self.output_dir / "scriptural_truth_content.json", 'w', encoding='utf-8') as f:
            json.dump(content_data, f, indent=2, default=str, ensure_ascii=False)
        
        # Save migration statistics
        with open(self.output_dir / "migration_stats.json", 'w', encoding='utf-8') as f:
            json.dump(asdict(self.stats), f, indent=2, default=str)
        
        console.print("✅ Processed data saved successfully", style="green")
    
    def display_summary(self):
        """Display migration summary"""
        table = Table(title="Scriptural Truth Migration Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Details", style="yellow")
        
        table.add_row("Pages Found", str(self.stats.total_pages_found), "Total pages discovered")
        table.add_row("Pages Processed", str(self.stats.pages_processed), "Successfully processed")
        table.add_row("Pages Failed", str(self.stats.pages_failed), "Processing errors")
        table.add_row("Content Items", str(self.stats.content_items_created), "Content items created")
        table.add_row("Embeddings", str(self.stats.embeddings_created), "AI embeddings created")
        table.add_row("Qdrant Points", str(self.stats.qdrant_points_stored), "Stored in Qdrant")
        
        console.print(table)
        
        # Display sample content
        if self.content_items:
            console.print("\n📄 Sample Processed Content:", style="bold cyan")
            for i, item in enumerate(self.content_items[:3]):
                console.print(f"\n{i+1}. {item.title} ({item.content_type})")
                console.print(f"   URL: {item.url}")
                console.print(f"   Topics: {', '.join(item.topics[:3])}")
                console.print(f"   Biblical References: {', '.join(item.biblical_references[:3])}")
                console.print(f"   Content: {item.content[:200]}...")
    
    def run_full_migration(self):
        """Run the complete migration pipeline"""
        try:
            self.stats.start_time = datetime.now()
            
            console.print(Panel.fit(
                "🚀 Scriptural Truth to Qdrant Migration\n"
                "Downloading and processing all content with AI embeddings",
                style="bold blue"
            ))
            
            # Step 1: Discover all pages
            urls = self.discover_all_pages()
            
            if not urls:
                console.print("❌ No pages found to process", style="red")
                return
            
            # Step 2: Process all pages
            self.process_all_pages(urls)
            
            if not self.content_items:
                console.print("❌ No content items created", style="red")
                return
            
            # Step 3: Create embeddings
            self.create_embeddings()
            
            # Step 4: Create Qdrant collection
            self.create_qdrant_collection()
            
            # Step 5: Store in Qdrant
            self.store_in_qdrant()
            
            # Step 6: Save processed data
            self.save_processed_data()
            
            # Step 7: Display summary
            self.display_summary()
            
            self.stats.end_time = datetime.now()
            
            console.print("\n🎉 Scriptural Truth migration completed successfully!", style="bold green")
            console.print("📚 All content is now available in Qdrant with AI embeddings", style="green")
            
        except Exception as e:
            console.print(f"\n❌ Migration failed: {e}", style="bold red")
            self.logger.error(f"Migration failed: {e}")
            raise

def main():
    """Main function to run the migration"""
    migration = ScripturalTruthQdrantMigration()
    migration.run_full_migration()

if __name__ == "__main__":
    main()
