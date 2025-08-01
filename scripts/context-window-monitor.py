#!/usr/bin/env python3
"""
🎯 Context Window Monitor for Continue-Witty v2.7
================================================

Intelligent monitoring system that detects context window usage approaching
auto-compaction thresholds and triggers proactive backup workflow.

Two-Tier Trigger System:
- 10% Warning: Optional base context backup
- 5% Critical: Mandatory delta session backup or full backup

Author: Francis & Claude (v2.7 Production Release)
Created: July 31, 2025
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import re

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


class ContextWindowMonitor:
    """Intelligent context window monitoring with two-tier backup system"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.config_path = os.path.expanduser("~/.continue-witty/config.json")
        self.state_path = os.path.expanduser("~/.continue-witty/context-monitor-state.json")
        self.config = self._load_config()
        self.state = self._load_state()
        
        # Context window estimation patterns
        self.context_indicators = [
            # Token count indicators
            r"(\d+)\s*(?:tokens?|words?)\s*(?:used|remaining|left)",
            r"context\s*(?:window|size|limit)\s*:\s*(\d+)",
            r"(\d+)\s*(?:/|of)\s*(\d+)\s*(?:tokens?|context)",
            
            # Percentage indicators  
            r"(\d+)%\s*(?:context|usage|capacity|used)",
            r"context\s*:\s*(\d+)%",
            
            # Compaction warnings
            r"compacting|summarizing|truncating",
            r"context\s*(?:window\s*)?(?:full|limit|exceeded)",
            r"reducing\s*(?:context|conversation\s*history)"
        ]
        
        # Estimated context thresholds (tokens)
        self.max_context_estimate = 200000  # Conservative estimate for Claude
        self.warning_threshold = 0.90  # 90% = 10% warning
        self.critical_threshold = 0.95  # 95% = 5% critical
        
        self.generator = None
        if EnhancedPackageGenerator:
            self.generator = EnhancedPackageGenerator(str(project_path))
    
    def _load_config(self) -> Dict:
        """Load configuration with context monitoring settings"""
        default_config = {
            "context_monitoring": True,
            "warning_threshold": 0.90,
            "critical_threshold": 0.95,
            "auto_delta_backup": True,
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
    
    def _load_state(self) -> Dict:
        """Load monitoring state"""
        default_state = {
            "last_check": None,
            "warning_triggered": False,
            "base_context_created": False,
            "base_context_snapshot": None,
            "base_context_timestamp": None,
            "critical_triggered": False,
            "estimated_context_usage": 0.0,
            "conversation_exchanges_since_base": 0
        }
        
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r') as f:
                    saved_state = json.load(f)
                    default_state.update(saved_state)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return default_state
    
    def _save_state(self):
        """Save current monitoring state"""
        self.state["last_check"] = datetime.now().isoformat()
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save state: {e}")
    
    def estimate_context_usage(self, conversation_text: str = "") -> float:
        """
        Estimate context window usage based on conversation length and indicators
        Returns: float between 0.0 and 1.0 representing estimated usage percentage
        """
        # Method 1: Look for explicit context indicators in conversation
        for pattern in self.context_indicators:
            matches = re.findall(pattern, conversation_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        # Handle patterns like "1000/2000 tokens"
                        if len(match) == 2 and match[1].isdigit():
                            used = int(match[0]) if match[0].isdigit() else 0
                            total = int(match[1])
                            if total > 0:
                                return min(used / total, 1.0)
                        # Handle single number patterns
                        elif match[0].isdigit():
                            percentage = int(match[0])
                            if percentage <= 100:
                                return percentage / 100.0
                    elif isinstance(match, str) and match.isdigit():
                        percentage = int(match)
                        if percentage <= 100:
                            return percentage / 100.0
        
        # Method 2: Estimate based on conversation length (rough approximation)
        char_count = len(conversation_text)
        estimated_tokens = char_count / 4  # Rough chars-to-tokens ratio
        estimated_usage = estimated_tokens / self.max_context_estimate
        
        # Method 3: Increment based on exchange count (conservative estimate)
        exchanges = self.state.get("conversation_exchanges_since_base", 0)
        base_usage = self.state.get("estimated_context_usage", 0.0)
        
        # Each exchange adds roughly 0.5-2% context usage
        exchange_increment = exchanges * 0.015  # 1.5% per exchange
        
        # Use the highest estimate (most conservative)
        final_estimate = max(estimated_usage, base_usage + exchange_increment)
        
        return min(final_estimate, 1.0)
    
    def check_context_thresholds(self, conversation_text: str = "") -> Dict:
        """Check if context usage has crossed warning or critical thresholds"""
        current_usage = self.estimate_context_usage(conversation_text)
        self.state["estimated_context_usage"] = current_usage
        
        result = {
            "current_usage": current_usage,
            "current_percentage": f"{current_usage * 100:.1f}%",
            "warning_threshold_crossed": False,
            "critical_threshold_crossed": False,
            "action_required": None,
            "message": None
        }
        
        # Check critical threshold (5% remaining)
        if current_usage >= self.critical_threshold and not self.state.get("critical_triggered"):
            result["critical_threshold_crossed"] = True
            result["action_required"] = "critical_backup"
            
            if self.state.get("base_context_created"):
                result["message"] = f"🔴 CRITICAL: {result['current_percentage']} context used! Creating delta session backup..."
                result["backup_type"] = "delta_session"
            else:
                result["message"] = f"🔴 CRITICAL: {result['current_percentage']} context used! Full backup required!"
                result["backup_type"] = "full_backup"
            
            self.state["critical_triggered"] = True
        
        # Check warning threshold (10% remaining)
        elif current_usage >= self.warning_threshold and not self.state.get("warning_triggered"):
            result["warning_threshold_crossed"] = True
            result["action_required"] = "warning_backup"
            result["message"] = f"🟡 WARNING: {result['current_percentage']} context used. Create base context backup?"
            result["backup_type"] = "base_context"
            
            self.state["warning_triggered"] = True
        
        self._save_state()
        return result
    
    def handle_warning_trigger(self, auto_response: str = None) -> Dict:
        """Handle 10% warning trigger - optional base context creation"""
        if not self.generator:
            return {"error": "Enhanced package generator not available"}
        
        print(f"\\n🟡 Context Window Warning - 10% Remaining")
        print(f"Create base context backup now? This preserves current state.")
        print(f"If declined, you'll get another chance at 5% remaining.")
        print()
        
        if auto_response:
            choice = auto_response.lower()
            print(f"Auto-response: {choice}")
        else:
            while True:
                choice = input("Create base context backup? [y/n]: ").strip().lower()
                break
        
        if choice in ["y", "yes"]:
            return self._create_base_context()
        elif choice in ["n", "no"]:
            print("⏭️  Skipping base context backup. Will prompt again at 5%.")
            return {"skipped": True, "reason": "User declined base context backup"}
        else:
            print("❌ Invalid choice, defaulting to 'no'")
            return {"skipped": True, "reason": "Invalid input, defaulted to no"}
    
    def handle_critical_trigger(self) -> Dict:
        """Handle 5% critical trigger - mandatory backup"""
        if not self.generator:
            return {"error": "Enhanced package generator not available"}
        
        if self.state.get("base_context_created"):
            # Create delta session (10% → 5% conversation)
            return self._create_delta_session()
        else:
            # Create full backup (user declined at 10%)
            return self._create_full_critical_backup()
    
    def _create_base_context(self) -> Dict:
        """Create base context backup at 10% warning"""
        try:
            print("\\n🎯 Creating Base Context Backup...")
            
            result = self.generator.create_enhanced_package(
                PackageType.FULL,
                trigger_reason="context-warning-10pct",
                auto_created=False
            )
            
            if result.get("success"):
                self.state["base_context_created"] = True
                self.state["base_context_snapshot"] = result.get("snapshot_id")
                self.state["base_context_timestamp"] = datetime.now().isoformat()
                self.state["conversation_exchanges_since_base"] = 0
                self._save_state()
                
                print(f"\\n✅ Base Context Created: {result.get('snapshot_id')}")
                print(f"📊 Monitoring continues... Next backup at 5% if needed.")
                
                result.update({
                    "backup_type": "base_context",
                    "base_context_snapshot": result.get("snapshot_id")
                })
            
            return result
        
        except Exception as e:
            return {"error": f"Base context creation failed: {str(e)}"}
    
    def _create_delta_session(self) -> Dict:
        """Create delta session backup (10% → 5% conversation)"""
        try:
            print("\\n🔄 Creating Delta Session Backup...")
            print(f"Base Context: {self.state.get('base_context_snapshot', 'unknown')}")
            print(f"Delta: {self.state.get('conversation_exchanges_since_base', 0)} exchanges since base")
            
            # Create delta session with conversation export focused on recent exchanges
            delta_exchanges = max(self.state.get("conversation_exchanges_since_base", 0), 3)
            
            result = self.generator.create_enhanced_package(
                PackageType.COMPLEX,  # Complex for maximum delta detail  
                trigger_reason="context-critical-5pct-delta",
                auto_created=True,
                conversation_exchanges=delta_exchanges
            )
            
            if result.get("success"):
                # Update metadata to reference base context
                snapshot_path = self.generator.snapshots_dir / result["snapshot_id"]
                metadata_file = snapshot_path / "metadata.json"
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        metadata.update({
                            'title': f"Delta Session ({delta_exchanges} exchanges)",
                            'backup_type': 'delta_session',
                            'base_context_snapshot': self.state.get('base_context_snapshot'),
                            'base_context_timestamp': self.state.get('base_context_timestamp'),
                            'delta_exchanges': delta_exchanges,
                            'context_usage_at_trigger': f"{self.state.get('estimated_context_usage', 0) * 100:.1f}%"
                        })
                        
                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                            
                    except Exception as e:
                        print(f"⚠️  Could not update delta metadata: {e}")
                
                print(f"\\n✅ Delta Session Created: {result.get('snapshot_id')}")
                print(f"📊 Base Context: {self.state.get('base_context_snapshot')}")
                print(f"🔄 Delta Exchanges: {delta_exchanges}")
                
                result.update({
                    "backup_type": "delta_session",
                    "base_context_snapshot": self.state.get('base_context_snapshot'),
                    "delta_exchanges": delta_exchanges
                })
            
            return result
        
        except Exception as e:
            return {"error": f"Delta session creation failed: {str(e)}"}
    
    def _create_full_critical_backup(self) -> Dict:
        """Create full backup at 5% critical (user declined 10% warning)"""
        try:
            print("\\n🔴 Creating Full Critical Backup...")
            print("Base context was not created at 10%. Creating comprehensive backup now.")
            
            result = self.generator.create_enhanced_package(
                PackageType.COMPLEX,
                trigger_reason="context-critical-5pct-full",
                auto_created=True
            )
            
            if result.get("success"):
                print(f"\\n✅ Full Critical Backup Created: {result.get('snapshot_id')}")
                print(f"📊 Context Usage: {self.state.get('estimated_context_usage', 0) * 100:.1f}%")
                
                result.update({
                    "backup_type": "full_critical",
                    "context_usage_at_trigger": f"{self.state.get('estimated_context_usage', 0) * 100:.1f}%"
                })
            
            return result
        
        except Exception as e:
            return {"error": f"Full critical backup failed: {str(e)}"}
    
    def increment_exchange_count(self):
        """Increment conversation exchange count since base context"""
        self.state["conversation_exchanges_since_base"] = self.state.get("conversation_exchanges_since_base", 0) + 1
        self._save_state()
    
    def reset_monitoring(self):
        """Reset monitoring state (e.g., after session restart)"""
        self.state = {
            "last_check": None,
            "warning_triggered": False,
            "base_context_created": False,
            "base_context_snapshot": None,
            "base_context_timestamp": None,
            "critical_triggered": False,
            "estimated_context_usage": 0.0,
            "conversation_exchanges_since_base": 0
        }
        self._save_state()
        print("🔄 Context monitoring state reset")
    
    def monitor_conversation(self, conversation_text: str = "") -> Optional[Dict]:
        """
        Main monitoring function - call this with conversation text
        Returns action dict if threshold crossed, None otherwise
        """
        if not self.config.get("context_monitoring", True):
            return None
        
        # Increment exchange count
        self.increment_exchange_count()
        
        # Check thresholds
        threshold_result = self.check_context_thresholds(conversation_text)
        
        if threshold_result.get("critical_threshold_crossed"):
            return self.handle_critical_trigger()
        elif threshold_result.get("warning_threshold_crossed"):
            return self.handle_warning_trigger()
        
        return None
    
    def get_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            "context_usage": f"{self.state.get('estimated_context_usage', 0) * 100:.1f}%",
            "warning_triggered": self.state.get("warning_triggered", False),
            "critical_triggered": self.state.get("critical_triggered", False),
            "base_context_created": self.state.get("base_context_created", False),
            "base_context_snapshot": self.state.get("base_context_snapshot"),
            "exchanges_since_base": self.state.get("conversation_exchanges_since_base", 0),
            "monitoring_active": self.config.get("context_monitoring", True)
        }


def main():
    """Command-line interface for context window monitor"""
    import sys
    
    monitor = ContextWindowMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            status = monitor.get_status()
            print("🎯 Context Window Monitor Status:")
            print("=" * 40)
            for key, value in status.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        elif command == "reset":
            monitor.reset_monitoring()
        
        elif command == "test":
            # Test with sample conversation
            test_conversation = "This is a test conversation " * 100
            print(f"🧪 Testing with sample conversation ({len(test_conversation)} chars)")
            result = monitor.monitor_conversation(test_conversation)
            if result:
                print(f"🎯 Trigger activated: {result}")
            else:
                print("📝 No triggers activated")
        
        else:
            print("Usage:")
            print("  python context-window-monitor.py status  # Show current status")
            print("  python context-window-monitor.py reset   # Reset monitoring state")
            print("  python context-window-monitor.py test    # Test with sample data")
    
    else:
        print("🎯 Continue-Witty Context Window Monitor v2.7")
        print("=" * 50)
        print("Intelligent two-tier backup system:")
        print("  🟡 10% Warning → Optional base context backup")
        print("  🔴 5% Critical → Mandatory delta session or full backup")
        print("\\nUse 'status', 'reset', or 'test' commands")


if __name__ == "__main__":
    main()