#!/usr/bin/env python3
"""
Upload each book to its own collection
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import pandas as pd
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def upload_book_to_individual_collection(book_name, csv_path):
    """Upload a book to its own collection."""
    try:
        console.print(f"[blue]📖 Uploading {book_name} to collection 'kjv_{book_name.lower()}_verses'...[/blue]")
        
        # Initialize clients
        client = QdrantClient(path='qdrant_data')
        model = SentenceTransformer('all-MiniLM-L6-v2')
        collection_name = f"kjv_{book_name.lower()}_verses"
        
        # Create collection
        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=384,
                    distance=Distance.COSINE
                )
            )
            console.print(f"[green]✅ Created collection: {collection_name}[/green]")
        except Exception as e:
            console.print(f"[yellow]Collection {collection_name} may already exist[/yellow]")
        
        # Load data
        df = pd.read_csv(csv_path)
        console.print(f"[blue]📊 Loaded {len(df)} verses from {book_name}[/blue]")
        
        # Prepare points
        points = []
        for idx, row in df.iterrows():
            try:
                # Create embedding
                text = row.get('full_text', '')
                if text and pd.notna(text):
                    embedding = model.encode([text])[0].tolist()
                    
                    # Create point
                    point = PointStruct(
                        id=idx + 1,  # Use simple integer ID
                        vector=embedding,
                        payload={
                            'book': book_name,
                            'chapter': row.get('chapter', 0),
                            'verse': row.get('verse', 0),
                            'text': text,
                            'source': row.get('primary_source', 'Unknown'),
                            'reference': f"{book_name} {row.get('chapter', 0)}:{row.get('verse', 0)}"
                        }
                    )
                    points.append(point)
            except Exception as e:
                console.print(f"[red]Error processing verse: {e}[/red]")
                continue
        
        # Upload in batches
        batch_size = 100
        total_batches = (len(points) + batch_size - 1) // batch_size
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Uploading {book_name}...", total=total_batches)
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                progress.advance(task)
        
        console.print(f"[green]✅ Successfully uploaded {len(points)} verses for {book_name}[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error uploading {book_name}: {e}[/red]")
        return False

def main():
    """Upload all books to individual collections."""
    console.print("[bold blue]Uploading Each Book to Individual Collections[/bold blue]")
    
    books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    successful = []
    failed = []
    
    for book in books:
        csv_path = Path("output") / book / f"{book}.csv"
        
        if csv_path.exists():
            if upload_book_to_individual_collection(book, csv_path):
                successful.append(book)
            else:
                failed.append(book)
        else:
            console.print(f"[red]❌ No data file found for {book}[/red]")
            failed.append(book)
    
    # Summary
    console.print(f"\n[bold]Upload Summary:[/bold]")
    console.print(f"[green]✅ Successful: {len(successful)} books[/green]")
    for book in successful:
        console.print(f"   - {book}")
    
    if failed:
        console.print(f"[red]❌ Failed: {len(failed)} books[/red]")
        for book in failed:
            console.print(f"   - {book}")
    
    # Show collections
    console.print(f"\n[bold]Final Collections:[/bold]")
    try:
        client = QdrantClient(path='qdrant_data')
        collections = client.get_collections()
        for col in collections.collections:
            info = client.get_collection(col.name)
            console.print(f"   - {col.name}: {info.points_count} points")
    except Exception as e:
        console.print(f"[red]Error getting collection info: {e}[/red]")

if __name__ == "__main__":
    main()
