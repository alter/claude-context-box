#!/usr/bin/env python3
"""Check MCP Memory Service status and configuration"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def get_python_executable():
    """Get the Python executable from venv or system"""
    # Check if we're in a venv
    if sys.prefix != sys.base_prefix:
        return sys.executable
    
    # Check for venv in project
    project_dir = Path.cwd()
    for venv_name in ['venv', '.venv']:
        venv_path = project_dir / venv_name
        if venv_path.exists():
            if platform.system() == "Windows":
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"
            
            if python_exe.exists():
                return str(python_exe)
    
    # Fallback to system Python
    return sys.executable


def check_mcp_installed():
    """Check if MCP memory service is installed in venv"""
    python_exe = get_python_executable()
    
    try:
        # Try to run MCP from venv
        result = subprocess.run(
            [python_exe, "-m", "mcp_memory_service", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "venv", result.stdout.strip()
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
        
        # Check for backup
        backup_path = Path.cwd() / ".local" / "mcp" / "memory_pre_compact.db"
        has_backup = backup_path.exists()
        
        return True, str(db_path), f"{size_mb:.2f} MB", has_backup
    return False, None, None, False


def check_claude_config():
    """Check if Claude Desktop is configured for MCP"""
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
                        # Check if using venv Python
                        command = config["mcpServers"]["memory"].get("command", "")
                        using_venv = "venv" in command or ".venv" in command
                        return True, str(path), using_venv
            except:
                pass
    
    return False, None, False


def check_hooks_config():
    """Check if MCP hooks are configured"""
    hooks_path = Path.cwd() / ".claude-hooks.toml"
    if hooks_path.exists():
        with open(hooks_path, 'r', encoding='utf-8') as f:
            content = f.read()
            has_mcp_hooks = "MCP Memory Context" in content
            has_pre_compact = "PreCompact" in content and "memory_pre_compact.db" in content
            has_post_compact = "PostCompact" in content and "memory_pre_compact.db" in content
            return True, has_mcp_hooks, has_pre_compact, has_post_compact
    return False, False, False, False


def main():
    """Main status check"""
    print("🧠 MCP Memory Service Status")
    print("=" * 50)
    
    # Check venv
    python_exe = get_python_executable()
    if "venv" in python_exe or ".venv" in python_exe:
        print(f"✅ Using venv Python: {python_exe}")
    else:
        print(f"⚠️  Using system Python: {python_exe}")
    
    # Check installation
    installed, method, version = check_mcp_installed()
    if installed:
        print(f"✅ MCP installed in {method}")
        if version:
            print(f"   Version: {version}")
    else:
        print("❌ MCP not installed")
        print("   Run: python3 .claude/mcp_setup.py")
    
    # Check database
    has_db, db_path, db_size, has_backup = check_mcp_database()
    if has_db:
        print(f"✅ Database exists: {db_path}")
        print(f"   Size: {db_size}")
        if has_backup:
            print("   ✅ Pre-compact backup exists")
    else:
        print("❌ No database found")
        print("   Will be created on first use")
    
    # Check Claude config
    configured, config_path, using_venv = check_claude_config()
    if configured:
        print(f"✅ Claude Desktop configured")
        print(f"   Config: {config_path}")
        if using_venv:
            print("   ✅ Using venv Python")
        else:
            print("   ⚠️  Not using venv Python")
    else:
        print("❌ Claude Desktop not configured")
        print("   Run: python3 .claude/mcp_setup.py")
    
    # Check hooks
    has_hooks, has_mcp, has_pre, has_post = check_hooks_config()
    if has_hooks:
        print("✅ Hooks configuration exists")
        if has_mcp:
            print("   ✅ MCP memory hooks configured")
            if has_pre and has_post:
                print("   ✅ Pre/post compact hooks ready")
        else:
            print("   ⚠️  MCP hooks not configured")
    else:
        print("⚠️  No hooks configuration")
    
    # Overall status
    print("\n" + "=" * 50)
    if installed and configured and using_venv:
        print("✅ MCP Memory Service is ready!")
        print("\n📚 Available commands:")
        print("  /memory-store \"content\" --tags work,important")
        print("  /memory-search --query \"database decisions\"")
        print("  /memory-recall \"what did we decide last week?\"")
        print("  /memory-health")
        if has_mcp and has_pre and has_post:
            print("\n✅ Memory context preserved during compact")
    elif installed:
        print("⚠️  MCP installed but Claude not configured")
        print("   Run: python3 .claude/mcp_setup.py")
    else:
        print("❌ MCP not set up")
        print("   To install: MCP_ENABLE=1 python3 install.py")
    
    return 0 if (installed and configured) else 1


if __name__ == "__main__":
    sys.exit(main())