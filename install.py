#!/usr/bin/env python3
"""
Claude Context Box Universal Installer

One-command installation for Claude Context Box system.
Supports customization via environment variables.

Usage:
    curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -

Environment Variables:
    CLAUDE_VERSION    - Specific version to install (default: latest)
    CLAUDE_HOME       - Installation directory (default: current dir)
    CLAUDE_NO_VENV    - Skip virtual environment creation (default: create)
    CLAUDE_FORCE      - Force reinstall even if exists (default: false)
    CLAUDE_UNINSTALL  - Uninstall instead of install (default: false)
"""

import os
import sys
import subprocess
import shutil
import tempfile
import urllib.request
import json
from pathlib import Path

# Configuration
GITHUB_REPO = "alter/claude-context-box"
PACKAGE_NAME = "claude-context-box"

class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text, color=Colors.GREEN):
    print(f"{color}{text}{Colors.END}")

def print_header():
    print_colored("=" * 60, Colors.BLUE)
    print_colored("🚀 Claude Context Box Universal Installer", Colors.BOLD)
    print_colored("=" * 60, Colors.BLUE)

def check_python():
    """Ensure Python 3.7+ is available"""
    if sys.version_info < (3, 7):
        print_colored("❌ Python 3.7+ required. Current version: " + sys.version, Colors.RED)
        sys.exit(1)
    print_colored(f"✅ Python {sys.version.split()[0]} detected", Colors.GREEN)

def get_env_config():
    """Get configuration from environment variables"""
    config = {
        'version': os.getenv('CLAUDE_VERSION', 'latest'),
        'home': Path(os.getenv('CLAUDE_HOME', os.getcwd())),
        'no_venv': os.getenv('CLAUDE_NO_VENV', '').lower() in ('1', 'true', 'yes'),
        'force': os.getenv('CLAUDE_FORCE', '').lower() in ('1', 'true', 'yes'),
        'uninstall': os.getenv('CLAUDE_UNINSTALL', '').lower() in ('1', 'true', 'yes'),
    }
    
    print_colored(f"📁 Installation directory: {config['home']}", Colors.BLUE)
    print_colored(f"🐍 Virtual environment: {'disabled' if config['no_venv'] else 'enabled'}", Colors.BLUE)
    
    return config

def run_command(cmd, cwd=None, capture=True, env=None):
    """Run shell command with error handling. Returns result object on success, None on failure."""
    print_colored(f"▶️  Executing: {cmd}", Colors.BLUE)
    try:
        # Always capture output to provide debug info on failure.
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            env=env
        )
        # If the original call didn't want to capture, we can print stdout
        # to simulate the non-captured behavior.
        if not capture and result.stdout:
            print(result.stdout.strip())
        
        return result
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Command failed with exit code {e.returncode}: {cmd}", Colors.RED)
        if e.stdout:
            print_colored("------- STDOUT -------", Colors.YELLOW)
            print(e.stdout.strip())
            print_colored("----------------------", Colors.YELLOW)
        if e.stderr:
            print_colored("------- STDERR -------", Colors.RED)
            print(e.stderr.strip())
            print_colored("----------------------", Colors.RED)
        return None

def check_existing_installation(config):
    """Check if Claude Context Box is already installed"""
    claude_dir = config['home'] / '.claude'
    venv_dir = config['home'] / 'venv'
    
    if claude_dir.exists() or venv_dir.exists():
        if config['force']:
            print_colored("🔄 Force reinstall enabled - removing existing installation", Colors.YELLOW)
            if claude_dir.exists():
                shutil.rmtree(claude_dir)
            return False
        else:
            print_colored("⚠️  Claude Context Box already installed", Colors.YELLOW)
            print_colored("Use CLAUDE_FORCE=1 to reinstall", Colors.YELLOW)
            return True
    
    return False

def setup_virtual_environment(config):
    """Create and setup virtual environment"""
    if config['no_venv']:
        print_colored("⏭️  Skipping virtual environment creation", Colors.YELLOW)
        return sys.executable
    
    # Check for existing virtual environments first
    print_colored("🔍 Checking for existing virtual environments...", Colors.BLUE)
    
    # Common venv paths to check
    venv_candidates = [
        config['home'] / '.venv',  # Poetry/modern style
        config['home'] / 'venv',   # Traditional style
        config['home'] / 'env',    # Alternative style
    ]
    
    # Check if project uses Poetry
    is_poetry_project = (config['home'] / 'pyproject.toml').exists()
    if is_poetry_project:
        try:
            with open(config['home'] / 'pyproject.toml', 'r') as f:
                content = f.read()
                is_poetry_project = '[tool.poetry]' in content
        except:
            is_poetry_project = False
    
    # Find existing venv
    existing_venv = None
    for venv_path in venv_candidates:
        if venv_path.exists():
            # Check if it's a valid venv
            if os.name == 'nt':
                python_exe = venv_path / 'Scripts' / 'python.exe'
            else:
                python_exe = venv_path / 'bin' / 'python'
            
            if python_exe.exists():
                existing_venv = venv_path
                print_colored(f"✅ Found existing virtual environment: {venv_path.name}", Colors.GREEN)
                break
    
    # Use existing venv or create new one
    if existing_venv:
        venv_dir = existing_venv
    else:
        # Create new venv
        if is_poetry_project:
            venv_dir = config['home'] / '.venv'
            print_colored("🎭 Poetry project detected - creating .venv", Colors.BLUE)
        else:
            venv_dir = config['home'] / 'venv'
            print_colored("📦 Creating standard venv", Colors.BLUE)
        
        if not run_command(f"{sys.executable} -m venv {venv_dir}", config['home']):
            print_colored("❌ Failed to create virtual environment", Colors.RED)
            sys.exit(1)
    
    # Determine python executable in venv
    if os.name == 'nt':  # Windows
        python_exe = venv_dir / 'Scripts' / 'python.exe'
    else:  # Unix/Linux/macOS
        python_exe = venv_dir / 'bin' / 'python'
    
    if not python_exe.exists():
        print_colored("❌ Virtual environment python not found", Colors.RED)
        sys.exit(1)
    
    print_colored("✅ Virtual environment ready", Colors.GREEN)
    return str(python_exe)

def install_package(python_exe, config):
    """Install Claude Context Box package"""
    print_colored("📦 Installing Claude Context Box...", Colors.BLUE)
    
    # Clone the repository to a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print_colored("📥 Cloning repository...", Colors.BLUE)
        clone_cmd = f"git clone https://github.com/{GITHUB_REPO}.git {temp_dir}"
        
        if not run_command(clone_cmd, capture=True):
            print_colored("❌ Failed to clone repository", Colors.RED)
            sys.exit(1)
        
        # Checkout specific version if requested
        if config['version'] != 'latest':
            checkout_cmd = f"git checkout {config['version']}"
            if not run_command(checkout_cmd, temp_dir, capture=False):
                print_colored(f"❌ Failed to checkout version {config['version']}", Colors.RED)
                sys.exit(1)
        
        # Install from source
        install_cmd = f"{python_exe} -m pip install {temp_dir}"
        
        if not run_command(install_cmd, config['home'], capture=False):
            print_colored("❌ Package installation failed", Colors.RED)
            sys.exit(1)
    
    print_colored("✅ Package installed successfully", Colors.GREEN)

def initialize_project(python_exe, config):
    """Initialize Claude Context Box in the project"""
    print_colored("🔧 Initializing project...", Colors.BLUE)
    
    # Set environment variables for the installer
    env = os.environ.copy()
    env['CLAUDE_HOME'] = str(config['home'])
    if config['force']:
        env['CLAUDE_FORCE'] = '1'
    if config['no_venv']:
        env['CLAUDE_NO_VENV'] = '1'
    
    # Try to run initialization via Python module
    init_cmd = f"{python_exe} -c \"from claude_context.installer import ClaudeContextInstaller; installer = ClaudeContextInstaller(); installer.run()\""
    result = run_command(init_cmd, config['home'], capture=False, env=env)
    
    if result is None:
        print_colored("⚠️  Could not run auto-initialization", Colors.YELLOW)
        print_colored("Run manually after installation: python -m claude_context.cli init", Colors.YELLOW)
    else:
        print_colored("✅ Project initialized", Colors.GREEN)

def uninstall(config):
    """Uninstall Claude Context Box"""
    print_colored("🗑️  Uninstalling Claude Context Box...", Colors.YELLOW)
    
    # Remove directories
    dirs_to_remove = ['.claude', 'venv']
    files_to_remove = ['CLAUDE.md', 'PROJECT.llm']
    
    for dir_name in dirs_to_remove:
        dir_path = config['home'] / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print_colored(f"✅ Removed {dir_name}/", Colors.GREEN)
    
    for file_name in files_to_remove:
        file_path = config['home'] / file_name
        if file_path.exists():
            file_path.unlink()
            print_colored(f"✅ Removed {file_name}", Colors.GREEN)
    
    print_colored("🗑️  Uninstall complete", Colors.GREEN)

def print_success_message(config):
    """Print installation success message"""
    print_colored("=" * 60, Colors.GREEN)
    print_colored("🎉 Installation Complete!", Colors.BOLD)
    print_colored("=" * 60, Colors.GREEN)
    
    print("\n📋 Next steps:")
    if not config['no_venv']:
        print_colored("1. Activate virtual environment:", Colors.BLUE)
        if os.name == 'nt':
            print(f"   .\\venv\\Scripts\\activate")
        else:
            print(f"   source venv/bin/activate")
    
    print_colored("2. In Claude, type these commands:", Colors.BLUE)
    print("   u     - Universal update")
    print("   c     - Health check") 
    print("   s     - Show structure")
    print("   h     - Help")
    
    print_colored("\n🚀 Ready for Claude development!", Colors.GREEN)

def main():
    print_header()
    
    # Check prerequisites
    check_python()
    
    # Get configuration
    config = get_env_config()
    
    # Handle uninstall
    if config['uninstall']:
        uninstall(config)
        return
    
    # Ensure installation directory exists
    config['home'].mkdir(parents=True, exist_ok=True)
    os.chdir(config['home'])
    
    # Check existing installation
    if check_existing_installation(config):
        return
    
    # Setup virtual environment
    python_exe = setup_virtual_environment(config)
    
    # Install package
    install_package(python_exe, config)
    
    # Initialize project
    initialize_project(python_exe, config)
    
    # Success message
    print_success_message(config)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n❌ Installation cancelled by user", Colors.RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Installation failed: {e}", Colors.RED)
        sys.exit(1)