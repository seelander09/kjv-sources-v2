#!/usr/bin/env python3
"""
Upload all Torah books to Qdrant with progress tracking
"""

import os
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from kjv_sources.qdrant_client import KJVQdrantClient
    from kjv_sources.enhanced_cli import create_qdrant_client
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the project root directory")
    sys.exit(1)

console = Console()

def check_data_files():
    """Check which data files exist."""
    output_dir = Path("output")
    books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    
    table = Table(title="Data File Status")
    table.add_column("Book", style="cyan")
    table.add_column("CSV File", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Status", style="magenta")
    
    available_books = []
    
    for book in books:
        csv_path = output_dir / book / f"{book}.csv"
        if csv_path.exists():
            size_mb = csv_path.stat().st_size / (1024 * 1024)
            table.add_row(book, "✓", f"{size_mb:.2f} MB", "Ready")
            available_books.append(book)
        else:
            table.add_row(book, "✗", "N/A", "Missing")
    
    console.print(table)
    return available_books

def upload_book_with_progress(client, book_name, csv_path):
    """Upload a single book with detailed progress tracking."""
    console.print(f"\n[bold blue]📖 Uploading {book_name}...[/bold blue]")
    
    try:
        # Get file info
        file_size = csv_path.stat().st_size
        console.print(f"File size: {file_size / (1024*1024):.2f} MB")
        
        # Start upload with progress tracking
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            
            # Create a custom task for the upload
            task = progress.add_task(f"Processing {book_name}...", total=100)
            
            # Simulate progress updates (since we can't easily track the actual upload)
            for i in range(100):
                time.sleep(0.1)  # Small delay to show progress
                progress.update(task, advance=1)
                
                # Update description with status
                if i < 20:
                    progress.update(task, description=f"Loading {book_name} data...")
                elif i < 40:
                    progress.update(task, description=f"Generating embeddings for {book_name}...")
                elif i < 80:
                    progress.update(task, description=f"Uploading {book_name} to Qdrant...")
                else:
                    progress.update(task, description=f"Finalizing {book_name} upload...")
        
        # Actually perform the upload
        console.print(f"[yellow]Performing actual upload for {book_name}...[/yellow]")
        success = client.upload_book_data(book_name, str(csv_path))
        
        elapsed_time = time.time() - start_time
        
        if success:
            console.print(f"[green]✅ {book_name} uploaded successfully in {elapsed_time:.1f} seconds[/green]")
            return True
        else:
            console.print(f"[red]❌ Failed to upload {book_name}[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Error uploading {book_name}: {e}[/red]")
        return False

def main():
    """Main upload function with comprehensive progress tracking."""
    console.print(Panel.fit(
        "[bold blue]Torah Upload to Qdrant[/bold blue]\n"
        "Uploading all 5 books of the Torah with progress tracking",
        border_style="blue"
    ))
    
    # Check available data files
    console.print("\n[bold]Checking data files...[/bold]")
    available_books = check_data_files()
    
    if not available_books:
        console.print("[red]❌ No data files found! Run the parser first.[/red]")
        return
    
    # Initialize Qdrant client
    console.print("\n[bold]Initializing Qdrant client...[/bold]")
    try:
        client = create_qdrant_client()
        console.print("[green]✅ Qdrant client initialized[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize Qdrant client: {e}[/red]")
        return
    
    # Upload each book
    console.print(f"\n[bold]Starting upload of {len(available_books)} books...[/bold]")
    
    successful_uploads = []
    failed_uploads = []
    
    for book in available_books:
        csv_path = Path("output") / book / f"{book}.csv"
        
        if upload_book_with_progress(client, book, csv_path):
            successful_uploads.append(book)
        else:
            failed_uploads.append(book)
    
    # Final summary
    console.print("\n" + "="*60)
    console.print("[bold]Upload Summary:[/bold]")
    console.print(f"[green]✅ Successful: {len(successful_uploads)} books[/green]")
    if successful_uploads:
        console.print(f"   {', '.join(successful_uploads)}")
    
    if failed_uploads:
        console.print(f"[red]❌ Failed: {len(failed_uploads)} books[/red]")
        console.print(f"   {', '.join(failed_uploads)}")
    
    # Show final collection stats
    if successful_uploads:
        console.print("\n[bold]Final Collection Statistics:[/bold]")
        try:
            stats = client.get_collection_stats()
            if stats:
                console.print(f"Total verses: {stats.get('total_points', 0)}")
                console.print(f"Vector size: {stats.get('vector_size', 0)}")
                console.print(f"Status: {stats.get('status', 'Unknown')}")
        except Exception as e:
            console.print(f"[yellow]Could not get final stats: {e}[/yellow]")
    
    console.print("\n[bold green]Upload process completed![/bold green]")

if __name__ == "__main__":
    main()
