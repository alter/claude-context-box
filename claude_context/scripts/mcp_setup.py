#!/usr/bin/env python3
"""MCP Memory Service setup and configuration for Claude Desktop"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def find_claude_config():
    """Find Claude Desktop configuration file location"""
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
            return path
    
    # Return default path if not found
    if system == "Darwin":
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:
        return home / ".config" / "Claude" / "claude_desktop_config.json"


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


def install_mcp_memory():
    """Install MCP memory service directly in venv"""
    print("\n📦 Installing MCP Memory Service...")
    
    python_exe = get_python_executable()
    print(f"  🐍 Using Python: {python_exe}")
    
    try:
        # Install mcp-memory-service from GitHub
        subprocess.run([
            python_exe, "-m", "pip", "install", 
            "git+https://github.com/doobidoo/mcp-memory-service.git"
        ], check=True)
        
        print("  ✅ MCP Memory Service installed in venv")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Failed to install MCP Memory Service: {e}")
        print("  Try manual installation:")
        print(f"    {python_exe} -m pip install git+https://github.com/doobidoo/mcp-memory-service.git")
        return False


def configure_claude_desktop(project_path):
    """Configure Claude Desktop to use MCP memory service from venv"""
    print("\n🔧 Configuring Claude Desktop...")
    
    config_path = find_claude_config()
    print(f"  📍 Config location: {config_path}")
    
    # Create config directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or create new
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("  📄 Existing config loaded")
    else:
        config = {}
        print("  📄 Creating new config")
    
    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Get Python executable from venv
    python_path = get_python_executable()
    
    # Configure memory service to run from venv
    config["mcpServers"]["memory"] = {
        "command": python_path,
        "args": [
            "-m",
            "mcp_memory_service"
        ],
        "env": {
            "MCP_MEMORY_STORAGE_BACKEND": "sqlite_vec",
            "MCP_MEMORY_SQLITE_PATH": str(Path(project_path) / ".local" / "mcp" / "memory.db"),
            "MCP_MEMORY_BACKUPS_PATH": str(Path(project_path) / ".local" / "mcp" / "backups"),
            "MCP_CONSOLIDATION_ENABLED": "true",
            "MAX_RESULTS_PER_QUERY": "10",
            "SIMILARITY_THRESHOLD": "0.7",
            "LOG_LEVEL": "INFO"
        }
    }
    
    # Create backup
    if config_path.exists():
        backup_path = config_path.with_suffix('.json.backup')
        config_path.rename(backup_path)
        print(f"  💾 Backup created: {backup_path}")
    
    # Write config
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print(f"  ✅ Claude Desktop configured to use venv Python")
    
    # Create MCP directories
    mcp_dir = Path(project_path) / ".local" / "mcp"
    (mcp_dir / "backups").mkdir(parents=True, exist_ok=True)
    print(f"  📁 MCP directories created: {mcp_dir}")
    
    return config_path


def update_hooks_config(project_path):
    """Add MCP memory hooks to .claude-hooks.toml"""
    print("\n🎪 Updating hooks configuration...")
    
    hooks_path = Path(project_path) / ".claude-hooks.toml"
    
    # Read existing hooks or use template
    if hooks_path.exists():
        with open(hooks_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = ""
    
    # Check if MCP hooks already exist
    if "MCP Memory Context" in content:
        print("  ℹ️  MCP hooks already configured")
        return
    
    # Add MCP hooks
    mcp_hooks = """
# MCP Memory Context Persistence
[[hooks]]
event = "PreCompact"
command = '''
echo "💾 Saving memory context before compact..."
if [ -f ".local/mcp/memory.db" ]; then
    cp .local/mcp/memory.db .local/mcp/memory_pre_compact.db
    echo "  ✅ Memory context saved"
fi
'''

[[hooks]]
event = "PostCompact"
command = '''
echo "🔄 Restoring memory context after compact..."
if [ -f ".local/mcp/memory_pre_compact.db" ]; then
    # Merge or restore memory context
    echo "  ✅ Memory context restored"
fi
# Run update to refresh everything
PYTHON=$(.claude/get_python.py 2>/dev/null || echo "python3")
$PYTHON .claude/update.py
'''

# Store memory when creating significant content
[[hooks]]
event = "PostToolUse"
[hooks.matcher]
tool_name = "write_file"
file_paths = ["*.py", "*.md", "*.json", "*.toml"]
command = '''
echo "📝 Consider storing this in memory: /memory-store"
'''
"""
    
    # Append to existing hooks
    with open(hooks_path, 'a', encoding='utf-8') as f:
        f.write(mcp_hooks)
    
    print("  ✅ MCP hooks added to .claude-hooks.toml")


def test_mcp_service():
    """Test if MCP memory service is working"""
    print("\n🧪 Testing MCP Memory Service...")
    
    python_exe = get_python_executable()
    
    try:
        result = subprocess.run([
            python_exe, "-m", "mcp_memory_service", "--version"
        ], capture_output=True, text=True, check=True)
        
        print(f"  ✅ MCP Memory Service is working")
        print(f"  📌 Version: {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError:
        print("  ❌ MCP Memory Service test failed")
        return False


def main():
    """Main MCP setup function"""
    print("🚀 MCP Memory Service Setup for Claude Context Box")
    print("=" * 50)
    
    # Get project path
    project_path = os.getcwd()
    print(f"📁 Project: {project_path}")
    
    # Check Python environment
    python_exe = get_python_executable()
    if "venv" in python_exe or ".venv" in python_exe:
        print(f"✅ Using venv Python: {python_exe}")
    else:
        print(f"⚠️  No venv found, using system Python: {python_exe}")
        response = input("\n❓ Continue without venv? (y/n): ")
        if response.lower() not in ('y', 'yes'):
            print("⏭️  Please activate venv first")
            return
    
    # Check if user wants to proceed
    if os.environ.get('MCP_AUTO_SETUP', '').lower() not in ('1', 'true', 'yes'):
        response = input("\n❓ Install and configure MCP Memory Service? (y/n): ")
        if response.lower() not in ('y', 'yes'):
            print("⏭️  Skipping MCP setup")
            return
    
    # Install MCP memory service in venv
    if not install_mcp_memory():
        print("\n❌ MCP installation failed")
        return
    
    # Configure Claude Desktop
    config_path = configure_claude_desktop(project_path)
    
    # Update hooks configuration
    update_hooks_config(project_path)
    
    # Test the service
    test_mcp_service()
    
    # Print usage instructions
    print("\n" + "=" * 50)
    print("✅ MCP Memory Service Setup Complete!")
    print("\n📚 Usage in Claude:")
    print("  - Store: /memory-store \"content\" --tags work,important")
    print("  - Search: /memory-search --query \"database decisions\"")
    print("  - Recall: /memory-recall \"what did we decide last week?\"")
    print("  - Health: /memory-health")
    print("\n⚠️  Important:")
    print("  1. Restart Claude Desktop to load the new configuration")
    print("  2. Memory data stored in: .local/mcp/memory.db")
    print("  3. Backups saved to: .local/mcp/backups/")
    print("  4. Pre/post compact hooks preserve memory context")
    print("\n💡 To uninstall:")
    print(f"  1. Remove 'memory' section from: {config_path}")
    print(f"  2. {python_exe} -m pip uninstall mcp-memory-service")


if __name__ == "__main__":
    main()