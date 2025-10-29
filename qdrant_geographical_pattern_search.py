#!/usr/bin/env python3
"""
Qdrant Semantic Search for Geographical Directional Patterns
Searches for verses containing directional references (north, south, east, west) 
combined with geographical locations (Mount Sinai, Jordan River, etc.)
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class GeographicalPatternSearcher:
    def __init__(self, qdrant_path: str = "qdrant_data"):
        """Initialize the geographical pattern searcher."""
        self.client = QdrantClient(path=qdrant_path)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # Search all biblical collections (using the local Qdrant instance)
        self.collections = ["kjv_sources"]
        
    def get_geographical_search_patterns(self) -> List[str]:
        """Define geographical directional search patterns."""
        patterns = [
            # Directional + Location patterns
            "north south east west geographical locations directions",
            "mount sinai in the east west north south",
            "jordan river toward the north south east west",
            "promised land directions north south east west",
            "red sea west east north south directions",
            "canaan land directions geographical locations",
            "wilderness journey directions north south east west",
            "boundaries territories north south east west",
            "land flowing milk honey directions",
            "egypt toward the north south east west",
            "babylon directions geographical locations",
            "jerusalem directions north south east west",
            "temple mount directions geographical",
            "olive mount directions locations",
            "zion directions geographical references",
            "galilee directions north south east west",
            "samaria directions geographical locations",
            "judea directions north south east west",
            "transjordan directions geographical",
            "mediterranean sea directions west",
            "dead sea directions geographical",
            "sea of galilee directions north",
            "mount hermon directions north",
            "mount carmel directions west",
            "mount tabor directions geographical",
            "valley of jezreel directions",
            "jordan valley directions",
            "negev desert directions south",
            "araba valley directions",
            "shephelah directions west",
            "judean hills directions",
            "samarian hills directions",
            "galilean hills directions",
            "coastal plain directions west",
            "esdraelon plain directions",
            "hazor directions north",
            "megiddo directions geographical",
            "bethlehem directions south",
            "hebron directions south",
            "beersheba directions south",
            "dan directions north",
            "beersheba to dan directions",
            "from dan to beersheba",
            "boundaries of the land",
            "territorial boundaries directions",
            "land inheritance directions",
            "tribal territories directions",
            "geographical boundaries north south east west",
            # Specific Deuteronomy geographical patterns
            "mount hermon directions north",
            "mount seir directions south", 
            "mount paran directions",
            "mount sinai directions",
            "mount horeb directions",
            "mount ebal directions",
            "mount gerizim directions",
            "valley of shittim directions",
            "valley of achor directions",
            "brook of egypt directions",
            "river euphrates directions",
            "great sea directions west",
            "salt sea directions",
            "sea of arabah directions",
            "land of gilead directions",
            "land of bashan directions",
            "land of ammon directions",
            "land of moab directions",
            "land of edom directions",
            "land of canaan directions",
            "land of promise directions",
            "from dan to beersheba",
            "from the wilderness to the great sea",
            "from the river to the sea",
            "borders boundaries territories",
            "coast borders boundaries",
            "inheritance land division",
            "tribal allotment boundaries",
            "possession land territory"
        ]
        return patterns
    
    def search_geographical_patterns(self, limit: int = 50, score_threshold: float = 0.25) -> List[Dict[str, Any]]:
        """Search for geographical directional patterns across all biblical collections."""
        patterns = self.get_geographical_search_patterns()
        all_results = []
        
        total_tasks = len(patterns) * len(self.collections)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Searching geographical patterns across all collections...", total=total_tasks)
            
            for pattern in patterns:
                try:
                    # Generate embedding for the search pattern
                    query_embedding = self.model.encode([pattern])[0].tolist()
                    
                    # Search in each collection
                    for collection_name in self.collections:
                        try:
                            search_results = self.client.query_points(
                                collection_name=collection_name,
                                query=query_embedding,
                                limit=limit,
                                score_threshold=score_threshold,
                                with_payload=True
                            ).points
                            
                            # Process results
                            for result in search_results:
                                payload = result.payload
                                verse_data = {
                                    'similarity_score': result.score,
                                    'verse_reference': f"{payload.get('book', 'Unknown')} {payload.get('chapter', '?')}:{payload.get('verse', '?')}",
                                    'source_attribution': payload.get('source', 'Unknown'),
                                    'verse_text': payload.get('text', '')[:100] + '...' if len(payload.get('text', '')) > 100 else payload.get('text', ''),
                                    'full_verse_text': payload.get('text', ''),
                                    'search_pattern': pattern,
                                    'collection': collection_name,
                                    'theological_theme': self._identify_theological_theme(payload.get('text', ''))
                                }
                                all_results.append(verse_data)
                            
                        except Exception as e:
                            console.print(f"[red]Error searching collection '{collection_name}' with pattern '{pattern}': {e}[/red]")
                        
                        progress.advance(task)
                    
                except Exception as e:
                    console.print(f"[red]Error processing pattern '{pattern}': {e}[/red]")
                    progress.advance(task)
                    continue
        
        # Remove duplicates and sort by similarity score
        unique_results = self._remove_duplicates(all_results)
        unique_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return unique_results[:limit]
    
    def _identify_theological_theme(self, verse_text: str) -> str:
        """Identify theological theme based on verse content."""
        text_lower = verse_text.lower()
        
        if any(word in text_lower for word in ['covenant', 'promise', 'oath']):
            return "Covenant"
        elif any(word in text_lower for word in ['land', 'territory', 'boundary', 'inheritance']):
            return "Land Promise"
        elif any(word in text_lower for word in ['journey', 'travel', 'way', 'path']):
            return "Journey/Exodus"
        elif any(word in text_lower for word in ['temple', 'sanctuary', 'holy', 'sacred']):
            return "Sacred Space"
        elif any(word in text_lower for word in ['battle', 'war', 'conquest', 'victory']):
            return "Conquest"
        elif any(word in text_lower for word in ['blessing', 'curse', 'prosperity']):
            return "Blessing/Curse"
        elif any(word in text_lower for word in ['law', 'commandment', 'statute', 'ordinance']):
            return "Law"
        else:
            return "General"
    
    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on verse reference."""
        seen = set()
        unique_results = []
        
        for result in results:
            verse_ref = result['verse_reference']
            if verse_ref not in seen:
                seen.add(verse_ref)
                unique_results.append(result)
        
        return unique_results
    
    def analyze_results_by_source(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze results by Documentary Hypothesis source attribution."""
        source_counts = {}
        source_themes = {}
        
        for result in results:
            source = result['source_attribution']
            theme = result['theological_theme']
            
            # Count by source
            source_counts[source] = source_counts.get(source, 0) + 1
            
            # Track themes by source
            if source not in source_themes:
                source_themes[source] = {}
            source_themes[source][theme] = source_themes[source].get(theme, 0) + 1
        
        return {
            'source_counts': source_counts,
            'source_themes': source_themes,
            'total_results': len(results)
        }
    
    def display_results(self, results: List[Dict[str, Any]], analysis: Dict[str, Any]):
        """Display search results in a formatted table."""
        console.print("\n[bold blue]Geographical Directional Pattern Search Results[/bold blue]")
        console.print(f"[green]Found {len(results)} verses with geographical directional patterns[/green]\n")
        
        # Create results table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Score", style="dim", width=6)
        table.add_column("Reference", style="cyan", width=12)
        table.add_column("Source", style="yellow", width=6)
        table.add_column("Collection", style="blue", width=15)
        table.add_column("Theme", style="green", width=12)
        table.add_column("Verse Text", style="white", width=50)
        
        for result in results:
            table.add_row(
                f"{result['similarity_score']:.3f}",
                result['verse_reference'],
                result['source_attribution'],
                result.get('collection', 'Unknown'),
                result['theological_theme'],
                result['verse_text']
            )
        
        console.print(table)
        
        # Display analysis
        console.print("\n[bold blue]Analysis by Documentary Hypothesis Source:[/bold blue]")
        for source, count in analysis['source_counts'].items():
            percentage = (count / analysis['total_results']) * 100
            console.print(f"[yellow]{source}[/yellow]: {count} verses ({percentage:.1f}%)")
            
            # Show themes for this source
            themes = analysis['source_themes'].get(source, {})
            theme_str = ", ".join([f"{theme}({count})" for theme, count in themes.items()])
            console.print(f"  Themes: {theme_str}")
    
    def save_results(self, results: List[Dict[str, Any]], analysis: Dict[str, Any]):
        """Save results to timestamped JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qdrant_geographical_search_results_{timestamp}.json"
        
        output_data = {
            'search_timestamp': datetime.now().isoformat(),
            'search_type': 'geographical_directional_patterns',
            'total_results': len(results),
            'analysis': analysis,
            'results': results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"\n[green]Results saved to: {filename}[/green]")
        return filename

def main():
    """Main function to execute geographical pattern search."""
    console.print("[bold blue]KJV Sources - Geographical Directional Pattern Search[/bold blue]")
    console.print("Searching for verses with directional references and geographical locations...\n")
    
    try:
        # Initialize searcher
        searcher = GeographicalPatternSearcher()
        
        # Perform search
        results = searcher.search_geographical_patterns(limit=20, score_threshold=0.3)
        
        if not results:
            console.print("[red]No results found with the specified criteria.[/red]")
            return
        
        # Analyze results
        analysis = searcher.analyze_results_by_source(results)
        
        # Display results
        searcher.display_results(results, analysis)
        
        # Save results
        filename = searcher.save_results(results, analysis)
        
        console.print(f"\n[bold green]Search completed successfully![/bold green]")
        console.print(f"Found {len(results)} verses with geographical directional patterns")
        console.print(f"Results saved to: {filename}")
        
    except Exception as e:
        console.print(f"[red]Error during search: {e}[/red]")
        raise

if __name__ == "__main__":
    main()
