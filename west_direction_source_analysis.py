#!/usr/bin/env python3
"""
Deep Dive Analysis: "West" Direction Usage by Source
===================================================

Analyzes how each source (J, E, P, D, R) uses the direction "west" and creates
summary vectors showing patterns for each source tradition.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import numpy as np

console = Console()

class WestDirectionAnalyzer:
    def __init__(self):
        self.client = QdrantClient(path='qdrant_data')
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collections = [
            "kjv_genesis_verses", "kjv_exodus_verses", "kjv_leviticus_verses", 
            "kjv_numbers_verses", "kjv_deuteronomy_verses"
        ]
        
        # Source color mapping
        self.source_colors = {
            'J': '#000088',  # Navy Blue
            'E': '#008888',  # Teal  
            'P': '#888800',  # Olive Yellow
            'D': '#000000',  # Black
            'R': '#880000'   # Maroon Red
        }
        
        self.source_names = {
            'J': 'Jahwist (Early Narrative)',
            'E': 'Elohist (Northern Narrative)', 
            'P': 'Priestly (Liturgical)',
            'D': 'Deuteronomist (Deuteronomy-focused)',
            'R': 'Redactor (Editorial)'
        }
    
    def search_west_patterns(self) -> List[Dict[str, Any]]:
        """Search for all verses containing 'west' patterns."""
        console.print("[bold blue]Searching for 'west' direction patterns...[/bold blue]")
        
        west_patterns = [
            "west",
            "western", 
            "westward",
            "west side",
            "westward side",
            "toward the west",
            "from the west",
            "going west",
            "facing west"
        ]
        
        all_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("Searching collections...", total=len(self.collections))
            
            for collection in self.collections:
                try:
                    for pattern in west_patterns:
                        results = self.client.query_points(
                            collection_name=collection,
                            query=self.model.encode([pattern])[0].tolist(),
                            limit=50,
                            score_threshold=0.3,
                            with_payload=True
                        )
                        
                        for result in results.points:
                            payload = result.payload
                            all_results.append({
                                'collection': collection,
                                'pattern': pattern,
                                'score': result.score,
                                'book': payload.get('book', 'Unknown'),
                                'chapter': payload.get('chapter', 'Unknown'),
                                'verse': payload.get('verse', 'Unknown'),
                                'source': payload.get('source', 'Unknown'),
                                'text': payload.get('text', ''),
                                'full_text': payload.get('full_text', '')
                            })
                    
                    progress.update(task, advance=1, description=f"Searched {collection}")
                    
                except Exception as e:
                    console.print(f"[red]Error searching {collection}: {e}[/red]")
                    progress.update(task, advance=1)
        
        console.print(f"[green]Found {len(all_results)} west-related verses[/green]")
        return all_results
    
    def analyze_by_source(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze west usage patterns by source."""
        console.print("\n[bold blue]Analyzing patterns by source...[/bold blue]")
        
        source_data = defaultdict(list)
        
        # Group by source
        for result in results:
            source = result['source']
            if source in self.source_colors:
                source_data[source].append(result)
        
        source_analysis = {}
        
        for source, verses in source_data.items():
            console.print(f"\n[bold cyan]Analyzing {self.source_names[source]} ({source})[/bold cyan]")
            console.print(f"Found {len(verses)} verses")
            
            # Extract all text for this source
            all_texts = [v['text'] for v in verses if v['text']]
            
            if not all_texts:
                continue
            
            # Create summary vector
            summary_vector = self.model.encode([' '.join(all_texts)])[0]
            
            # Analyze patterns
            books = Counter([v['book'] for v in verses])
            chapters = Counter([f"{v['book']} {v['chapter']}" for v in verses])
            
            # Extract west-related phrases
            west_phrases = []
            for verse in verses:
                text = verse['text'].lower()
                if 'west' in text:
                    # Extract context around 'west'
                    words = text.split()
                    for i, word in enumerate(words):
                        if 'west' in word:
                            start = max(0, i-3)
                            end = min(len(words), i+4)
                            context = ' '.join(words[start:end])
                            west_phrases.append(context)
            
            # Find common west contexts
            west_contexts = Counter(west_phrases)
            
            source_analysis[source] = {
                'name': self.source_names[source],
                'verse_count': len(verses),
                'summary_vector': summary_vector.tolist(),
                'books': dict(books),
                'chapters': dict(chapters),
                'west_contexts': dict(west_contexts.most_common(10)),
                'verses': verses,
                'sample_texts': all_texts[:5]  # First 5 texts
            }
        
        return source_analysis
    
    def create_source_summary_vectors(self, source_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, np.ndarray]:
        """Create summary vectors for each source."""
        console.print("\n[bold blue]Creating source summary vectors...[/bold blue]")
        
        summary_vectors = {}
        
        for source, data in source_analysis.items():
            # Use the summary vector we already created
            summary_vectors[source] = np.array(data['summary_vector'])
            console.print(f"[green]✓ {source}: Vector shape {summary_vectors[source].shape}[/green]")
        
        return summary_vectors
    
    def compare_source_vectors(self, summary_vectors: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
        """Compare similarity between source vectors."""
        console.print("\n[bold blue]Comparing source vector similarities...[/bold blue]")
        
        similarities = {}
        sources = list(summary_vectors.keys())
        
        for i, source1 in enumerate(sources):
            similarities[source1] = {}
            for j, source2 in enumerate(sources):
                if i != j:
                    # Calculate cosine similarity
                    vec1 = summary_vectors[source1]
                    vec2 = summary_vectors[source2]
                    
                    similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                    similarities[source1][source2] = float(similarity)
        
        return similarities
    
    def display_results(self, source_analysis: Dict[str, Dict[str, Any]], 
                       similarities: Dict[str, Dict[str, float]]):
        """Display comprehensive results."""
        
        # Create main results table
        table = Table(title="West Direction Usage by Source")
        table.add_column("Source", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Verses", style="green", justify="right")
        table.add_column("Books", style="yellow")
        table.add_column("Top Context", style="magenta")
        
        for source, data in source_analysis.items():
            books_str = ", ".join([f"{book}({count})" for book, count in list(data['books'].items())[:3]])
            top_context = list(data['west_contexts'].keys())[0] if data['west_contexts'] else "None"
            
            table.add_row(
                source,
                data['name'],
                str(data['verse_count']),
                books_str,
                top_context[:50] + "..." if len(top_context) > 50 else top_context
            )
        
        console.print(table)
        
        # Create similarity matrix
        console.print("\n[bold blue]Source Vector Similarities (West Usage)[/bold blue]")
        sim_table = Table(title="Cosine Similarity Matrix")
        sim_table.add_column("Source", style="cyan")
        
        sources = list(source_analysis.keys())
        for source in sources:
            sim_table.add_column(source, style="white", justify="right")
        
        for source1 in sources:
            row = [source1]
            for source2 in sources:
                if source1 == source2:
                    row.append("1.000")
                else:
                    sim = similarities[source1].get(source2, 0.0)
                    row.append(f"{sim:.3f}")
            sim_table.add_row(*row)
        
        console.print(sim_table)
        
        # Show detailed analysis for each source
        for source, data in source_analysis.items():
            console.print(f"\n[bold cyan]{self.source_names[source]} ({source}) - Detailed Analysis[/bold cyan]")
            
            # Books breakdown
            books_table = Table(title=f"Books in {source}")
            books_table.add_column("Book", style="cyan")
            books_table.add_column("Count", style="green", justify="right")
            
            for book, count in data['books'].items():
                books_table.add_row(book, str(count))
            
            console.print(books_table)
            
            # Top west contexts
            if data['west_contexts']:
                context_table = Table(title=f"Top West Contexts in {source}")
                context_table.add_column("Context", style="white")
                context_table.add_column("Count", style="green", justify="right")
                
                for context, count in list(data['west_contexts'].items())[:5]:
                    context_table.add_row(context, str(count))
                
                console.print(context_table)
            
            # Sample verses
            console.print(f"\n[bold yellow]Sample Verses from {source}:[/bold yellow]")
            for i, verse in enumerate(data['verses'][:3]):
                console.print(f"[blue]{i+1}. {verse['book']} {verse['chapter']}:{verse['verse']}[/blue]")
                console.print(f"   {verse['text'][:100]}...")
                console.print()
    
    def save_results(self, source_analysis: Dict[str, Dict[str, Any]], 
                    similarities: Dict[str, Dict[str, float]]):
        """Save results to JSON file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"west_direction_source_analysis_{timestamp}.json"
        
        # Prepare data for JSON serialization
        results_data = {
            'timestamp': timestamp,
            'analysis_type': 'west_direction_by_source',
            'source_analysis': {},
            'similarities': similarities,
            'summary': {
                'total_sources': len(source_analysis),
                'total_verses': sum(data['verse_count'] for data in source_analysis.values())
            }
        }
        
        # Convert numpy arrays to lists for JSON
        for source, data in source_analysis.items():
            results_data['source_analysis'][source] = {
                'name': data['name'],
                'verse_count': data['verse_count'],
                'summary_vector': data['summary_vector'],
                'books': data['books'],
                'chapters': data['chapters'],
                'west_contexts': data['west_contexts'],
                'sample_texts': data['sample_texts']
            }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✅ Results saved to {filename}[/green]")
        return filename

def main():
    """Main analysis function."""
    console.print(Panel.fit(
        "[bold blue]West Direction Source Analysis[/bold blue]\n"
        "Deep dive into how each source uses 'west' direction",
        border_style="blue"
    ))
    
    analyzer = WestDirectionAnalyzer()
    
    # Search for west patterns
    results = analyzer.search_west_patterns()
    
    if not results:
        console.print("[red]❌ No west patterns found![/red]")
        return
    
    # Analyze by source
    source_analysis = analyzer.analyze_by_source(results)
    
    if not source_analysis:
        console.print("[red]❌ No source analysis possible![/red]")
        return
    
    # Create summary vectors
    summary_vectors = analyzer.create_source_summary_vectors(source_analysis)
    
    # Compare vectors
    similarities = analyzer.compare_source_vectors(summary_vectors)
    
    # Display results
    analyzer.display_results(source_analysis, similarities)
    
    # Save results
    filename = analyzer.save_results(source_analysis, similarities)
    
    console.print(f"\n[bold green]🎉 Analysis complete![/bold green]")
    console.print(f"[green]Analyzed {len(source_analysis)} sources[/green]")
    console.print(f"[green]Results saved to {filename}[/green]")

if __name__ == "__main__":
    main()
