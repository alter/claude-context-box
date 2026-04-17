#!/usr/bin/env python3
"""
Quick project health check
"""

import os
import sys
import subprocess
from pathlib import Path

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

def main():
    """Run quick checks"""
    print("🔍 Quick project check...\\n")
    
    # Python environment
    print("Python Environment:")
    venv_status = "✅ Active" if venv_check() else "❌ Not active"
    print(f"  Venv: {venv_status}")
    
    # Project files
    print("\\nProject Files:")
    files_to_check = [
        ('PROJECT.llm', 'Project manifest'),
        ('CLAUDE.md', 'Claude instructions'),
        ('requirements.txt', 'Python dependencies'),
        ('.claude/prompt.md', 'System prompt'),
        ('.claude/format.md', 'Project context')
    ]
    
    for file, desc in files_to_check:
        status = "✅" if os.path.exists(file) else "❌"
        print(f"  {status} {desc}: {file}")
    
    # CONTEXT.llm files
    print("\\nModule Documentation:")
    context_files = list(Path('.').rglob('CONTEXT.llm'))
    if context_files:
        print(f"  ✅ Found {len(context_files)} CONTEXT.llm files")
        for ctx in context_files[:3]:
            print(f"     - {ctx}")
        if len(context_files) > 3:
            print(f"     ... and {len(context_files)-3} more")
    else:
        print("  ❌ No CONTEXT.llm files found")
    
    # Baseline tests
    print("\\nBaseline Tests:")
    test_files = list(Path('.').glob('test_baseline_*.py'))
    if test_files:
        print(f"  ✅ Found {len(test_files)} baseline test files")
    else:
        print("  ⚠️  No baseline tests found")
    
    print("\\n💡 Tips:")
    print("  - Run 'u' to update context")
    print("  - Run 'ctx init' to create CONTEXT.llm files")
    print("  - Run 'baseline' to create baseline tests")

if __name__ == "__main__":
    main()
