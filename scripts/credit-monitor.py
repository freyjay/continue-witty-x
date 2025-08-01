#!/usr/bin/env python3
"""
💳 Credit Monitor for Continue-Witty Auto-Trigger
================================================

Intelligent monitoring system that detects Claude credit limit warnings
and proactively suggests context backup before session interruption.

Triggers:
- Credit limit notifications
- Usage warnings  
- Session pause alerts
- "Resume at X time" messages

Author: Francis & Claude (v2.5 Enhancement)
Created: July 31, 2025
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

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


class CreditMonitor:
    """Intelligent credit limit monitoring and auto-trigger system"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.config_path = os.path.expanduser("~/.continue-witty/config.json")
        self.config = self._load_config()
        
        # Credit warning patterns to detect
        self.credit_patterns = [
            r"credits?\s+running\s+low",
            r"usage\s+limit\s+(reached|approaching)",
            r"approaching\s+usage\s+limit",
            r"resume\s+at\s+\d+[ap]m",
            r"resets?\s+at\s+\d+[ap]m",
            r"upgrade\s+.*more\s+credit",
            r"session\s+will\s+pause",
            r"daily\s+limit\s+reached",
            r"credits?\s+.*refresh"
        ]
        
        self.generator = None
        if EnhancedPackageGenerator:
            self.generator = EnhancedPackageGenerator(str(project_path))
    
    def _load_config(self) -> Dict:
        """Load configuration with credit monitoring settings"""
        default_config = {
            "credit_auto_trigger": True,
            "credit_prompt_style": "friendly",
            "credit_backup_default": "quick_save",
            "version": "2.5.0"
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return default_config
    
    def detect_credit_warning(self, message: str) -> Dict:
        """Detect if message contains credit limit warnings"""
        message_lower = message.lower()
        
        detected_patterns = []
        for pattern in self.credit_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                detected_patterns.append(pattern)
        
        if detected_patterns:
            # Extract specific details
            resume_time = self._extract_resume_time(message)
            warning_type = self._classify_warning_type(message_lower)
            
            return {
                "credit_warning_detected": True,
                "patterns_matched": detected_patterns,
                "resume_time": resume_time,
                "warning_type": warning_type,
                "original_message": message,
                "confidence": len(detected_patterns) / len(self.credit_patterns)
            }
        
        return {"credit_warning_detected": False}
    
    def _extract_resume_time(self, message: str) -> Optional[str]:
        """Extract resume time from message"""
        time_patterns = [
            r"resume\s+at\s+(\d+[ap]m)",
            r"available\s+at\s+(\d+[ap]m)",
            r"refresh\s+at\s+(\d+[ap]m)"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _classify_warning_type(self, message: str) -> str:
        """Classify the type of credit warning"""
        if "daily limit" in message or "24 hour" in message:
            return "daily_limit"
        elif "upgrade" in message:
            return "upgrade_suggestion"
        elif "running low" in message:
            return "low_credits"
        elif "pause" in message:
            return "session_pause"
        else:
            return "general_limit"
    
    def trigger_backup_prompt(self, warning_info: Dict) -> Dict:
        """Show proactive backup prompt when threshold warning detected"""
        if not self.config.get("credit_auto_trigger", True):
            return {"skipped": True, "reason": "Credit auto-trigger disabled"}
        
        if not self.generator:
            return {"error": "Enhanced package generator not available"}
        
        # Step 1: Ask if they want to backup
        print(f"\\n⚠️  Claude threshold detected - session will pause soon")
        print(f"\\n💾 Would you like to backup your progress before the break? [y/n]")
        
        while True:
            choice = input("\\nBackup? [y/n]: ").strip().lower()
            
            if choice in ["y", "yes"]:
                # Step 2: Show backup options
                return self._show_backup_options(warning_info)
                
            elif choice in ["n", "no"]:
                return {"skipped": True, "reason": "User chose to skip backup"}
                
            else:
                print("❌ Please enter y or n")
    
    def _show_backup_options(self, warning_info: Dict) -> Dict:
        """Show backup package options and execute chosen backup"""
        print(f"\\n📦 Backup Options:")
        print()
        print("1. /continue-witty light    (Quick summary, key findings only)")
        print("2. /continue-witty full     (Complete project state, comprehensive context)")
        print("3. /continue-witty complex  (Maximum detail, technical deep-dive)")
        
        while True:
            choice = input("\\nEnter your choice [1/2/3]: ").strip()
            
            if choice == "1":
                return self._execute_threshold_backup("light", warning_info)
            elif choice == "2":
                return self._execute_threshold_backup("full", warning_info)
            elif choice == "3":
                return self._execute_threshold_backup("complex", warning_info)
            else:
                print("❌ Please enter 1, 2, or 3")
    
    def _generate_threshold_title(self, warning_type: str, resume_time: Optional[str]) -> str:
        """Generate automatic title for threshold backup"""
        time_part = f" (resume {resume_time})" if resume_time else ""
        return f"Threshold backup{time_part}"
    
    def _execute_threshold_backup(self, package_type: str, warning_info: Dict) -> Dict:
        """Execute the backup with threshold warning context"""
        try:
            # Convert package type
            if package_type == "light":
                pkg_type = PackageType.LIGHT
            elif package_type == "full":
                pkg_type = PackageType.FULL
            elif package_type == "complex":
                pkg_type = PackageType.COMPLEX
            else:
                pkg_type = PackageType.FULL  # Default fallback
            
            # Generate threshold title
            resume_time = warning_info.get("resume_time")
            warning_type = warning_info.get("warning_type", "general_limit")
            title = self._generate_threshold_title(warning_type, resume_time)
            
            # Create backup with threshold trigger reason
            trigger_reason = f"threshold-{warning_info.get('warning_type', 'general')}"
            
            # Create backup with auto-created flag
            result = self.generator.create_enhanced_package(
                pkg_type, 
                trigger_reason, 
                auto_created=True
            )
            
            # Update the metadata with our custom title
            if result.get("snapshot_id"):
                snapshot_path = self.generator.snapshots_dir / result["snapshot_id"]
                metadata_file = snapshot_path / "metadata.json"
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        metadata['title'] = title
                        metadata['threshold_trigger'] = True
                        metadata['warning_info'] = warning_info
                        
                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                            
                    except Exception as e:
                        print(f"⚠️  Could not update title: {e}")
            
            result.update({
                "threshold_triggered": True,
                "backup_title": title,
                "warning_info": warning_info
            })
            
            print(f"\\n✅ Threshold backup created: {title}")
            print(f"📸 Snapshot: {result.get('snapshot_id', 'unknown')}")
            print()
            print(f"🌸 Restoration Plan:")
            print(f"   When threshold resets → Wait 2-3 mins → /bloom → Continue!")
            
            return result
            
        except Exception as e:
            return {"error": f"Backup failed: {str(e)}"}
    
    def monitor_session(self, message: str) -> Optional[Dict]:
        """Main monitoring function - call this with Claude messages"""
        warning_info = self.detect_credit_warning(message)
        
        if warning_info.get("credit_warning_detected"):
            return self.trigger_backup_prompt(warning_info)
        
        return None


def main():
    """Command-line interface for credit monitoring"""
    import sys
    
    monitor = CreditMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            # Test with sample credit warning messages
            test_messages = [
                "Your credits are running low. You'll be able to resume at 7am.",
                "Daily usage limit reached. Consider upgrading for more credits.",
                "Session will pause soon due to credit limits.",
                "Credits refresh at 8am tomorrow."
            ]
            
            print("🧪 Testing credit warning detection:")
            for msg in test_messages:
                print(f"\\nTesting: '{msg}'")
                result = monitor.monitor_session(msg)
                if result:
                    print(f"✅ Detected and triggered backup prompt")
                else:
                    print(f"❌ No trigger detected")
        
        elif command == "monitor":
            # Interactive monitoring mode
            print("💳 Credit Monitor Active - paste Claude messages to test detection:")
            print("(Type 'exit' to quit)")
            
            while True:
                message = input("\\nClaude message: ").strip()
                if message.lower() == 'exit':
                    break
                
                result = monitor.monitor_session(message)
                if result:
                    print("🎯 Credit warning detected and backup triggered!")
                else:
                    print("📝 No credit warning detected in message")
        
        else:
            print("Usage:")
            print("  python credit-monitor.py test      # Test detection patterns")
            print("  python credit-monitor.py monitor   # Interactive monitoring")
    
    else:
        print("💳 Continue-Witty Credit Monitor")
        print("================================")
        print("Intelligent credit limit detection and backup triggering")
        print("\\nUse 'test' or 'monitor' commands to try it out!")


if __name__ == "__main__":
    main()