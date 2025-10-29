#!/usr/bin/env python3
"""
Migration Progress Bar
Shows real-time progress with visual progress bar
"""

import json
import os
import psutil
import time
from pathlib import Path
from datetime import datetime, timedelta

def create_progress_bar(current, total, width=50):
    """Create a visual progress bar"""
    if total == 0:
        return "[" + " " * width + "] 0%"
    
    percentage = (current / total) * 100
    filled = int((current / total) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percentage:.1f}%"

def get_migration_progress():
    """Get current migration progress"""
    progress_file = Path("scriptural_truth_data/migration_progress.json")
    
    if not progress_file.exists():
        return None
    
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def get_discovered_urls():
    """Get discovered URLs count"""
    urls_file = Path("scriptural_truth_data/discovered_urls.json")
    
    if not urls_file.exists():
        return 0
    
    try:
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = json.load(f)
            return len(urls) if isinstance(urls, list) else len(urls.keys())
    except:
        return 0

def get_processed_items():
    """Get processed items count"""
    processed_file = Path("scriptural_truth_data/processed_items.json")
    
    if not processed_file.exists():
        return 0
    
    try:
        with open(processed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return len(data) if isinstance(data, list) else len(data.keys())
    except:
        return 0

def is_migration_running():
    """Check if migration is running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = ' '.join(proc.info['cmdline'])
                if 'enhanced_scriptural_truth_migration.py' in cmdline:
                    return True, proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False, None

def display_progress():
    """Display progress with visual bar"""
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("Scriptural Truth Migration Progress")
    print("=" * 60)
    
    # Check if running
    is_running, pid = is_migration_running()
    if is_running:
        print(f"Status: RUNNING (PID: {pid})")
    else:
        print("Status: NOT RUNNING")
    
    # Get progress data
    progress = get_migration_progress()
    discovered_urls = get_discovered_urls()
    processed_items = get_processed_items()
    
    print(f"Phase: {progress.get('current_phase', 'unknown').upper() if progress else 'unknown'}")
    print()
    
    # URL Discovery Progress
    print("URL Discovery:")
    if discovered_urls > 0:
        print(f"  URLs Found: {discovered_urls}")
        print(f"  Progress: {create_progress_bar(discovered_urls, 200)}")  # Estimate 200 total URLs
    else:
        print("  No URLs discovered yet")
    
    print()
    
    # Content Processing Progress
    print("Content Processing:")
    if discovered_urls > 0:
        print(f"  Processed: {processed_items}")
        print(f"  Progress: {create_progress_bar(processed_items, discovered_urls)}")
        
        if processed_items > 0:
            remaining = discovered_urls - processed_items
            print(f"  Remaining: {remaining}")
    else:
        print("  No content processed yet")
    
    print()
    
    # Time information
    if progress and progress.get('start_time'):
        try:
            start_time = datetime.fromisoformat(progress['start_time'])
            elapsed = datetime.now() - start_time
            print(f"Elapsed Time: {elapsed}")
            
            if processed_items > 0 and discovered_urls > 0:
                rate = processed_items / elapsed.total_seconds() * 60  # items per minute
                print(f"Processing Rate: {rate:.1f} items/minute")
                
                if rate > 0:
                    remaining_items = discovered_urls - processed_items
                    eta_seconds = remaining_items / (rate / 60)
                    eta = datetime.now() + timedelta(seconds=eta_seconds)
                    print(f"Estimated Completion: {eta.strftime('%H:%M:%S')}")
        except:
            pass
    
    # File sizes
    print()
    print("File Status:")
    
    files_to_check = [
        ("discovered_urls.json", "URLs"),
        ("processed_items.json", "Processed Items"),
        ("migration_errors.json", "Errors"),
        ("migration_progress.json", "Progress")
    ]
    
    for filename, description in files_to_check:
        filepath = Path(f"scriptural_truth_data/{filename}")
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  {description}: {size:,} bytes")
        else:
            print(f"  {description}: Not found")
    
    print()
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)

def main():
    """Main progress monitoring loop"""
    try:
        while True:
            display_progress()
            time.sleep(2)  # Update every 2 seconds
    except KeyboardInterrupt:
        print("\nProgress monitoring stopped.")

if __name__ == "__main__":
    main()
