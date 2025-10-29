#!/usr/bin/env python3
"""
Upload Scriptural Truth Data in Small Batches
=============================================

Uploads scriptural truth data in very small batches to avoid memory issues.
Resumes from where it left off.
"""

import json
import time
import gc
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

console = Console()

class SmallBatchUploader:
    def __init__(self):
        self.client = QdrantClient(path='qdrant_data')
        self.collection_name = "scriptural_truth_complete"
        self.batch_size = 10  # Very small batches
        self.resume_file = "upload_progress.json"
        
    def get_current_count(self):
        """Get current number of points in collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except:
            return 0
    
    def save_progress(self, processed_count: int):
        """Save progress to resume later."""
        progress_data = {
            'processed_count': processed_count,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(self.resume_file, 'w') as f:
            json.dump(progress_data, f)
    
    def load_progress(self):
        """Load progress to resume from where we left off."""
        if Path(self.resume_file).exists():
            with open(self.resume_file, 'r') as f:
                return json.load(f)
        return {'processed_count': 0}
    
    def upload_small_batches(self):
        """Upload data in very small batches with memory management."""
        training_path = Path("output/scriptural_truth_training.jsonl")
        if not training_path.exists():
            console.print("[red]❌ Training data file not found![/red]")
            return False
        
        # Load progress
        progress_data = self.load_progress()
        start_from = progress_data['processed_count']
        
        console.print(f"[blue]Resuming from item {start_from}[/blue]")
        
        # Count total lines
        console.print("[blue]Counting total lines...[/blue]")
        total_lines = 0
        with open(training_path, 'r', encoding='utf-8') as f:
            for _ in f:
                total_lines += 1
        
        remaining_items = total_lines - start_from
        console.print(f"[green]Total items: {total_lines}[/green]")
        console.print(f"[green]Already uploaded: {start_from}[/green]")
        console.print(f"[green]Remaining: {remaining_items}[/green]")
        
        if remaining_items <= 0:
            console.print("[green]✅ All items already uploaded![/green]")
            return True
        
        # Upload in small batches
        batch_count = 0
        processed_count = start_from
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Uploading in small batches...", total=remaining_items)
            
            with open(training_path, 'r', encoding='utf-8') as f:
                # Skip already processed items
                for _ in range(start_from):
                    next(f)
                
                batch_points = []
                
                for line_num, line in enumerate(f, start=start_from):
                    try:
                        item = json.loads(line.strip())
                        
                        # Create placeholder embedding (384 dimensions)
                        embedding = [0.0] * 384
                        
                        point = PointStruct(
                            id=line_num + 1,
                            vector=embedding,
                            payload={
                                'id': item.get('id', f'item_{line_num}'),
                                'title': item.get('title', '')[:200],  # Truncate long titles
                                'content': item.get('content', '')[:1000],  # Truncate long content
                                'content_type': item.get('content_type', ''),
                                'source_url': item.get('source_url', ''),
                                'uploaded_at': time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                        )
                        batch_points.append(point)
                        
                        # Upload when batch is full
                        if len(batch_points) >= self.batch_size:
                            try:
                                self.client.upsert(
                                    collection_name=self.collection_name,
                                    points=batch_points
                                )
                                batch_count += 1
                                processed_count += len(batch_points)
                                
                                # Save progress every batch
                                self.save_progress(processed_count)
                                
                                # Clear memory
                                batch_points.clear()
                                gc.collect()
                                
                                progress.update(task, advance=len(batch_points), 
                                             description=f"Uploaded batch {batch_count}, {processed_count}/{total_lines} items")
                                
                            except Exception as e:
                                console.print(f"[red]Error uploading batch {batch_count}: {e}[/red]")
                                # Continue with next batch
                                batch_points.clear()
                                gc.collect()
                                continue
                        
                    except json.JSONDecodeError as e:
                        console.print(f"[red]Error parsing line {line_num + 1}: {e}[/red]")
                        continue
                
                # Upload remaining points
                if batch_points:
                    try:
                        self.client.upsert(
                            collection_name=self.collection_name,
                            points=batch_points
                        )
                        batch_count += 1
                        processed_count += len(batch_points)
                        self.save_progress(processed_count)
                        
                        progress.update(task, advance=len(batch_points),
                                     description=f"Final batch uploaded, {processed_count}/{total_lines} items")
                        
                    except Exception as e:
                        console.print(f"[red]Error uploading final batch: {e}[/red]")
        
        console.print(f"[green]✅ Upload completed! Processed {processed_count} items in {batch_count} batches[/green]")
        return True
    
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
    """Main upload function with small batch processing."""
    console.print(Panel.fit(
        "[bold blue]Scriptural Truth Small Batch Upload[/bold blue]\n"
        "Uploading in very small batches to avoid memory issues",
        border_style="blue"
    ))
    
    uploader = SmallBatchUploader()
    
    # Show current status
    current_count = uploader.get_current_count()
    console.print(f"[blue]Current items in collection: {current_count}[/blue]")
    
    # Upload in small batches
    start_time = time.time()
    success = uploader.upload_small_batches()
    elapsed_time = time.time() - start_time
    
    if success:
        # Show final stats
        uploader.show_final_stats()
        
        console.print(f"\n[bold green]🎉 Upload completed in {elapsed_time:.1f} seconds![/bold green]")
        
        # Clean up progress file
        if Path(uploader.resume_file).exists():
            Path(uploader.resume_file).unlink()
            console.print("[blue]Cleaned up progress file[/blue]")
    else:
        console.print("[red]❌ Upload failed[/red]")

if __name__ == "__main__":
    main()
