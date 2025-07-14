#!/usr/bin/env python3
"""
Dead code cleanup utility
"""

import os
import sys
import ast
from pathlib import Path
import argparse

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

def find_unused_imports(filepath):
    """Find potentially unused imports in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Get all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
        
        # Simple check - look for usage in code
        unused = []
        for imp in set(imports):
            if content.count(imp) <= 1:  # Only in import statement
                unused.append(imp)
        
        return unused
    except:
        return []

def find_unused_functions(filepath):
    """Find potentially unused functions"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):
                    # Count occurrences
                    count = content.count(node.name)
                    if count <= 1:  # Only definition
                        functions.append(node.name)
        
        return functions
    except:
        return []

def scan_project():
    """Scan project for dead code"""
    print("🔍 Scanning for dead code...\\n")
    
    findings = {
        'unused_imports': {},
        'unused_functions': {},
        'empty_files': []
    }
    
    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        # Check file size
        if py_file.stat().st_size == 0:
            findings['empty_files'].append(str(py_file))
            continue
        
        # Check imports
        unused_imports = find_unused_imports(py_file)
        if unused_imports:
            findings['unused_imports'][str(py_file)] = unused_imports
        
        # Check functions
        unused_funcs = find_unused_functions(py_file)
        if unused_funcs:
            findings['unused_functions'][str(py_file)] = unused_funcs
    
    return findings

def interactive_cleanup(findings):
    """Interactive cleanup mode"""
    print("\\n🧹 Interactive Cleanup Mode\\n")
    
    # Empty files
    if findings['empty_files']:
        print(f"Found {len(findings['empty_files'])} empty files:")
        for file in findings['empty_files']:
            response = input(f"  Delete {file}? [y/N]: ").lower()
            if response == 'y':
                os.remove(file)
                print(f"  ✅ Deleted {file}")
    
    # Unused imports
    if findings['unused_imports']:
        print(f"\\nFound potentially unused imports in {len(findings['unused_imports'])} files")
        print("(Note: Some might be used dynamically)")
        for file, imports in list(findings['unused_imports'].items())[:5]:
            print(f"\\n📄 {file}:")
            for imp in imports:
                print(f"  - {imp}")
    
    # Summary
    print("\\n📊 Summary:")
    print(f"  - Empty files: {len(findings['empty_files'])}")
    print(f"  - Files with unused imports: {len(findings['unused_imports'])}")
    print(f"  - Files with unused functions: {len(findings['unused_functions'])}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Clean up dead code')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive cleanup mode')
    
    args = parser.parse_args()
    
    if not venv_check():
        print("⚠️  Warning: Not running in virtual environment!")
    
    findings = scan_project()
    
    if args.interactive:
        interactive_cleanup(findings)
    else:
        # Just report
        print("📊 Dead Code Report:")
        print(f"  - Empty files: {len(findings['empty_files'])}")
        print(f"  - Files with unused imports: {len(findings['unused_imports'])}")
        print(f"  - Files with unused functions: {len(findings['unused_functions'])}")
        print("\\n💡 Run with --interactive to clean up")

if __name__ == "__main__":
    main()
