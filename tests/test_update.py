#!/usr/bin/env python3
"""Tests for update.py module"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / '.claude'))

# Import the module
from update import find_modules, EXCLUDE_DIRS


def test_find_modules_excludes_venv():
    """Test that find_modules properly excludes venv directories"""
    
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
            
            # Venv that should be excluded
            os.makedirs('venv/lib/python3.13/site-packages/click', exist_ok=True)
            Path('venv/lib/python3.13/site-packages/click/__init__.py').touch()
            Path('venv/lib/python3.13/site-packages/click/core.py').touch()
            
            # Another venv variant
            os.makedirs('.venv/lib/site-packages/pytest', exist_ok=True)
            Path('.venv/lib/site-packages/pytest/__init__.py').touch()
            
            # Run find_modules
            modules = find_modules()
            
            # Check results
            module_paths = list(modules.keys())
            
            # Should find myapp modules
            assert 'myapp' in module_paths, f"Expected to find 'myapp', got: {module_paths}"
            assert 'myapp/core' in module_paths, f"Expected to find 'myapp/core', got: {module_paths}"
            
            # Should NOT find venv modules
            venv_modules = [m for m in module_paths if 'venv' in m or 'site-packages' in m]
            assert len(venv_modules) == 0, f"Found venv modules that should be excluded: {venv_modules}"
            
            # Should NOT find any modules starting with system paths
            system_modules = [m for m in module_paths if m.startswith(('lib/', 'bin/', 'Scripts/'))]
            assert len(system_modules) == 0, f"Found system modules that should be excluded: {system_modules}"
            
            print("✅ Test passed: venv directories are properly excluded")
            
        finally:
            # Restore directory
            os.chdir(original_cwd)


def test_exclude_dirs_contains_venv():
    """Test that EXCLUDE_DIRS contains venv"""
    assert 'venv' in EXCLUDE_DIRS, "EXCLUDE_DIRS should contain 'venv'"
    print("✅ Test passed: EXCLUDE_DIRS contains 'venv'")


if __name__ == '__main__':
    print("Running update.py tests...")
    test_exclude_dirs_contains_venv()
    test_find_modules_excludes_venv()
    print("\nAll tests passed! 🎉")