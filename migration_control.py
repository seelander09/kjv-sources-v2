#!/usr/bin/env python3
"""
Migration Control Script
Provides easy commands to manage the Scriptural Truth migration
"""

import sys
import subprocess
import time
from pathlib import Path

def show_help():
    """Show help information"""
    print("🚀 Scriptural Truth Migration Control")
    print("=" * 50)
    print("Commands:")
    print("  start     - Start/resume migration")
    print("  status    - Show current status")
    print("  errors    - Show recent errors")
    print("  stop      - Stop running migration")
    print("  cleanup   - Clean up progress files")
    print("  monitor   - Monitor migration in real-time")
    print("  help      - Show this help")
    print()

def start_migration():
    """Start or resume migration"""
    print("🚀 Starting enhanced migration...")
    try:
        subprocess.run([sys.executable, "enhanced_scriptural_truth_migration.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
    except KeyboardInterrupt:
        print("\n⏸️ Migration interrupted by user")

def show_status():
    """Show migration status"""
    try:
        subprocess.run([sys.executable, "enhanced_migration_status.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Status check failed: {e}")

def show_errors():
    """Show recent errors"""
    try:
        subprocess.run([sys.executable, "enhanced_migration_status.py", "--errors"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error display failed: {e}")

def stop_migration():
    """Stop running migration"""
    print("🛑 Stopping migration...")
    try:
        subprocess.run(["taskkill", "/f", "/im", "python.exe"], check=True)
        print("✅ Migration stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to stop migration: {e}")

def cleanup_progress():
    """Clean up progress files"""
    print("🧹 Cleaning up progress files...")
    try:
        subprocess.run([sys.executable, "enhanced_migration_status.py", "--cleanup"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Cleanup failed: {e}")

def monitor_migration():
    """Monitor migration in real-time"""
    print("📊 Monitoring migration (Press Ctrl+C to stop)...")
    print("=" * 50)
    
    try:
        while True:
            # Clear screen (works on Windows)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print(f"📊 Migration Status - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 50)
            
            # Show status
            subprocess.run([sys.executable, "enhanced_migration_status.py"], check=True)
            
            print("\n⏰ Refreshing in 30 seconds... (Press Ctrl+C to stop)")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped")

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start_migration()
    elif command == "status":
        show_status()
    elif command == "errors":
        show_errors()
    elif command == "stop":
        stop_migration()
    elif command == "cleanup":
        cleanup_progress()
    elif command == "monitor":
        monitor_migration()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()
