#!/usr/bin/env python3
"""
Utility functions for working with virtual environments
"""

import os
import sys
import json
from pathlib import Path


def get_venv_info():
    """Get virtual environment information from venv_info.json"""
    venv_info_file = Path('.claude') / 'venv_info.json'
    
    if venv_info_file.exists():
        try:
            with open(venv_info_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    return None


def get_python_executable():
    """Get Python executable path from venv info or fallback"""
    venv_info = get_venv_info()
    
    if venv_info and 'python' in venv_info:
        python_exe = venv_info['python']
        if Path(python_exe).exists():
            return python_exe
    
    # Fallback to old behavior
    venv_python = Path('venv') / 'bin' / 'python3'
    if not venv_python.exists():
        venv_python = Path('venv') / 'Scripts' / 'python.exe'
    
    if venv_python.exists():
        return str(venv_python)
    
    return sys.executable


def get_pip_executable():
    """Get pip executable path from venv info or fallback"""
    venv_info = get_venv_info()
    
    if venv_info and 'python' in venv_info:
        python_exe = venv_info['python']
        if Path(python_exe).exists():
            # Convert python path to pip path
            pip_exe = python_exe.replace('python3', 'pip3').replace('python.exe', 'pip.exe')
            if Path(pip_exe).exists():
                return pip_exe
            
            # Try alternative paths
            venv_path = Path(venv_info['path'])
            pip_candidates = [
                venv_path / 'bin' / 'pip3',
                venv_path / 'bin' / 'pip',
                venv_path / 'Scripts' / 'pip.exe'
            ]
            
            for pip_path in pip_candidates:
                if pip_path.exists():
                    return str(pip_path)
    
    # Fallback to old behavior
    venv_path = Path('venv')
    pip_candidates = [
        venv_path / 'bin' / 'pip3',
        venv_path / 'bin' / 'pip',
        venv_path / 'Scripts' / 'pip.exe'
    ]
    
    for pip_path in pip_candidates:
        if pip_path.exists():
            return str(pip_path)
    
    return 'pip3'


def is_poetry_project():
    """Check if this is a Poetry project"""
    venv_info = get_venv_info()
    
    if venv_info and 'type' in venv_info:
        return venv_info['type'] == 'poetry'
    
    # Fallback check
    return Path('pyproject.toml').exists() and '[tool.poetry]' in Path('pyproject.toml').read_text()


def venv_check():
    """Check if running in virtual environment"""
    # First check if we have venv info
    venv_info = get_venv_info()
    if venv_info:
        return True
    
    # Check if VIRTUAL_ENV environment variable is set (most reliable)
    if os.environ.get('VIRTUAL_ENV'):
        return True
    
    # Fallback: check if sys.prefix is different from sys.base_prefix
    if hasattr(sys, 'base_prefix'):
        return sys.prefix != sys.base_prefix
    
    # For older Python versions
    if hasattr(sys, 'real_prefix'):
        return True
    
    # Last resort: check for venv/virtualenv markers
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))