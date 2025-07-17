#!/usr/bin/env python3
"""Tests for installer virtual environment handling"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_context.installer import ClaudeContextInstaller


def test_find_existing_venvs():
    """Test finding existing virtual environments"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock venv structure
        venv_dir = tmpdir / 'venv'
        venv_dir.mkdir()
        (venv_dir / 'bin').mkdir()
        (venv_dir / 'bin' / 'activate').touch()
        
        # Create working python3 executable (symlink to system python)
        python3_path = venv_dir / 'bin' / 'python3'
        python3_path.symlink_to(sys.executable)
        
        # Create mock .venv structure
        dot_venv_dir = tmpdir / '.venv'
        dot_venv_dir.mkdir()
        (dot_venv_dir / 'bin').mkdir()
        (dot_venv_dir / 'bin' / 'activate').touch()
        
        # Create working python3 executable (symlink to system python)
        python3_path = dot_venv_dir / 'bin' / 'python3'
        python3_path.symlink_to(sys.executable)
        
        # Create installer instance
        installer = ClaudeContextInstaller()
        installer.install_dir = tmpdir
        
        # Test finding venvs
        venvs = installer.find_existing_venvs()
        
        # Should find 2 venvs
        assert len(venvs) == 2, f"Expected 2 venvs, found {len(venvs)}"
        
        # Check that both venv and .venv are found
        venv_names = {venv['path'].name for venv in venvs}
        assert 'venv' in venv_names, "Should find 'venv' directory"
        assert '.venv' in venv_names, "Should find '.venv' directory"
        
        print("✅ Test passed: find_existing_venvs works correctly")


def test_detect_project_type():
    """Test project type detection"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create installer instance
        installer = ClaudeContextInstaller()
        installer.install_dir = tmpdir
        
        # Test 1: Standard project
        project_info = installer.detect_project_type()
        assert project_info['type'] == 'standard', "Should detect standard project"
        assert not project_info['has_poetry'], "Should not detect poetry"
        
        # Test 2: Poetry project
        pyproject_content = """
[tool.poetry]
name = "test-project"
version = "0.1.0"
description = ""
"""
        (tmpdir / 'pyproject.toml').write_text(pyproject_content)
        
        project_info = installer.detect_project_type()
        assert project_info['type'] == 'poetry', "Should detect poetry project"
        assert project_info['has_poetry'], "Should detect poetry"
        assert project_info['has_pyproject'], "Should detect pyproject.toml"
        
        # Test 3: With requirements.txt
        (tmpdir / 'requirements.txt').write_text("requests>=2.0.0")
        
        project_info = installer.detect_project_type()
        assert project_info['has_requirements'], "Should detect requirements.txt"
        
        print("✅ Test passed: detect_project_type works correctly")


def test_venv_selection_preference():
    """Test that .venv is preferred for Poetry projects"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create both venv and .venv
        for venv_name in ['venv', '.venv']:
            venv_dir = tmpdir / venv_name
            venv_dir.mkdir()
            (venv_dir / 'bin').mkdir()
            (venv_dir / 'bin' / 'activate').touch()
            
            # Create working python3 executable (symlink to system python)
            python3_path = venv_dir / 'bin' / 'python3'
            python3_path.symlink_to(sys.executable)
        
        # Create Poetry project
        pyproject_content = """
[tool.poetry]
name = "test-project"
version = "0.1.0"
"""
        (tmpdir / 'pyproject.toml').write_text(pyproject_content)
        
        # Create installer instance
        installer = ClaudeContextInstaller()
        installer.install_dir = tmpdir
        
        # Find venvs and project info
        existing_venvs = installer.find_existing_venvs()
        project_info = installer.detect_project_type()
        
        # Select venv (same logic as in setup_venv)
        selected_venv = existing_venvs[0]
        if project_info['has_poetry']:
            for venv in existing_venvs:
                if venv['path'].name == '.venv':
                    selected_venv = venv
                    break
        
        assert selected_venv['path'].name == '.venv', "Should prefer .venv for Poetry projects"
        
        print("✅ Test passed: .venv is preferred for Poetry projects")


if __name__ == '__main__':
    print("Running installer venv tests...")
    test_find_existing_venvs()
    test_detect_project_type()
    test_venv_selection_preference()
    print("\nAll tests passed! 🎉")