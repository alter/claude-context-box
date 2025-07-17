#!/usr/bin/env python3
"""Tests for virtual environment detection"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'claude_context' / 'scripts'))

from venv_utils import get_venv_info, get_python_executable, is_poetry_project


def test_venv_detection_with_info_file():
    """Test that venv detection works with venv_info.json"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save current directory
        original_cwd = os.getcwd()
        
        try:
            # Change to temp directory
            os.chdir(tmpdir)
            
            # Create .claude directory and venv_info.json
            os.makedirs('.claude', exist_ok=True)
            venv_info = {
                'path': '/project/.venv',
                'python': '/project/.venv/bin/python3',
                'activate': '/project/.venv/bin/activate',
                'type': 'poetry'
            }
            
            with open('.claude/venv_info.json', 'w') as f:
                json.dump(venv_info, f)
            
            # Test get_venv_info
            info = get_venv_info()
            assert info is not None, "Should find venv info"
            assert info['type'] == 'poetry', "Should detect poetry project"
            assert info['python'] == '/project/.venv/bin/python3', "Should return correct python path"
            
            # Test is_poetry_project
            assert is_poetry_project(), "Should detect poetry project from venv_info"
            
            print("✅ Test passed: venv detection works with venv_info.json")
            
        finally:
            # Restore directory
            os.chdir(original_cwd)


def test_fallback_detection():
    """Test fallback detection when no venv_info.json exists"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save current directory
        original_cwd = os.getcwd()
        
        try:
            # Change to temp directory
            os.chdir(tmpdir)
            
            # Create pyproject.toml with poetry section
            pyproject_content = """
[tool.poetry]
name = "test-project"
version = "0.1.0"
description = ""
authors = ["Test Author <test@example.com>"]

[tool.poetry.dependencies]
python = "^3.9"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
            
            with open('pyproject.toml', 'w') as f:
                f.write(pyproject_content)
            
            # Test is_poetry_project fallback
            assert is_poetry_project(), "Should detect poetry project from pyproject.toml"
            
            # Test get_venv_info
            info = get_venv_info()
            assert info is None, "Should return None when no venv_info.json exists"
            
            print("✅ Test passed: fallback detection works")
            
        finally:
            # Restore directory
            os.chdir(original_cwd)


def test_get_python_executable_fallback():
    """Test get_python_executable fallback behavior"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save current directory
        original_cwd = os.getcwd()
        
        try:
            # Change to temp directory
            os.chdir(tmpdir)
            
            # Test without any venv
            python_exe = get_python_executable()
            assert python_exe == sys.executable, f"Should fallback to system python: {python_exe}"
            
            print("✅ Test passed: get_python_executable fallback works")
            
        finally:
            # Restore directory
            os.chdir(original_cwd)


if __name__ == '__main__':
    print("Running venv detection tests...")
    test_venv_detection_with_info_file()
    test_fallback_detection()
    test_get_python_executable_fallback()
    print("\nAll tests passed! 🎉")