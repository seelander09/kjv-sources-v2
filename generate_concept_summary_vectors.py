#!/usr/bin/env python3
"""
Generate Per-Concept Summary Vectors and Similarity Matrix
=========================================================

Creates summary vectors for each "Hidden/Lost Testament" concept from the
retrieved results and computes a cross-concept similarity matrix.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

console = Console()

def load_probe_results(filename: str) -> Dict[str, Any]:
    """Load the vector probe results."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_text_for_concept(concept_results: List[Dict[str, Any]]) -> str:
    """Extract and combine all text snippets for a concept."""
    texts = []
    for result in concept_results:
        snippet = result.get('snippet', '')
        reference = result.get('reference', '')
        if snippet and reference:
            texts.append(f"{reference}: {snippet}")
    return ' '.join(texts)

def create_summary_vectors(results: Dict[str, Any], model: SentenceTransformer) -> Dict[str, np.ndarray]:
    """Create summary vectors for each concept."""
    console.print("[bold blue]Creating summary vectors for each concept...[/bold blue]")
    
    summary_vectors = {}
    concept_results = results.get('results', {})
    
    for concept, concept_data in concept_results.items():
        if not concept_data:  # Skip empty concepts
            console.print(f"[yellow]Skipping {concept} - no results[/yellow]")
            continue
            
        # Extract all text for this concept
        combined_text = extract_text_for_concept(concept_data)
        
        if not combined_text.strip():
            console.print(f"[yellow]Skipping {concept} - no text content[/yellow]")
            continue
        
        # Create summary vector
        summary_vector = model.encode([combined_text])[0]
        summary_vectors[concept] = summary_vector
        
        console.print(f"[green]✓ {concept}: Vector shape {summary_vector.shape}[/green]")
    
    return summary_vectors

def compute_similarity_matrix(summary_vectors: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
    """Compute cosine similarity matrix between all concept vectors."""
    console.print("\n[bold blue]Computing similarity matrix...[/bold blue]")
    
    concepts = list(summary_vectors.keys())
    similarity_matrix = {}
    
    for i, concept1 in enumerate(concepts):
        similarity_matrix[concept1] = {}
        vec1 = summary_vectors[concept1]
        
        for j, concept2 in enumerate(concepts):
            vec2 = summary_vectors[concept2]
            
            # Compute cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            similarity_matrix[concept1][concept2] = float(similarity)
    
    return similarity_matrix

def find_most_similar_pairs(similarity_matrix: Dict[str, Dict[str, float]]) -> List[Tuple[str, str, float]]:
    """Find the most similar concept pairs (excluding self-similarity)."""
    pairs = []
    concepts = list(similarity_matrix.keys())
    
    for i, concept1 in enumerate(concepts):
        for j, concept2 in enumerate(concepts):
            if i < j:  # Avoid duplicates and self-similarity
                similarity = similarity_matrix[concept1][concept2]
                pairs.append((concept1, concept2, similarity))
    
    # Sort by similarity (descending)
    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs

def display_results(summary_vectors: Dict[str, np.ndarray], 
                   similarity_matrix: Dict[str, Dict[str, float]],
                   most_similar_pairs: List[Tuple[str, str, float]]):
    """Display the results in formatted tables."""
    
    # Summary vectors info
    console.print(f"\n[bold green]Summary Vectors Created: {len(summary_vectors)}[/bold green]")
    for concept, vector in summary_vectors.items():
        console.print(f"[blue]• {concept}: {vector.shape[0]} dimensions[/blue]")
    
    # Similarity matrix table
    concepts = list(similarity_matrix.keys())
    table = Table(title="Concept Similarity Matrix (Cosine Similarity)")
    table.add_column("Concept", style="cyan", no_wrap=True)
    
    for concept in concepts:
        table.add_column(concept[:15] + "...", style="white", justify="right")
    
    for concept1 in concepts:
        row = [concept1[:20] + "..."]
        for concept2 in concepts:
            similarity = similarity_matrix[concept1][concept2]
            if concept1 == concept2:
                row.append("1.000")
            else:
                row.append(f"{similarity:.3f}")
        table.add_row(*row)
    
    console.print(table)
    
    # Most similar pairs
    console.print(f"\n[bold cyan]Most Similar Concept Pairs:[/bold cyan]")
    for i, (concept1, concept2, similarity) in enumerate(most_similar_pairs[:5], 1):
        console.print(f"[green]{i}. {concept1} ↔ {concept2}: {similarity:.3f}[/green]")
    
    # Least similar pairs
    console.print(f"\n[bold cyan]Least Similar Concept Pairs:[/bold cyan]")
    for i, (concept1, concept2, similarity) in enumerate(most_similar_pairs[-3:], 1):
        console.print(f"[yellow]{i}. {concept1} ↔ {concept2}: {similarity:.3f}[/yellow]")

def save_results(summary_vectors: Dict[str, np.ndarray], 
                similarity_matrix: Dict[str, Dict[str, float]],
                most_similar_pairs: List[Tuple[str, str, float]],
                original_results: Dict[str, Any]):
    """Save all results to a comprehensive JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"concept_summary_vectors_{timestamp}.json"
    
    # Convert numpy arrays to lists for JSON serialization
    summary_vectors_serializable = {
        concept: vector.tolist() 
        for concept, vector in summary_vectors.items()
    }
    
    results_data = {
        "timestamp": timestamp,
        "analysis_type": "concept_summary_vectors_and_similarity",
        "model_used": "all-MiniLM-L6-v2",
        "summary_vectors": summary_vectors_serializable,
        "similarity_matrix": similarity_matrix,
        "most_similar_pairs": [
            {"concept1": pair[0], "concept2": pair[1], "similarity": pair[2]}
            for pair in most_similar_pairs
        ],
        "statistics": {
            "total_concepts": len(summary_vectors),
            "vector_dimensions": summary_vectors[list(summary_vectors.keys())[0]].shape[0] if summary_vectors else 0,
            "highest_similarity": most_similar_pairs[0][2] if most_similar_pairs else 0,
            "lowest_similarity": most_similar_pairs[-1][2] if most_similar_pairs else 0,
            "average_similarity": np.mean([pair[2] for pair in most_similar_pairs]) if most_similar_pairs else 0
        },
        "original_probe_results": original_results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    
    console.print(f"[green]✅ Results saved to {filename}[/green]")
    return filename

def main():
    """Main function."""
    console.print(Panel.fit(
        "[bold blue]Concept Summary Vectors and Similarity Analysis[/bold blue]\n"
        "Generating summary vectors and similarity matrix for Hidden/Lost Testament concepts",
        border_style="blue"
    ))
    
    # Find the most recent probe results file
    probe_files = list(Path('.').glob('hidden_testament_vector_probe_*.json'))
    if not probe_files:
        console.print("[red]❌ No vector probe results found![/red]")
        return
    
    latest_file = max(probe_files, key=lambda f: f.stat().st_mtime)
    console.print(f"[blue]Loading results from: {latest_file}[/blue]")
    
    # Load results
    results = load_probe_results(str(latest_file))
    
    # Initialize model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Create summary vectors
    summary_vectors = create_summary_vectors(results, model)
    
    if not summary_vectors:
        console.print("[red]❌ No summary vectors created![/red]")
        return
    
    # Compute similarity matrix
    similarity_matrix = compute_similarity_matrix(summary_vectors)
    
    # Find most similar pairs
    most_similar_pairs = find_most_similar_pairs(similarity_matrix)
    
    # Display results
    display_results(summary_vectors, similarity_matrix, most_similar_pairs)
    
    # Save results
    filename = save_results(summary_vectors, similarity_matrix, most_similar_pairs, results)
    
    console.print(f"\n[bold green]🎉 Analysis complete![/bold green]")
    console.print(f"[green]Created {len(summary_vectors)} summary vectors[/green]")
    console.print(f"[green]Computed similarity matrix for {len(summary_vectors)} concepts[/green]")
    console.print(f"[green]Results saved to {filename}[/green]")

if __name__ == "__main__":
    main()
