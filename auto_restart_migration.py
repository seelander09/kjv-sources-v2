#!/usr/bin/env python3
"""
Auto-Restart Scriptural Truth Migration
Automatically restarts the migration if it stops or gets stuck
"""

import subprocess
import time
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import psutil

class AutoRestartMigration:
    def __init__(self):
        self.migration_script = "enhanced_scriptural_truth_migration.py"
        self.status_script = "enhanced_migration_status.py"
        self.progress_file = Path("scriptural_truth_data/migration_progress.json")
        self.check_interval = 60  # Check every 60 seconds
        self.stuck_threshold = 300  # 5 minutes without updates = stuck
        self.max_restarts = 10  # Maximum restart attempts
        self.restart_count = 0
        self.start_time = datetime.now()
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def is_migration_running(self):
        """Check if migration process is running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe':
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'enhanced_scriptural_truth_migration.py' in cmdline:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def get_migration_status(self):
        """Get current migration status"""
        try:
            result = subprocess.run(
                [os.sys.executable, "simple_migration_status.py"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse status from output
                output = result.stdout
                status = {}
                
                for line in output.split('\n'):
                    if 'Status:' in line:
                        status['running'] = 'RUNNING' in line
                    elif 'Current Phase:' in line:
                        status['phase'] = line.split(':')[1].strip()
                    elif 'URLs Discovered:' in line:
                        status['urls'] = int(line.split(':')[1].strip())
                    elif 'Last Updated:' in line:
                        try:
                            last_updated_str = line.split(':', 1)[1].strip()
                            status['last_updated'] = datetime.fromisoformat(last_updated_str)
                        except:
                            status['last_updated'] = None
                    elif 'Elapsed Time:' in line:
                        status['elapsed'] = line.split(':', 1)[1].strip()
                
                return status
            else:
                self.log(f"❌ Status check failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.log("⏰ Status check timed out")
            return None
        except Exception as e:
            self.log(f"❌ Error checking status: {e}")
            return None
    
    def is_migration_stuck(self, status):
        """Check if migration is stuck"""
        if not status or not status.get('last_updated'):
            return True
            
        time_since_update = datetime.now() - status['last_updated']
        return time_since_update.total_seconds() > self.stuck_threshold
    
    def start_migration(self):
        """Start the migration process"""
        try:
            self.log(f"🚀 Starting migration (attempt {self.restart_count + 1})")
            
            # Start migration in background
            process = subprocess.Popen(
                [os.sys.executable, self.migration_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.log(f"✅ Migration started with PID: {process.pid}")
            return process
            
        except Exception as e:
            self.log(f"❌ Failed to start migration: {e}")
            return None
    
    def should_restart(self, status):
        """Determine if migration should be restarted"""
        # Check if process is running
        if not self.is_migration_running():
            self.log("🔄 Migration process not running")
            return True
            
        # Check if migration is stuck
        if self.is_migration_stuck(status):
            self.log("⏰ Migration appears to be stuck")
            return True
            
        # Check if migration completed
        if status and status.get('phase') == 'completed':
            self.log("✅ Migration completed successfully")
            return False
            
        return False
    
    def kill_migration_processes(self):
        """Kill any existing migration processes"""
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe':
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'enhanced_scriptural_truth_migration.py' in cmdline:
                        proc.kill()
                        killed_count += 1
                        self.log(f"🛑 Killed migration process PID: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed_count > 0:
            time.sleep(2)  # Wait for processes to terminate
            
        return killed_count
    
    def run(self):
        """Main auto-restart loop"""
        self.log("🔄 Auto-Restart Migration Manager Started")
        self.log(f"📊 Check interval: {self.check_interval} seconds")
        self.log(f"⏰ Stuck threshold: {self.stuck_threshold} seconds")
        self.log(f"🔄 Max restarts: {self.max_restarts}")
        self.log("=" * 60)
        
        while self.restart_count < self.max_restarts:
            try:
                # Check current status
                status = self.get_migration_status()
                
                if status:
                    self.log(f"📊 Status: {'RUNNING' if status.get('running') else 'NOT RUNNING'}")
                    self.log(f"📊 Phase: {status.get('phase', 'unknown')}")
                    self.log(f"📊 URLs: {status.get('urls', 0)}")
                    self.log(f"📊 Elapsed: {status.get('elapsed', 'unknown')}")
                
                # Check if restart is needed
                if self.should_restart(status):
                    if self.restart_count >= self.max_restarts:
                        self.log(f"❌ Maximum restart attempts ({self.max_restarts}) reached")
                        break
                    
                    # Kill existing processes
                    killed = self.kill_migration_processes()
                    if killed > 0:
                        self.log(f"🛑 Killed {killed} existing processes")
                    
                    # Start new migration
                    process = self.start_migration()
                    if process:
                        self.restart_count += 1
                        self.log(f"🔄 Restart count: {self.restart_count}/{self.max_restarts}")
                    else:
                        self.log("❌ Failed to start migration")
                        break
                else:
                    self.log("✅ Migration running normally")
                
                # Wait before next check
                self.log(f"⏰ Waiting {self.check_interval} seconds before next check...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.log("\n🛑 Auto-restart stopped by user")
                break
            except Exception as e:
                self.log(f"❌ Error in auto-restart loop: {e}")
                time.sleep(self.check_interval)
        
        # Final cleanup
        self.log("🧹 Cleaning up...")
        self.kill_migration_processes()
        
        total_time = datetime.now() - self.start_time
        self.log(f"⏰ Total runtime: {total_time}")
        self.log(f"🔄 Total restarts: {self.restart_count}")
        self.log("✅ Auto-restart manager stopped")

def main():
    """Main entry point"""
    print("🔄 Scriptural Truth Migration Auto-Restart Manager")
    print("=" * 60)
    print("💡 This will automatically restart the migration if it stops or gets stuck")
    print("💡 Press Ctrl+C to stop the auto-restart manager")
    print("=" * 60)
    
    manager = AutoRestartMigration()
    manager.run()

if __name__ == "__main__":
    main()
