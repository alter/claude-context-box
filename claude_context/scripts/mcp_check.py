#!/usr/bin/env python3
"""Check MCP Memory Service status and configuration"""

import json
import os
import subprocess
import sys
from pathlib import Path


def check_mcp_installed():
    """Check if MCP memory service is installed"""
    try:
        # Try via uvx
        result = subprocess.run(
            ["uvx", "--from", "git+https://github.com/doobidoo/mcp-memory-service.git", 
             "mcp-memory-service", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "uvx", result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Try direct import
    try:
        import mcp_memory_service
        return True, "python", mcp_memory_service.__version__
    except ImportError:
        pass
    
    return False, None, None


def check_mcp_database():
    """Check if MCP database exists"""
    db_path = Path.cwd() / ".local" / "mcp" / "memory.db"
    if db_path.exists():
        size = db_path.stat().st_size
        size_mb = size / (1024 * 1024)
        return True, str(db_path), f"{size_mb:.2f} MB"
    return False, None, None


def check_claude_config():
    """Check if Claude Desktop is configured for MCP"""
    import platform
    
    system = platform.system()
    home = Path.home()
    
    config_paths = {
        "Darwin": [
            home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            home / ".config" / "Claude" / "claude_desktop_config.json"
        ],
        "Windows": [
            Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
            home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        ],
        "Linux": [
            home / ".config" / "Claude" / "claude_desktop_config.json",
            home / ".local" / "share" / "Claude" / "claude_desktop_config.json"
        ]
    }
    
    for path in config_paths.get(system, []):
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "mcpServers" in config and "memory" in config["mcpServers"]:
                        return True, str(path)
            except:
                pass
    
    return False, None


def main():
    """Main status check"""
    print("🧠 MCP Memory Service Status")
    print("=" * 50)
    
    # Check installation
    installed, method, version = check_mcp_installed()
    if installed:
        print(f"✅ MCP installed via {method}")
        if version:
            print(f"   Version: {version}")
    else:
        print("❌ MCP not installed")
        print("   Run: python3 .claude/mcp_setup.py")
    
    # Check database
    has_db, db_path, db_size = check_mcp_database()
    if has_db:
        print(f"✅ Database exists: {db_path}")
        print(f"   Size: {db_size}")
    else:
        print("❌ No database found")
        print("   Will be created on first use")
    
    # Check Claude config
    configured, config_path = check_claude_config()
    if configured:
        print(f"✅ Claude Desktop configured")
        print(f"   Config: {config_path}")
    else:
        print("❌ Claude Desktop not configured")
        print("   Run: python3 .claude/mcp_setup.py")
    
    # Overall status
    print("\n" + "=" * 50)
    if installed and configured:
        print("✅ MCP Memory Service is ready!")
        print("\n📚 Available commands:")
        print("  /memory-store \"content\" --tags work,important")
        print("  /memory-search --query \"database decisions\"")
        print("  /memory-recall \"what did we decide last week?\"")
        print("  /memory-health")
    elif installed:
        print("⚠️  MCP installed but Claude not configured")
        print("   Run: python3 .claude/mcp_setup.py")
    else:
        print("❌ MCP not set up")
        print("   To install: MCP_ENABLE=1 python3 install.py")
    
    return 0 if (installed and configured) else 1


if __name__ == "__main__":
    sys.exit(main())