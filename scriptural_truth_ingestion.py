#!/usr/bin/env python3
"""
Scriptural Truth Content Ingestion Pipeline
===========================================

This script processes all downloaded Scriptural Truth content and prepares it
for AI learning integration with the KJV Sources project and Elysia framework.

Features:
- Extract text from PDFs, HTML pages, and audio transcripts
- Process and clean content for AI consumption
- Create structured data for vector database ingestion
- Generate training data for LLM fine-tuning
- Integrate with existing Qdrant collections
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

# Content processing libraries
import PyPDF2
import requests
from bs4 import BeautifulSoup
import re

# Data processing
import pandas as pd
from sentence_transformers import SentenceTransformer

# Vector database
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Rich for beautiful output
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

@dataclass
class ContentItem:
    """Represents a processed content item from Scriptural Truth"""
    id: str
    title: str
    content_type: str  # 'pdf', 'audio', 'video', 'webpage'
    source_url: str
    content: str
    metadata: Dict[str, Any]
    file_path: str
    file_size: int
    created_at: datetime
    processed_at: datetime

@dataclass
class IngestionStats:
    """Statistics for the ingestion process"""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    total_content_length: int = 0
    pdf_files: int = 0
    audio_files: int = 0
    video_files: int = 0
    webpage_files: int = 0

class ScripturalTruthIngestion:
    """Main ingestion pipeline for Scriptural Truth content"""
    
    def __init__(self, base_path: str = "scriptural-truth-website"):
        self.base_path = Path(base_path)
        self.stats = IngestionStats()
        self.content_items: List[ContentItem] = []
        self.embedding_model = None
        self.qdrant_client = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scriptural_truth_ingestion.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
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
        """Initialize Qdrant client for vector storage"""
        console.print("🔧 Setting up Qdrant client...", style="cyan")
        try:
            self.qdrant_client = QdrantClient(path="qdrant_data")
            
            # Create collection for Scriptural Truth content
            collection_name = "scriptural_truth"
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
    
    def extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text content from PDF files"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            self.logger.error(f"Failed to extract text from {pdf_path}: {e}")
            return ""
    
    def extract_html_text(self, html_path: Path) -> str:
        """Extract text content from HTML files"""
        try:
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text
        except Exception as e:
            self.logger.error(f"Failed to extract text from {html_path}: {e}")
            return ""
    
    def generate_content_id(self, file_path: str, content_type: str) -> str:
        """Generate a unique ID for content items"""
        content_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"st_{content_type}_{content_hash}"
    
    def process_pdf_file(self, pdf_path: Path) -> Optional[ContentItem]:
        """Process a single PDF file"""
        try:
            content = self.extract_pdf_text(pdf_path)
            if not content:
                return None
            
            # Extract title from filename
            title = pdf_path.stem.replace('_', ' ').replace('-', ' ')
            
            content_item = ContentItem(
                id=self.generate_content_id(str(pdf_path), "pdf"),
                title=title,
                content_type="pdf",
                source_url="",  # Will be filled from metadata if available
                content=content,
                metadata={
                    "file_type": "pdf",
                    "original_filename": pdf_path.name,
                    "content_length": len(content),
                    "word_count": len(content.split())
                },
                file_path=str(pdf_path),
                file_size=pdf_path.stat().st_size,
                created_at=datetime.fromtimestamp(pdf_path.stat().st_ctime),
                processed_at=datetime.now()
            )
            
            self.stats.pdf_files += 1
            self.stats.total_content_length += len(content)
            return content_item
            
        except Exception as e:
            self.logger.error(f"Failed to process PDF {pdf_path}: {e}")
            self.stats.failed_files += 1
            return None
    
    def process_html_file(self, html_path: Path) -> Optional[ContentItem]:
        """Process a single HTML file"""
        try:
            content = self.extract_html_text(html_path)
            if not content or len(content) < 100:  # Skip very short content
                return None
            
            # Extract title from filename
            title = html_path.stem.replace('_', ' ').replace('-', ' ')
            
            content_item = ContentItem(
                id=self.generate_content_id(str(html_path), "webpage"),
                title=title,
                content_type="webpage",
                source_url="",  # Will be filled from metadata if available
                content=content,
                metadata={
                    "file_type": "html",
                    "original_filename": html_path.name,
                    "content_length": len(content),
                    "word_count": len(content.split())
                },
                file_path=str(html_path),
                file_size=html_path.stat().st_size,
                created_at=datetime.fromtimestamp(html_path.stat().st_ctime),
                processed_at=datetime.now()
            )
            
            self.stats.webpage_files += 1
            self.stats.total_content_length += len(content)
            return content_item
            
        except Exception as e:
            self.logger.error(f"Failed to process HTML {html_path}: {e}")
            self.stats.failed_files += 1
            return None
    
    def process_audio_file(self, audio_path: Path) -> Optional[ContentItem]:
        """Process a single audio file (placeholder for future transcription)"""
        try:
            # For now, create a placeholder content item
            # In the future, this could integrate with speech-to-text services
            
            title = audio_path.stem.replace('_', ' ').replace('-', ' ')
            
            content_item = ContentItem(
                id=self.generate_content_id(str(audio_path), "audio"),
                title=title,
                content_type="audio",
                source_url="",
                content=f"[Audio file: {title}] - Transcription not yet available",
                metadata={
                    "file_type": "mp3",
                    "original_filename": audio_path.name,
                    "duration": "unknown",  # Could be extracted with audio libraries
                    "transcription_status": "pending"
                },
                file_path=str(audio_path),
                file_size=audio_path.stat().st_size,
                created_at=datetime.fromtimestamp(audio_path.stat().st_ctime),
                processed_at=datetime.now()
            )
            
            self.stats.audio_files += 1
            return content_item
            
        except Exception as e:
            self.logger.error(f"Failed to process audio {audio_path}: {e}")
            self.stats.failed_files += 1
            return None
    
    def process_video_file(self, video_path: Path) -> Optional[ContentItem]:
        """Process a single video file (placeholder for future transcription)"""
        try:
            title = video_path.stem.replace('_', ' ').replace('-', ' ')
            
            content_item = ContentItem(
                id=self.generate_content_id(str(video_path), "video"),
                title=title,
                content_type="video",
                source_url="",
                content=f"[Video file: {title}] - Transcription not yet available",
                metadata={
                    "file_type": "mp4",
                    "original_filename": video_path.name,
                    "duration": "unknown",
                    "transcription_status": "pending"
                },
                file_path=str(video_path),
                file_size=video_path.stat().st_size,
                created_at=datetime.fromtimestamp(video_path.stat().st_ctime),
                processed_at=datetime.now()
            )
            
            self.stats.video_files += 1
            return content_item
            
        except Exception as e:
            self.logger.error(f"Failed to process video {video_path}: {e}")
            self.stats.failed_files += 1
            return None
    
    def load_scraping_metadata(self) -> Dict[str, Any]:
        """Load metadata from the scraping process"""
        metadata_path = self.base_path / "metadata" / "scrape_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load scraping metadata: {e}")
        return {}
    
    def process_all_content(self):
        """Process all downloaded content"""
        console.print("🚀 Starting Scriptural Truth content ingestion...", style="bold cyan")
        
        # Load scraping metadata
        scraping_metadata = self.load_scraping_metadata()
        
        # Get all files to process
        pdf_files = list((self.base_path / "pdfs").glob("*.pdf"))
        html_files = list((self.base_path / "pages").glob("*.html"))
        audio_files = list((self.base_path / "audio").glob("*.mp3"))
        video_files = list((self.base_path / "video").glob("*.mp4"))
        
        total_files = len(pdf_files) + len(html_files) + len(audio_files) + len(video_files)
        self.stats.total_files = total_files
        
        console.print(f"📊 Found {total_files} files to process:", style="yellow")
        console.print(f"  📚 PDFs: {len(pdf_files)}")
        console.print(f"  🌐 HTML: {len(html_files)}")
        console.print(f"  🎵 Audio: {len(audio_files)}")
        console.print(f"  🎬 Video: {len(video_files)}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Processing content...", total=total_files)
            
            # Process PDF files
            for pdf_path in pdf_files:
                content_item = self.process_pdf_file(pdf_path)
                if content_item:
                    self.content_items.append(content_item)
                self.stats.processed_files += 1
                progress.update(task, advance=1)
            
            # Process HTML files
            for html_path in html_files:
                content_item = self.process_html_file(html_path)
                if content_item:
                    self.content_items.append(content_item)
                self.stats.processed_files += 1
                progress.update(task, advance=1)
            
            # Process audio files
            for audio_path in audio_files:
                content_item = self.process_audio_file(audio_path)
                if content_item:
                    self.content_items.append(content_item)
                self.stats.processed_files += 1
                progress.update(task, advance=1)
            
            # Process video files
            for video_path in video_files:
                content_item = self.process_video_file(video_path)
                if content_item:
                    self.content_items.append(content_item)
                self.stats.processed_files += 1
                progress.update(task, advance=1)
    
    def create_embeddings(self):
        """Create embeddings for all content items in small batches"""
        if not self.embedding_model:
            console.print("❌ Embedding model not initialized", style="red")
            return
        
        console.print("🧠 Creating embeddings for content...", style="cyan")
        
        # Process in small batches to avoid memory issues
        batch_size = 10  # Small batch size to prevent memory overflow
        total_items = len(self.content_items)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Creating embeddings...", total=total_items)
            
            for i in range(0, total_items, batch_size):
                batch = self.content_items[i:i + batch_size]
                
                try:
                    # Process batch
                    for item in batch:
                        try:
                            # Truncate very long content to prevent memory issues
                            content = item.content
                            if len(content) > 8000:  # Limit content length
                                content = content[:8000] + "..."
                            
                            # Create embedding for the content
                            embedding = self.embedding_model.encode(content)
                            item.metadata['embedding'] = embedding.tolist()
                            progress.update(task, advance=1)
                        except Exception as e:
                            self.logger.error(f"Failed to create embedding for {item.id}: {e}")
                            progress.update(task, advance=1)
                    
                    # Force garbage collection after each batch
                    import gc
                    gc.collect()
                    
                except Exception as e:
                    self.logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
                    # Still advance progress for failed batch
                    for _ in batch:
                        progress.update(task, advance=1)
    
    def store_in_qdrant(self):
        """Store processed content in Qdrant vector database"""
        if not self.qdrant_client:
            console.print("❌ Qdrant client not initialized", style="red")
            return
        
        console.print("💾 Storing content in Qdrant...", style="cyan")
        
        collection_name = "scriptural_truth"
        points = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Storing in Qdrant...", total=len(self.content_items))
            
            for item in self.content_items:
                try:
                    if 'embedding' in item.metadata:
                        # Create a simple, unique ID
                        point_id = abs(hash(item.id)) % (2**63 - 1)
                        
                        # Ensure payload is clean and serializable
                        payload = {
                            "id": str(item.id),  # Convert to string
                            "title": str(item.title)[:500],  # Limit length
                            "content_type": str(item.content_type),
                            "content": str(item.content)[:8000],  # Limit content length
                            "source_url": str(item.source_url)[:500] if item.source_url else "",
                            "file_path": str(item.file_path)[:500] if item.file_path else "",
                            "file_size": int(item.file_size) if item.file_size else 0,
                            "created_at": item.created_at.isoformat() if item.created_at else "",
                            "processed_at": item.processed_at.isoformat() if item.processed_at else ""
                        }
                        
                        # Remove None values and ensure all values are serializable
                        payload = {k: v for k, v in payload.items() if v is not None}
                        
                        point = PointStruct(
                            id=point_id,
                            vector=item.metadata['embedding'],
                            payload=payload
                        )
                        points.append(point)
                    
                    progress.update(task, advance=1)
                except Exception as e:
                    self.logger.error(f"Failed to prepare point for {item.id}: {e}")
                    progress.update(task, advance=1)
        
        # Store points one by one to avoid batch hanging issues
        if points:
            try:
                console.print(f"📦 Storing {len(points)} items individually to avoid batch issues...", style="blue")
                
                stored_count = 0
                failed_count = 0
                
                for i, point in enumerate(points):
                    try:
                        # Store one point at a time
                        self.qdrant_client.upsert(
                            collection_name=collection_name,
                            points=[point]  # Single point in a list
                        )
                        stored_count += 1
                        
                        # Progress update every 10 items
                        if (i + 1) % 10 == 0:
                            console.print(f"📦 Stored {i + 1}/{len(points)} items...", style="blue")
                            
                    except Exception as point_error:
                        failed_count += 1
                        console.print(f"❌ Failed to store item {i + 1}: {point_error}", style="red")
                        # Continue with next item
                        continue
                
                console.print(f"✅ Completed: {stored_count} stored, {failed_count} failed", style="green")
                
            except Exception as e:
                console.print(f"❌ Failed to store points in Qdrant: {e}", style="red")
    
    def save_processed_data(self):
        """Save processed data to JSON files for backup and analysis"""
        console.print("💾 Saving processed data...", style="cyan")
        
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save content items
        content_data = [asdict(item) for item in self.content_items]
        with open(output_dir / "scriptural_truth_content.json", 'w', encoding='utf-8') as f:
            json.dump(content_data, f, indent=2, default=str)
        
        # Save statistics
        with open(output_dir / "scriptural_truth_ingestion_stats.json", 'w', encoding='utf-8') as f:
            json.dump(asdict(self.stats), f, indent=2, default=str)
        
        # Create training data for LLM fine-tuning
        training_data = []
        for item in self.content_items:
            if item.content_type in ['pdf', 'webpage'] and len(item.content) > 100:
                training_data.append({
                    "text": item.content,
                    "metadata": {
                        "title": item.title,
                        "content_type": item.content_type,
                        "source": "scriptural_truth"
                    }
                })
        
        with open(output_dir / "scriptural_truth_training_data.jsonl", 'w', encoding='utf-8') as f:
            for item in training_data:
                f.write(json.dumps(item) + '\n')
        
        console.print("✅ Processed data saved successfully", style="green")
    
    def display_summary(self):
        """Display ingestion summary"""
        table = Table(title="Scriptural Truth Ingestion Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Details", style="yellow")
        
        table.add_row("Total Files", str(self.stats.total_files), "All files found")
        table.add_row("Processed Files", str(self.stats.processed_files), "Successfully processed")
        table.add_row("Failed Files", str(self.stats.failed_files), "Processing errors")
        table.add_row("PDF Files", str(self.stats.pdf_files), "Text extracted")
        table.add_row("Audio Files", str(self.stats.audio_files), "Placeholder created")
        table.add_row("Video Files", str(self.stats.video_files), "Placeholder created")
        table.add_row("Webpage Files", str(self.stats.webpage_files), "Text extracted")
        table.add_row("Total Content Length", f"{self.stats.total_content_length:,} chars", "All text content")
        table.add_row("Content Items", str(len(self.content_items)), "Ready for AI learning")
        
        console.print(table)
        
        # Display sample content
        if self.content_items:
            console.print("\n📄 Sample Content Items:", style="bold cyan")
            for i, item in enumerate(self.content_items[:3]):
                console.print(f"\n{i+1}. {item.title} ({item.content_type})")
                console.print(f"   Content: {item.content[:200]}...")
                console.print(f"   File: {item.file_path}")
    
    def run_full_pipeline(self):
        """Run the complete ingestion pipeline"""
        try:
            console.print(Panel.fit(
                "🚀 Scriptural Truth Content Ingestion Pipeline\n"
                "Processing all downloaded content for AI learning integration",
                style="bold blue"
            ))
            
            # Setup
            self.setup_embedding_model()
            self.setup_qdrant_client()
            
            # Process content
            self.process_all_content()
            
            # Create embeddings
            self.create_embeddings()
            
            # Store in vector database
            self.store_in_qdrant()
            
            # Save processed data
            self.save_processed_data()
            
            # Display summary
            self.display_summary()
            
            console.print("\n🎉 Scriptural Truth ingestion pipeline completed successfully!", style="bold green")
            console.print("📚 Content is now ready for AI learning and Elysia integration", style="green")
            
        except Exception as e:
            console.print(f"\n❌ Ingestion pipeline failed: {e}", style="bold red")
            self.logger.error(f"Ingestion pipeline failed: {e}")
            raise

def main():
    """Main function to run the ingestion pipeline"""
    ingestion = ScripturalTruthIngestion()
    ingestion.run_full_pipeline()

if __name__ == "__main__":
    main()
