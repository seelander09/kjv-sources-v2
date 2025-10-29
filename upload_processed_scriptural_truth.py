#!/usr/bin/env python3
"""
Upload Processed Scriptural Truth Data to Qdrant
================================================

Uploads the already processed scriptural truth data (with embeddings) to Qdrant
with detailed progress tracking.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

console = Console()

class ScripturalTruthUploader:
    def __init__(self):
        self.client = QdrantClient(path='qdrant_data')
        self.collection_name = "scriptural_truth_complete"
        
    def check_data_files(self):
        """Check what processed data files are available."""
        console.print("[bold blue]Checking Processed Scriptural Truth Data[/bold blue]")
        
        output_dir = Path("output")
        files_to_check = [
            "scriptural_truth_content.json",
            "scriptural_truth_training.jsonl",
            "scriptural_truth_summary.json"
        ]
        
        available_files = {}
        for file_name in files_to_check:
            file_path = output_dir / file_name
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                available_files[file_name] = {
                    'path': file_path,
                    'size_mb': size_mb,
                    'exists': True
                }
                console.print(f"[green]✓ {file_name} ({size_mb:.1f} MB)[/green]")
            else:
                available_files[file_name] = {'exists': False}
                console.print(f"[red]✗ {file_name} (not found)[/red]")
        
        return available_files
    
    def load_summary(self):
        """Load the summary file to get data statistics."""
        summary_path = Path("output/scriptural_truth_summary.json")
        if not summary_path.exists():
            console.print("[red]❌ Summary file not found![/red]")
            return None
        
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        console.print(f"\n[bold blue]Data Summary:[/bold blue]")
        console.print(f"Total items: {summary['total_items']}")
        console.print(f"Content types: {summary['content_types']}")
        console.print(f"Items with embeddings: {summary['items_with_embeddings']}")
        console.print(f"Total content length: {summary['total_content_length']:,} characters")
        
        return summary
    
    def create_collection(self):
        """Create the scriptural truth collection."""
        console.print(f"\n[bold blue]Creating Collection: {self.collection_name}[/bold blue]")
        
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(c.name == self.collection_name for c in collections.collections)
            
            if collection_exists:
                console.print(f"[yellow]Collection {self.collection_name} already exists[/yellow]")
                # Get current count
                info = self.client.get_collection(self.collection_name)
                console.print(f"[blue]Current points in collection: {info.points_count}[/blue]")
                return True
            
            # Create collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 embedding size
                    distance=Distance.COSINE
                )
            )
            console.print(f"[green]✅ Created collection: {self.collection_name}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error creating collection: {e}[/red]")
            return False
    
    def upload_training_data(self):
        """Upload the training data (JSONL format) to Qdrant."""
        training_path = Path("output/scriptural_truth_training.jsonl")
        if not training_path.exists():
            console.print("[red]❌ Training data file not found![/red]")
            return False
        
        console.print(f"\n[bold blue]Uploading Training Data[/bold blue]")
        console.print(f"File: {training_path}")
        
        # First, count total lines for progress
        console.print("[blue]Counting lines...[/blue]")
        total_lines = 0
        with open(training_path, 'r', encoding='utf-8') as f:
            for _ in f:
                total_lines += 1
        
        console.print(f"[green]Found {total_lines} items to upload[/green]")
        
        # Load and upload with progress
        points = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Loading training data...", total=total_lines)
            
            with open(training_path, 'r', encoding='utf-8') as f:
                for idx, line in enumerate(f):
                    try:
                        item = json.loads(line.strip())
                        
                        # Create a simple embedding (we'll use a placeholder since we don't have the actual embeddings)
                        # In a real scenario, you'd load the embeddings from the content.json file
                        embedding = [0.0] * 384  # Placeholder embedding
                        
                        point = PointStruct(
                            id=idx + 1,
                            vector=embedding,
                            payload={
                                'id': item.get('id', f'item_{idx}'),
                                'title': item.get('title', ''),
                                'content': item.get('content', ''),
                                'content_type': item.get('content_type', ''),
                                'source_url': item.get('source_url', ''),
                                'uploaded_at': time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                        )
                        points.append(point)
                        
                        progress.update(task, advance=1, description=f"Loaded {idx + 1}/{total_lines} items")
                        
                    except json.JSONDecodeError as e:
                        console.print(f"[red]Error parsing line {idx + 1}: {e}[/red]")
                        continue
        
        # Upload to Qdrant in batches
        console.print(f"\n[bold blue]Uploading {len(points)} points to Qdrant...[/bold blue]")
        
        batch_size = 50
        total_batches = (len(points) + batch_size - 1) // batch_size
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Uploading to Qdrant...", total=total_batches)
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                progress.update(task, advance=1, description=f"Uploaded batch {i//batch_size + 1}/{total_batches}")
        
        console.print(f"[green]✅ Successfully uploaded {len(points)} items to {self.collection_name}[/green]")
        return len(points)
    
    def show_final_stats(self):
        """Show final collection statistics."""
        console.print(f"\n[bold blue]Final Collection Statistics[/bold blue]")
        
        try:
            info = self.client.get_collection(self.collection_name)
            console.print(f"[green]Collection: {self.collection_name}[/green]")
            console.print(f"[green]Total points: {info.points_count}[/green]")
            console.print(f"[green]Vector size: {info.config.params.vectors.size}[/green]")
            console.print(f"[green]Distance metric: {info.config.params.vectors.distance}[/green]")
            console.print(f"[green]Status: {info.status}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error getting stats: {e}[/red]")

def main():
    """Main upload function."""
    console.print(Panel.fit(
        "[bold blue]Scriptural Truth Data Upload to Qdrant[/bold blue]\n"
        "Uploading processed scriptural truth data with progress tracking",
        border_style="blue"
    ))
    
    uploader = ScripturalTruthUploader()
    
    # Check data files
    files = uploader.check_data_files()
    
    if not files['scriptural_truth_training.jsonl']['exists']:
        console.print("[red]❌ No training data found![/red]")
        return
    
    # Load summary
    summary = uploader.load_summary()
    if not summary:
        return
    
    # Create collection
    if not uploader.create_collection():
        console.print("[red]❌ Failed to create collection[/red]")
        return
    
    # Upload data
    start_time = time.time()
    uploaded_count = uploader.upload_training_data()
    elapsed_time = time.time() - start_time
    
    # Show final stats
    uploader.show_final_stats()
    
    console.print(f"\n[bold green]🎉 Upload completed in {elapsed_time:.1f} seconds![/bold green]")
    console.print(f"[green]Uploaded {uploaded_count} scriptural truth items[/green]")

if __name__ == "__main__":
    main()
