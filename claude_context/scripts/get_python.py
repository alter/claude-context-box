#!/usr/bin/env python3
"""
Get the correct Python executable path for the project
"""

import os
import sys
import json
from pathlib import Path

def find_python():
    """Find the correct Python executable"""
    
    # 1. Check if we're already in a venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return sys.executable
    
    # 2. Check venv_info.json
    venv_info_path = Path('.claude/venv_info.json')
    if venv_info_path.exists():
        try:
            with open(venv_info_path, 'r') as f:
                info = json.load(f)
                python_path = Path(info['python'])
                if python_path.exists():
                    return str(python_path)
        except:
            pass
    
    # 3. Check common venv locations
    venv_paths = [
        Path('.venv/bin/python3'),
        Path('.venv/bin/python'),
        Path('venv/bin/python3'),
        Path('venv/bin/python'),
        Path('env/bin/python3'),
        Path('env/bin/python'),
        Path('.venv/Scripts/python.exe'),  # Windows
        Path('venv/Scripts/python.exe'),   # Windows
    ]
    
    for venv_path in venv_paths:
        if venv_path.exists():
            return str(venv_path.absolute())
    
    # 4. Fallback to system python3
    return 'python3'

def main():
    """Print the Python path"""
    print(find_python())

if __name__ == "__main__":
    main()