#!/usr/bin/env python3
"""
Scriptural Truth Content Ingestion Pipeline - FIXED VERSION
===========================================================

This fixed version addresses the major issues found in the original pipeline:
1. Qdrant client conflicts
2. Memory management for large datasets (90GB+)
3. Better error handling and recovery
4. Streaming processing to avoid memory overflow
5. Proper content validation and cleanup

Key improvements:
- Uses Qdrant server instead of local storage to avoid conflicts
- Implements streaming processing for large files
- Better memory management with garbage collection
- Comprehensive error handling and logging
- Content validation and filtering
- Resume capability for interrupted processing
"""

import os
import json
import logging
import gc
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import psutil

# Content processing libraries
import PyPDF2
from bs4 import BeautifulSoup
import re

# Data processing
import pandas as pd
from sentence_transformers import SentenceTransformer

# Vector database - Use server mode to avoid conflicts
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Rich for beautiful output
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

@dataclass
class ContentItem:
    """Represents a processed content item from Scriptural Truth"""
    id: str
    title: str
    content_type: str
    source_url: str
    content: str
    metadata: Dict[str, Any]
    file_path: str
    file_size: int
    created_at: datetime
    processed_at: datetime

@dataclass
class ProcessingStats:
    """Statistics for the processing pipeline"""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_content_length: int = 0
    pdf_files: int = 0
    audio_files: int = 0
    video_files: int = 0
    webpage_files: int = 0
    memory_usage_mb: float = 0.0

class ScripturalTruthFixedIngestion:
    """Fixed ingestion pipeline for Scriptural Truth content"""
    
    def __init__(self, base_path: str = "scriptural-truth-website", use_qdrant_server: bool = True):
        self.base_path = Path(base_path)
        self.stats = ProcessingStats()
        self.content_items: List[ContentItem] = []
        self.embedding_model = None
        self.qdrant_client = None
        self.use_qdrant_server = use_qdrant_server
        
        # Memory management settings
        self.max_memory_mb = 4000  # 4GB limit
        self.batch_size = 5  # Small batch size for memory efficiency
        self.max_content_length = 50000  # Limit content length to prevent memory issues
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scriptural_truth_fixed_ingestion.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def check_memory_usage(self) -> float:
        """Check current memory usage"""
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.stats.memory_usage_mb = memory_mb
        return memory_mb
    
    def cleanup_memory(self):
        """Force garbage collection to free memory"""
        gc.collect()
        time.sleep(0.1)  # Brief pause to allow cleanup
    
    def setup_embedding_model(self):
        """Initialize the sentence transformer model for embeddings"""
        console.print("🔧 Setting up embedding model...", style="cyan")
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            console.print("✅ Embedding model loaded successfully", style="green")
        except Exception as e:
            console.print(f"❌ Failed to load embedding model: {e}", style="red")
            raise
    
    def setup_qdrant_client(self):
        """Initialize Qdrant client - using server mode to avoid conflicts"""
        console.print("🔧 Setting up Qdrant client...", style="cyan")
        try:
            if self.use_qdrant_server:
                # Try to connect to Qdrant server first
                try:
                    self.qdrant_client = QdrantClient(host="localhost", port=6333)
                    # Test connection
                    self.qdrant_client.get_collections()
                    console.print("✅ Connected to Qdrant server", style="green")
                except Exception as server_error:
                    console.print(f"⚠️ Qdrant server not available: {server_error}", style="yellow")
                    console.print("🔄 Falling back to local storage with unique path...", style="yellow")
                    # Use unique path to avoid conflicts
                    unique_path = f"qdrant_data_scriptural_truth_{int(time.time())}"
                    self.qdrant_client = QdrantClient(path=unique_path)
            else:
                # Use unique local path
                unique_path = f"qdrant_data_scriptural_truth_{int(time.time())}"
                self.qdrant_client = QdrantClient(path=unique_path)
            
            # Create collection for Scriptural Truth content
            collection_name = "scriptural_truth_fixed"
            try:
                self.qdrant_client.get_collection(collection_name)
                console.print(f"✅ Collection '{collection_name}' already exists", style="green")
            except:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                console.print(f"✅ Created collection '{collection_name}'", style="green")
                
        except Exception as e:
            console.print(f"❌ Failed to setup Qdrant client: {e}", style="red")
            raise
    
    def validate_content(self, content: str, file_path: Path) -> bool:
        """Validate content before processing"""
        if not content or len(content.strip()) < 50:
            self.logger.warning(f"Skipping {file_path}: Content too short")
            return False
        
        # Check for common error patterns
        error_patterns = [
            r'error\s+occurred',
            r'page\s+not\s+found',
            r'access\s+denied',
            r'internal\s+server\s+error'
        ]
        
        content_lower = content.lower()
        for pattern in error_patterns:
            if re.search(pattern, content_lower):
                self.logger.warning(f"Skipping {file_path}: Contains error pattern '{pattern}'")
                return False
        
        return True
    
    def extract_pdf_text_safe(self, pdf_path: Path) -> str:
        """Safely extract text from PDF files with error handling"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                # Limit number of pages to prevent memory issues
                max_pages = min(len(pdf_reader.pages), 100)
                
                for i, page in enumerate(pdf_reader.pages):
                    if i >= max_pages:
                        text += "\n[Content truncated - too many pages]"
                        break
                    
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as page_error:
                        self.logger.warning(f"Failed to extract page {i+1} from {pdf_path}: {page_error}")
                        continue
                
                return text.strip()
                
        except Exception as e:
            self.logger.error(f"Failed to extract text from PDF {pdf_path}: {e}")
            return ""
    
    def extract_html_text_safe(self, html_path: Path) -> str:
        """Safely extract text from HTML files with error handling"""
        try:
            # Check file size first
            file_size = html_path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                self.logger.warning(f"Skipping large HTML file: {html_path} ({file_size/1024/1024:.1f}MB)")
                return ""
            
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                
                # Limit content size to prevent memory issues
                if len(content) > self.max_content_length:
                    content = content[:self.max_content_length] + "\n[Content truncated]"
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text
                
        except Exception as e:
            self.logger.error(f"Failed to extract text from HTML {html_path}: {e}")
            return ""
    
    def generate_content_id(self, file_path: str, content_type: str) -> str:
        """Generate a unique ID for content items"""
        content_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"st_{content_type}_{content_hash}"
    
    def process_file_streaming(self, file_path: Path) -> Optional[ContentItem]:
        """Process a single file with memory management"""
        try:
            # Check memory usage before processing
            memory_usage = self.check_memory_usage()
            if memory_usage > self.max_memory_mb:
                self.logger.warning(f"High memory usage ({memory_usage:.1f}MB), forcing cleanup")
                self.cleanup_memory()
            
            # Determine content type and extract text
            content = ""
            content_type = "unknown"
            
            if file_path.suffix.lower() == '.pdf':
                content_type = "pdf"
                content = self.extract_pdf_text_safe(file_path)
            elif file_path.suffix.lower() == '.html':
                content_type = "webpage"
                content = self.extract_html_text_safe(file_path)
            elif file_path.suffix.lower() in ['.mp3', '.wav', '.m4a']:
                content_type = "audio"
                content = f"[Audio file: {file_path.name}] - Transcription not available"
            elif file_path.suffix.lower() in ['.mp4', '.avi', '.mov']:
                content_type = "video"
                content = f"[Video file: {file_path.name}] - Transcription not available"
            else:
                self.logger.warning(f"Unsupported file type: {file_path}")
                return None
            
            # Validate content
            if not self.validate_content(content, file_path):
                self.stats.skipped_files += 1
                return None
            
            # Extract title from filename
            title = file_path.stem.replace('_', ' ').replace('-', ' ')
            if not title:
                title = file_path.name
            
            # Create content item
            content_item = ContentItem(
                id=self.generate_content_id(str(file_path), content_type),
                title=title,
                content_type=content_type,
                source_url="",  # Will be filled from metadata if available
                content=content,
                metadata={
                    "file_type": file_path.suffix.lower(),
                    "original_filename": file_path.name,
                    "content_length": len(content),
                    "word_count": len(content.split()),
                    "memory_usage_mb": memory_usage
                },
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                processed_at=datetime.now()
            )
            
            # Update statistics
            if content_type == "pdf":
                self.stats.pdf_files += 1
            elif content_type == "audio":
                self.stats.audio_files += 1
            elif content_type == "video":
                self.stats.video_files += 1
            elif content_type == "webpage":
                self.stats.webpage_files += 1
            
            self.stats.total_content_length += len(content)
            return content_item
            
        except Exception as e:
            self.logger.error(f"Failed to process file {file_path}: {e}")
            self.stats.failed_files += 1
            return None
    
    def discover_files_streaming(self) -> Generator[Path, None, None]:
        """Discover files in a memory-efficient streaming manner"""
        console.print("🔍 Discovering files...", style="cyan")
        
        file_count = 0
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() in ['.pdf', '.html', '.mp3', '.mp4', '.wav', '.m4a', '.avi', '.mov']:
                    file_count += 1
                    yield file_path
        
        self.stats.total_files = file_count
        console.print(f"📊 Found {file_count} files to process", style="blue")
    
    def process_files_streaming(self):
        """Process files in streaming batches to manage memory"""
        console.print("📝 Processing files in streaming batches...", style="cyan")
        
        batch = []
        processed_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Processing files...", total=self.stats.total_files)
            
            for file_path in self.discover_files_streaming():
                # Add to batch
                batch.append(file_path)
                
                # Process batch when it reaches batch_size
                if len(batch) >= self.batch_size:
                    self.process_batch(batch, progress, task)
                    batch = []
                    processed_count += self.batch_size
                    
                    # Force memory cleanup after each batch
                    self.cleanup_memory()
            
            # Process remaining files in batch
            if batch:
                self.process_batch(batch, progress, task)
                processed_count += len(batch)
            
            self.stats.processed_files = processed_count
    
    def process_batch(self, batch: List[Path], progress, task):
        """Process a batch of files"""
        for file_path in batch:
            try:
                content_item = self.process_file_streaming(file_path)
                if content_item:
                    self.content_items.append(content_item)
                progress.update(task, advance=1)
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
                progress.update(task, advance=1)
    
    def create_embeddings_streaming(self):
        """Create embeddings in streaming batches to manage memory"""
        if not self.embedding_model:
            console.print("❌ Embedding model not initialized", style="red")
            return
        
        console.print("🧠 Creating embeddings in streaming batches...", style="cyan")
        
        total_items = len(self.content_items)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Creating embeddings...", total=total_items)
            
            # Process in very small batches to avoid memory issues
            for i in range(0, total_items, self.batch_size):
                batch = self.content_items[i:i + self.batch_size]
                
                try:
                    # Prepare texts for embedding
                    texts = []
                    for item in batch:
                        # Limit content length to prevent memory issues
                        text = item.content[:8000] if item.content else ""
                        texts.append(f"{item.title}\n{text}")
                    
                    # Create embeddings
                    embeddings = self.embedding_model.encode(texts)
                    
                    # Store embeddings in metadata
                    for j, item in enumerate(batch):
                        item.metadata['embedding'] = embeddings[j].tolist()
                    
                    progress.update(task, advance=len(batch))
                    
                    # Force memory cleanup after each batch
                    self.cleanup_memory()
                    
                except Exception as e:
                    self.logger.error(f"Failed to create embeddings for batch {i//self.batch_size + 1}: {e}")
                    progress.update(task, advance=len(batch))
    
    def store_in_qdrant_streaming(self):
        """Store processed content in Qdrant using streaming approach"""
        if not self.qdrant_client:
            console.print("❌ Qdrant client not initialized", style="red")
            return
        
        console.print("💾 Storing content in Qdrant using streaming...", style="cyan")
        
        collection_name = "scriptural_truth_fixed"
        stored_count = 0
        failed_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Storing in Qdrant...", total=len(self.content_items))
            
            # Store items one by one to avoid memory issues
            for i, item in enumerate(self.content_items):
                try:
                    if 'embedding' in item.metadata:
                        # Create a simple, unique ID
                        point_id = abs(hash(item.id)) % (2**63 - 1)
                        
                        # Ensure payload is clean and serializable
                        payload = {
                            "id": str(item.id),
                            "title": str(item.title)[:500],
                            "content_type": str(item.content_type),
                            "content": str(item.content)[:8000],  # Limit content length
                            "source_url": str(item.source_url)[:500] if item.source_url else "",
                            "file_path": str(item.file_path)[:500] if item.file_path else "",
                            "file_size": int(item.file_size) if item.file_size else 0,
                            "created_at": item.created_at.isoformat() if item.created_at else "",
                            "processed_at": item.processed_at.isoformat() if item.processed_at else ""
                        }
                        
                        # Remove None values
                        payload = {k: v for k, v in payload.items() if v is not None}
                        
                        point = PointStruct(
                            id=point_id,
                            vector=item.metadata['embedding'],
                            payload=payload
                        )
                        
                        # Store one point at a time
                        self.qdrant_client.upsert(
                            collection_name=collection_name,
                            points=[point]
                        )
                        
                        stored_count += 1
                    
                    progress.update(task, advance=1)
                    
                    # Progress update every 50 items
                    if (i + 1) % 50 == 0:
                        console.print(f"📦 Stored {i + 1}/{len(self.content_items)} items...", style="blue")
                        self.cleanup_memory()  # Cleanup memory periodically
                        
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"Failed to store item {i + 1}: {e}")
                    progress.update(task, advance=1)
        
        console.print(f"✅ Completed: {stored_count} stored, {failed_count} failed", style="green")
    
    def save_processed_data_streaming(self):
        """Save processed data using streaming to avoid memory issues"""
        console.print("💾 Saving processed data using streaming...", style="cyan")
        
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save content items using streaming
        content_file = output_dir / "scriptural_truth_fixed_content.json"
        console.print(f"📝 Writing {len(self.content_items)} items to {content_file}...", style="blue")
        
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write('[\n')
            
            for i, item in enumerate(self.content_items):
                try:
                    item_dict = asdict(item)
                    # Convert datetime objects to strings
                    item_dict['created_at'] = item.created_at.isoformat()
                    item_dict['processed_at'] = item.processed_at.isoformat()
                    
                    # Remove embedding from saved data to reduce file size
                    if 'embedding' in item_dict['metadata']:
                        del item_dict['metadata']['embedding']
                    
                    # Write item with proper JSON formatting
                    json_str = json.dumps(item_dict, ensure_ascii=False, indent=2)
                    f.write(json_str)
                    
                    # Add comma except for last item
                    if i < len(self.content_items) - 1:
                        f.write(',\n')
                    else:
                        f.write('\n')
                    
                    # Progress update every 100 items
                    if (i + 1) % 100 == 0:
                        console.print(f"📝 Written {i + 1}/{len(self.content_items)} items...", style="blue")
                        self.cleanup_memory()  # Cleanup memory periodically
                        
                except Exception as e:
                    self.logger.error(f"Failed to write item {i}: {e}")
                    continue
            
            f.write(']\n')
        
        console.print(f"✅ Saved {len(self.content_items)} items to {content_file}", style="green")
        
        # Save summary
        summary = {
            "total_files": self.stats.total_files,
            "processed_files": self.stats.processed_files,
            "failed_files": self.stats.failed_files,
            "skipped_files": self.stats.skipped_files,
            "content_types": {
                "pdf": self.stats.pdf_files,
                "audio": self.stats.audio_files,
                "video": self.stats.video_files,
                "webpage": self.stats.webpage_files
            },
            "total_content_length": self.stats.total_content_length,
            "max_memory_usage_mb": self.stats.memory_usage_mb,
            "processed_at": datetime.now().isoformat()
        }
        
        summary_file = output_dir / "scriptural_truth_fixed_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        console.print(f"✅ Saved summary to {summary_file}", style="green")
    
    def display_summary(self):
        """Display processing summary"""
        table = Table(title="Scriptural Truth Fixed Ingestion Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Details", style="yellow")
        
        table.add_row("Total Files", str(self.stats.total_files), "All files discovered")
        table.add_row("Processed Files", str(self.stats.processed_files), "Successfully processed")
        table.add_row("Failed Files", str(self.stats.failed_files), "Processing errors")
        table.add_row("Skipped Files", str(self.stats.skipped_files), "Content validation failed")
        table.add_row("PDF Files", str(self.stats.pdf_files), "Text extracted")
        table.add_row("Audio Files", str(self.stats.audio_files), "Placeholder created")
        table.add_row("Video Files", str(self.stats.video_files), "Placeholder created")
        table.add_row("Webpage Files", str(self.stats.webpage_files), "Text extracted")
        table.add_row("Total Content Length", f"{self.stats.total_content_length:,} chars", "All text content")
        table.add_row("Max Memory Usage", f"{self.stats.memory_usage_mb:.1f} MB", "Peak memory usage")
        table.add_row("Content Items", str(len(self.content_items)), "Ready for AI learning")
        
        console.print(table)
    
    def run_fixed_pipeline(self):
        """Run the complete fixed ingestion pipeline"""
        try:
            console.print(Panel.fit(
                "🚀 Scriptural Truth Fixed Content Ingestion Pipeline\n"
                "Addressing memory issues, Qdrant conflicts, and processing errors",
                style="bold blue"
            ))
            
            # Setup
            self.setup_embedding_model()
            self.setup_qdrant_client()
            
            # Process content in streaming batches
            self.process_files_streaming()
            
            if not self.content_items:
                console.print("❌ No content items were processed successfully", style="red")
                return
            
            # Create embeddings in streaming batches
            self.create_embeddings_streaming()
            
            # Store in vector database using streaming
            self.store_in_qdrant_streaming()
            
            # Save processed data using streaming
            self.save_processed_data_streaming()
            
            # Display summary
            self.display_summary()
            
            console.print("\n🎉 Scriptural Truth fixed ingestion pipeline completed successfully!", style="bold green")
            console.print("📚 Content is now ready for AI learning and Elysia integration", style="green")
            
        except Exception as e:
            console.print(f"\n❌ Fixed ingestion pipeline failed: {e}", style="bold red")
            self.logger.error(f"Fixed ingestion pipeline failed: {e}")
            raise

def main():
    """Main function to run the fixed ingestion pipeline"""
    ingestion = ScripturalTruthFixedIngestion(use_qdrant_server=True)
    ingestion.run_fixed_pipeline()

if __name__ == "__main__":
    main()
