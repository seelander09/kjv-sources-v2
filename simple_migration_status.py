#!/usr/bin/env python3
"""
Simple Migration Status Checker
Checks the status of the Scriptural Truth migration without emojis
"""

import json
import os
import psutil
from pathlib import Path
from datetime import datetime

def check_migration_status():
    """Check migration status"""
    print("Scriptural Truth Migration Status")
    print("=" * 50)
    
    # Check if migration is running
    is_running = False
    migration_pid = None
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = ' '.join(proc.info['cmdline'])
                if 'enhanced_scriptural_truth_migration.py' in cmdline:
                    is_running = True
                    migration_pid = proc.info['pid']
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if is_running:
        print(f"Status: RUNNING (PID: {migration_pid})")
    else:
        print("Status: NOT RUNNING")
    
    # Check progress file
    progress_file = Path("scriptural_truth_data/migration_progress.json")
    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            print(f"Current Phase: {progress.get('current_phase', 'unknown').upper()}")
            print(f"URLs Discovered: {progress.get('discovered_urls', 0):,}")
            print(f"Items Processed: {progress.get('processed_items', 0):,}")
            print(f"Items Stored: {progress.get('stored_count', 0):,}")
            print(f"Errors: {progress.get('errors', 0)}")
            
            if progress.get('start_time'):
                print(f"Started: {progress['start_time']}")
            if progress.get('last_updated'):
                print(f"Last Updated: {progress['last_updated']}")
            
            # Calculate elapsed time
            if progress.get('start_time'):
                try:
                    start_time = datetime.fromisoformat(progress['start_time'])
                    elapsed = datetime.now() - start_time
                    print(f"Elapsed Time: {elapsed}")
                except:
                    pass
            
        except Exception as e:
            print(f"Error reading progress file: {e}")
    else:
        print("No progress file found")
    
    # Check log file
    log_file = Path("scriptural_truth_data/migration.log")
    if log_file.exists():
        size = log_file.stat().st_size
        print(f"Log File: {size:,} bytes")
    else:
        print("No log file found")
    
    print("=" * 50)

def main():
    """Main function"""
    check_migration_status()

if __name__ == "__main__":
    main()
