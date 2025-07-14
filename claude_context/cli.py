#!/usr/bin/env python3
"""
CLI interface for Claude Context Box
"""

import sys
import argparse
import subprocess
from pathlib import Path
from .installer import ClaudeContextInstaller

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Claude Context Box - Context management for Claude AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-context init          # Initialize in current directory
  claude-context update        # Update all contexts
  claude-context check         # Check project health
  claude-context --version     # Show version
  
Quick commands (after init):
  u    # Update everything
  c    # Check health
  h    # Show help
"""
    )
    
    parser.add_argument('command', nargs='?', default='help',
                        choices=['init', 'update', 'check', 'help', 'version'],
                        help='Command to run')
    
    parser.add_argument('--version', action='store_true',
                        help='Show version information')
    
    parser.add_argument('--force', action='store_true',
                        help='Force operation (override existing installation)')
    
    parser.add_argument('--no-venv', action='store_true',
                        help='Skip virtual environment creation')
    
    parser.add_argument('--dir', type=str, default='.',
                        help='Target directory (default: current)')
    
    args = parser.parse_args()
    
    # Handle version
    if args.version or args.command == 'version':
        from . import __version__
        print(f"Claude Context Box v{__version__}")
        return 0
    
    # Handle commands
    if args.command == 'init':
        # Run installer
        import os
        os.environ['CLAUDE_HOME'] = str(Path(args.dir).resolve())
        if args.force:
            os.environ['CLAUDE_FORCE'] = '1'
        if args.no_venv:
            os.environ['CLAUDE_NO_VENV'] = '1'
        
        installer = ClaudeContextInstaller()
        return 0 if installer.run() else 1
    
    elif args.command == 'update':
        # Run update script
        target_dir = Path(args.dir).resolve()
        update_script = target_dir / '.claude' / 'update.py'
        
        if not update_script.exists():
            print("❌ Claude Context Box not initialized in this directory")
            print("   Run: claude-context init")
            return 1
        
        # Check for venv
        venv_python = target_dir / 'venv' / 'bin' / 'python3'
        if not venv_python.exists():
            venv_python = target_dir / 'venv' / 'Scripts' / 'python.exe'
        
        python_exe = str(venv_python) if venv_python.exists() else sys.executable
        
        result = subprocess.run([python_exe, str(update_script)], cwd=target_dir)
        return result.returncode
    
    elif args.command == 'check':
        # Run check script
        target_dir = Path(args.dir).resolve()
        check_script = target_dir / '.claude' / 'check.py'
        
        if not check_script.exists():
            print("❌ Claude Context Box not initialized in this directory")
            print("   Run: claude-context init")
            return 1
        
        # Check for venv
        venv_python = target_dir / 'venv' / 'bin' / 'python3'
        if not venv_python.exists():
            venv_python = target_dir / 'venv' / 'Scripts' / 'python.exe'
        
        python_exe = str(venv_python) if venv_python.exists() else sys.executable
        
        result = subprocess.run([python_exe, str(check_script)], cwd=target_dir)
        return result.returncode
    
    else:  # help
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())