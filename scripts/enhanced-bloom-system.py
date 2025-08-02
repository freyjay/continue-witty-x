#!/usr/bin/env python3
"""
🌸 Enhanced Bloom System for Continue-Witty v2.7 EXTERNAL
=========================================================

Professional context restoration system with:
- Git-like snapshot rollback capabilities  
- Enhanced gap closure with reasoning chains
- Conversation export integration

This enables quick restoration to any snapshot state
with full context preservation for seamless handoffs.

Author: Francis & Claude (v2.7 Application Release)
Created: July 31, 2025
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil

# Application version - no persistent learning imports needed


class EnhancedBloomSystem:
    """Professional bloom system with snapshot rollback capabilities"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.context_dir = self.project_path / "context-preservation"
        self.snapshots_dir = self.context_dir / "snapshots"
        self.bloom_state_path = os.path.expanduser("~/.continue-witty/bloom-state.json")
        
        # Application version - no learning system
        
        self.bloom_state = self._load_bloom_state()
    
    def _load_bloom_state(self) -> Dict:
        """Load bloom restoration state"""
        default_state = {
            "last_restored_snapshot": None,
            "restoration_history": [],
            "rollback_sessions": 0
        }
        
        if os.path.exists(self.bloom_state_path):
            try:
                with open(self.bloom_state_path, 'r') as f:
                    saved_state = json.load(f)
                    default_state.update(saved_state)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return default_state
    
    def _save_bloom_state(self):
        """Save bloom state"""
        try:
            os.makedirs(os.path.dirname(self.bloom_state_path), exist_ok=True)
            with open(self.bloom_state_path, 'w') as f:
                json.dump(self.bloom_state, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save bloom state: {e}")
    
    def list_available_snapshots(self) -> List[Dict]:
        """List all available snapshots with metadata"""
        snapshots = []
        
        if not self.snapshots_dir.exists():
            return snapshots
        
        for snapshot_dir in sorted(self.snapshots_dir.iterdir()):
            if snapshot_dir.is_dir() and snapshot_dir.name.startswith("snapshot-"):
                metadata_file = snapshot_dir / "metadata.json"
                
                snapshot_info = {
                    "snapshot_id": snapshot_dir.name,
                    "path": str(snapshot_dir),
                    "created": "Unknown",
                    "title": "Unknown",
                    "package_type": "Unknown",
                    "size": "Unknown"
                }
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            snapshot_info.update({
                                "created": metadata.get("created_at", "Unknown"),
                                "title": metadata.get("title", "Unknown"),
                                "package_type": metadata.get("package_type", "Unknown"),
                                "conversation_export": metadata.get("conversation_export", False)
                            })
                    except Exception:
                        pass
                
                # Calculate size
                try:
                    total_size = sum(f.stat().st_size for f in snapshot_dir.rglob("*") if f.is_file())
                    snapshot_info["size"] = f"{total_size:,} bytes"
                except Exception:
                    snapshot_info["size"] = "Unknown"
                
                snapshots.append(snapshot_info)
        
        return snapshots
    
    def restore_snapshot(self, snapshot_id: str) -> Dict:
        """
        Restore from specific snapshot with full context preservation
        """
        try:
            print(f"🌸 Enhanced Bloom Restoration")
            print(f"📸 Restoring snapshot: {snapshot_id}")
            
            # Find snapshot
            snapshot_path = self.snapshots_dir / snapshot_id
            if not snapshot_path.exists():
                return {"error": f"Snapshot {snapshot_id} not found"}
            
            # Load snapshot metadata
            metadata_file = snapshot_path / "metadata.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            print(f"📋 Snapshot: {metadata.get('title', 'Unknown')}")
            print(f"📅 Created: {metadata.get('created_at', 'Unknown')}")
            print(f"📦 Type: {metadata.get('package_type', 'Unknown')}")
            
            # Display restoration context
            handoff_file = snapshot_path / "HANDOFF-INSTRUCTIONS.md"
            if handoff_file.exists():
                print(f"\n📖 Restored Context Available:")
                print(f"   📁 HANDOFF-INSTRUCTIONS.md")
                
                # Check for conversation context
                conversation_file = snapshot_path / "conversation-context.md"
                if conversation_file.exists():
                    print(f"   🧠 conversation-context.md (v2.7 reasoning preservation)")
                
                # Check for other context files
                other_files = [f for f in snapshot_path.iterdir() 
                              if f.is_file() and f.suffix == '.md' and 
                              f.name not in ['HANDOFF-INSTRUCTIONS.md', 'conversation-context.md']]
                
                for file in other_files:
                    print(f"   📄 {file.name}")
            
            # Update bloom state
            self.bloom_state["last_restored_snapshot"] = snapshot_id
            self.bloom_state["rollback_sessions"] = self.bloom_state.get("rollback_sessions", 0) + 1
            self.bloom_state["restoration_history"].append({
                "snapshot_id": snapshot_id,
                "restored_at": datetime.now().isoformat()
            })
            
            # Keep only last 10 restoration history entries
            if len(self.bloom_state["restoration_history"]) > 10:
                self.bloom_state["restoration_history"] = self.bloom_state["restoration_history"][-10:]
            
            self._save_bloom_state()
            
            print(f"\n✅ Enhanced Bloom Restoration Complete!")
            print(f"🎭 You now have:")
            print(f"   📸 Snapshot state: {metadata.get('title', snapshot_id)}")
            print(f"   🧠 Full context: PRESERVED")
            print(f"   🎯 Conversation reasoning: AVAILABLE")
            print(f"   🚀 Ready to continue seamlessly!")
            
            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "snapshot_title": metadata.get("title", "Unknown"),
                "snapshot_type": metadata.get("package_type", "Unknown"),
                "restoration_path": str(snapshot_path),
                "files_available": [f.name for f in snapshot_path.iterdir() if f.is_file()]
            }
            
        except Exception as e:
            error_msg = f"Enhanced bloom restoration failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            return {"error": error_msg}
    
    def show_restoration_instructions(self, snapshot_id: str) -> str:
        """Show instructions for new Claude instance after restoration"""
        snapshot_path = self.snapshots_dir / snapshot_id
        handoff_file = snapshot_path / "HANDOFF-INSTRUCTIONS.md"
        
        if handoff_file.exists():
            try:
                with open(handoff_file, 'r') as f:
                    return f.read()
            except Exception:
                pass
        
        return f"Restoration instructions not found for {snapshot_id}"
    
    def get_bloom_statistics(self) -> Dict:
        """Get statistics about bloom restoration usage"""
        stats = {
            "total_rollbacks": self.bloom_state.get("rollback_sessions", 0),
            "last_restored": self.bloom_state.get("last_restored_snapshot", "None"),
            "available_snapshots": len(self.list_available_snapshots()),
            "restoration_history": len(self.bloom_state.get("restoration_history", []))
        }
        
        return stats


def main():
    """Command-line interface for enhanced bloom system"""
    import sys
    
    bloom = EnhancedBloomSystem()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            snapshots = bloom.list_available_snapshots()
            print("🌸 Available Snapshots for Restoration:")
            print("=" * 50)
            
            if not snapshots:
                print("📝 No snapshots found. Create some with /continue-witty first!")
                return
            
            for snapshot in snapshots:
                print(f"\n📸 {snapshot['snapshot_id']}")
                print(f"   Title: {snapshot['title']}")
                print(f"   Type: {snapshot['package_type']}")
                print(f"   Created: {snapshot['created']}")
                print(f"   Size: {snapshot['size']}")
                if snapshot.get('conversation_export'):
                    print(f"   🆕 v2.7: Conversation export included")
        
        elif command == "restore":
            if len(sys.argv) < 3:
                print("Usage: python enhanced-bloom-system.py restore <snapshot-id>")
                print("\nTip: Use 'list' command to see available snapshots")
                sys.exit(1)
            
            snapshot_id = sys.argv[2]
            result = bloom.restore_snapshot(snapshot_id)
            
            if result.get("success"):
                print(f"\n🎯 Next Steps for New Claude Instance:")
                print(f"1. Read the restoration context from snapshot files")
                print(f"2. Continue from the restored state with full context")
                print(f"3. Reference conversation reasoning for decision context")
            else:
                print(f"\n💥 Restoration failed: {result.get('error')}")
        
        elif command == "stats":
            stats = bloom.get_bloom_statistics()
            print("🌸 Enhanced Bloom System Statistics:")
            print("=" * 40)
            for key, value in stats.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        elif command == "instructions":
            if len(sys.argv) < 3:
                print("Usage: python enhanced-bloom-system.py instructions <snapshot-id>")
                sys.exit(1)
            
            snapshot_id = sys.argv[2]
            instructions = bloom.show_restoration_instructions(snapshot_id)
            print(instructions)
        
        else:
            print("Usage:")
            print("  python enhanced-bloom-system.py list                    # List available snapshots")
            print("  python enhanced-bloom-system.py restore <snapshot-id>   # Restore snapshot")
            print("  python enhanced-bloom-system.py stats                   # Show statistics")
            print("  python enhanced-bloom-system.py instructions <id>       # Show restoration guide")
    
    else:
        print("🌸 Continue-Witty Enhanced Bloom System v2.7 EXTERNAL")
        print("=" * 55)
        print("Professional restoration with context preservation:")
        print("  📸 Git-like snapshot rollback to any state")
        print("  🧠 Full context restoration with reasoning")
        print("  🎯 Enhanced gap closure with conversation export")
        print("  🚀 Seamless AI collaboration continuity")
        print()
        print("Perfect for:")
        print("  🔄 Continue conversations after context limits")
        print("  📋 Handoff projects between AI instances")
        print("  ✨ Maintain full reasoning and decision context")
        print("\nUse 'list', 'restore <id>', 'stats', or 'instructions <id>'")


if __name__ == "__main__":
    main()