#!/usr/bin/env python3
"""
Baseline test generator for safe code modifications
"""

import os
import sys
import ast
import argparse
from pathlib import Path

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

def analyze_module(module_path):
    """Analyze module to find testable functions"""
    functions = []
    
    for py_file in Path(module_path).glob('*.py'):
        if py_file.name.startswith(('test_', '__')):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):
                        functions.append({
                            'name': node.name,
                            'file': py_file.name,
                            'args': [arg.arg for arg in node.args.args]
                        })
                elif isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                            functions.append({
                                'name': f"{node.name}.{item.name}",
                                'file': py_file.name,
                                'args': [arg.arg for arg in item.args.args if arg.arg != 'self']
                            })
        except:
            continue
    
    return functions

def generate_baseline_test(module_name, functions):
    """Generate baseline test file content"""
    content = f'"""Baseline tests for {module_name}\nGenerated to capture current behavior before modifications\n"""\n\n'
    content += 'import pytest\nimport sys\nfrom pathlib import Path\n\n'
    content += '# Add module to path\n'
    content += 'sys.path.insert(0, str(Path(__file__).parent))\n\n'
    content += '# Import module components\n'
    content += f'from {module_name} import *\n\n'
    content += f'class TestBaseline{module_name.title().replace("_", "")}:\n'
    content += '    """Baseline tests to ensure current functionality is preserved"""\n    \n'
    
    for func in functions[:10]:  # Limit to 10 functions
        test_name = func['name'].replace('.', '_').lower()
        content += f"""
    def test_baseline_{test_name}(self):
        \"\"\"Test current behavior of {func['name']}\"\"\"
        # TODO: Add actual test implementation
        # Example structure:
        # result = {func['name']}({', '.join(['arg' + str(i) for i in range(len(func['args']))])})
        # assert result is not None
        pass
"""
    
    content += 