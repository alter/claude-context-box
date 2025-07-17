#!/usr/bin/env python3
"""
CONTEXT.llm management system
"""

import os
import sys
import re
from pathlib import Path
import ast
import argparse

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

def analyze_python_file(filepath):
    """Analyze Python file to extract interface info"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        classes = []
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                        methods.append(item.name)
                classes.append({
                    'name': node.name,
                    'methods': methods
                })
            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                if not node.name.startswith('_'):
                    functions.append(node.name)
        
        return {'classes': classes, 'functions': functions}
    except:
        return {'classes': [], 'functions': []}

def generate_context_llm(module_path):
    """Generate CONTEXT.llm for a module"""
    module_name = os.path.basename(module_path)
    py_files = list(Path(module_path).glob('*.py'))
    
    if not py_files:
        return None
    
    # Analyze all Python files
    all_classes = []
    all_functions = []
    
    for py_file in py_files:
        if py_file.name.startswith('test_'):
            continue
        analysis = analyze_python_file(py_file)
        all_classes.extend(analysis['classes'])
        all_functions.extend(analysis['functions'])
    
    # Determine module type
    if 'api' in module_path.lower():
        module_type = 'api'
    elif 'model' in module_path.lower():
        module_type = 'data'
    elif 'service' in module_path.lower():
        module_type = 'service'
    elif 'util' in module_path.lower():
        module_type = 'util'
    else:
        module_type = 'module'
    
    # Build content
    content = f"""@component: {module_name.title().replace('_', '')}
@type: {module_type}
@deps: []
@purpose: [Add module purpose]

@interface:"""
    
    # Add classes
    for cls in all_classes:
        content += f"\\n- class {cls['name']}"
        for method in cls['methods']:
            content += f"\\n  - {method}()"
    
    # Add functions
    for func in all_functions:
        content += f"\\n- {func}()"
    
    content += """

@behavior:
- [Add key behavior]
- [Add error handling]
- [Add performance notes]
"""
    
    return content

def init_contexts():
    """Initialize CONTEXT.llm for all modules"""
    print("🔍 Scanning for modules...")
    
    created = 0
    skipped = 0
    
    for root, dirs, files in os.walk('.'):
        # Skip system directories
        dirs[:] = [d for d in dirs if d not in {'venv', '__pycache__', '.git', 'node_modules', '.claude', 'build', 'dist', '.tox'}]
        
        if any(f.endswith('.py') for f in files) and root != '.':
            context_path = os.path.join(root, 'CONTEXT.llm')
            
            if os.path.exists(context_path):
                skipped += 1
                continue
            
            content = generate_context_llm(root)
            if content:
                with open(context_path, 'w') as f:
                    f.write(content)
                print(f"✅ Created: {context_path}")
                created += 1
    
    print(f"\\n📊 Summary: {created} created, {skipped} skipped")
    if created > 0:
        print("\\n💡 Next: Review and update the generated CONTEXT.llm files")

def update_contexts():
    """Update existing CONTEXT.llm files"""
    print("🔄 Updating CONTEXT.llm files...")
    
    updated = 0
    
    for context_file in Path('.').rglob('CONTEXT.llm'):
        module_path = context_file.parent
        
        # Re-analyze module
        analysis = {'classes': [], 'functions': []}
        for py_file in module_path.glob('*.py'):
            if not py_file.name.startswith('test_'):
                file_analysis = analyze_python_file(py_file)
                analysis['classes'].extend(file_analysis['classes'])
                analysis['functions'].extend(file_analysis['functions'])
        
        # Read existing content
        with open(context_file, 'r') as f:
            content = f.read()
        
        # Update interface section
        new_interface = "\\n@interface:"
        for cls in analysis['classes']:
            new_interface += f"\\n- class {cls['name']}"
            for method in cls['methods']:
                new_interface += f"\\n  - {method}()"
        for func in analysis['functions']:
            new_interface += f"\\n- {func}()"
        
        # Replace interface section
        if '@interface:' in content:
            before = content.split('@interface:')[0]
            after = '\\n@behavior:' + content.split('@behavior:')[1] if '@behavior:' in content else ''
            new_content = before + new_interface + after
            
            with open(context_file, 'w') as f:
                f.write(new_content)
            print(f"✅ Updated: {context_file}")
            updated += 1
    
    print(f"\\n📊 Updated {updated} CONTEXT.llm files")

def scan_missing():
    """Scan for modules without CONTEXT.llm"""
    print("🔍 Scanning for modules without CONTEXT.llm...\\n")
    
    missing = []
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in {'venv', '__pycache__', '.git', 'node_modules', '.claude', 'build', 'dist', '.tox'}]
        
        if any(f.endswith('.py') for f in files) and root != '.':
            if not os.path.exists(os.path.join(root, 'CONTEXT.llm')):
                missing.append(root)
    
    if missing:
        print("❌ Modules without CONTEXT.llm:")
        for module in missing:
            print(f"   - {module}/")
        print(f"\\n💡 Run 'ctx init' to create CONTEXT.llm files")
    else:
        print("✅ All modules have CONTEXT.llm files!")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='CONTEXT.llm management')
    parser.add_argument('command', choices=['init', 'update', 'scan'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    if not venv_check():
        print("⚠️  Warning: Not running in virtual environment!")
    
    if args.command == 'init':
        init_contexts()
    elif args.command == 'update':
        update_contexts()
    elif args.command == 'scan':
        scan_missing()

if __name__ == "__main__":
    main()
