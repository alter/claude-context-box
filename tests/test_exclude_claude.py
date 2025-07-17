#!/usr/bin/env python3
"""Tests for .claude directory exclusion"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / '.claude'))

from update import find_modules, EXCLUDE_DIRS


def test_exclude_dirs_contains_claude():
    """Test that EXCLUDE_DIRS contains .claude"""
    assert '.claude' in EXCLUDE_DIRS, "EXCLUDE_DIRS should contain '.claude'"
    print("✅ Test passed: EXCLUDE_DIRS contains '.claude'")


def test_find_modules_excludes_claude():
    """Test that find_modules properly excludes .claude directories"""
    
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save current directory
        original_cwd = os.getcwd()
        
        try:
            # Change to temp directory
            os.chdir(tmpdir)
            
            # Create test structure
            # Good modules
            os.makedirs('myapp/core', exist_ok=True)
            Path('myapp/__init__.py').touch()
            Path('myapp/core/__init__.py').touch()
            Path('myapp/core/utils.py').touch()
            
            # .claude directory that should be excluded
            os.makedirs('.claude', exist_ok=True)
            Path('.claude/__init__.py').touch()
            Path('.claude/update.py').touch()
            Path('.claude/check.py').touch()
            
            # Another module inside .claude (should be excluded)
            os.makedirs('.claude/submodule', exist_ok=True)
            Path('.claude/submodule/__init__.py').touch()
            Path('.claude/submodule/test.py').touch()
            
            # Run find_modules
            modules = find_modules()
            
            # Check results
            module_paths = list(modules.keys())
            
            # Should find myapp modules
            assert 'myapp' in module_paths, f"Expected to find 'myapp', got: {module_paths}"
            assert 'myapp/core' in module_paths, f"Expected to find 'myapp/core', got: {module_paths}"
            
            # Should NOT find .claude modules
            claude_modules = [m for m in module_paths if '.claude' in m]
            assert len(claude_modules) == 0, f"Found .claude modules that should be excluded: {claude_modules}"
            
            print("✅ Test passed: .claude directories are properly excluded")
            
        finally:
            # Restore directory
            os.chdir(original_cwd)


def test_path_startswith_claude():
    """Test that paths starting with .claude/ are excluded"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save current directory
        original_cwd = os.getcwd()
        
        try:
            # Change to temp directory
            os.chdir(tmpdir)
            
            # Create nested .claude structure
            os.makedirs('.claude/nested/deep/module', exist_ok=True)
            Path('.claude/nested/deep/module/__init__.py').touch()
            Path('.claude/nested/deep/module/code.py').touch()
            
            # Create normal module for comparison
            os.makedirs('normal/module', exist_ok=True)
            Path('normal/module/__init__.py').touch()
            Path('normal/module/code.py').touch()
            
            # Run find_modules
            modules = find_modules()
            module_paths = list(modules.keys())
            
            # Should find normal module
            assert 'normal/module' in module_paths, f"Expected to find 'normal/module', got: {module_paths}"
            
            # Should NOT find any .claude paths
            claude_paths = [m for m in module_paths if m.startswith('.claude/')]
            assert len(claude_paths) == 0, f"Found paths starting with .claude/ that should be excluded: {claude_paths}"
            
            print("✅ Test passed: paths starting with .claude/ are excluded")
            
        finally:
            # Restore directory
            os.chdir(original_cwd)


if __name__ == '__main__':
    print("Running .claude exclusion tests...")
    test_exclude_dirs_contains_claude()
    test_find_modules_excludes_claude()
    test_path_startswith_claude()
    print("\nAll tests passed! 🎉")