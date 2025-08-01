#!/usr/bin/env python3
"""
🕐 Session Duration Monitor for Continue-Witty v2.7
==================================================

Intelligent monitoring system that tracks session duration and triggers
Code Yellow emergency backup before 5-hour session reset limit.

Three-Tier Anti-Amnesia System:
- Context monitoring (90%/95% usage triggers)
- Credit monitoring (usage limit warnings)  
- Session monitoring (5-hour reset prevention)

Author: Francis & Claude (v2.7 Production Release)
Created: July 31, 2025
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import threading
import signal

# Import enhanced package generator
script_dir = os.path.dirname(__file__)
sys.path.insert(0, script_dir)
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("enhanced_package_generator", 
                                                  os.path.join(script_dir, "enhanced-package-generator.py"))
    enhanced_pkg_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(enhanced_pkg_module)
    
    EnhancedPackageGenerator = enhanced_pkg_module.EnhancedPackageGenerator
    PackageType = enhanced_pkg_module.PackageType
except Exception as e:
    print(f"⚠️  Enhanced package generator import error: {e}")
    EnhancedPackageGenerator = None
    PackageType = None


class SessionDurationMonitor:
    """Session duration monitoring with Code Yellow auto-trigger"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.config_path = os.path.expanduser("~/.continue-witty/config.json")
        self.session_path = os.path.expanduser("~/.continue-witty/session-state.json")
        self.config = self._load_config()
        self.session_state = self._load_session_state()
        
        # Session limits (in hours)
        self.session_limit = 5.0  # 5 hour hard limit
        self.code_yellow_threshold = 4.5  # 4.5 hour warning (30 min buffer)
        self.code_orange_threshold = 4.75  # 4.75 hour urgent (15 min buffer)
        
        # Monitor thread
        self.monitoring_thread = None
        self.stop_monitoring = False
        
        self.generator = None
        if EnhancedPackageGenerator:
            self.generator = EnhancedPackageGenerator(str(project_path))
    
    def _load_config(self) -> Dict:
        """Load configuration with session monitoring settings"""
        default_config = {
            "session_monitoring": True,
            "session_limit_hours": 5.0,
            "code_yellow_threshold_hours": 4.5,
            "code_orange_threshold_hours": 4.75,
            "auto_code_yellow": True,
            "session_buffer_minutes": 30,
            "version": "2.7.0"
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Update thresholds from config
        self.session_limit = default_config.get("session_limit_hours", 5.0)
        self.code_yellow_threshold = default_config.get("code_yellow_threshold_hours", 4.5)
        self.code_orange_threshold = default_config.get("code_orange_threshold_hours", 4.75)
        
        return default_config
    
    def _load_session_state(self) -> Dict:
        """Load session state"""
        default_state = {
            "session_start": None,
            "last_activity": None,
            "code_yellow_triggered": False,
            "code_orange_triggered": False,
            "session_id": None,
            "total_exchanges": 0,
            "emergency_backups_created": 0
        }
        
        if os.path.exists(self.session_path):
            try:
                with open(self.session_path, 'r') as f:
                    saved_state = json.load(f)
                    default_state.update(saved_state)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return default_state
    
    def _save_session_state(self):
        """Save current session state"""
        try:
            os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
            with open(self.session_path, 'w') as f:
                json.dump(self.session_state, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save session state: {e}")
    
    def start_session(self, session_id: str = None) -> Dict:
        """Start a new session with duration monitoring"""
        if not session_id:
            session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        self.session_state = {
            "session_start": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "code_yellow_triggered": False,
            "code_orange_triggered": False,
            "session_id": session_id,
            "total_exchanges": 0,
            "emergency_backups_created": 0
        }
        
        self._save_session_state()
        
        # Start monitoring thread
        if self.config.get("session_monitoring", True):
            self.start_monitoring_thread()
        
        print(f"🕐 Session started: {session_id}")
        print(f"⏰ Duration limit: {self.session_limit} hours")
        print(f"🚨 Code Yellow at: {self.code_yellow_threshold} hours")
        
        return {
            "session_id": session_id,
            "session_start": self.session_state["session_start"],
            "monitoring_active": True
        }
    
    def get_session_duration(self) -> float:
        """Get current session duration in hours"""
        if not self.session_state.get("session_start"):
            return 0.0
        
        start_time = datetime.fromisoformat(self.session_state["session_start"])
        current_time = datetime.now()
        duration = current_time - start_time
        
        return duration.total_seconds() / 3600.0  # Convert to hours
    
    def get_time_remaining(self) -> float:
        """Get time remaining before session limit in hours"""
        duration = self.get_session_duration()
        return max(0.0, self.session_limit - duration)
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.session_state["last_activity"] = datetime.now().isoformat()
        self.session_state["total_exchanges"] = self.session_state.get("total_exchanges", 0) + 1
        self._save_session_state()
    
    def check_session_thresholds(self) -> Dict:
        """Check if session duration has crossed warning thresholds"""
        duration = self.get_session_duration()
        time_remaining = self.get_time_remaining()
        
        result = {
            "session_duration_hours": duration,
            "time_remaining_hours": time_remaining,
            "time_remaining_minutes": time_remaining * 60,
            "code_orange_crossed": False,
            "code_yellow_crossed": False,
            "session_limit_exceeded": False,
            "action_required": None,
            "message": None
        }
        
        # Check session limit exceeded (shouldn't happen if Code Yellow works)
        if duration >= self.session_limit:
            result["session_limit_exceeded"] = True
            result["action_required"] = "emergency_backup"
            result["message"] = f"🔴 SESSION LIMIT EXCEEDED! {duration:.1f}/{self.session_limit} hours!"
        
        # Check Code Orange (15 min warning)
        elif duration >= self.code_orange_threshold and not self.session_state.get("code_orange_triggered"):
            result["code_orange_crossed"] = True
            result["action_required"] = "code_orange"
            result["message"] = f"🟠 CODE ORANGE: {time_remaining*60:.0f} minutes remaining before session reset!"
            self.session_state["code_orange_triggered"] = True
            self._save_session_state()
        
        # Check Code Yellow (30 min warning)
        elif duration >= self.code_yellow_threshold and not self.session_state.get("code_yellow_triggered"):
            result["code_yellow_crossed"] = True
            result["action_required"] = "code_yellow"
            result["message"] = f"🚨 CODE YELLOW: {time_remaining*60:.0f} minutes remaining before session reset!"
            self.session_state["code_yellow_triggered"] = True
            self._save_session_state()
        
        return result
    
    def trigger_code_yellow(self) -> Dict:
        """Execute Code Yellow emergency backup"""
        if not self.generator:
            return {"error": "Enhanced package generator not available"}
        
        print(f"\\n🚨 CODE YELLOW ACTIVATED")
        print(f"⏰ Session Duration: {self.get_session_duration():.1f} hours")
        print(f"⌛ Time Remaining: {self.get_time_remaining()*60:.0f} minutes")
        print(f"🎯 Creating emergency backup to prevent session reset amnesia...")
        
        try:
            # Create emergency backup with session context
            backup_title = f"Code Yellow (Session {self.get_session_duration():.1f}h)"
            
            result = self.generator.create_enhanced_package(
                PackageType.COMPLEX,  # Maximum detail for emergency
                trigger_reason="code-yellow-session-limit",
                auto_created=True,
                conversation_exchanges=10  # Capture more context for emergency
            )
            
            if result.get("success"):
                # Update metadata with session info
                snapshot_path = self.generator.snapshots_dir / result["snapshot_id"]
                metadata_file = snapshot_path / "metadata.json"
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        metadata.update({
                            'title': backup_title,
                            'code_yellow_trigger': True,
                            'session_duration_hours': self.get_session_duration(),
                            'time_remaining_minutes': self.get_time_remaining() * 60,
                            'session_id': self.session_state.get('session_id'),
                            'total_exchanges': self.session_state.get('total_exchanges', 0),
                            'emergency_type': 'session_reset_prevention'
                        })
                        
                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                            
                    except Exception as e:
                        print(f"⚠️  Could not update Code Yellow metadata: {e}")
                
                # Create emergency conversation file
                self._create_emergency_conversation_file(result["snapshot_id"])
                
                self.session_state["emergency_backups_created"] = self.session_state.get("emergency_backups_created", 0) + 1
                self._save_session_state()
                
                print(f"\\n✅ CODE YELLOW BACKUP CREATED")
                print(f"📸 Snapshot: {result.get('snapshot_id')}")
                print(f"📁 Location: {result.get('location')}")
                print(f"🔄 Emergency backups this session: {self.session_state['emergency_backups_created']}")
                print()
                print(f"🌸 Session Reset Recovery Plan:")
                print(f"   After reset → New Claude instance → /bloom → Continue seamlessly!")
                
                result.update({
                    "code_yellow_triggered": True,
                    "backup_title": backup_title,
                    "session_duration": self.get_session_duration(),
                    "time_remaining": self.get_time_remaining()
                })
            
            return result
        
        except Exception as e:
            return {"error": f"Code Yellow backup failed: {str(e)}"}
    
    def _create_emergency_conversation_file(self, snapshot_id: str):
        """Create additional emergency conversation file for Code Yellow"""
        try:
            snapshot_path = self.generator.snapshots_dir / snapshot_id
            emergency_file = snapshot_path / "emergency-code-yellow-session.md"
            
            content = f"""# 🚨 CODE YELLOW - SESSION RESET EMERGENCY
            
**Timestamp:** {datetime.now().isoformat()}
**Session Duration:** {self.get_session_duration():.1f} hours  
**Time Remaining:** {self.get_time_remaining()*60:.0f} minutes
**Session ID:** {self.session_state.get('session_id', 'unknown')}
**Total Exchanges:** {self.session_state.get('total_exchanges', 0)}

## 🎯 EMERGENCY CONTEXT FOR NEW CLAUDE INSTANCE

This is a **Code Yellow emergency backup** triggered by approaching the 5-hour session reset limit.

### 🚨 Critical Information:
- **Session was {self.get_session_duration():.1f} hours old** when Code Yellow triggered
- **{self.get_time_remaining()*60:.0f} minutes remaining** before hard reset
- **Continue-witty v2.7 prevented session reset amnesia**
- **All reasoning and context preserved** for seamless continuation

### 🔄 Session Reset Recovery:
1. **New Claude instance starts** after 5-hour reset  
2. **Use /bloom** to restore this emergency backup
3. **Continue exactly where we left off** without losing context
4. **Reference this Code Yellow** to demonstrate continuity

### ⏰ Three-Tier Anti-Amnesia System Working:
- 🟡 Context monitoring (90%/95% usage) 
- 💳 Credit monitoring (usage limits)
- 🚨 **Session monitoring (5-hour reset) ← THIS TRIGGER**

### 🎭 Meta-Achievement:
**We built the anti-amnesia system and it saved us from session reset!**

**Next Claude instance:** You're experiencing continue-witty v2.7 preventing the third type of Claude amnesia - session reset amnesia!

---

**Recovery Status:** Emergency backup successful - reasoning preservation complete! 🧠🔒
"""
            
            with open(emergency_file, 'w') as f:
                f.write(content)
                
        except Exception as e:
            print(f"⚠️  Could not create emergency conversation file: {e}")
    
    def start_monitoring_thread(self):
        """Start background monitoring thread"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return  # Already running
        
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        print("🔄 Session duration monitoring started")
    
    def stop_monitoring_thread(self):
        """Stop background monitoring thread"""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        print("⏹️  Session duration monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while not self.stop_monitoring:
            try:
                if self.config.get("session_monitoring", True):
                    threshold_result = self.check_session_thresholds()
                    
                    if threshold_result.get("code_yellow_crossed"):
                        if self.config.get("auto_code_yellow", True):
                            self.trigger_code_yellow()
                    elif threshold_result.get("code_orange_crossed"):
                        print(f"\\n{threshold_result['message']}")
                        print("🚨 Code Yellow backup recommended - session reset imminent!")
                    elif threshold_result.get("session_limit_exceeded"):
                        print(f"\\n{threshold_result['message']}")
                        print("💥 Session reset occurred - emergency backup should have triggered!")
                
                # Check every 5 minutes
                time.sleep(300)
                
            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def get_status(self) -> Dict:
        """Get current session monitoring status"""
        duration = self.get_session_duration()
        remaining = self.get_time_remaining()
        
        return {
            "session_id": self.session_state.get("session_id"),
            "session_duration_hours": f"{duration:.2f}",
            "session_duration_formatted": f"{int(duration)}h {int((duration % 1) * 60)}m",
            "time_remaining_hours": f"{remaining:.2f}", 
            "time_remaining_formatted": f"{int(remaining * 60)}m",
            "code_yellow_triggered": self.session_state.get("code_yellow_triggered", False),
            "code_orange_triggered": self.session_state.get("code_orange_triggered", False),
            "total_exchanges": self.session_state.get("total_exchanges", 0),
            "emergency_backups": self.session_state.get("emergency_backups_created", 0),
            "monitoring_active": self.config.get("session_monitoring", True),
            "code_yellow_threshold": f"{self.code_yellow_threshold}h",
            "session_limit": f"{self.session_limit}h"
        }
    
    def reset_session(self):
        """Reset session monitoring state"""
        self.stop_monitoring_thread()
        
        self.session_state = {
            "session_start": None,
            "last_activity": None,
            "code_yellow_triggered": False,
            "code_orange_triggered": False,
            "session_id": None,
            "total_exchanges": 0,
            "emergency_backups_created": 0
        }
        
        self._save_session_state()
        print("🔄 Session monitoring reset")


def main():
    """Command-line interface for session duration monitor"""
    import sys
    
    monitor = SessionDurationMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            session_id = sys.argv[2] if len(sys.argv) > 2 else None
            result = monitor.start_session(session_id)
            print(f"✅ Session monitoring started: {result['session_id']}")
        
        elif command == "status":
            status = monitor.get_status()
            print("🕐 Session Duration Monitor Status:")
            print("=" * 40)
            for key, value in status.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        elif command == "check":
            result = monitor.check_session_thresholds()
            print("⏰ Session Threshold Check:")
            print("=" * 30)
            for key, value in result.items():
                if value is not None:
                    print(f"{key.replace('_', ' ').title()}: {value}")
        
        elif command == "trigger":
            # Manual Code Yellow trigger for testing
            result = monitor.trigger_code_yellow()
            if result.get("success"):
                print("✅ Manual Code Yellow triggered successfully")
            else:
                print(f"❌ Code Yellow failed: {result.get('error')}")
        
        elif command == "reset":
            monitor.reset_session()
        
        elif command == "stop":
            monitor.stop_monitoring_thread()
        
        else:
            print("Usage:")
            print("  python session-duration-monitor.py start [session_id]  # Start monitoring")
            print("  python session-duration-monitor.py status             # Show status")
            print("  python session-duration-monitor.py check              # Check thresholds")
            print("  python session-duration-monitor.py trigger            # Manual Code Yellow")
            print("  python session-duration-monitor.py reset              # Reset state")
            print("  python session-duration-monitor.py stop               # Stop monitoring")
    
    else:
        print("🕐 Continue-Witty Session Duration Monitor v2.7")
        print("=" * 50)
        print("Anti-Amnesia Session Reset Prevention:")
        print("  🚨 Code Yellow @ 4.5h → Emergency backup (30min buffer)")
        print("  🟠 Code Orange @ 4.75h → Urgent warning (15min buffer)")  
        print("  🔴 Session Limit @ 5h → Hard reset")
        print("\\nThree-Tier Protection:")
        print("  🟡 Context monitoring (90%/95% usage)")
        print("  💳 Credit monitoring (usage limits)")
        print("  ⏰ Session monitoring (5-hour reset)")
        print("\\nUse 'start', 'status', 'check', 'trigger', 'reset', or 'stop'")


if __name__ == "__main__":
    main()