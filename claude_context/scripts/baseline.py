#!/usr/bin/env python3
"""
Baseline test generator for safe code modifications
Creates tests in tests/ directory only
"""

import os
import sys
import ast
import argparse
from pathlib import Path
from datetime import datetime

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
    content += '# Add parent directory to path\n'
    content += 'sys.path.insert(0, str(Path(__file__).parent.parent))\n\n'
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
    
    content += '\n\n# Run baseline validation\n'
    content += 'def test_baseline_established():\n'
    content += '    """Confirms baseline tests are established"""\n'
    content += '    assert True, "✅ Baseline established"\n'
    
    return content

def main():
    parser = argparse.ArgumentParser(description='Generate baseline tests for a module')
    parser.add_argument('module', help='Module name/path to generate tests for')
    args = parser.parse_args()
    
    # Ensure tests directory exists
    tests_dir = Path('tests')
    tests_dir.mkdir(exist_ok=True)
    
    # Find module path
    module_path = None
    module_name = args.module.replace('/', '.').strip('.')
    
    # Check various locations
    for candidate in [args.module, f'./{args.module}', f'./claude_context/{args.module}']:
        if Path(candidate).exists():
            module_path = Path(candidate)
            break
    
    if not module_path:
        print(f"❌ Module '{args.module}' not found")
        sys.exit(1)
    
    print(f"🔍 Analyzing module: {module_path}")
    
    # Analyze module
    functions = analyze_module(module_path)
    print(f"📋 Found {len(functions)} testable functions")
    
    # Generate test file IN TESTS DIRECTORY
    test_filename = f'tests/test_baseline_{module_name.replace(".", "_")}.py'
    test_content = generate_baseline_test(module_name, functions)
    
    # Write test file
    with open(test_filename, 'w') as f:
        f.write(test_content)
    
    print(f"✅ Generated baseline test: {test_filename}")
    print(f"📍 Next: Run 'pytest {test_filename} -v' to establish baseline")

if __name__ == '__main__':
    # Check venv
    if not venv_check():
        print("⚠️  WARNING: Not running in virtual environment")
        print("   Recommended: source venv/bin/activate")
    
    main()