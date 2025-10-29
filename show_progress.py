#!/usr/bin/env python3
"""
Simple Progress Display
"""

import json
import psutil
from pathlib import Path

def show_progress():
    """Show current progress"""
    print("Scriptural Truth Migration Progress")
    print("=" * 50)
    
    # Check if running
    is_running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'python.exe':
                cmdline = ' '.join(proc.info['cmdline'])
                if 'enhanced_scriptural_truth_migration.py' in cmdline:
                    is_running = True
                    print(f"Status: RUNNING (PID: {proc.info['pid']})")
                    break
        except:
            continue
    
    if not is_running:
        print("Status: NOT RUNNING")
    
    # Get counts
    urls_file = Path("scriptural_truth_data/discovered_urls.json")
    processed_file = Path("scriptural_truth_data/processed_items.json")
    
    discovered = 0
    processed = 0
    
    if urls_file.exists():
        try:
            with open(urls_file, 'r') as f:
                data = json.load(f)
                discovered = len(data) if isinstance(data, list) else len(data.keys())
        except:
            pass
    
    if processed_file.exists():
        try:
            with open(processed_file, 'r') as f:
                data = json.load(f)
                processed = len(data) if isinstance(data, list) else len(data.keys())
        except:
            pass
    
    print(f"URLs Discovered: {discovered}")
    print(f"Items Processed: {processed}")
    
    if discovered > 0:
        percentage = (processed / discovered) * 100
        filled = int((processed / discovered) * 30)
        bar = "█" * filled + "░" * (30 - filled)
        print(f"Progress: [{bar}] {percentage:.1f}%")
        print(f"Remaining: {discovered - processed}")
    else:
        print("Progress: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%")
    
    print("=" * 50)

if __name__ == "__main__":
    show_progress()
