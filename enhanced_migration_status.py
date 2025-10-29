#!/usr/bin/env python3
"""
Enhanced Scriptural Truth Migration Status Checker
Provides detailed status information and migration controls
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class MigrationStatusChecker:
    def __init__(self):
        self.output_dir = Path("scriptural_truth_data")
        self.progress_file = self.output_dir / "migration_progress.json"
        self.discovered_urls_file = self.output_dir / "discovered_urls.json"
        self.processed_items_file = self.output_dir / "processed_items.json"
        self.error_log_file = self.output_dir / "migration_errors.json"
        self.final_content_file = self.output_dir / "scriptural_truth_content.json"
    
    def check_status(self) -> Dict[str, Any]:
        """Check and return comprehensive migration status"""
        status = {
            "is_running": False,
            "phase": "unknown",
            "discovered_urls": 0,
            "processed_items": 0,
            "stored_count": 0,
            "errors": 0,
            "start_time": None,
            "last_updated": None,
            "elapsed_time": None,
            "estimated_completion": None,
            "files": {},
            "recommendations": []
        }
        
        if not self.output_dir.exists():
            status["recommendations"].append("Migration has not been started yet")
            return status
        
        # Check if migration is currently running
        status["is_running"] = self._is_migration_running()
        
        # Load progress information
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                
                status["phase"] = progress.get("phase", "unknown")
                status["stored_count"] = progress.get("stored_count", 0)
                status["start_time"] = progress.get("start_time")
                status["last_updated"] = progress.get("last_updated")
                
                if status["start_time"]:
                    start_time = datetime.fromisoformat(status["start_time"])
                    elapsed = datetime.now() - start_time
                    status["elapsed_time"] = str(elapsed).split('.')[0]  # Remove microseconds
                    
                    # Estimate completion time
                    if status["phase"] == "discovery" and progress.get("total_discovered", 0) > 0:
                        # Rough estimate based on discovery rate
                        estimated_total = 500  # Rough estimate of total URLs
                        completion_ratio = progress.get("total_discovered", 0) / estimated_total
                        if completion_ratio > 0:
                            estimated_total_time = elapsed / completion_ratio
                            remaining_time = estimated_total_time - elapsed
                            status["estimated_completion"] = str(remaining_time).split('.')[0]
                
            except Exception as e:
                status["recommendations"].append(f"Error reading progress file: {e}")
        
        # Load discovered URLs
        if self.discovered_urls_file.exists():
            try:
                with open(self.discovered_urls_file, 'r') as f:
                    urls = json.load(f)
                status["discovered_urls"] = len(urls)
            except Exception as e:
                status["recommendations"].append(f"Error reading discovered URLs: {e}")
        
        # Load processed items
        if self.processed_items_file.exists():
            try:
                with open(self.processed_items_file, 'r') as f:
                    items = json.load(f)
                status["processed_items"] = len(items)
            except Exception as e:
                status["recommendations"].append(f"Error reading processed items: {e}")
        
        # Load error log
        if self.error_log_file.exists():
            try:
                with open(self.error_log_file, 'r') as f:
                    errors = json.load(f)
                status["errors"] = len(errors)
            except Exception as e:
                status["recommendations"].append(f"Error reading error log: {e}")
        
        # Check final content file
        if self.final_content_file.exists():
            try:
                with open(self.final_content_file, 'r') as f:
                    content = json.load(f)
                status["files"]["final_content"] = {
                    "size": len(content),
                    "file_size": self.final_content_file.stat().st_size,
                    "modified": datetime.fromtimestamp(self.final_content_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                }
            except Exception as e:
                status["recommendations"].append(f"Error reading final content: {e}")
        
        # Check all files in directory
        status["files"]["directory"] = {}
        for file in self.output_dir.iterdir():
            if file.is_file():
                status["files"]["directory"][file.name] = {
                    "size": file.stat().st_size,
                    "modified": datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                }
        
        # Generate recommendations
        self._generate_recommendations(status)
        
        return status
    
    def _is_migration_running(self) -> bool:
        """Check if migration is currently running"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] == 'python.exe':
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'scriptural_truth_migration' in cmdline:
                        return True
        except ImportError:
            # Fallback method without psutil
            pass
        return False
    
    def _generate_recommendations(self, status: Dict[str, Any]):
        """Generate recommendations based on current status"""
        if not status["is_running"] and status["phase"] != "unknown":
            if status["phase"] in ["discovery", "processing", "embedding"]:
                status["recommendations"].append("Migration is paused - you can resume by running the script again")
        
        if status["errors"] > 0:
            status["recommendations"].append(f"Found {status['errors']} errors - check error log for details")
        
        if status["phase"] == "discovery" and status["discovered_urls"] == 0:
            status["recommendations"].append("Discovery phase hasn't started yet")
        
        if status["phase"] == "processing" and status["processed_items"] == 0:
            status["recommendations"].append("Processing phase hasn't started yet")
        
        if status["phase"] == "embedding" and status["stored_count"] == 0:
            status["recommendations"].append("Embedding phase hasn't started yet")
        
        if status["last_updated"]:
            last_update = datetime.fromisoformat(status["last_updated"])
            time_since_update = datetime.now() - last_update
            if time_since_update.total_seconds() > 300:  # 5 minutes
                status["recommendations"].append("No updates in over 5 minutes - migration may be stuck")
    
    def display_status(self):
        """Display formatted status information"""
        status = self.check_status()
        
        print("Enhanced Scriptural Truth Migration Status")
        print("=" * 60)
        
        # Running status
        if status["is_running"]:
            print("Status: RUNNING")
        else:
            print("Status: NOT RUNNING")
        
        # Phase information
        print(f"📊 Current Phase: {status['phase'].upper()}")
        
        # Progress information
        print(f"📊 URLs Discovered: {status['discovered_urls']}")
        print(f"📊 Items Processed: {status['processed_items']}")
        print(f"📊 Items Stored: {status['stored_count']}")
        print(f"📊 Errors: {status['errors']}")
        
        # Time information
        if status["start_time"]:
            print(f"⏰ Started: {status['start_time']}")
        if status["last_updated"]:
            print(f"⏰ Last Updated: {status['last_updated']}")
        if status["elapsed_time"]:
            print(f"⏰ Elapsed Time: {status['elapsed_time']}")
        if status["estimated_completion"]:
            print(f"⏰ Estimated Remaining: {status['estimated_completion']}")
        
        # File information
        if status["files"].get("final_content"):
            content_info = status["files"]["final_content"]
            print(f"📁 Final Content: {content_info['size']} items ({content_info['file_size']:,} bytes)")
            print(f"📁 Last Modified: {content_info['modified']}")
        
        # Recommendations
        if status["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in status["recommendations"]:
                print(f"   • {rec}")
        
        # File listing
        if status["files"].get("directory"):
            print("\n📁 Files in migration directory:")
            for filename, info in status["files"]["directory"].items():
                print(f"   📄 {filename} ({info['size']:,} bytes, {info['modified']})")
    
    def show_errors(self, limit: int = 10):
        """Show recent errors from the error log"""
        if not self.error_log_file.exists():
            print("❌ No error log found")
            return
        
        try:
            with open(self.error_log_file, 'r') as f:
                errors = json.load(f)
            
            if not errors:
                print("✅ No errors found")
                return
            
            print(f"⚠️ Recent Errors (showing last {min(limit, len(errors))}):")
            print("=" * 60)
            
            for error in errors[-limit:]:
                print(f"🔴 {error['timestamp']}")
                print(f"   URL: {error['url']}")
                print(f"   Phase: {error['phase']}")
                print(f"   Error: {error['error']}")
                print()
                
        except Exception as e:
            print(f"❌ Error reading error log: {e}")
    
    def cleanup_progress(self):
        """Clean up progress files (use with caution)"""
        print("🧹 Cleaning up progress files...")
        
        files_to_remove = [
            self.progress_file,
            self.discovered_urls_file,
            self.processed_items_file,
            self.error_log_file
        ]
        
        removed_count = 0
        for file in files_to_remove:
            if file.exists():
                try:
                    file.unlink()
                    print(f"   ✅ Removed {file.name}")
                    removed_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to remove {file.name}: {e}")
        
        if removed_count > 0:
            print(f"✅ Cleaned up {removed_count} progress files")
        else:
            print("ℹ️ No progress files to clean up")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Scriptural Truth Migration Status Checker")
    parser.add_argument("--errors", "-e", action="store_true", help="Show recent errors")
    parser.add_argument("--cleanup", "-c", action="store_true", help="Clean up progress files")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Limit number of errors to show")
    
    args = parser.parse_args()
    
    checker = MigrationStatusChecker()
    
    if args.cleanup:
        checker.cleanup_progress()
    elif args.errors:
        checker.show_errors(args.limit)
    else:
        checker.display_status()

if __name__ == "__main__":
    main()
