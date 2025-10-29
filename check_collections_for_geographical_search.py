#!/usr/bin/env python3
"""
Diagnostic script to check what collections contain biblical text
and identify the best ones for geographical directional pattern search
"""

from qdrant_client import QdrantClient
from rich.console import Console
from rich.table import Table

console = Console()

def check_collection_contents():
    """Check what's actually in each collection."""
    client = QdrantClient(host="localhost", port=6333)
    
    # Get all collections
    collections = client.get_collections()
    console.print("[bold blue]Available Collections:[/bold blue]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Collection Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Sample Book", style="yellow")
    table.add_column("Sample Text", style="white", width=60)
    
    for col in collections.collections:
        collection_name = col.name
        try:
            # Try to get a sample from the collection
            result = client.query_points(
                collection_name=collection_name,
                query=[0.1] * 384,  # Dummy vector
                limit=1,
                with_payload=True
            )
            
            if result.points:
                payload = result.points[0].payload
                book = payload.get('book', 'Unknown')
                text = payload.get('text', 'No text field')
                status = "✓ Working"
            else:
                book = "Empty"
                text = "No points found"
                status = "Empty"
                
        except Exception as e:
            book = "Error"
            text = str(e)[:60]
            status = "✗ Error"
        
        table.add_row(collection_name, status, book, text)
    
    console.print(table)
    
    # Now let's specifically look for geographical patterns in working collections
    console.print("\n[bold blue]Searching for geographical patterns in working collections:[/bold blue]")
    
    working_collections = []
    for col in collections.collections:
        try:
            result = client.query_points(
                collection_name=col.name,
                query=[0.1] * 384,
                limit=1,
                with_payload=True
            )
            if result.points:
                working_collections.append(col.name)
        except:
            continue
    
    # Search for geographical terms in each working collection
    geographical_terms = ["north", "south", "east", "west", "Jordan", "Sinai", "Canaan", "Egypt"]
    
    for collection_name in working_collections:
        console.print(f"\n[bold green]Checking {collection_name} for geographical terms:[/bold green]")
        
        try:
            # Get collection info
            collection_info = client.get_collection(collection_name)
            total_points = collection_info.points_count
            console.print(f"Total points: {total_points}")
            
            # Search for a few geographical terms
            found_geographical = []
            for term in geographical_terms[:3]:  # Check first 3 terms
                try:
                    # Create a simple search for the term
                    from sentence_transformers import SentenceTransformer
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    query_embedding = model.encode([term])[0].tolist()
                    
                    result = client.query_points(
                        collection_name=collection_name,
                        query=query_embedding,
                        limit=3,
                        score_threshold=0.3,
                        with_payload=True
                    )
                    
                    if result.points:
                        found_geographical.append(term)
                        console.print(f"  Found '{term}': {len(result.points)} results")
                        # Show sample
                        sample = result.points[0]
                        book = sample.payload.get('book', 'Unknown')
                        text = sample.payload.get('text', '')[:80]
                        console.print(f"    Sample: {book} - {text}...")
                        
                except Exception as e:
                    console.print(f"  Error searching for '{term}': {e}")
            
            if found_geographical:
                console.print(f"  [green]✓ Good collection for geographical search[/green]")
            else:
                console.print(f"  [yellow]? No obvious geographical terms found[/yellow]")
                
        except Exception as e:
            console.print(f"  [red]Error checking collection: {e}[/red]")

if __name__ == "__main__":
    check_collection_contents()
