#!/usr/bin/env python3
"""
🎯 Monitoring Coordinator for Continue-Witty v2.7
================================================

Unified coordinator that manages all three monitoring systems:
- Context Window Monitor (90%/95% usage triggers)
- Credit Limit Monitor (usage warning triggers)
- Session Duration Monitor (4.5h/4.75h/5h triggers)

Provides single interface for complete anti-amnesia protection.

Author: Francis & Claude (v2.7 Production Release)
Created: July 31, 2025
"""

import os
import json
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import all monitoring systems
script_dir = os.path.dirname(__file__)
sys.path.insert(0, script_dir)

try:
    import importlib.util
    
    # Import session duration monitor
    spec = importlib.util.spec_from_file_location("session_duration_monitor", 
                                                  os.path.join(script_dir, "session-duration-monitor.py"))
    session_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(session_module)
    SessionDurationMonitor = session_module.SessionDurationMonitor
    
    # Import credit monitor
    spec = importlib.util.spec_from_file_location("credit_monitor", 
                                                  os.path.join(script_dir, "credit-monitor.py"))
    credit_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(credit_module)
    CreditMonitor = credit_module.CreditMonitor
    
    # Import context window monitor
    spec = importlib.util.spec_from_file_location("context_window_monitor", 
                                                  os.path.join(script_dir, "context-window-monitor.py"))
    context_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(context_module)
    ContextWindowMonitor = context_module.ContextWindowMonitor
    
except Exception as e:
    print(f"⚠️  Monitor import error: {e}")
    SessionDurationMonitor = None
    CreditMonitor = None
    ContextWindowMonitor = None


class MonitoringCoordinator:
    """Unified coordinator for all continue-witty monitoring systems"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.config_path = os.path.expanduser("~/.continue-witty/config.json")
        self.coordinator_state_path = os.path.expanduser("~/.continue-witty/coordinator-state.json")
        
        self.config = self._load_config()
        self.coordinator_state = self._load_coordinator_state()
        
        # Initialize monitors
        self.session_monitor = None
        self.credit_monitor = None
        self.context_monitor = None
        
        if SessionDurationMonitor:
            self.session_monitor = SessionDurationMonitor(str(project_path))
        if CreditMonitor:
            self.credit_monitor = CreditMonitor(str(project_path))
        if ContextWindowMonitor:
            self.context_monitor = ContextWindowMonitor(str(project_path))
        
        # Coordination thread
        self.coordination_thread = None
        self.stop_coordination = False
    
    def _load_config(self) -> Dict:
        """Load unified configuration"""
        default_config = {
            "unified_monitoring": True,
            "session_monitoring": True,
            "credit_monitoring": True,
            "context_monitoring": True,
            "auto_start_session": True,
            "coordination_check_interval": 30,  # seconds
            "version": "2.7.0"
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return default_config
    
    def _load_coordinator_state(self) -> Dict:
        """Load coordinator state"""
        default_state = {
            "coordinator_started": None,
            "session_id": None,
            "total_triggers_fired": 0,
            "triggers_history": [],
            "last_coordination_check": None
        }
        
        if os.path.exists(self.coordinator_state_path):
            try:
                with open(self.coordinator_state_path, 'r') as f:
                    saved_state = json.load(f)
                    default_state.update(saved_state)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return default_state
    
    def _save_coordinator_state(self):
        """Save coordinator state"""
        try:
            os.makedirs(os.path.dirname(self.coordinator_state_path), exist_ok=True)
            with open(self.coordinator_state_path, 'w') as f:
                json.dump(self.coordinator_state, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save coordinator state: {e}")
    
    def start_unified_monitoring(self, session_id: str = None) -> Dict:
        """Start all monitoring systems in coordinated fashion"""
        if not session_id:
            session_id = f"unified-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        print("🎯 Starting Continue-Witty v2.7 Unified Monitoring")
        print("=" * 50)
        
        results = {
            "session_id": session_id,
            "monitors_started": [],
            "errors": []
        }
        
        # 1. Start session duration monitoring
        if self.session_monitor and self.config.get("session_monitoring", True):
            try:
                session_result = self.session_monitor.start_session(session_id)
                results["monitors_started"].append("session_duration")
                print(f"✅ Session monitoring started: {session_result['session_id']}")
            except Exception as e:
                results["errors"].append(f"Session monitor: {str(e)}")
                print(f"❌ Session monitor failed: {e}")
        
        # 2. Initialize credit monitoring (passive, no start needed)
        if self.credit_monitor and self.config.get("credit_monitoring", True):
            try:
                # Credit monitor is passive - just verify it's working
                test_result = self.credit_monitor.detect_credit_warning("test message")
                results["monitors_started"].append("credit_limit")
                print("✅ Credit monitoring initialized")
            except Exception as e:
                results["errors"].append(f"Credit monitor: {str(e)}")
                print(f"❌ Credit monitor failed: {e}")
        
        # 3. Initialize context window monitoring (passive, no start needed)
        if self.context_monitor and self.config.get("context_monitoring", True):
            try:
                # Context monitor is passive - just verify it's working
                context_status = self.context_monitor.get_status()
                results["monitors_started"].append("context_window")
                print("✅ Context monitoring initialized")
            except Exception as e:
                results["errors"].append(f"Context monitor: {str(e)}")
                print(f"❌ Context monitor failed: {e}")
        
        # 4. Start coordination thread
        if self.config.get("unified_monitoring", True):
            self.start_coordination_thread()
            results["monitors_started"].append("coordination")
            print("✅ Unified coordination started")
        
        # Update coordinator state
        self.coordinator_state.update({
            "coordinator_started": datetime.now().isoformat(),
            "session_id": session_id,
            "total_triggers_fired": 0,
            "triggers_history": []
        })
        self._save_coordinator_state()
        
        print(f"\\n🎭 Three-Tier Anti-Amnesia System Active:")
        print(f"   🟡 Context Window → 90%/95% usage triggers")
        print(f"   💳 Credit Limits → Usage warning triggers")
        print(f"   🚨 Session Duration → 4.5h/4.75h/5h triggers")
        print(f"\\n📊 Monitors: {len(results['monitors_started'])} active, {len(results['errors'])} errors")
        
        return results
    
    def update_activity(self, conversation_text: str = "", claude_message: str = ""):
        """Update all monitors with new activity"""
        activity_time = datetime.now().isoformat()
        
        # 1. Update session monitor
        if self.session_monitor:
            try:
                self.session_monitor.update_activity()
            except Exception as e:
                print(f"⚠️  Session activity update failed: {e}")
        
        # 2. Check credit monitor for warnings
        if self.credit_monitor and claude_message:
            try:
                credit_result = self.credit_monitor.monitor_session(claude_message)
                if credit_result:
                    self._log_trigger("credit_warning", credit_result)
                    return credit_result  # Return immediately if credit trigger fires
            except Exception as e:
                print(f"⚠️  Credit monitoring failed: {e}")
        
        # 3. Check context window monitor
        if self.context_monitor and conversation_text:
            try:
                context_result = self.context_monitor.monitor_conversation(conversation_text)
                if context_result:
                    self._log_trigger("context_window", context_result)
                    return context_result  # Return immediately if context trigger fires
            except Exception as e:
                print(f"⚠️  Context monitoring failed: {e}")
        
        return None
    
    def _log_trigger(self, trigger_type: str, trigger_result: Dict):
        """Log trigger event in coordinator state"""
        trigger_event = {
            "timestamp": datetime.now().isoformat(),
            "type": trigger_type,
            "result": trigger_result,
            "success": trigger_result.get("success", False)
        }
        
        self.coordinator_state["total_triggers_fired"] = self.coordinator_state.get("total_triggers_fired", 0) + 1
        self.coordinator_state["triggers_history"] = self.coordinator_state.get("triggers_history", [])
        self.coordinator_state["triggers_history"].append(trigger_event)
        
        # Keep only last 10 trigger events
        if len(self.coordinator_state["triggers_history"]) > 10:
            self.coordinator_state["triggers_history"] = self.coordinator_state["triggers_history"][-10:]
        
        self._save_coordinator_state()
        
        print(f"📝 Trigger logged: {trigger_type} → {'Success' if trigger_result.get('success') else 'Failed'}")
    
    def start_coordination_thread(self):
        """Start background coordination thread"""
        if self.coordination_thread and self.coordination_thread.is_alive():
            return  # Already running
        
        self.stop_coordination = False
        self.coordination_thread = threading.Thread(target=self._coordination_loop, daemon=True)
        self.coordination_thread.start()
    
    def stop_coordination_thread(self):
        """Stop background coordination thread"""
        self.stop_coordination = True
        if self.coordination_thread:
            self.coordination_thread.join(timeout=1.0)
    
    def _coordination_loop(self):
        """Background coordination loop"""
        while not self.stop_coordination:
            try:
                # Check session duration triggers
                if self.session_monitor:
                    threshold_result = self.session_monitor.check_session_thresholds()
                    
                    if threshold_result.get("code_yellow_crossed"):
                        result = self.session_monitor.trigger_code_yellow()
                        self._log_trigger("code_yellow", result)
                    elif threshold_result.get("code_orange_crossed"):
                        print(f"\\n{threshold_result['message']}")
                
                # Update coordinator state
                self.coordinator_state["last_coordination_check"] = datetime.now().isoformat()
                self._save_coordinator_state()
                
                # Check every 30 seconds
                time.sleep(self.config.get("coordination_check_interval", 30))
                
            except Exception as e:
                print(f"⚠️  Coordination error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def get_unified_status(self) -> Dict:
        """Get status of all monitoring systems"""
        status = {
            "coordinator": {
                "started": self.coordinator_state.get("coordinator_started"),
                "session_id": self.coordinator_state.get("session_id"),
                "total_triggers": self.coordinator_state.get("total_triggers_fired", 0),
                "last_check": self.coordinator_state.get("last_coordination_check")
            },
            "session_monitor": None,
            "credit_monitor": None,
            "context_monitor": None,
            "overall_health": "unknown"
        }
        
        active_monitors = 0
        total_monitors = 0
        
        # Session monitor status
        if self.session_monitor:
            total_monitors += 1
            try:
                status["session_monitor"] = self.session_monitor.get_status()
                active_monitors += 1
            except Exception as e:
                status["session_monitor"] = {"error": str(e)}
        
        # Credit monitor status
        if self.credit_monitor:
            total_monitors += 1
            try:
                status["credit_monitor"] = {
                    "patterns_active": len(self.credit_monitor.credit_patterns),
                    "monitoring_enabled": True
                }
                active_monitors += 1
            except Exception as e:
                status["credit_monitor"] = {"error": str(e)}
        
        # Context monitor status
        if self.context_monitor:
            total_monitors += 1
            try:
                status["context_monitor"] = self.context_monitor.get_status()
                active_monitors += 1
            except Exception as e:
                status["context_monitor"] = {"error": str(e)}
        
        # Overall health
        if active_monitors == total_monitors and total_monitors > 0:
            status["overall_health"] = "healthy"
        elif active_monitors > 0:
            status["overall_health"] = "partial"
        else:
            status["overall_health"] = "failed"
        
        status["monitors_summary"] = f"{active_monitors}/{total_monitors} active"
        
        return status
    
    def stop_unified_monitoring(self):
        """Stop all monitoring systems"""
        print("🛑 Stopping Continue-Witty v2.7 Unified Monitoring")
        
        # Stop coordination thread
        self.stop_coordination_thread()
        
        # Stop session monitor
        if self.session_monitor:
            try:
                self.session_monitor.stop_monitoring_thread()
                print("✅ Session monitoring stopped")
            except Exception as e:
                print(f"⚠️  Session monitor stop error: {e}")
        
        print("✅ Unified monitoring stopped")
    
    def reset_all_monitoring(self):
        """Reset all monitoring systems"""
        print("🔄 Resetting Continue-Witty v2.7 Monitoring Systems")
        
        # Stop everything first
        self.stop_unified_monitoring()
        
        # Reset individual monitors
        if self.session_monitor:
            self.session_monitor.reset_session()
        
        if self.context_monitor:
            self.context_monitor.reset_monitoring()
        
        # Reset coordinator state
        self.coordinator_state = {
            "coordinator_started": None,
            "session_id": None,
            "total_triggers_fired": 0,
            "triggers_history": [],
            "last_coordination_check": None
        }
        self._save_coordinator_state()
        
        print("✅ All monitoring systems reset")


def main():
    """Command-line interface for monitoring coordinator"""
    import sys
    
    coordinator = MonitoringCoordinator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            session_id = sys.argv[2] if len(sys.argv) > 2 else None
            result = coordinator.start_unified_monitoring(session_id)
            print(f"\\n🎯 Unified monitoring result: {result['monitors_started']}")
        
        elif command == "status":
            status = coordinator.get_unified_status()
            print("🎯 Continue-Witty v2.7 Unified Status:")
            print("=" * 40)
            print(f"Overall Health: {status['overall_health']}")
            print(f"Monitors: {status['monitors_summary']}")
            print(f"Total Triggers: {status['coordinator']['total_triggers']}")
            
            if status.get("session_monitor"):
                print(f"\\n📅 Session: {status['session_monitor'].get('session_duration_formatted', 'N/A')}")
                print(f"⏰ Remaining: {status['session_monitor'].get('time_remaining_formatted', 'N/A')}")
        
        elif command == "stop":
            coordinator.stop_unified_monitoring()
        
        elif command == "reset":
            coordinator.reset_all_monitoring()
        
        elif command == "test":
            # Test activity update
            print("🧪 Testing unified activity update...")
            result = coordinator.update_activity(
                conversation_text="Test conversation with 95% context usage",
                claude_message="Approaching usage limit - test trigger"
            )
            if result:
                print(f"🎯 Trigger activated: {result.get('action_required', 'unknown')}")
            else:
                print("📝 No triggers activated")
        
        else:
            print("Usage:")
            print("  python monitoring-coordinator.py start [session_id]  # Start unified monitoring")
            print("  python monitoring-coordinator.py status             # Show unified status")
            print("  python monitoring-coordinator.py stop               # Stop all monitoring")
            print("  python monitoring-coordinator.py reset              # Reset all systems")
            print("  python monitoring-coordinator.py test               # Test trigger system")
    
    else:
        print("🎯 Continue-Witty v2.7 Monitoring Coordinator")
        print("=" * 50)
        print("Unified Anti-Amnesia Protection:")
        print("  🟡 Context Window → 90%/95% usage triggers")
        print("  💳 Credit Limits → Usage warning triggers")
        print("  🚨 Session Duration → 4.5h/4.75h/5h triggers")
        print("\\nSingle interface for complete Claude amnesia prevention!")
        print("\\nUse 'start', 'status', 'stop', 'reset', or 'test'")


if __name__ == "__main__":
    main()