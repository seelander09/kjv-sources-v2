#!/usr/bin/env python3
"""
Geographical Directional Pattern Search across ALL 5 books of the Torah
"""

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table

console = Console()

def search_torah_geographical_patterns():
    """Search for geographical directional patterns across all Torah books."""
    console.print("[bold blue]Torah Geographical Directional Pattern Search[/bold blue]")
    console.print("Searching across ALL 5 books: Genesis, Exodus, Leviticus, Numbers, Deuteronomy\n")
    
    # Initialize clients
    client = QdrantClient(path='qdrant_data')
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # All Torah collections
    collections = [
        'kjv_genesis_verses',
        'kjv_exodus_verses', 
        'kjv_leviticus_verses',
        'kjv_numbers_verses',
        'kjv_deuteronomy_verses'
    ]
    
    # Geographical search patterns
    patterns = [
        "north south east west directions",
        "mount sinai directions",
        "jordan river directions",
        "red sea directions", 
        "canaan land directions",
        "egypt directions",
        "wilderness journey directions",
        "promised land directions",
        "boundaries territories directions",
        "land inheritance directions"
    ]
    
    all_results = []
    
    for pattern in patterns:
        console.print(f"[blue]Searching: {pattern}[/blue]")
        query_embedding = model.encode([pattern])[0].tolist()
        
        for collection_name in collections:
            try:
                search_results = client.query_points(
                    collection_name=collection_name,
                    query=query_embedding,
                    limit=10,
                    score_threshold=0.3,
                    with_payload=True
                )
                
                for result in search_results.points:
                    payload = result.payload
                    verse_data = {
                        'score': result.score,
                        'reference': f"{payload.get('book', 'Unknown')} {payload.get('chapter', '?')}:{payload.get('verse', '?')}",
                        'source': payload.get('source', 'Unknown'),
                        'text': payload.get('text', '')[:150] + '...' if len(payload.get('text', '')) > 150 else payload.get('text', ''),
                        'full_text': payload.get('text', ''),
                        'pattern': pattern,
                        'collection': collection_name
                    }
                    all_results.append(verse_data)
                    
            except Exception as e:
                console.print(f"[red]Error searching {collection_name}: {e}[/red]")
    
    # Sort by score
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Display results
    console.print(f"\n[bold green]Found {len(all_results)} geographical directional patterns across the Torah![/bold green]\n")
    
    # Create results table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Score", style="dim", width=6)
    table.add_column("Reference", style="cyan", width=12)
    table.add_column("Source", style="yellow", width=6)
    table.add_column("Book", style="blue", width=8)
    table.add_column("Verse Text", style="white", width=60)
    
    for result in all_results[:20]:  # Show top 20
        book = result['collection'].replace('kjv_', '').replace('_verses', '').title()
        table.add_row(
            f"{result['score']:.3f}",
            result['reference'],
            result['source'],
            book,
            result['text']
        )
    
    console.print(table)
    
    # Analysis by book
    console.print(f"\n[bold blue]Results by Book:[/bold blue]")
    book_counts = {}
    for result in all_results:
        book = result['collection'].replace('kjv_', '').replace('_verses', '').title()
        book_counts[book] = book_counts.get(book, 0) + 1
    
    for book, count in sorted(book_counts.items()):
        console.print(f"[green]{book}: {count} verses[/green]")
    
    # Analysis by source
    console.print(f"\n[bold blue]Results by Documentary Hypothesis Source:[/bold blue]")
    source_counts = {}
    for result in all_results:
        source = result['source']
        source_counts[source] = source_counts.get(source, 0) + 1
    
    for source, count in sorted(source_counts.items()):
        console.print(f"[yellow]{source}: {count} verses[/yellow]")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"torah_geographical_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[green]Results saved to: {filename}[/green]")
    console.print(f"[bold green]🎉 Search completed! Found geographical patterns across the entire Torah![/bold green]")

if __name__ == "__main__":
    search_torah_geographical_patterns()
