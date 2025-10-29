#!/usr/bin/env python3
"""
Document Ingestion Pipeline for KJV Sources Project
==================================================

This pipeline allows you to easily add new documents for AI analysis.
Simply drop documents into the 'new_documents' folder and run this script
to automatically process and integrate them into your research system.

Supported formats: PDF, TXT, MD, HTML, DOCX, RTF
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import shutil

# Document processing libraries
import PyPDF2
import docx
from bs4 import BeautifulSoup
import re

# Data processing
import pandas as pd
from sentence_transformers import SentenceTransformer

# Vector database
import weaviate
import weaviate.classes.config as wvcc

# Rich for beautiful output
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

@dataclass
class DocumentMetadata:
    """Metadata for processed documents"""
    id: str
    title: str
    content_type: str  # 'pdf', 'docx', 'txt', 'md', 'html', 'rtf'
    source_file: str
    content: str
    word_count: int
    character_count: int
    language: str
    topics: List[str]
    biblical_references: List[str]
    source_attributions: List[str]  # J, E, P, D, R if applicable
    created_at: datetime
    processed_at: datetime
    file_size: int
    checksum: str

@dataclass
class ProcessingStats:
    """Statistics for document processing"""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    total_content_length: int = 0
    pdf_files: int = 0
    docx_files: int = 0
    txt_files: int = 0
    md_files: int = 0
    html_files: int = 0
    rtf_files: int = 0

class DocumentIngestionPipeline:
    """Main pipeline for ingesting new documents"""
    
    def __init__(self, input_dir: str = "new_documents", output_dir: str = "processed_documents"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.stats = ProcessingStats()
        self.documents: List[DocumentMetadata] = []
        self.embedding_model = None
        self.weaviate_client = None
        
        # Create directories
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('document_ingestion.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_embedding_model(self):
        """Initialize the sentence transformer model"""
        console.print("🔧 Setting up embedding model...", style="cyan")
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            console.print("✅ Embedding model loaded successfully", style="green")
        except Exception as e:
            console.print(f"❌ Failed to load embedding model: {e}", style="red")
            raise
    
    def setup_weaviate_connection(self):
        """Initialize Weaviate client"""
        console.print("🔧 Setting up Weaviate connection...", style="cyan")
        try:
            self.weaviate_client = weaviate.connect_to_local(host='localhost', port=8080)
            console.print("✅ Connected to Weaviate successfully", style="green")
        except Exception as e:
            console.print(f"❌ Failed to connect to Weaviate: {e}", style="red")
            raise
    
    def discover_documents(self) -> List[Path]:
        """Discover all documents to process"""
        console.print("🔍 Discovering documents...", style="cyan")
        
        supported_extensions = {'.pdf', '.docx', '.txt', '.md', '.html', '.htm', '.rtf'}
        documents = []
        
        for file_path in self.input_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                documents.append(file_path)
        
        self.stats.total_files = len(documents)
        
        console.print(f"📊 Found {len(documents)} documents to process:", style="blue")
        for ext in supported_extensions:
            count = len([f for f in documents if f.suffix.lower() == ext])
            if count > 0:
                console.print(f"  📄 {ext.upper()}: {count}")
        
        return documents
    
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
    
    def extract_text_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            self.logger.error(f"Failed to extract text from DOCX {file_path}: {e}")
            return ""
    
    def extract_text_from_html(self, file_path: Path) -> str:
        """Extract text from HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                return soup.get_text().strip()
        except Exception as e:
            self.logger.error(f"Failed to extract text from HTML {file_path}: {e}")
            return ""
    
    def extract_text_from_file(self, file_path: Path) -> str:
        """Extract text from any supported file type"""
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif extension in ['.html', '.htm']:
            return self.extract_text_from_html(file_path)
        elif extension in ['.txt', '.md', '.rtf']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    return file.read().strip()
            except Exception as e:
                self.logger.error(f"Failed to read text file {file_path}: {e}")
                return ""
        
        return ""
    
    def generate_document_id(self, file_path: Path, content: str) -> str:
        """Generate unique document ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"doc_{file_path.stem}_{content_hash}"
    
    def extract_biblical_references(self, content: str) -> List[str]:
        """Extract biblical references from content"""
        # Pattern to match biblical references like "Genesis 1:1", "Exodus 2:3-5", etc.
        pattern = r'\b(?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalms|Proverbs|Ecclesiastes|Song of Songs|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|Jude|Revelation)\s+\d+(?::\d+(?:-\d+)?)?(?:\s*,\s*\d+(?::\d+(?:-\d+)?)?)*'
        
        references = re.findall(pattern, content, re.IGNORECASE)
        return list(set(references))  # Remove duplicates
    
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
            'blessing': ['bless', 'blessing', 'blessed', 'favor']
        }
        
        for topic, keywords in theme_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def process_document(self, file_path: Path) -> Optional[DocumentMetadata]:
        """Process a single document"""
        try:
            # Extract text
            content = self.extract_text_from_file(file_path)
            if not content or len(content) < 50:  # Skip very short content
                self.logger.warning(f"Skipping {file_path}: content too short")
                return None
            
            # Generate metadata
            doc_id = self.generate_document_id(file_path, content)
            title = file_path.stem.replace('_', ' ').replace('-', ' ').title()
            content_type = file_path.suffix.lower().lstrip('.')
            
            # Extract additional metadata
            biblical_refs = self.extract_biblical_references(content)
            source_attrs = self.extract_source_attributions(content)
            topics = self.extract_topics(content)
            
            # Calculate checksum
            checksum = hashlib.md5(content.encode()).hexdigest()
            
            document = DocumentMetadata(
                id=doc_id,
                title=title,
                content_type=content_type,
                source_file=str(file_path),
                content=content,
                word_count=len(content.split()),
                character_count=len(content),
                language='en',  # Could be enhanced with language detection
                topics=topics,
                biblical_references=biblical_refs,
                source_attributions=source_attrs,
                created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                processed_at=datetime.now(),
                file_size=file_path.stat().st_size,
                checksum=checksum
            )
            
            # Update stats
            self.stats.processed_files += 1
            self.stats.total_content_length += len(content)
            
            if content_type == 'pdf':
                self.stats.pdf_files += 1
            elif content_type == 'docx':
                self.stats.docx_files += 1
            elif content_type == 'txt':
                self.stats.txt_files += 1
            elif content_type == 'md':
                self.stats.md_files += 1
            elif content_type in ['html', 'htm']:
                self.stats.html_files += 1
            elif content_type == 'rtf':
                self.stats.rtf_files += 1
            
            return document
            
        except Exception as e:
            self.logger.error(f"Failed to process document {file_path}: {e}")
            self.stats.failed_files += 1
            return None
    
    def process_all_documents(self, documents: List[Path]):
        """Process all discovered documents"""
        console.print("📝 Processing documents...", style="cyan")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Processing documents...", total=len(documents))
            
            for file_path in documents:
                document = self.process_document(file_path)
                if document:
                    self.documents.append(document)
                progress.update(task, advance=1)
    
    def create_embeddings(self):
        """Create embeddings for all documents"""
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
            
            task = progress.add_task("Creating embeddings...", total=len(self.documents))
            
            # Process in small batches
            batch_size = 10
            for i in range(0, len(self.documents), batch_size):
                batch = self.documents[i:i + batch_size]
                
                try:
                    # Prepare texts for embedding
                    texts = []
                    for doc in batch:
                        # Limit content length to prevent memory issues
                        text = doc.content[:8000] if doc.content else ""
                        texts.append(f"{doc.title}\n{text}")
                    
                    # Create embeddings
                    embeddings = self.embedding_model.encode(texts)
                    
                    # Store embeddings in document metadata
                    for j, doc in enumerate(batch):
                        doc.embedding = embeddings[j].tolist()
                    
                    progress.update(task, advance=len(batch))
                    
                except Exception as e:
                    self.logger.error(f"Failed to create embeddings for batch {i//batch_size + 1}: {e}")
                    progress.update(task, advance=len(batch))
    
    def store_in_weaviate(self):
        """Store processed documents in Weaviate"""
        if not self.weaviate_client:
            console.print("❌ Weaviate client not initialized", style="red")
            return
        
        console.print("💾 Storing documents in Weaviate...", style="cyan")
        
        # Create collection if it doesn't exist
        collection_name = "AdditionalDocuments"
        try:
            collection = self.weaviate_client.collections.get(collection_name)
            console.print(f"✅ Collection '{collection_name}' already exists", style="green")
        except:
            console.print(f"📋 Creating collection '{collection_name}'...", style="cyan")
            collection = self.weaviate_client.collections.create(
                name=collection_name,
                description="Additional documents for biblical research and analysis",
                properties=[
                    wvcc.Property(name="document_id", data_type=wvcc.DataType.TEXT),
                    wvcc.Property(name="title", data_type=wvcc.DataType.TEXT),
                    wvcc.Property(name="content_type", data_type=wvcc.DataType.TEXT),
                    wvcc.Property(name="content", data_type=wvcc.DataType.TEXT),
                    wvcc.Property(name="word_count", data_type=wvcc.DataType.INT),
                    wvcc.Property(name="character_count", data_type=wvcc.DataType.INT),
                    wvcc.Property(name="language", data_type=wvcc.DataType.TEXT),
                    wvcc.Property(name="topics", data_type=wvcc.DataType.TEXT_ARRAY),
                    wvcc.Property(name="biblical_references", data_type=wvcc.DataType.TEXT_ARRAY),
                    wvcc.Property(name="source_attributions", data_type=wvcc.DataType.TEXT_ARRAY),
                    wvcc.Property(name="created_at", data_type=wvcc.DataType.TEXT),
                    wvcc.Property(name="processed_at", data_type=wvcc.DataType.TEXT),
                    wvcc.Property(name="file_size", data_type=wvcc.DataType.INT),
                    wvcc.Property(name="checksum", data_type=wvcc.DataType.TEXT),
                ],
                vectorizer_config=wvcc.Configure.Vectorizer.none()
            )
            console.print(f"✅ Created collection '{collection_name}'", style="green")
        
        # Store documents
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Storing in Weaviate...", total=len(self.documents))
            
            for doc in self.documents:
                try:
                    # Prepare data object
                    data_object = {
                        "document_id": doc.id,
                        "title": doc.title,
                        "content_type": doc.content_type,
                        "content": doc.content[:10000],  # Limit content length
                        "word_count": doc.word_count,
                        "character_count": doc.character_count,
                        "language": doc.language,
                        "topics": doc.topics,
                        "biblical_references": doc.biblical_references,
                        "source_attributions": doc.source_attributions,
                        "created_at": doc.created_at.isoformat(),
                        "processed_at": doc.processed_at.isoformat(),
                        "file_size": doc.file_size,
                        "checksum": doc.checksum
                    }
                    
                    # Store with embedding if available
                    if hasattr(doc, 'embedding'):
                        collection.data.insert(
                            data_object,
                            vector=doc.embedding
                        )
                    else:
                        collection.data.insert(data_object)
                    
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    self.logger.error(f"Failed to store document {doc.id}: {e}")
                    progress.update(task, advance=1)
        
        console.print(f"✅ Stored {len(self.documents)} documents in Weaviate", style="green")
    
    def save_processed_data(self):
        """Save processed data to JSON files"""
        console.print("💾 Saving processed data...", style="cyan")
        
        # Save document metadata
        documents_data = [asdict(doc) for doc in self.documents]
        with open(self.output_dir / "processed_documents.json", 'w', encoding='utf-8') as f:
            json.dump(documents_data, f, indent=2, default=str, ensure_ascii=False)
        
        # Save processing statistics
        with open(self.output_dir / "processing_stats.json", 'w', encoding='utf-8') as f:
            json.dump(asdict(self.stats), f, indent=2, default=str)
        
        # Create training data for LLM
        training_data = []
        for doc in self.documents:
            if len(doc.content) > 100:
                training_data.append({
                    "text": doc.content,
                    "metadata": {
                        "title": doc.title,
                        "content_type": doc.content_type,
                        "topics": doc.topics,
                        "biblical_references": doc.biblical_references,
                        "source_attributions": doc.source_attributions,
                        "source": "additional_documents"
                    }
                })
        
        with open(self.output_dir / "training_data.jsonl", 'w', encoding='utf-8') as f:
            for item in training_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        console.print("✅ Processed data saved successfully", style="green")
    
    def move_processed_files(self):
        """Move processed files to archive directory"""
        console.print("📁 Archiving processed files...", style="cyan")
        
        archive_dir = self.input_dir / "processed"
        archive_dir.mkdir(exist_ok=True)
        
        for doc in self.documents:
            source_path = Path(doc.source_file)
            if source_path.exists():
                archive_path = archive_dir / source_path.name
                shutil.move(str(source_path), str(archive_path))
        
        console.print(f"✅ Moved {len(self.documents)} files to archive", style="green")
    
    def display_summary(self):
        """Display processing summary"""
        table = Table(title="Document Processing Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Details", style="yellow")
        
        table.add_row("Total Files", str(self.stats.total_files), "Files discovered")
        table.add_row("Processed Files", str(self.stats.processed_files), "Successfully processed")
        table.add_row("Failed Files", str(self.stats.failed_files), "Processing errors")
        table.add_row("PDF Files", str(self.stats.pdf_files), "PDF documents")
        table.add_row("DOCX Files", str(self.stats.docx_files), "Word documents")
        table.add_row("TXT Files", str(self.stats.txt_files), "Text documents")
        table.add_row("MD Files", str(self.stats.md_files), "Markdown documents")
        table.add_row("HTML Files", str(self.stats.html_files), "HTML documents")
        table.add_row("RTF Files", str(self.stats.rtf_files), "Rich text documents")
        table.add_row("Total Content", f"{self.stats.total_content_length:,} chars", "All text content")
        table.add_row("Documents", str(len(self.documents)), "Ready for AI analysis")
        
        console.print(table)
        
        # Display sample documents
        if self.documents:
            console.print("\n📄 Sample Processed Documents:", style="bold cyan")
            for i, doc in enumerate(self.documents[:3]):
                console.print(f"\n{i+1}. {doc.title} ({doc.content_type})")
                console.print(f"   Topics: {', '.join(doc.topics[:3])}")
                console.print(f"   Biblical References: {', '.join(doc.biblical_references[:3])}")
                console.print(f"   Source Attributions: {', '.join(doc.source_attributions)}")
                console.print(f"   Content: {doc.content[:200]}...")
    
    def run_full_pipeline(self):
        """Run the complete document ingestion pipeline"""
        try:
            console.print(Panel.fit(
                "🚀 Document Ingestion Pipeline\n"
                "Processing new documents for AI analysis integration",
                style="bold blue"
            ))
            
            # Setup
            self.setup_embedding_model()
            self.setup_weaviate_connection()
            
            # Discover and process documents
            documents = self.discover_documents()
            if not documents:
                console.print("ℹ️ No documents found in new_documents folder", style="yellow")
                console.print("💡 Add documents to the 'new_documents' folder and run again", style="blue")
                return
            
            self.process_all_documents(documents)
            
            # Create embeddings
            self.create_embeddings()
            
            # Store in vector database
            self.store_in_weaviate()
            
            # Save processed data
            self.save_processed_data()
            
            # Archive processed files
            self.move_processed_files()
            
            # Display summary
            self.display_summary()
            
            console.print("\n🎉 Document ingestion pipeline completed successfully!", style="bold green")
            console.print("📚 New documents are now available for AI analysis in Elysia", style="green")
            
        except Exception as e:
            console.print(f"\n❌ Document ingestion pipeline failed: {e}", style="bold red")
            self.logger.error(f"Document ingestion pipeline failed: {e}")
            raise

def main():
    """Main function to run the document ingestion pipeline"""
    pipeline = DocumentIngestionPipeline()
    pipeline.run_full_pipeline()

if __name__ == "__main__":
    main()
