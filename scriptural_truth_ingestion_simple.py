#!/usr/bin/env python3
"""
Scriptural Truth Content Ingestion Pipeline - Simplified Version
Processes downloaded content and saves to JSON files for Elysia integration
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from sentence_transformers import SentenceTransformer
import PyPDF2
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scriptural_truth_ingestion_simple.log'),
        logging.StreamHandler()
    ]
)

console = Console()

@dataclass
class ContentItem:
    id: str
    title: str
    content_type: str
    content: str
    source_url: str
    file_path: str
    file_size: int
    created_at: datetime
    processed_at: datetime
    metadata: Dict[str, Any]

class ScripturalTruthIngestionSimple:
    def __init__(self, content_dir: str = "scriptural-truth-website"):
        self.content_dir = Path(content_dir)
        self.content_items: List[ContentItem] = []
        self.embedding_model = None
        self.logger = logging.getLogger(__name__)
        
    def setup_embedding_model(self):
        """Setup the embedding model"""
        console.print("🔧 Setting up embedding model...", style="cyan")
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            console.print("✅ Embedding model loaded successfully", style="green")
        except Exception as e:
            console.print(f"❌ Failed to load embedding model: {e}", style="red")
            raise
    
    def discover_files(self) -> List[Path]:
        """Discover all files to process"""
        console.print("🔍 Discovering files...", style="cyan")
        
        files = []
        for file_path in self.content_dir.rglob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() in ['.pdf', '.html', '.mp3', '.mp4']:
                    files.append(file_path)
        
        console.print(f"📊 Found {len(files)} files to process:", style="blue")
        pdf_count = len([f for f in files if f.suffix.lower() == '.pdf'])
        html_count = len([f for f in files if f.suffix.lower() == '.html'])
        audio_count = len([f for f in files if f.suffix.lower() == '.mp3'])
        video_count = len([f for f in files if f.suffix.lower() == '.mp4'])
        
        console.print(f"  📚 PDFs: {pdf_count}")
        console.print(f"  🌐 HTML: {html_count}")
        console.print(f"  🎵 Audio: {audio_count}")
        console.print(f"  🎬 Video: {video_count}")
        
        return files
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            self.logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            return ""
    
    def extract_text_from_html(self, file_path: Path) -> str:
        """Extract text from HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                return soup.get_text().strip()
        except Exception as e:
            self.logger.error(f"Failed to extract text from HTML {file_path}: {e}")
            return ""
    
    def process_files(self, files: List[Path]):
        """Process all files and extract content"""
        console.print("📝 Processing files...", style="cyan")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Processing files...", total=len(files))
            
            for file_path in files:
                try:
                    # Determine content type
                    if file_path.suffix.lower() == '.pdf':
                        content_type = "pdf"
                        content = self.extract_text_from_pdf(file_path)
                    elif file_path.suffix.lower() == '.html':
                        content_type = "html"
                        content = self.extract_text_from_html(file_path)
                    elif file_path.suffix.lower() in ['.mp3', '.mp4']:
                        content_type = "media"
                        content = f"[{file_path.suffix.upper()} Media File] {file_path.name}"
                    else:
                        content_type = "unknown"
                        content = ""
                    
                    # Create content item
                    item = ContentItem(
                        id=f"scriptural_truth_{file_path.stem}",
                        title=file_path.stem.replace('_', ' ').title(),
                        content_type=content_type,
                        content=content,
                        source_url=f"https://scriptural-truth.com/{file_path.relative_to(self.content_dir)}",
                        file_path=str(file_path),
                        file_size=file_path.stat().st_size,
                        created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                        processed_at=datetime.now(),
                        metadata={}
                    )
                    
                    self.content_items.append(item)
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    self.logger.error(f"Failed to process file {file_path}: {e}")
                    progress.update(task, advance=1)
    
    def create_embeddings(self):
        """Create embeddings for all content items"""
        if not self.embedding_model:
            console.print("❌ Embedding model not initialized", style="red")
            return
        
        console.print("🧠 Creating embeddings...", style="cyan")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Creating embeddings...", total=len(self.content_items))
            
            # Process in small batches to avoid memory issues
            batch_size = 10
            for i in range(0, len(self.content_items), batch_size):
                batch = self.content_items[i:i + batch_size]
                
                # Prepare texts for embedding
                texts = []
                for item in batch:
                    # Limit content length to prevent memory issues
                    text = item.content[:8000] if item.content else ""
                    texts.append(f"{item.title}\n{text}")
                
                try:
                    # Create embeddings
                    embeddings = self.embedding_model.encode(texts)
                    
                    # Store embeddings in metadata
                    for j, item in enumerate(batch):
                        item.metadata['embedding'] = embeddings[j].tolist()
                    
                    progress.update(task, advance=len(batch))
                    
                except Exception as e:
                    self.logger.error(f"Failed to create embeddings for batch {i//batch_size + 1}: {e}")
                    progress.update(task, advance=len(batch))
    
    def save_to_json(self):
        """Save processed data to JSON files using streaming to avoid memory issues"""
        console.print("💾 Saving data to JSON files...", style="cyan")
        
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save to JSON file using streaming to avoid memory issues
        output_file = output_dir / "scriptural_truth_content.json"
        console.print(f"📝 Writing {len(self.content_items)} items to {output_file}...", style="blue")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('[\n')
            
            for i, item in enumerate(self.content_items):
                try:
                    item_dict = asdict(item)
                    # Convert datetime objects to strings
                    item_dict['created_at'] = item.created_at.isoformat()
                    item_dict['processed_at'] = item.processed_at.isoformat()
                    
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
                        
                except Exception as e:
                    self.logger.error(f"Failed to write item {i}: {e}")
                    continue
            
            f.write(']\n')
        
        console.print(f"✅ Saved {len(self.content_items)} items to {output_file}", style="green")
        
        # Save training data (without embeddings for LLM training) using streaming
        training_file = output_dir / "scriptural_truth_training.jsonl"
        console.print(f"📝 Writing training data to {training_file}...", style="blue")
        
        with open(training_file, 'w', encoding='utf-8') as f:
            for i, item in enumerate(self.content_items):
                try:
                    training_item = {
                        "id": item.id,
                        "title": item.title,
                        "content_type": item.content_type,
                        "content": item.content,
                        "source_url": item.source_url
                    }
                    f.write(json.dumps(training_item, ensure_ascii=False) + '\n')
                    
                    # Progress update every 100 items
                    if (i + 1) % 100 == 0:
                        console.print(f"📝 Written {i + 1}/{len(self.content_items)} training items...", style="blue")
                        
                except Exception as e:
                    self.logger.error(f"Failed to write training item {i}: {e}")
                    continue
        
        console.print(f"✅ Saved {len(self.content_items)} training items to {training_file}", style="green")
        
        # Save summary
        summary = {
            "total_items": len(self.content_items),
            "content_types": {
                "pdf": len([item for item in self.content_items if item.content_type == "pdf"]),
                "html": len([item for item in self.content_items if item.content_type == "html"]),
                "media": len([item for item in self.content_items if item.content_type == "media"])
            },
            "total_content_length": sum(len(item.content) for item in self.content_items),
            "items_with_embeddings": len([item for item in self.content_items if 'embedding' in item.metadata]),
            "processed_at": datetime.now().isoformat()
        }
        
        summary_file = output_dir / "scriptural_truth_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        console.print(f"✅ Saved summary to {summary_file}", style="green")
    
    def run_full_pipeline(self):
        """Run the complete ingestion pipeline"""
        try:
            console.print("🚀 Starting Scriptural Truth content ingestion...", style="cyan")
            
            # Setup
            self.setup_embedding_model()
            
            # Discover and process files
            files = self.discover_files()
            if not files:
                console.print("❌ No files found to process", style="red")
                return
            
            self.process_files(files)
            
            # Create embeddings
            self.create_embeddings()
            
            # Save to JSON files
            self.save_to_json()
            
            console.print("🎉 Ingestion pipeline completed successfully!", style="green")
            
        except Exception as e:
            console.print(f"❌ Ingestion pipeline failed: {e}", style="red")
            self.logger.error(f"Ingestion pipeline failed: {e}")
            raise

def main():
    """Main function"""
    ingestion = ScripturalTruthIngestionSimple()
    ingestion.run_full_pipeline()

if __name__ == "__main__":
    main()
