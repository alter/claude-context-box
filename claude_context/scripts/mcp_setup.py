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


def check_uv_installed():
    """Check if uv package manager is installed"""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_uv():
    """Install uv package manager"""
    print("📦 Installing uv package manager...")
    
    if platform.system() == "Windows":
        # Windows installation
        subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-c",
            "irm https://astral.sh/uv/install.ps1 | iex"
        ], check=True)
    else:
        # Unix-like systems
        subprocess.run([
            "sh", "-c",
            "curl -LsSf https://astral.sh/uv/install.sh | sh"
        ], check=True)
    
    print("  ✅ uv installed successfully")


def install_mcp_memory():
    """Install MCP memory service via uvx"""
    print("\n📦 Installing MCP Memory Service...")
    
    try:
        # First ensure uv is installed
        if not check_uv_installed():
            install_uv()
        
        # Install via uvx
        subprocess.run([
            "uvx", "--from", 
            "git+https://github.com/doobidoo/mcp-memory-service.git",
            "mcp-memory-service", "--version"
        ], capture_output=True, check=True)
        
        print("  ✅ MCP Memory Service installed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Failed to install MCP Memory Service: {e}")
        print("  Try manual installation:")
        print("    pip install uv")
        print("    uvx --from git+https://github.com/doobidoo/mcp-memory-service.git mcp-memory-service")
        return False


def configure_claude_desktop(project_path):
    """Configure Claude Desktop to use MCP memory service"""
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
    
    # Determine Python path
    if sys.prefix != sys.base_prefix:
        # In virtual environment
        python_path = str(Path(sys.executable))
    else:
        python_path = sys.executable
    
    # Configure memory service
    config["mcpServers"]["memory"] = {
        "command": "uvx",
        "args": [
            "--from",
            "git+https://github.com/doobidoo/mcp-memory-service.git",
            "mcp-memory-service"
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
    
    print(f"  ✅ Claude Desktop configured")
    
    # Create MCP directories
    mcp_dir = Path(project_path) / ".local" / "mcp"
    (mcp_dir / "backups").mkdir(parents=True, exist_ok=True)
    print(f"  📁 MCP directories created: {mcp_dir}")
    
    return config_path


def test_mcp_service():
    """Test if MCP memory service is working"""
    print("\n🧪 Testing MCP Memory Service...")
    
    try:
        result = subprocess.run([
            "uvx", "--from",
            "git+https://github.com/doobidoo/mcp-memory-service.git",
            "mcp-memory-service", "--version"
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
    
    # Check if user wants to proceed
    if os.environ.get('MCP_AUTO_SETUP', '').lower() not in ('1', 'true', 'yes'):
        response = input("\n❓ Install and configure MCP Memory Service? (y/n): ")
        if response.lower() not in ('y', 'yes'):
            print("⏭️  Skipping MCP setup")
            return
    
    # Install MCP memory service
    if not install_mcp_memory():
        print("\n❌ MCP installation failed")
        return
    
    # Configure Claude Desktop
    config_path = configure_claude_desktop(project_path)
    
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
    print("\n💡 To uninstall:")
    print(f"  Remove 'memory' section from: {config_path}")


if __name__ == "__main__":
    main()