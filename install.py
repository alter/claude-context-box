#!/usr/bin/env python3
"""
Claude Context Box - Lightweight installer/loader
https://github.com/alter/claude-context-box

Usage:
    curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -
    
Or with options:
    curl -sSL ... | CLAUDE_VERSION=v0.0.2 CLAUDE_HOME=/opt/claude python3 -
"""

import os
import sys
import json
import urllib.request
import urllib.error
import tempfile
import subprocess
import shutil
from pathlib import Path

REPO_OWNER = "alter"
REPO_NAME = "claude-context-box"
DEFAULT_BRANCH = "main"

class Colors:
    """Terminal colors"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'
    
    @staticmethod
    def disable():
        Colors.GREEN = Colors.YELLOW = Colors.RED = Colors.BLUE = Colors.BOLD = Colors.END = ''

def print_banner():
    """Display installation banner"""
    print(f"""
{Colors.BLUE}╔═══════════════════════════════════════════╗
║  Claude Context Box Installer v2.0        ║
║  https://github.com/{REPO_OWNER}/{REPO_NAME}  ║
╚═══════════════════════════════════════════╝{Colors.END}
""")

def get_env_config():
    """Get configuration from environment variables"""
    return {
        'version': os.environ.get('CLAUDE_VERSION', 'latest'),
        'home': os.environ.get('CLAUDE_HOME', os.getcwd()),
        'no_venv': os.environ.get('CLAUDE_NO_VENV', '').lower() in ('1', 'true', 'yes'),
        'no_modify_path': os.environ.get('CLAUDE_NO_MODIFY_PATH', '').lower() in ('1', 'true', 'yes'),
        'uninstall': os.environ.get('CLAUDE_UNINSTALL', '').lower() in ('1', 'true', 'yes'),
        'branch': os.environ.get('CLAUDE_BRANCH', DEFAULT_BRANCH),
        'quiet': os.environ.get('CLAUDE_QUIET', '').lower() in ('1', 'true', 'yes'),
        'force': os.environ.get('CLAUDE_FORCE', '').lower() in ('1', 'true', 'yes'),
    }

def fetch_latest_version():
    """Fetch the latest release version from GitHub"""
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read())
            return data['tag_name']
    except:
        # Fallback to main branch
        return DEFAULT_BRANCH

def download_file(url, dest_path):
    """Download a file with progress indicator"""
    try:
        print(f"  ⬇️  Downloading from {url}")
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            block_size = 8192
            
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        bar_length = 40
                        filled = int(bar_length * downloaded / total_size)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        print(f"\r  [{bar}] {percent:.1f}%", end='', flush=True)
            
            print()  # New line after progress bar
            return True
    except Exception as e:
        print(f"\n  {Colors.RED}❌ Download failed: {e}{Colors.END}")
        return False

def check_python_version():
    """Ensure Python 3.7+ is being used"""
    if sys.version_info < (3, 7):
        print(f"{Colors.RED}❌ Python 3.7+ required (found {sys.version}){Colors.END}")
        sys.exit(1)

def uninstall(config):
    """Uninstall Claude Context Box"""
    print(f"\n{Colors.YELLOW}🗑️  Uninstalling Claude Context Box...{Colors.END}")
    
    install_dir = Path(config['home'])
    
    # Remove .claude directory
    claude_dir = install_dir / '.claude'
    if claude_dir.exists():
        shutil.rmtree(claude_dir)
        print(f"  ✅ Removed {claude_dir}")
    
    # Remove PROJECT.llm and CLAUDE.md
    for file in ['PROJECT.llm', 'CLAUDE.md']:
        file_path = install_dir / file
        if file_path.exists():
            file_path.unlink()
            print(f"  ✅ Removed {file}")
    
    # Remove baseline tests
    for test_file in install_dir.glob('test_baseline_*.py'):
        test_file.unlink()
        print(f"  ✅ Removed {test_file.name}")
    
    print(f"\n{Colors.GREEN}✅ Uninstallation complete!{Colors.END}")
    return 0

def install(config):
    """Main installation process"""
    install_dir = Path(config['home'])
    
    # Determine version/branch to install
    version = config['version']
    if version == 'latest':
        version = fetch_latest_version()
    
    # Construct download URL
    if version == DEFAULT_BRANCH or version.startswith('v'):
        # It's a tag or branch
        base_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{version}"
    else:
        # Assume it's a branch
        base_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{version}"
    
    print(f"\n📦 Installing Claude Context Box {version}...")
    print(f"   Installation directory: {install_dir}")
    
    # Create temp directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Download the full installer
        installer_url = f"{base_url}/claude_context/installer.py"
        installer_path = temp_path / "installer.py"
        
        # Try new structure first
        if not download_file(installer_url, installer_path):
            # Fallback to old structure
            print(f"  ℹ️  Trying legacy installer...")
            installer_url = f"{base_url}/install-claude-context.py"
            if not download_file(installer_url, installer_path):
                print(f"{Colors.RED}❌ Failed to download installer{Colors.END}")
                return 1
        
        # Download configuration
        config_url = f"{base_url}/claude_context/config.json"
        config_path = temp_path / "config.json"
        download_file(config_url, config_path)  # Optional, may not exist
        
        # Run the main installer
        print(f"\n🔧 Running installer...")
        
        cmd = [sys.executable, str(installer_path)]
        
        # Pass configuration via environment
        env = os.environ.copy()
        env.update({
            'CLAUDE_VERSION': version,
            'CLAUDE_HOME': str(install_dir),
            'CLAUDE_BASE_URL': base_url,
            'CLAUDE_NO_VENV': '1' if config['no_venv'] else '0',
            'CLAUDE_FORCE': '1' if config['force'] else '0',
        })
        
        try:
            result = subprocess.run(cmd, env=env, cwd=str(install_dir))
            if result.returncode != 0:
                print(f"{Colors.RED}❌ Installation failed{Colors.END}")
                return 1
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to run installer: {e}{Colors.END}")
            return 1
    
    # Post-installation steps
    if not config['no_modify_path']:
        add_to_path(install_dir)
    
    print(f"\n{Colors.GREEN}✅ Installation complete!{Colors.END}")
    print(f"\n📋 Next steps:")
    
    if not config['no_venv']:
        print(f"   1. Activate virtual environment:")
        print(f"      source {install_dir}/venv/bin/activate  # Linux/Mac")
        print(f"      {install_dir}\\venv\\Scripts\\activate     # Windows")
    
    print(f"   2. Run initial update:")
    print(f"      claude-context update")
    print(f"\n   Or simply type 'u' in your project directory!")
    
    return 0

def add_to_path(install_dir):
    """Add claude-context to PATH"""
    # This would detect shell type and modify appropriate config
    # For now, just print instructions
    print(f"\n📝 To add claude-context to your PATH permanently:")
    print(f"   Add this line to your shell config (~/.bashrc, ~/.zshrc, etc):")
    print(f"   export PATH=\"{install_dir}/.claude/bin:$PATH\"")

def main():
    """Entry point"""
    check_python_version()
    
    # Disable colors if not in terminal
    if not sys.stdout.isatty():
        Colors.disable()
    
    config = get_env_config()
    
    if not config['quiet']:
        print_banner()
    
    # Handle uninstall
    if config['uninstall']:
        return uninstall(config)
    
    # Regular installation
    return install(config)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Installation cancelled{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {e}{Colors.END}")
        sys.exit(1)