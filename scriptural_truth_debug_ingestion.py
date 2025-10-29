#!/usr/bin/env python3
"""
Scriptural Truth Debug Ingestion Pipeline
=========================================

This version has extensive debugging and monitoring to see exactly what's happening.
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

# Vector database
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

class ScripturalTruthDebugIngestion:
    """Debug version of the ingestion pipeline with extensive logging"""
    
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
        
        # Setup logging with more detail
        logging.basicConfig(
            level=logging.DEBUG,  # More verbose logging
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scriptural_truth_debug_ingestion.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log_status(self, message: str, level: str = "INFO"):
        """Log with both file and console output"""
        if level == "INFO":
            self.logger.info(message)
            console.print(f"ℹ️ {message}", style="blue")
        elif level == "WARNING":
            self.logger.warning(message)
            console.print(f"⚠️ {message}", style="yellow")
        elif level == "ERROR":
            self.logger.error(message)
            console.print(f"❌ {message}", style="red")
        elif level == "SUCCESS":
            self.logger.info(message)
            console.print(f"✅ {message}", style="green")
    
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
        self.log_status("Setting up embedding model...")
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.log_status("Embedding model loaded successfully", "SUCCESS")
        except Exception as e:
            self.log_status(f"Failed to load embedding model: {e}", "ERROR")
            raise
    
    def setup_qdrant_client(self):
        """Initialize Qdrant client - using server mode to avoid conflicts"""
        self.log_status("Setting up Qdrant client...")
        try:
            if self.use_qdrant_server:
                # Try to connect to Qdrant server first
                try:
                    self.qdrant_client = QdrantClient(host="localhost", port=6333)
                    # Test connection
                    self.qdrant_client.get_collections()
                    self.log_status("Connected to Qdrant server", "SUCCESS")
                except Exception as server_error:
                    self.log_status(f"Qdrant server not available: {server_error}", "WARNING")
                    self.log_status("Falling back to local storage with unique path...", "WARNING")
                    # Use unique path to avoid conflicts
                    unique_path = f"qdrant_data_scriptural_truth_debug_{int(time.time())}"
                    self.qdrant_client = QdrantClient(path=unique_path)
            else:
                # Use unique local path
                unique_path = f"qdrant_data_scriptural_truth_debug_{int(time.time())}"
                self.qdrant_client = QdrantClient(path=unique_path)
            
            # Create collection for Scriptural Truth content
            collection_name = "scriptural_truth_debug"
            try:
                self.qdrant_client.get_collection(collection_name)
                self.log_status(f"Collection '{collection_name}' already exists", "SUCCESS")
            except:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                self.log_status(f"Created collection '{collection_name}'", "SUCCESS")
                
        except Exception as e:
            self.log_status(f"Failed to setup Qdrant client: {e}", "ERROR")
            raise
    
    def discover_files_debug(self) -> List[Path]:
        """Discover files with detailed logging"""
        self.log_status("Discovering files with detailed analysis...")
        
        all_files = []
        pdf_files = []
        html_files = []
        audio_files = []
        video_files = []
        
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() in ['.pdf', '.html', '.mp3', '.mp4', '.wav', '.m4a', '.avi', '.mov']:
                    all_files.append(file_path)
                    
                    if file_path.suffix.lower() == '.pdf':
                        pdf_files.append(file_path)
                    elif file_path.suffix.lower() == '.html':
                        html_files.append(file_path)
                    elif file_path.suffix.lower() in ['.mp3', '.wav', '.m4a']:
                        audio_files.append(file_path)
                    elif file_path.suffix.lower() in ['.mp4', '.avi', '.mov']:
                        video_files.append(file_path)
        
        self.stats.total_files = len(all_files)
        
        self.log_status(f"File Discovery Results:")
        self.log_status(f"  Total files found: {len(all_files)}")
        self.log_status(f"  PDF files: {len(pdf_files)}")
        self.log_status(f"  HTML files: {len(html_files)}")
        self.log_status(f"  Audio files: {len(audio_files)}")
        self.log_status(f"  Video files: {len(video_files)}")
        
        # Analyze HTML file sizes
        large_html_count = 0
        small_html_count = 0
        for html_file in html_files:
            try:
                size_mb = html_file.stat().st_size / (1024 * 1024)
                if size_mb > 10:
                    large_html_count += 1
                else:
                    small_html_count += 1
            except:
                pass
        
        self.log_status(f"  Large HTML files (>10MB): {large_html_count}")
        self.log_status(f"  Small HTML files (≤10MB): {small_html_count}")
        
        return all_files
    
    def process_file_debug(self, file_path: Path) -> Optional[ContentItem]:
        """Process a single file with extensive debugging"""
        try:
            self.log_status(f"Processing file: {file_path.name}")
            
            # Check memory usage before processing
            memory_usage = self.check_memory_usage()
            if memory_usage > self.max_memory_mb:
                self.log_status(f"High memory usage ({memory_usage:.1f}MB), forcing cleanup", "WARNING")
                self.cleanup_memory()
            
            # Determine content type and extract text
            content = ""
            content_type = "unknown"
            
            if file_path.suffix.lower() == '.pdf':
                content_type = "pdf"
                self.log_status(f"Extracting text from PDF: {file_path.name}")
                content = self.extract_pdf_text_safe(file_path)
                self.log_status(f"PDF text extraction result: {len(content)} characters")
            elif file_path.suffix.lower() == '.html':
                content_type = "webpage"
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                self.log_status(f"Processing HTML file: {file_path.name} ({file_size_mb:.1f}MB)")
                
                if file_size_mb > 10:
                    self.log_status(f"Skipping large HTML file: {file_path.name}", "WARNING")
                    self.stats.skipped_files += 1
                    return None
                
                content = self.extract_html_text_safe(file_path)
                self.log_status(f"HTML text extraction result: {len(content)} characters")
            elif file_path.suffix.lower() in ['.mp3', '.wav', '.m4a']:
                content_type = "audio"
                content = f"[Audio file: {file_path.name}] - Transcription not available"
                self.log_status(f"Created audio placeholder: {file_path.name}")
            elif file_path.suffix.lower() in ['.mp4', '.avi', '.mov']:
                content_type = "video"
                content = f"[Video file: {file_path.name}] - Transcription not available"
                self.log_status(f"Created video placeholder: {file_path.name}")
            else:
                self.log_status(f"Unsupported file type: {file_path}", "WARNING")
                return None
            
            # Validate content
            if not self.validate_content(content, file_path):
                self.log_status(f"Content validation failed for: {file_path.name}", "WARNING")
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
                source_url="",
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
            self.stats.processed_files += 1
            
            self.log_status(f"Successfully processed: {file_path.name} ({content_type}, {len(content)} chars)", "SUCCESS")
            return content_item
            
        except Exception as e:
            self.log_status(f"Failed to process file {file_path}: {e}", "ERROR")
            self.stats.failed_files += 1
            return None
    
    def validate_content(self, content: str, file_path: Path) -> bool:
        """Validate content before processing"""
        if not content or len(content.strip()) < 50:
            self.log_status(f"Content too short for {file_path.name}: {len(content)} characters", "WARNING")
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
                self.log_status(f"Content contains error pattern '{pattern}' for {file_path.name}", "WARNING")
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
                self.log_status(f"Processing PDF {pdf_path.name}: {len(pdf_reader.pages)} pages, limiting to {max_pages}")
                
                for i, page in enumerate(pdf_reader.pages):
                    if i >= max_pages:
                        text += "\n[Content truncated - too many pages]"
                        break
                    
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as page_error:
                        self.log_status(f"Failed to extract page {i+1} from {pdf_path}: {page_error}", "WARNING")
                        continue
                
                return text.strip()
                
        except Exception as e:
            self.log_status(f"Failed to extract text from PDF {pdf_path}: {e}", "ERROR")
            return ""
    
    def extract_html_text_safe(self, html_path: Path) -> str:
        """Safely extract text from HTML files with error handling"""
        try:
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
            self.log_status(f"Failed to extract text from HTML {html_path}: {e}", "ERROR")
            return ""
    
    def generate_content_id(self, file_path: str, content_type: str) -> str:
        """Generate a unique ID for content items"""
        content_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"st_{content_type}_{content_hash}"
    
    def run_debug_pipeline(self):
        """Run the debug pipeline with extensive monitoring"""
        try:
            console.print(Panel.fit(
                "🔍 Scriptural Truth Debug Ingestion Pipeline\n"
                "Extensive logging and monitoring to identify issues",
                style="bold blue"
            ))
            
            # Setup
            self.setup_embedding_model()
            self.setup_qdrant_client()
            
            # Discover files with detailed analysis
            files = self.discover_files_debug()
            if not files:
                self.log_status("No files found to process", "ERROR")
                return
            
            self.log_status(f"Starting to process {len(files)} files...")
            
            # Process files one by one with detailed logging
            processed_count = 0
            for i, file_path in enumerate(files):
                self.log_status(f"Processing file {i+1}/{len(files)}: {file_path.name}")
                
                content_item = self.process_file_debug(file_path)
                if content_item:
                    self.content_items.append(content_item)
                    processed_count += 1
                
                # Progress update every 10 files
                if (i + 1) % 10 == 0:
                    self.log_status(f"Progress: {i+1}/{len(files)} files processed, {processed_count} successful")
                    self.cleanup_memory()  # Cleanup memory periodically
            
            self.log_status(f"File processing complete: {processed_count} items processed successfully", "SUCCESS")
            
            if not self.content_items:
                self.log_status("No content items were processed successfully", "ERROR")
                return
            
            # Save results
            self.save_debug_results()
            
            # Display summary
            self.display_debug_summary()
            
            self.log_status("Debug pipeline completed successfully!", "SUCCESS")
            
        except Exception as e:
            self.log_status(f"Debug pipeline failed: {e}", "ERROR")
            self.logger.exception("Debug pipeline error")
            raise
    
    def save_debug_results(self):
        """Save debug results"""
        self.log_status("Saving debug results...")
        
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save content items
        content_file = output_dir / "scriptural_truth_debug_content.json"
        self.log_status(f"Saving {len(self.content_items)} items to {content_file}")
        
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(item) for item in self.content_items], f, indent=2, default=str)
        
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
        
        summary_file = output_dir / "scriptural_truth_debug_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.log_status(f"Debug results saved successfully", "SUCCESS")
    
    def display_debug_summary(self):
        """Display debug summary"""
        table = Table(title="Scriptural Truth Debug Processing Summary")
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

def main():
    """Main function to run the debug pipeline"""
    ingestion = ScripturalTruthDebugIngestion(use_qdrant_server=True)
    ingestion.run_debug_pipeline()

if __name__ == "__main__":
    main()
