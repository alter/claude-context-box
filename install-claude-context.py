#!/usr/bin/env python3
"""
Claude Context Box - Ultimate Hybrid Installer
Combines the best from both old and new versions:
- Skylos integration (new)
- Script auto-generation (old) 
- Advanced project analysis (new)
- Detailed Claude instructions (old)
- CLI management (new)
- Smart installation logic (enhanced)
"""
import os
import sys
import stat
import json
import shutil
import hashlib
import subprocess
import tempfile
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any

# ===== SKYLOS SCANNER INTEGRATION (FROM NEW VERSION) =====
class SkylosScanner:
    """Wrapper for Skylos dead code detection tool"""
    
    def __init__(self, root_path: Path = None):
        self.root = root_path or Path.cwd()
        self.claude_dir = self.root / '.claude'
        self.reports_dir = self.claude_dir / 'reports'
        
    def check_skylos_installation(self) -> bool:
        """Check if Skylos is installed"""
        try:
            # First try current environment
            result = subprocess.run(['skylos', '--help'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True
        except FileNotFoundError:
            pass
            
        # Check in venv if it exists
        venv_path = self.root / 'venv'
        if venv_path.exists():
            if sys.platform == "win32":
                skylos_exe = venv_path / 'Scripts' / 'skylos.exe'
            else:
                skylos_exe = venv_path / 'bin' / 'skylos'
            
            if skylos_exe.exists():
                try:
                    result = subprocess.run([str(skylos_exe), '--help'], 
                                          capture_output=True, text=True)
                    return result.returncode == 0
                except:
                    pass
        
        return False
            
    def install_skylos(self) -> bool:
        """Install Skylos from GitHub"""
        print("🔧 Installing Skylos...")
        
        try:
            # Check if git is available
            subprocess.run(['git', '--version'], check=True, capture_output=True)
            
            # Check if we're in a virtual environment
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            
            if not in_venv:
                # Create virtual environment
                venv_path = self.root / 'venv'
                if not venv_path.exists():
                    print("🔨 Creating virtual environment...")
                    subprocess.run(['python3', '-m', 'venv', str(venv_path)], check=True)
                
                # Use venv python for installation
                if sys.platform == "win32":
                    python_exe = venv_path / 'Scripts' / 'python.exe'
                    pip_exe = venv_path / 'Scripts' / 'pip.exe'
                else:
                    python_exe = venv_path / 'bin' / 'python3'
                    pip_exe = venv_path / 'bin' / 'pip3'
            else:
                python_exe = 'python3'
                pip_exe = 'pip3'
            
            # Clone and install Skylos
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Clone repository
                print("📥 Cloning Skylos repository...")
                subprocess.run([
                    'git', 'clone', 
                    'https://github.com/duriantaco/skylos.git',
                    str(temp_path / 'skylos')
                ], check=True)
                
                # Install using pip
                print("📦 Installing Skylos...")
                subprocess.run([
                    str(pip_exe), 'install', str(temp_path / 'skylos')
                ], check=True)
                
                # Install inquirer dependency
                subprocess.run([
                    str(pip_exe), 'install', 'inquirer'
                ], check=True)
            
            print("✅ Skylos installed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install Skylos: {e}")
            return False
    
    def run_skylos_analysis(self, confidence: int = 60) -> Optional[Dict]:
        """Run Skylos analysis and return results"""
        
        # Ensure Skylos is installed
        if not self.check_skylos_installation():
            print("⚠️  Skylos not found, installing...")
            if not self.install_skylos():
                return None
        
        # Determine skylos executable
        venv_path = self.root / 'venv'
        if venv_path.exists():
            if sys.platform == "win32":
                skylos_exe = str(venv_path / 'Scripts' / 'skylos.exe')
            else:
                skylos_exe = str(venv_path / 'bin' / 'skylos')
        else:
            skylos_exe = 'skylos'
        
        # Create reports directory
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"skylos_raw_{timestamp}.json"
        
        try:
            print(f"🔍 Running Skylos analysis (confidence: {confidence})...")
            
            # Run skylos with JSON output
            result = subprocess.run([
                skylos_exe,
                str(self.root),
                '--json',
                '--confidence', str(confidence),
                '--output', str(report_file)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Analysis complete. Raw data saved to", report_file)
                
                # Read and return the JSON data
                if report_file.exists():
                    with open(report_file, 'r') as f:
                        return json.load(f)
                        
            else:
                print(f"❌ Skylos analysis failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("⏰ Skylos analysis timed out (5 minutes)")
            return None
        except Exception as e:
            print(f"❌ Error running Skylos: {e}")
            return None

# ===== PROJECT ANALYZER (FROM NEW VERSION, ENHANCED) =====
class ProjectAnalyzer:
    """Advanced project structure analyzer"""
    
    def __init__(self, root_path: Path = None):
        self.root = root_path or Path.cwd()
        self.claude_dir = self.root / '.claude'
        
    def analyze(self) -> Dict[str, Any]:
        """Comprehensive project analysis"""
        analysis = {
            'project_name': self.root.name,
            'last_updated': datetime.now().isoformat(),
            'total_files': 0,
            'python_files': 0,
            'module_directories': [],
            'scattered_scripts': [],
            'readme_coverage': 0.0,
            'has_claude_context': (self.root / 'CLAUDE.md').exists(),
            'chaos_indicators': 0,
            'organization_indicators': 0,
            'type': 'unknown',
            'recommendations': [],
            'dead_code_analysis': None
        }
        
        # Count files and analyze structure
        self._analyze_file_structure(analysis)
        
        # Calculate indicators
        analysis['chaos_indicators'] = self._calculate_chaos_indicators(analysis)
        analysis['organization_indicators'] = self._calculate_organization_indicators(analysis)
        
        # Determine project type
        analysis['type'] = self._determine_project_type()
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        # Run dead code analysis if possible
        analysis['dead_code_analysis'] = self._analyze_dead_code()
        
        return analysis
    
    def _analyze_file_structure(self, analysis: Dict):
        """Analyze file structure and count various metrics"""
        python_files = list(self.root.rglob("*.py"))
        analysis['python_files'] = len([f for f in python_files if not self._should_ignore_path(f)])
        
        # Count total files
        all_files = list(self.root.rglob("*"))
        analysis['total_files'] = len([f for f in all_files if f.is_file() and not self._should_ignore_path(f)])
        
        # Find module directories (directories with __init__.py)
        for path in self.root.rglob("__init__.py"):
            if not self._should_ignore_path(path):
                module_dir = str(path.parent.relative_to(self.root))
                if module_dir not in analysis['module_directories']:
                    analysis['module_directories'].append(module_dir)
        
        # Find scattered scripts in root
        for py_file in self.root.glob("*.py"):
            if py_file.name not in ['setup.py', '__init__.py', 'manage.py']:
                analysis['scattered_scripts'].append(py_file.name)
        
        # Calculate README coverage
        total_modules = len(analysis['module_directories'])
        if total_modules > 0:
            modules_with_readme = 0
            for module_dir in analysis['module_directories']:
                readme_path = self.root / module_dir / "README.md"
                if readme_path.exists():
                    modules_with_readme += 1
            analysis['readme_coverage'] = modules_with_readme / total_modules
    
    def _should_ignore_path(self, path: Path) -> bool:
        """Check if path should be ignored"""
        ignore_patterns = {
            '__pycache__', '.git', '.claude', 'node_modules', 
            '.venv', 'venv', 'env', '.env', '.DS_Store',
            'dist', 'build', '.pytest_cache', '.mypy_cache',
            '.tox', 'htmlcov', '.coverage'
        }
        
        return any(pattern in str(path) for pattern in ignore_patterns)
    
    def _calculate_chaos_indicators(self, analysis: Dict) -> int:
        """Calculate chaos indicators (0-10)"""
        indicators = 0
        
        # Many scattered scripts
        scattered = len(analysis.get("scattered_scripts", []))
        if scattered >= 10:
            indicators += 3
        elif scattered >= 5:
            indicators += 2
        elif scattered >= 2:
            indicators += 1
            
        # No clear module structure
        if len(analysis.get("module_directories", [])) == 0 and analysis["python_files"] > 5:
            indicators += 2
            
        # Poor README coverage
        if analysis.get("readme_coverage", 0) < 0.3:
            indicators += 1
            
        return indicators
        
    def _calculate_organization_indicators(self, analysis: Dict) -> int:
        """Calculate organization indicators (0-10)"""
        indicators = 0
        
        # Good module structure
        modules = len(analysis.get("module_directories", []))
        if modules >= 5:
            indicators += 2
        elif modules >= 2:
            indicators += 1
            
        # Good README coverage
        if analysis.get("readme_coverage", 0) >= 0.8:
            indicators += 2
        elif analysis.get("readme_coverage", 0) >= 0.5:
            indicators += 1
            
        # Few scattered scripts
        scattered = len(analysis.get("scattered_scripts", []))
        if scattered == 0:
            indicators += 2
        elif scattered <= 2:
            indicators += 1
            
        return indicators
        
    def _determine_project_type(self) -> str:
        """Determine project type based on analysis"""
        analysis = self.analysis if hasattr(self, 'analysis') else {}
        chaos = analysis.get("chaos_indicators", 0)
        organized = analysis.get("organization_indicators", 0)
        
        # Already has Claude setup
        if analysis.get("has_claude_context"):
            return "existing_claude"
            
        # New/empty project
        if analysis.get("total_files", 0) < 10:
            return "new_project"
            
        # Clear determination
        if chaos >= 6:
            return "legacy_chaotic"
        elif organized >= 6:
            return "organized"
        elif chaos > organized:
            return "legacy_chaotic"
        else:
            return "organized"
                
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recs = []
        
        project_type = analysis.get("type", "unknown")
        
        if project_type == "legacy_chaotic":
            recs.append("Use Legacy Refactoring System to organize the project")
            if analysis.get("scattered_scripts"):
                recs.append(f"Organize {len(analysis['scattered_scripts'])} scattered scripts")
            
        elif project_type == "organized":
            recs.append("Use Enhanced Context Box for documentation management")
            if analysis.get("readme_coverage", 0) < 1.0:
                recs.append("Complete README.md coverage for all modules")
            
        elif project_type == "new_project":
            recs.append("Use Enhanced Context Box to start with best practices")
            recs.append("Create initial module structure")
            
        return recs
        
    def _analyze_dead_code(self) -> Optional[Dict]:
        """Analyze dead code using Skylos"""
        print("🔍 Analyzing dead code with Skylos...")
        
        try:
            scanner = SkylosScanner(self.root)
            analysis_data = scanner.run_skylos_analysis(confidence=60)
            
            if analysis_data:
                # Count dead code items
                imports = analysis_data.get('unused_imports', [])
                functions = analysis_data.get('unused_functions', [])
                classes = analysis_data.get('unused_classes', [])
                variables = analysis_data.get('unused_variables', [])
                
                return {
                    'total_items': len(imports) + len(functions) + len(classes) + len(variables),
                    'unused_imports': len(imports),
                    'unused_functions': len(functions),
                    'unused_classes': len(classes),
                    'unused_variables': len(variables),
                    'has_dead_code': len(imports) + len(functions) + len(classes) + len(variables) > 0
                }
        except Exception as e:
            print(f"⚠️  Dead code analysis failed: {e}")
            return None

# ===== ENHANCED INSTALLER (HYBRID OF BOTH VERSIONS) =====
class ClaudeContextHybridInstaller:
    """Ultimate hybrid installer combining best of both versions"""
    
    def __init__(self):
        self.root = Path.cwd()
        self.claude_dir = self.root / '.claude'
        self.analyzer = ProjectAnalyzer(self.root)
        self.scanner = SkylosScanner(self.root)
        
    def claude_md_exists(self) -> bool:
        """Check if CLAUDE.md exists"""
        return (self.root / 'CLAUDE.md').exists()
        
    def ask_installation_type(self) -> str:
        """Ask user what type of installation to perform"""
        print("\n📋 CLAUDE.md already exists!")
        print("📄 Current content will be analyzed and preserved.")
        print("\nInstallation options:")
        print("  1. 🔄 UPDATE - Update existing installation (recommended)")
        print("  2. 🆕 FRESH - Complete fresh installation (with backup)")
        print("  3. ❌ CANCEL - Exit without changes")
        
        while True:
            choice = input("\nSelect option (1-3): ").strip()
            if choice == "1":
                return "update"
            elif choice == "2":
                return "fresh" 
            elif choice == "3":
                return "cancel"
            else:
                print("❌ Invalid choice. Please select 1, 2, or 3.")
    
    def fresh_install(self):
        """Complete fresh installation"""
        print("\n🚀 Fresh installation started...")
        
        # Analyze project
        analysis = self.analyzer.analyze()
        self._display_analysis(analysis)
        
        # Create directory structure
        self.create_directory_structure()
        
        # Create all scripts (FROM OLD VERSION)
        self.create_update_py()
        self.create_check_py() 
        self.create_setup_sh()
        self.create_gitignore()
        
        # Create CLAUDE.md with full instructions (FROM OLD VERSION)
        self.create_claude_md_full()
        
        # Run initial update
        self.run_initial_update()
        
        print("\n✅ Fresh installation completed!")
        self._show_completion_message()
        
    def fresh_install_with_backup(self):
        """Fresh installation with backup of existing files"""
        print("\n🚀 Fresh installation with backup started...")
        
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.root / f'.claude_backup_{timestamp}'
        
        # Backup CLAUDE.md
        claude_md = self.root / 'CLAUDE.md'
        if claude_md.exists():
            backup_dir.mkdir(exist_ok=True)
            shutil.copy2(claude_md, backup_dir / 'CLAUDE.md')
            print(f"💾 CLAUDE.md backed up to {backup_dir}/")
        
        # Backup .claude directory if exists
        if self.claude_dir.exists():
            if not backup_dir.exists():
                backup_dir.mkdir(exist_ok=True)
            shutil.copytree(self.claude_dir, backup_dir / '.claude', dirs_exist_ok=True)
            print(f"💾 .claude directory backed up to {backup_dir}/")
        
        # Proceed with fresh installation
        self.fresh_install()
        
    def update_existing_installation(self):
        """Update existing installation preserving content"""
        print("\n🔄 Updating existing installation...")
        
        # Analyze current state
        analysis = self.analyzer.analyze()
        self._display_analysis(analysis)
        
        # Always recreate scripts (they might have updates)
        print("📝 Updating management scripts...")
        self.create_directory_structure()
        self.create_update_py()
        self.create_check_py()
        self.create_setup_sh() 
        self.create_gitignore()
        
        # Handle CLAUDE.md intelligently
        self._handle_existing_claude_md()
        
        # Run update
        self.run_initial_update()
        
        print("\n✅ Update completed!")
        self._show_completion_message()
        
    def _handle_existing_claude_md(self):
        """Simply merge existing CLAUDE.md with new command structure"""
        claude_md = self.root / 'CLAUDE.md'
        
        if not claude_md.exists():
            self.create_claude_md_full()
            return
            
        print("📄 Merging existing CLAUDE.md with new command structure...")
        existing_content = claude_md.read_text()
        
        # Check if it already has the FULL command mappings (not just old partial ones)
        has_full_rules = all([
            'Code unification principle' in existing_content,
            'AVOID DUPLICATION' in existing_content,
            'Context update workflow' in existing_content,
            'Python-specific rules' in existing_content
        ])
        
        if has_full_rules:
            print("✅ CLAUDE.md already has full command mappings")
            return
            
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
        backup_file = self.root / f'CLAUDE_backup_{timestamp}.md'
        backup_file.write_text(existing_content)
        print(f"💾 Backup created: {backup_file.name}")
        
        # Generate new header with command mappings
        new_header = self._generate_command_header()
        
        # Simple merge: new header + separator + existing content
        merged_content = f"""{new_header}

---

# Original Project Documentation

{existing_content}
"""
        
        claude_md.write_text(merged_content)
        print("✅ CLAUDE.md merged with command mappings")
    
    def _generate_command_header(self) -> str:
        """Generate the command header section for CLAUDE.md"""
        return """## ===== Claude Context Box Rules =====

## Automatic project context
@.claude/format.md

## 💡 QUICK COMMANDS
Just type these commands and I'll execute them:
- `update` or `u` - Update project context
- `check` or `c` - Quick conflict check
- `structure` or `s` - Show full project structure
- `conflicts` or `cf` - Show only conflicts
- `venv` or `v` - Setup/check Python environment
- `help` or `h` - Show all commands
- `deps` or `d` - Show dependencies

## ⚠️ CRITICAL RULES

### Code style
- **NO COMMENTS** in code files
- **Use ENGLISH ONLY** for all code, variables, functions, and documentation
- Self-documenting code with clear naming

### Python environment
- ALWAYS use `python3` instead of `python`
- ALWAYS use `pip3` instead of `pip`
- ALWAYS work in virtual environment `venv`
- Activate venv: `source venv/bin/activate` (Linux/Mac) or `venv\\Scripts\\activate` (Windows)

### Directory structure
- ALWAYS check existing directories before creating new ones
- Use `python3 .claude/update.py` to update context
- DO NOT create new config*/test*/src* directories without checking

### Code unification principle
- **AVOID DUPLICATION**: Before creating new functionality, check existing code
- **EXTEND, DON'T DUPLICATE**: Build on existing solutions rather than creating parallel implementations
- **UNIFIED APPROACH**: If similar functionality exists, refactor to create a single, flexible solution
- Examples:
  - Don't create `user_validator.py` if `validators.py` exists - extend it
  - Don't create `config2/` if `config/` exists - reorganize existing
  - Don't create `new_utils.py` if `utils.py` exists - add to existing

### ⚠️ IMPORTANT UPDATE RULE
If I make structural changes (create/delete directories, add new modules),
you MUST suggest running:
```bash
python3 .claude/update.py
```

### Automatic checks
- **Before creating new directories** → first run: `python3 .claude/update.py`
- **Before creating similar functionality** → check existing code structure
- **After refactoring structure** → must run: `python3 .claude/update.py`
- **When unsure about structure** → update context before continuing

### Context update workflow
1. Ensure venv is activated
2. Run: `python3 .claude/update.py`
3. Check updated context: `cat .claude/format.md`
4. Continue work with current context

## Typical scenarios requiring update

### 1. Creating new functionality
```bash
# FIRST update context
python3 .claude/update.py
# THEN create files/folders
```

### 2. Structure refactoring
```bash
# Before refactoring - check current structure
python3 .claude/update.py
# After refactoring - update context
python3 .claude/update.py
```

### 3. Resolving conflicts
If I say something like:
- "put in configs" (but config exists)
- "create tests" (but test exists)
- "add to src" (but source exists)

YOU MUST:
1. Stop
2. Suggest running `python3 .claude/update.py`
3. Show existing directories from context
4. Ask which one to use

## Python-specific rules

### Installing dependencies
```bash
# ALWAYS in venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows
pip3 install -r requirements.txt
```

### Creating venv if missing
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install --upgrade pip
```

### Adding new packages
```bash
# In activated venv
pip3 install package_name
pip3 freeze > requirements.txt
python3 .claude/update.py  # Update context!
```

## 🔧 SKYLOS INTEGRATION (Dead Code Cleanup)
```bash
# Interactive cleanup - shows what will be removed and asks for confirmation
python3 claude-context.py cleancode --interactive

# Preview changes only (dry run)
python3 claude-context.py cleancode --dry-run

# High confidence only (80%+ confidence)
python3 claude-context.py cleancode --confidence 80

# Auto-install if missing
python3 claude-context.py cleancode  # Will install Skylos if needed
```

### Command mappings:
When I type `update` or `u`, you MUST run: `python3 .claude/update.py`
When I type `check` or `c`, you MUST run: `python3 .claude/check.py`
When I type `structure` or `s`, you MUST run: `cat .claude/context.json | python3 -m json.tool`
When I type `conflicts` or `cf`, you MUST run: `cat .claude/format.md | grep -A20 "WARNINGS"`
When I type `venv` or `v`, you MUST run: `bash .claude/setup.sh`
When I type `help` or `h`, you MUST show: the command list from CLAUDE.md
When I type `deps` or `d`, you MUST run: `cat .claude/format.md | grep -A10 "Dependencies"`
When I type `cleancode` or `cc`, you MUST run: `python3 claude-context.py cleancode --interactive`

## Initial setup (if not done yet)
```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate venv
source venv/bin/activate  # Linux/Mac
# or
venv\\Scripts\\activate     # Windows

# 3. Update context
python3 .claude/update.py
```"""
    
    def _check_claude_md_needs_update(self, content: str) -> bool:
        """Check if CLAUDE.md needs format updates"""
        # Look for modern format indicators
        modern_indicators = [
            'Claude Context Box Rules',
            'Quick Commands for Claude', 
            'python3 claude-context.py',
            'Skylos integration'
        ]
        
        # If it doesn't have modern structure, it needs update
        has_modern_structure = any(indicator in content for indicator in modern_indicators)
        return not has_modern_structure
    
    def _extract_preserved_content(self, content: str) -> Dict[str, str]:
        """Extract content to preserve from existing CLAUDE.md"""
        # This would analyze existing content and extract valuable sections
        # For now, return the full content to be preserved
        return {
            'existing_content': content,
            'project_description': '',
            'custom_sections': []
        }
        
    def _generate_enhanced_claude_md(self, preserved: Dict[str, str]) -> str:
        """Generate enhanced CLAUDE.md with preserved content"""
        timestamp = datetime.now().strftime('%Y-%m-%d')
        
        template = f"""## ===== Claude Context Box Rules =====

## Automatic project context
@.claude/format.md

## Quick Commands for Claude
When user types single letter commands, respond with:
- `h` or `help` - Show Claude Context Box commands: `python3 claude-context.py help`
- `s` or `sync` - Sync project: `python3 claude-context.py sync` 
- `u` or `update` - Update context: `python3 claude-context.py update`
- `c` or `check` - Check conflicts: `python3 claude-context.py check`
- `cc` or `cleancode` - Clean dead code: `python3 claude-context.py cleancode --interactive`

# {self.root.name} Project Context

## Quick Reference
- **Project**: {self.root.name}
- **Type**: Enhanced with Claude Context Box
- **Last Updated**: {timestamp}

## 💡 QUICK COMMANDS
Just type these commands and I'll execute them:
- `update` or `u` - Update project context
- `check` or `c` - Quick conflict check
- `structure` or `s` - Show full project structure
- `conflicts` or `cf` - Show only conflicts
- `venv` or `v` - Setup/check Python environment
- `help` or `h` - Show all commands
- `cleancode` or `cc` - Interactive dead code cleanup

## ⚠️ CRITICAL RULES

### Code style
- **NO COMMENTS** in code files
- Use **ENGLISH ONLY** for all code, variables, functions, and documentation
- Self-documenting code with clear naming

### Python environment
- ALWAYS use `python3` instead of `python`
- ALWAYS use `pip3` instead of `pip` 
- ALWAYS work in virtual environment `venv`
- Activate venv: `source venv/bin/activate` (Linux/Mac) or `venv\\Scripts\\activate` (Windows)

### Directory structure
- ALWAYS check existing directories before creating new ones
- Use `python3 .claude/update.py` to update context
- DO NOT create new config*/test*/src* directories without checking

### Code unification principle
- **AVOID DUPLICATION**: Before creating new functionality, check existing code
- **EXTEND, DON'T DUPLICATE**: Build on existing solutions rather than creating parallel implementations
- **UNIFIED APPROACH**: If similar functionality exists, refactor to create a single, flexible solution

### Claude Context Box Management
```bash
# Project context management  
python3 claude-context.py help         # Show all available commands
python3 claude-context.py sync         # Sync documentation and context
python3 claude-context.py update       # Update project context
python3 claude-context.py check        # Quick conflict check
python3 claude-context.py modules      # List modules with status
python3 claude-context.py structure    # Show project structure

# Code cleanup with Skylos
python3 claude-context.py cleancode --interactive  # Interactive cleanup
python3 claude-context.py cleancode --dry-run      # Preview changes only
python3 claude-context.py cleancode --confidence 80 # High confidence only

# Short aliases work too
python3 claude-context.py h    # help
python3 claude-context.py sy   # sync
python3 claude-context.py u    # update  
python3 claude-context.py cc   # cleancode
```

### Command mappings:
When I type `update` or `u`, you MUST run: `python3 .claude/update.py`
When I type `check` or `c`, you MUST run: `python3 .claude/check.py`
When I type `structure` or `s`, you MUST run: `cat .claude/context.json | python3 -m json.tool`
When I type `conflicts` or `cf`, you MUST run: `cat .claude/format.md | grep -A20 "WARNINGS"`
When I type `venv` or `v`, you MUST run: `bash .claude/setup.sh`
When I type `help` or `h`, you MUST show: the command list from CLAUDE.md
When I type `cleancode` or `cc`, you MUST run: `python3 claude-context.py cleancode --interactive`

## ⚠️ IMPORTANT UPDATE RULE
If I make structural changes (create/delete directories, add new modules),
you MUST suggest running:
```bash
python3 .claude/update.py
```

### Automatic checks
- **Before creating new directories** → first run: `python3 .claude/update.py`
- **Before creating similar functionality** → check existing code structure
- **After refactoring structure** → must run: `python3 .claude/update.py`
- **When unsure about structure** → update context before continuing

"""

        # Add preserved content if any
        if preserved.get('existing_content'):
            template += f"""

## Preserved Original Content
{preserved['existing_content']}

"""

        template += f"""
---
<!-- AUTO-GENERATED SECTION - DO NOT EDIT -->
*This file is managed by Claude Context Box*
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return template

    # ===== SCRIPT GENERATION (FROM OLD VERSION) =====
    
    def create_directory_structure(self):
        """Create necessary directories"""
        print("📁 Creating project structure...")
        self.claude_dir.mkdir(exist_ok=True)
        (self.claude_dir / 'reports').mkdir(exist_ok=True)
        
    def create_update_py(self):
        """Create update.py script with ProjectContextManager (FROM OLD VERSION)"""
        print("🐍 Creating update script...")
        
        # This is the FULL update.py content from the old version
        update_content = '''#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any

class ProjectContextManager:
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path).resolve()
        self.claude_dir = self.root / ".claude"
        self.context_file = self.claude_dir / "context.json"
        self.format_file = self.claude_dir / "format.md"
        
        self.ignore_patterns = {
            '__pycache__', '.git', '.claude', 'node_modules', 
            '.venv', 'venv', 'env', '.env', '*.pyc', '.DS_Store',
            'dist', 'build', '.pytest_cache', '.mypy_cache',
            '*.egg-info', '.tox', 'htmlcov', '.coverage'
        }
        
        self.claude_dir.mkdir(exist_ok=True)
    
    def check_python_env(self) -> Dict[str, Any]:
        env_info = {
            "python_version": sys.version.split()[0],
            "venv_active": False,
            "venv_path": None,
            "pip_version": None
        }
        
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            env_info["venv_active"] = True
            env_info["venv_path"] = sys.prefix
        
        venv_paths = ['venv', '.venv', 'env', '.env']
        for venv_name in venv_paths:
            venv_path = self.root / venv_name
            if venv_path.exists() and (venv_path / 'bin' / 'python').exists():
                env_info["venv_path"] = str(venv_path)
                break
        
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                env_info["pip_version"] = result.stdout.split()[1]
        except:
            pass
        
        return env_info
    
    def should_ignore(self, path) -> bool:
        if isinstance(path, str):
            name = path
        else:
            name = path.name
        
        if name in self.ignore_patterns:
            return True
            
        for pattern in self.ignore_patterns:
            if '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(name, pattern):
                    return True
        
        return False
    
    def scan_directory_structure(self) -> Dict[str, Any]:
        structure = {
            "directories": {},
            "file_types": {},
            "config_dirs": [],
            "test_dirs": [],
            "source_dirs": [],
            "python_files": 0,
            "has_requirements": False,
            "has_setup_py": False,
            "has_pyproject": False
        }
        
        if (self.root / "requirements.txt").exists():
            structure["has_requirements"] = True
        if (self.root / "setup.py").exists():
            structure["has_setup_py"] = True
        if (self.root / "pyproject.toml").exists():
            structure["has_pyproject"] = True
        
        for path in self.root.rglob("*"):
            if any(self.should_ignore(part) for part in path.parts):
                continue
                
            rel_path = path.relative_to(self.root)
            
            if path.is_dir():
                dir_name = path.name.lower()
                
                if 'config' in dir_name or 'settings' in dir_name:
                    structure["config_dirs"].append(str(rel_path))
                elif 'test' in dir_name or 'spec' in dir_name:
                    structure["test_dirs"].append(str(rel_path))
                elif dir_name in ['src', 'source', 'lib', 'app']:
                    structure["source_dirs"].append(str(rel_path))
                
                structure["directories"][str(rel_path)] = {
                    "type": self.classify_directory(path),
                    "file_count": len(list(path.glob("*")))
                }
            
            elif path.is_file():
                ext = path.suffix.lower()
                if ext:
                    structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                    if ext == '.py':
                        structure["python_files"] += 1
        
        return structure
    
    def classify_directory(self, path: Path) -> str:
        name = path.name.lower()
        
        if 'config' in name or 'settings' in name:
            return "configuration"
        elif 'test' in name or 'spec' in name:
            return "tests"
        elif name in ['src', 'source', 'lib', 'app']:
            return "source"
        elif name in ['docs', 'documentation']:
            return "documentation"
        elif name in ['scripts', 'bin']:
            return "scripts"
        elif name in ['static', 'assets', 'public']:
            return "assets"
        else:
            return "general"
    
    def analyze_naming_conflicts(self, structure: Dict) -> List[Dict]:
        conflicts = []
        
        config_dirs = structure["config_dirs"]
        if len(config_dirs) > 1:
            conflicts.append({
                "type": "config_conflict",
                "severity": "high",
                "message": f"Multiple config directories found: {config_dirs}",
                "recommendation": f"Use '{config_dirs[0]}' as primary config directory"
            })
        
        test_dirs = structure["test_dirs"]
        if len(test_dirs) > 1:
            conflicts.append({
                "type": "test_conflict",
                "severity": "high",
                "message": f"Multiple test directories found: {test_dirs}",
                "recommendation": f"Use '{test_dirs[0]}' as primary test directory"
            })
        
        all_dirs = list(structure["directories"].keys())
        for dir_path in all_dirs:
            dir_name = Path(dir_path).name
            
            if dir_name.endswith('s'):
                singular = dir_name[:-1]
                singular_paths = [d for d in all_dirs if Path(d).name == singular]
                if singular_paths:
                    conflicts.append({
                        "type": "naming_conflict",
                        "severity": "medium",
                        "message": f"Both '{singular}' and '{dir_name}' exist",
                        "recommendation": f"Use consistent naming (prefer '{dir_name}')"
                    })
        
        return conflicts
    
    def extract_dependencies(self) -> Dict[str, List[str]]:
        deps = {}
        
        req_files = ["requirements.txt", "requirements-dev.txt", "requirements.in", 
                     "pyproject.toml", "setup.py", "Pipfile"]
        python_deps = []
        for req_file in req_files:
            path = self.root / req_file
            if path.exists():
                python_deps.append(req_file)
        
        if python_deps:
            deps["python"] = python_deps
        
        if (self.root / "package.json").exists():
            deps["nodejs"] = ["package.json"]
            if (self.root / "package-lock.json").exists():
                deps["nodejs"].append("package-lock.json")
            if (self.root / "yarn.lock").exists():
                deps["nodejs"].append("yarn.lock")
        
        return deps
    
    def create_compact_context(self) -> Dict[str, Any]:
        structure = self.scan_directory_structure()
        conflicts = self.analyze_naming_conflicts(structure)
        dependencies = self.extract_dependencies()
        python_env = self.check_python_env()
        
        entry_points = []
        common_entries = ["main.py", "app.py", "index.py", "run.py", "start.py",
                         "manage.py", "__main__.py", "cli.py", "server.py"]
        
        for entry in common_entries:
            for path in self.root.rglob(entry):
                if not any(self.should_ignore(part) for part in path.parts):
                    entry_points.append(str(path.relative_to(self.root)))
        
        context = {
            "project_name": self.root.name,
            "last_updated": datetime.now().isoformat(),
            "python_env": python_env,
            "structure": structure,
            "conflicts": conflicts,
            "dependencies": dependencies,
            "entry_points": entry_points[:5],
            "statistics": {
                "total_directories": len(structure["directories"]),
                "total_python_files": structure["python_files"],
                "file_types": dict(sorted(
                    structure["file_types"].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10])
            }
        }
        
        return context
    
    def format_context_for_claude(self, context: Dict) -> str:
        md_lines = [
            f"# Project Context: {context['project_name']}",
            f"*Updated: {context['last_updated']}*",
            ""
        ]
        
        env = context["python_env"]
        md_lines.extend([
            "## 🐍 Python Environment",
            f"- Python: `{env['python_version']}`",
            f"- Venv: {'✅ ACTIVE' if env['venv_active'] else '❌ NOT ACTIVE'}",
        ])
        
        if env["venv_path"] and not env["venv_active"]:
            md_lines.append(f"- **ACTION REQUIRED**: Activate venv with `source {env['venv_path']}/bin/activate`")
        
        if not env["venv_path"]:
            md_lines.append("- **WARNING**: No venv found. Create with `python3 -m venv venv`")
        
        md_lines.append("")
        
        if context["conflicts"]:
            md_lines.extend([
                "## ⚠️ CRITICAL WARNINGS - READ FIRST!",
                ""
            ])
            for conflict in context["conflicts"]:
                severity_icon = "🔴" if conflict["severity"] == "high" else "🟡"
                md_lines.extend([
                    f"### {severity_icon} {conflict['type'].replace('_', ' ').title()}",
                    f"- **Issue**: {conflict['message']}",
                    f"- **REQUIRED ACTION**: {conflict['recommendation']}",
                    f"- **DO NOT**: Create new directories without resolving this",
                    ""
                ])
        
        md_lines.extend([
            "## Directory Structure",
            "",
            "### Primary Directories (USE THESE!):"
        ])
        
        if context["structure"]["config_dirs"]:
            md_lines.append(f"- **Config**: `{context['structure']['config_dirs'][0]}/` ✅ USE THIS")
            if len(context["structure"]["config_dirs"]) > 1:
                md_lines.append(f"  - ❌ DO NOT USE: {', '.join(context['structure']['config_dirs'][1:])}")
        
        if context["structure"]["test_dirs"]:
            md_lines.append(f"- **Tests**: `{context['structure']['test_dirs'][0]}/` ✅ USE THIS")
            if len(context["structure"]["test_dirs"]) > 1:
                md_lines.append(f"  - ❌ DO NOT USE: {', '.join(context['structure']['test_dirs'][1:])}")
                
        if context["structure"]["source_dirs"]:
            md_lines.append(f"- **Source**: `{context['structure']['source_dirs'][0]}/` ✅ USE THIS")
        
        md_lines.extend(["", "### All Directories:"])
        
        for dir_path, info in sorted(context["structure"]["directories"].items()):
            indent = "  " * dir_path.count("/")
            md_lines.append(f"{indent}- `{Path(dir_path).name}/` ({info['type']}, {info['file_count']} files)")
        
        md_lines.append("")
        
        if context["dependencies"]:
            md_lines.extend([
                "## Dependencies",
                ""
            ])
            for lang, files in context["dependencies"].items():
                icon = "🐍" if lang == "python" else "📦"
                md_lines.append(f"- {icon} **{lang}**: {', '.join(files)}")
            md_lines.append("")
        
        if context["structure"]["python_files"] > 0:
            md_lines.extend([
                "## Python Project Info",
                f"- Total Python files: {context['structure']['python_files']}",
                f"- Has requirements.txt: {'✅' if context['structure']['has_requirements'] else '❌'}",
                f"- Has setup.py: {'✅' if context['structure']['has_setup_py'] else '❌'}",
                f"- Has pyproject.toml: {'✅' if context['structure']['has_pyproject'] else '❌'}",
                ""
            ])
        
        if context["entry_points"]:
            md_lines.extend([
                "## Entry Points",
                ""
            ])
            for entry in context["entry_points"]:
                md_lines.append(f"- `{entry}`")
            md_lines.append("")
        
        md_lines.extend([
            "## File Types",
            ""
        ])
        for ext, count in list(context["statistics"]["file_types"].items())[:5]:
            md_lines.append(f"- `{ext}`: {count} files")
        
        md_lines.extend([
            "",
            "## 🔄 Context Update Reminder",
            "",
            "**Quick commands**: Type `u` (update), `c` (check), `s` (structure), `cf` (conflicts), `v` (venv)",
            "**Remember**: Always use `python3` and `pip3`, work in venv!",
        ])
        
        return "\\n".join(md_lines)
    
    def update(self):
        print("🔄 Scanning project structure...")
        
        context = self.create_compact_context()
        
        with open(self.context_file, 'w') as f:
            json.dump(context, f, indent=2)
        
        formatted = self.format_context_for_claude(context)
        with open(self.format_file, 'w') as f:
            f.write(formatted)
        
        print(f"✅ Context updated!")
        print(f"📊 Found {context['statistics']['total_directories']} directories")
        
        env = context["python_env"]
        if not env["venv_active"] and env["venv_path"]:
            print(f"\\n⚠️  Virtual environment found but NOT ACTIVE!")
            print(f"   Run: source {env['venv_path']}/bin/activate")
        elif not env["venv_path"]:
            print(f"\\n⚠️  No virtual environment found!")
            print(f"   Create one with: python3 -m venv venv")
        
        if context['conflicts']:
            print(f"\\n⚠️  {len(context['conflicts'])} warnings found:")
            for conflict in context['conflicts']:
                print(f"   - {conflict['message']}")
                print(f"     → {conflict['recommendation']}")
        
        print(f"\\n💾 Context saved to:")
        print(f"   - {self.context_file}")
        print(f"   - {self.format_file}")

if __name__ == "__main__":
    manager = ProjectContextManager()
    manager.update()
'''
        
        update_path = self.claude_dir / 'update.py'
        update_path.write_text(update_content)
        update_path.chmod(update_path.stat().st_mode | stat.S_IEXEC)
        
    def create_check_py(self):
        """Create check.py script (FROM OLD VERSION)"""
        print("🔍 Creating check script...")
        
        check_content = '''#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def quick_check():
    context_file = Path(".claude/context.json")
    if not context_file.exists():
        print("❌ Context not found. Run: python3 .claude/update.py")
        sys.exit(1)
    
    with open(context_file) as f:
        context = json.load(f)
    
    env = context.get("python_env", {})
    if not env.get("venv_active") and env.get("venv_path"):
        print("⚠️  VENV NOT ACTIVATED!")
        print(f"   Run: source {env['venv_path']}/bin/activate")
        print()
    
    if context.get("conflicts"):
        print("⚠️  CONFLICTS DETECTED:")
        for conflict in context["conflicts"]:
            print(f"\\n{conflict['type']}:")
            print(f"  Problem: {conflict['message']}")
            print(f"  Solution: {conflict['recommendation']}")
    else:
        print("✅ No conflicts found")
    
    print(f"\\nLast update: {context['last_updated']}")
    
    if context["statistics"].get("total_python_files", 0) > 0:
        print(f"\\nPython files: {context['statistics']['total_python_files']}")

if __name__ == "__main__":
    quick_check()
'''
        
        check_path = self.claude_dir / 'check.py'
        check_path.write_text(check_content)
        check_path.chmod(check_path.stat().st_mode | stat.S_IEXEC)
        
    def create_setup_sh(self):
        """Create setup.sh script (FROM OLD VERSION)"""
        print("🔧 Creating setup script...")
        
        setup_content = '''#!/bin/bash

echo "🚀 Setting up Python environment..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔄 Activating venv..."
source venv/bin/activate || {
    echo "❌ Failed to activate venv"
    echo "   Try: source venv/bin/activate"
    exit 1
}

echo "📦 Upgrading pip..."
pip3 install --upgrade pip

if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo "🔄 Updating project context..."
python3 .claude/update.py

echo "✅ Done! Now you can run: claude"
'''
        
        setup_path = self.claude_dir / 'setup.sh'
        setup_path.write_text(setup_content)
        setup_path.chmod(setup_path.stat().st_mode | stat.S_IEXEC)
        
    def create_gitignore(self):
        """Create .gitignore for .claude directory"""
        print("📄 Creating .claude/.gitignore...")
        
        gitignore_content = '''context.json
format.md
reports/

!update.py
!check.py
!setup.sh
!.gitignore
'''
        
        gitignore_path = self.claude_dir / '.gitignore'
        gitignore_path.write_text(gitignore_content)
        
    def create_claude_md_full(self):
        """Create full CLAUDE.md with enhanced instructions (FROM OLD VERSION + ENHANCEMENTS)"""
        print("📝 Creating comprehensive CLAUDE.md...")
        
        claude_md_path = self.root / 'CLAUDE.md'
        parent_claude = self.root.parent / 'CLAUDE.md'
        
        content = self._generate_enhanced_claude_md({})
        claude_md_path.write_text(content)
        
        print("✅ Comprehensive CLAUDE.md created with full instructions")
        
    def _display_analysis(self, analysis: Dict):
        """Display project analysis results"""
        print("\n📊 Project Analysis Results")
        print("=" * 50)
        
        # Basic stats
        print(f"\n📁 Project: {analysis.get('project_name', 'Unknown')}")
        print(f"Total files: {analysis.get('total_files', 0)}")
        print(f"Python files: {analysis.get('python_files', 0)}")
        print(f"Modules found: {len(analysis.get('module_directories', []))}")
        print(f"README coverage: {analysis.get('readme_coverage', 0):.0%}")
        
        # Dead code analysis
        dead_code = analysis.get('dead_code_analysis')
        if dead_code:
            print(f"Dead code items: {dead_code['total_items']}")
            if dead_code['has_dead_code']:
                print(f"  - Unused imports: {dead_code['unused_imports']}")
                print(f"  - Unused functions: {dead_code['unused_functions']}")
                print(f"  - Unused classes: {dead_code['unused_classes']}")
                print(f"  - Unused variables: {dead_code['unused_variables']}")
        
        # Indicators
        print(f"\n📈 Analysis scores:")
        chaos = analysis.get('chaos_indicators', 0)
        org = analysis.get('organization_indicators', 0)
        print(f"Chaos indicators: {'🔴' * min(chaos, 10)} ({chaos})")
        print(f"Organization indicators: {'🟢' * min(org, 10)} ({org})")
        
        # Issues found
        scattered_scripts = analysis.get('scattered_scripts', [])
        if scattered_scripts:
            print(f"\n⚠️  Scattered scripts in root: {len(scattered_scripts)}")
            for script in scattered_scripts[:5]:
                print(f"   - {script}")
            if len(scattered_scripts) > 5:
                print(f"   ... and {len(scattered_scripts) - 5} more")
        
        # Project type
        project_types = {
            "legacy_chaotic": "🔥 Legacy/Chaotic Project",
            "organized": "✅ Organized Project", 
            "new_project": "🌱 New/Empty Project",
            "existing_claude": "📦 Existing Claude Setup"
        }
        
        print(f"\n🎯 Detected project type: {project_types.get(analysis.get('type'), 'Unknown')}")
        
        # Recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
                
        print("\n" + "=" * 50)
    
    def run_initial_update(self):
        """Run initial context update"""
        print("\n🔄 Initial project scan...")
        
        try:
            result = subprocess.run([sys.executable, str(self.claude_dir / 'update.py')], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"❌ Error during initial scan: {result.stderr}")
        except Exception as e:
            print(f"❌ Failed to run initial update: {e}")
            
    def _show_completion_message(self):
        """Show completion message with available commands"""
        print("")
        print("✅ Claude Context Box installation completed!")
        print("")
        print("📋 Available commands:")
        print("   python3 claude-context.py help      - Show all commands") 
        print("   python3 claude-context.py sync      - Sync documentation")
        print("   python3 claude-context.py update    - Update context")
        print("   python3 claude-context.py check     - Quick check")
        print("   python3 claude-context.py cleancode - Clean dead code")
        print("")
        print("📋 Classic commands (still work):")
        print("   python3 .claude/update.py  - Update context")
        print("   python3 .claude/check.py   - Quick check")
        print("   bash .claude/setup.sh      - Setup Python environment")
        print("")
        print("💡 Now run: claude")
        print("")
        
    def install(self):
        """Main installation entry point"""
        print("🚀 Claude Context Box - Ultimate Hybrid Installer")
        print("=" * 55)
        
        # Check Python version
        if sys.version_info < (3, 6):
            print("❌ Python 3.6+ required")
            sys.exit(1)
        
        # Determine installation type
        if not self.claude_md_exists():
            # Fresh installation
            print("\n🌟 New project detected - starting fresh installation...")
            self.fresh_install()
        else:
            # Ask user what to do
            choice = self.ask_installation_type()
            
            if choice == "update":
                self.update_existing_installation()
            elif choice == "fresh":
                self.fresh_install_with_backup()
            elif choice == "cancel":
                print("\n❌ Installation cancelled.")
                return
        
        print("\n🎉 Installation completed successfully!")

# ===== CLI INTEGRATION (FROM NEW VERSION) =====
class ClaudeContextManager:
    """Main command handler for Claude Context Box (FROM NEW VERSION)"""
    
    def __init__(self):
        self.root = Path.cwd()
        self.claude_dir = self.root / '.claude'
        self.scanner = SkylosScanner(self.root)
        self.analyzer = ProjectAnalyzer(self.root)
        
    def show_help(self):
        """Show help information"""
        print("🚀 CLAUDE CONTEXT BOX - HYBRID MANAGEMENT")
        print("=" * 52)
        print()
        
        print("📋 MAIN COMMANDS:")
        print("  sync, sy      - Sync documentation and context")
        print("  update, u     - Update project context")
        print("  check, c      - Quick conflict check")
        print("  modules, m    - List modules with status")
        print("  brief, b      - Show PROJECT_BRIEF.md")
        print("  structure, s  - Show project structure")
        print("  cleancode, cc - Clean code (using Skylos)")
        print("  help, h       - Show this help")
        print("  install       - Install/update Claude Context Box")
        print()
        
        print("🔧 SKYLOS INTEGRATION:")
        print("  cleancode --interactive - Interactive cleanup")
        print("  cleancode --dry-run     - Preview changes")
        print("  cleancode --confidence 80 - High confidence only")
        print()
        
        print("📖 WORKFLOW:")
        print("  1. Start each session: sync")
        print("  2. Make changes")
        print("  3. End with: sync")
        print()
        
        print("💡 Classic commands also work:")
        print("  python3 .claude/update.py")
        print("  python3 .claude/check.py")
        print("  bash .claude/setup.sh")
        print()
        
        print("💡 Claude will run these automatically!")
        print("=" * 52)
        
    def sync(self):
        """Sync documentation and context"""
        print("🔄 Syncing documentation and context...")
        
        # Run sync if exists
        sync_script = self.claude_dir / 'sync.py'
        if sync_script.exists():
            result = subprocess.run(['python3', str(sync_script)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"❌ Sync failed: {result.stderr}")
        else:
            # Fallback to update
            print("📄 No sync script found, running update instead...")
            self.update()
            
    def update(self):
        """Update project context"""
        print("🔄 Updating project context...")
        
        # Run update if exists
        update_script = self.claude_dir / 'update.py'
        if update_script.exists():
            result = subprocess.run(['python3', str(update_script)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"❌ Update failed: {result.stderr}")
        else:
            print("⚠️  No update script found. Run install first.")
            
    def check(self):
        """Quick conflict check"""
        print("🔍 Running quick conflict check...")
        
        check_script = self.claude_dir / 'check.py'
        if check_script.exists():
            result = subprocess.run(['python3', str(check_script)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"❌ Check failed: {result.stderr}")
        else:
            print("⚠️  No check script found. Run install first.")
            
    def modules(self):
        """List modules with status"""
        print("📋 Listing modules with status...")
        
        analysis = self.analyzer.analyze()
        modules = analysis.get('module_directories', [])
        
        if not modules:
            print("📂 No modules found")
            return
            
        print(f"📂 Found {len(modules)} modules:")
        for module in modules:
            module_path = self.root / module
            has_readme = (module_path / "README.md").exists()
            has_init = (module_path / "__init__.py").exists()
            status = "✅" if has_readme and has_init else "⚠️"
            print(f"  {status} {module}")
            
    def brief(self):
        """Show PROJECT_BRIEF.md"""
        print("📋 Showing PROJECT_BRIEF.md...")
        
        brief_file = self.root / 'PROJECT_BRIEF.md'
        if brief_file.exists():
            print(brief_file.read_text())
        else:
            print("📄 PROJECT_BRIEF.md not found.")
            
    def structure(self):
        """Show project structure"""
        print("📊 Showing project structure...")
        
        context_file = self.claude_dir / 'context.json'
        if context_file.exists():
            result = subprocess.run(['python3', '-m', 'json.tool', str(context_file)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print("❌ Failed to read context file")
        else:
            print("⚠️  No context file found. Run update first.")
            
    def cleancode(self, interactive: bool = False, dry_run: bool = False, confidence: int = 60):
        """Clean code using Skylos"""
        print("🧹 Cleaning code with Skylos...")
        
        # Determine skylos executable
        venv_path = self.root / 'venv'
        if venv_path.exists():
            if sys.platform == "win32":
                skylos_exe = str(venv_path / 'Scripts' / 'skylos.exe')
            else:
                skylos_exe = str(venv_path / 'bin' / 'skylos')
        else:
            skylos_exe = 'skylos'
        
        # Build command
        cmd = [skylos_exe, str(self.root), '--confidence', str(confidence)]
        
        if interactive:
            cmd.append('--interactive')
        if dry_run:
            cmd.append('--dry-run')
            
        try:
            result = subprocess.run(cmd, text=True)
            if result.returncode == 0:
                print("✅ Code cleanup completed!")
            else:
                print("❌ Code cleanup failed!")
                
        except FileNotFoundError:
            print("⚠️  Skylos not found. Installing...")
            if self.scanner.install_skylos():
                print("✅ Skylos installed! Try cleancode again.")
            else:
                print("❌ Failed to install Skylos")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Claude Context Box - Hybrid Management')
    parser.add_argument('command', nargs='?', default='help',
                      help='Command to run: sync, update, check, modules, brief, structure, cleancode, help, install')
    parser.add_argument('--interactive', action='store_true',
                      help='Interactive mode (with cleancode)')
    parser.add_argument('--dry-run', action='store_true',
                      help='Dry run mode (with cleancode)')
    parser.add_argument('--confidence', type=int, default=60,
                      help='Confidence threshold for cleancode (0-100)')
    
    args = parser.parse_args()
    
    # Handle command aliases
    command_map = {
        'sy': 'sync',
        'u': 'update',
        'c': 'check',
        'm': 'modules',
        'b': 'brief',
        's': 'structure',
        'cc': 'cleancode',
        'h': 'help'
    }
    
    cmd = command_map.get(args.command, args.command)
    
    if cmd == 'install':
        installer = ClaudeContextHybridInstaller()
        installer.install()
    else:
        manager = ClaudeContextManager()
        
        if cmd == 'help':
            manager.show_help()
        elif cmd == 'sync':
            manager.sync()
        elif cmd == 'update':
            manager.update()
        elif cmd == 'check':
            manager.check()
        elif cmd == 'modules':
            manager.modules()
        elif cmd == 'brief':
            manager.brief()
        elif cmd == 'structure':
            manager.structure()
        elif cmd == 'cleancode':
            manager.cleancode(args.interactive, args.dry_run, args.confidence)
        else:
            print(f"Unknown command: {args.command}")
            print("Run 'python3 claude-context-hybrid.py help' for available commands")

if __name__ == '__main__':
    main()