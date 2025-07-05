#!/usr/bin/env python3
"""
Claude Context Box - Minimal Installer
Creates .claude/ directory with management scripts
"""
import os
import sys
import stat
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

class ClaudeContextInstaller:
    def __init__(self):
        self.root = Path.cwd()
        self.claude_dir = self.root / '.claude'
        
        # Common venv check code for all Python scripts
        self.venv_check = '''# Check if we should use venv Python
venv_python = Path.cwd() / 'venv' / 'bin' / 'python3'
if venv_python.exists() and sys.executable != str(venv_python):
    # Re-run with venv Python
    import subprocess
    result = subprocess.run([str(venv_python), __file__] + sys.argv[1:])
    sys.exit(result.returncode)
'''
        
    def install(self, auto_yes=False):
        """Main installation process"""
        print("🚀 Claude Context Box - Installation")
        print("=" * 50)
        
        # Check if already installed
        if (self.root / 'CLAUDE.md').exists():
            print("⚠️  CLAUDE.md already exists!")
            if not auto_yes:
                try:
                    response = input("Update existing installation? (y/n): ")
                    if response.lower() != 'y':
                        print("Installation cancelled.")
                        return
                except EOFError:
                    print("\n❌ Non-interactive mode detected. Use -y flag to auto-confirm.")
                    sys.exit(1)
            else:
                print("✅ Auto-updating existing installation...")
        
        print("📁 Creating directory structure...")
        self.create_directories()
        
        print("📝 Creating/Updating scripts...")
        # Always overwrite scripts to ensure latest version
        self.create_update_script()
        self.create_check_script()
        self.create_setup_script()
        self.create_help_script()
        self.create_cleancode_script()
        self.create_context_script()
        self.create_gitignore()
        print("✅ All scripts updated to latest version")
        
        print("📄 Creating/Updating CLAUDE.md...")
        self.create_or_update_claude_md()
        
        print("🔄 Running initial update...")
        self.run_initial_update()
        
        print("\n✅ Installation completed!")
        print("\n🚀 IMPORTANT: Initialize component documentation:")
        print("  1. Type: ctx init --auto")
        print("  2. Type: u (to update context)")
        print("\n📋 Quick commands (type in Claude):")
        print("  u     - Update context")
        print("  c     - Check conflicts")
        print("  cc    - Clean dead code")
        print("  ctx   - Manage CONTEXT.llm files")
        print("  h     - Show help")
        print("\n💡 Activate venv: source venv/bin/activate")
        
    def create_directories(self):
        """Create necessary directories"""
        self.claude_dir.mkdir(exist_ok=True)
        (self.claude_dir / 'reports').mkdir(exist_ok=True)
        
    def create_update_script(self):
        """Create update.py for context management"""
        content = '''#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any

''' + self.venv_check + '''

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
        
        # CONTEXT.llm Integration
        context_files = list(self.root.rglob('CONTEXT.llm'))
        if context_files:
            md_lines.extend([
                "",
                "## 📦 Component Architecture (from CONTEXT.llm)",
                ""
            ])
            
            components_by_type = {}
            for context_file in context_files:
                try:
                    content = context_file.read_text()
                    comp_type = 'unknown'
                    comp_name = 'Unknown'
                    purpose = ''
                    
                    # Simple parsing for format.md
                    for line in content.split('\\n'):
                        if line.startswith('@component:'):
                            comp_name = line.split(':', 1)[1].strip()
                        elif line.startswith('@type:'):
                            comp_type = line.split(':', 1)[1].strip()
                        elif line.startswith('@purpose:'):
                            purpose = line.split(':', 1)[1].strip()
                    
                    if comp_type not in components_by_type:
                        components_by_type[comp_type] = []
                    
                    rel_path = context_file.parent.relative_to(self.root)
                    components_by_type[comp_type].append({
                        'path': str(rel_path),
                        'name': comp_name,
                        'purpose': purpose
                    })
                except:
                    pass
            
            for comp_type, components in sorted(components_by_type.items()):
                md_lines.append(f"### {comp_type.title()} Components")
                for comp in components:
                    md_lines.append(f"- `{comp['path']}/{comp['name']}`: {comp['purpose']}")
                md_lines.append("")
        
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
        update_path.write_text(content)
        update_path.chmod(update_path.stat().st_mode | stat.S_IEXEC)
    
    def create_check_script(self):
        """Create check.py for quick conflict checking"""
        content = '''#!/usr/bin/env python3
import json
import sys
from pathlib import Path

''' + self.venv_check + '''

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
        check_path.write_text(content)
        check_path.chmod(check_path.stat().st_mode | stat.S_IEXEC)
    
    def create_setup_script(self):
        """Create setup.sh for environment setup"""
        content = '''#!/bin/bash

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

echo "✅ Done! Environment is ready."
'''
        
        setup_path = self.claude_dir / 'setup.sh'
        setup_path.write_text(content)
        setup_path.chmod(setup_path.stat().st_mode | stat.S_IEXEC)
    
    def create_help_script(self):
        """Create help.py for showing available commands"""
        content = '''#!/usr/bin/env python3
import sys
from pathlib import Path

''' + self.venv_check + '''

def show_help():
    print("🚀 CLAUDE CONTEXT BOX - HELP")
    print("=" * 52)
    print()
    
    print("📋 QUICK COMMANDS (just type these in chat):")
    print("  update, u     - Update project context")
    print("  check, c      - Quick conflict check")
    print("  structure, s  - Show project structure")
    print("  conflicts, cf - Show only conflicts")
    print("  venv, v       - Setup/check Python environment")
    print("  help, h       - Show this help")
    print("  deps, d       - Show dependencies")
    print("  cleancode, cc - Interactive dead code cleanup")
    print()
    print("📚 CONTEXT.llm COMMANDS:")
    print("  scan          - Find components without docs")
    print("  ctx init      - Create CONTEXT.llm for ALL modules")
    print("  ctx generate  - Create CONTEXT.llm for one module")
    print("  ctx update    - Update existing CONTEXT.llm files")
    print("  graph         - Show component dependencies")
    print()
    
    print("🔧 DIRECT COMMANDS:")
    print("  python3 .claude/update.py     - Update context")
    print("  python3 .claude/check.py      - Quick check")
    print("  python3 .claude/cleancode.py  - Clean dead code")
    print("  python3 .claude/context.py    - CONTEXT.llm tools")
    print("  bash .claude/setup.sh         - Setup environment")
    print()
    
    print("📖 WORKFLOW:")
    print("  1. Activate venv: source venv/bin/activate")
    print("  2. Update context when structure changes")
    print("  3. Use quick commands for daily work")
    print()
    
    print("💡 Claude automatically runs commands when you type shortcuts!")
    print("=" * 52)

if __name__ == "__main__":
    show_help()
'''
        
        help_path = self.claude_dir / 'help.py'
        help_path.write_text(content)
        help_path.chmod(help_path.stat().st_mode | stat.S_IEXEC)
    
    def create_cleancode_script(self):
        """Create cleancode.py for dead code detection"""
        content = '''#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
import argparse
from pathlib import Path

''' + self.venv_check + '''

class SkylosScanner:
    def __init__(self, root_path=None):
        self.root = root_path or Path.cwd()
        self.reports_dir = self.root / '.claude' / 'reports'
        
    def check_skylos_installation(self):
        try:
            result = subprocess.run(['skylos', '--help'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True
        except FileNotFoundError:
            pass
            
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
            
    def install_skylos(self):
        print("🔧 Installing Skylos...")
        
        try:
            subprocess.run(['git', '--version'], check=True, capture_output=True)
            
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            
            if not in_venv:
                venv_path = self.root / 'venv'
                if not venv_path.exists():
                    print("🔨 Creating virtual environment...")
                    subprocess.run(['python3', '-m', 'venv', str(venv_path)], check=True)
                
                if sys.platform == "win32":
                    pip_exe = venv_path / 'Scripts' / 'pip.exe'
                else:
                    pip_exe = venv_path / 'bin' / 'pip3'
            else:
                pip_exe = 'pip3'
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                print("📥 Cloning Skylos repository...")
                subprocess.run([
                    'git', 'clone', 
                    'https://github.com/duriantaco/skylos.git',
                    str(temp_path / 'skylos')
                ], check=True)
                
                print("📦 Installing Skylos...")
                subprocess.run([
                    str(pip_exe), 'install', str(temp_path / 'skylos')
                ], check=True)
                
                subprocess.run([
                    str(pip_exe), 'install', 'inquirer'
                ], check=True)
            
            print("✅ Skylos installed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install Skylos: {e}")
            return False

def cleancode(interactive=False, dry_run=False, confidence=60):
    print("🧹 Cleaning code with Skylos...")
    
    scanner = SkylosScanner()
    
    if not scanner.check_skylos_installation():
        print("⚠️  Skylos not found. Installing...")
        if not scanner.install_skylos():
            print("❌ Failed to install Skylos")
            return
    
    venv_path = Path.cwd() / 'venv'
    if venv_path.exists():
        if sys.platform == "win32":
            skylos_exe = str(venv_path / 'Scripts' / 'skylos.exe')
        else:
            skylos_exe = str(venv_path / 'bin' / 'skylos')
    else:
        skylos_exe = 'skylos'
    
    cmd = [skylos_exe, str(Path.cwd()), '--confidence', str(confidence)]
    
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
        print("❌ Skylos executable not found after installation")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def main():
    parser = argparse.ArgumentParser(description='Clean dead code with Skylos')
    parser.add_argument('--interactive', action='store_true',
                      help='Interactive mode')
    parser.add_argument('--dry-run', action='store_true',
                      help='Dry run mode')
    parser.add_argument('--confidence', type=int, default=60,
                      help='Confidence threshold (0-100)')
    
    args = parser.parse_args()
    
    cleancode(args.interactive, args.dry_run, args.confidence)

if __name__ == '__main__':
    main()
'''
        
        cleancode_path = self.claude_dir / 'cleancode.py'
        cleancode_path.write_text(content)
        cleancode_path.chmod(cleancode_path.stat().st_mode | stat.S_IEXEC)
    
    def create_context_script(self):
        """Create context.py for CONTEXT.llm management"""
        content = '''#!/usr/bin/env python3
"""
CONTEXT.llm management tool
Provides compact, LLM-optimized component documentation
"""
import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

''' + self.venv_check + '''

class ContextLLMParser:
    def __init__(self):
        self.sections = {}
        self.current_section = None
        self.current_content = []
        
    def parse_file(self, filepath: Path) -> Dict[str, Any]:
        self.sections = {}
        self.current_section = None
        self.current_content = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.rstrip()
            
            if line.startswith('@') and ':' in line:
                self._save_current_section()
                
                key, value = line.split(':', 1)
                key = key.strip('@').strip()
                value = value.strip()
                
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip() for v in value[1:-1].split(',')]
                elif value == '{':
                    self.current_section = key
                    self.current_content = []
                else:
                    self.sections[key] = value
                    self.current_section = key
                    self.current_content = []
            elif self.current_section:
                if line.strip():
                    self.current_content.append(line)
        
        self._save_current_section()
        return self.sections
    
    def _save_current_section(self):
        if self.current_section and self.current_content:
            content = self._parse_content(self.current_content)
            self.sections[self.current_section] = content
    
    def _parse_content(self, lines: List[str]) -> Any:
        if not lines:
            return None
            
        if all(line.startswith('- ') for line in lines if line.strip()):
            return [line[2:].strip() for line in lines if line.strip()]
        
        if all(':' in line for line in lines if line.strip() and not line.startswith('-')):
            result = {}
            for line in lines:
                if ':' in line and not line.startswith('-'):
                    key, value = line.split(':', 1)
                    result[key.strip()] = value.strip()
            return result
        
        return '\\n'.join(lines)

class ContextLLMGenerator:
    def __init__(self):
        self.template = {
            'component': '',
            'type': '',
            'deps': [],
            'exports': [],
            'purpose': '',
            'interface': [],
            'behavior': [],
        }
    
    def from_dict(self, data: Dict[str, Any]) -> str:
        lines = []
        
        for key, value in data.items():
            if isinstance(value, list):
                if value:
                    lines.append(f"@{key}: [{', '.join(str(v) for v in value)}]")
            elif isinstance(value, dict):
                lines.append(f"@{key}:")
                for k, v in value.items():
                    lines.append(f"- {k}: {v}")
            elif value:
                lines.append(f"@{key}: {value}")
                if key in ['purpose', 'interface', 'behavior', 'state', 'errors', 'config', 'notes']:
                    lines.append('')
        
        return '\\n'.join(lines)
    
    def from_code_analysis(self, filepath: Path) -> Dict[str, Any]:
        content = filepath.read_text()
        result = self.template.copy()
        
        result['component'] = filepath.stem
        
        if filepath.suffix == '.py':
            result['type'] = self._detect_python_type(content)
            result['deps'] = self._extract_python_imports(content)
            result['exports'] = self._extract_python_exports(content)
        elif filepath.suffix in ['.js', '.ts', '.jsx', '.tsx']:
            result['type'] = self._detect_js_type(content, filepath.suffix)
            result['deps'] = self._extract_js_imports(content)
            result['exports'] = self._extract_js_exports(content)
        
        return result
    
    def _detect_python_type(self, content: str) -> str:
        if 'class.*Model' in content or 'Base' in content:
            return 'data'
        elif 'app.' in content or 'router.' in content:
            return 'api'
        elif 'Service' in content:
            return 'service'
        else:
            return 'util'
    
    def _detect_js_type(self, content: str, ext: str) -> str:
        if ext in ['.jsx', '.tsx'] or 'React' in content:
            return 'ui'
        elif 'router' in content.lower() or 'express' in content:
            return 'api'
        elif 'service' in content.lower():
            return 'service'
        else:
            return 'module'
    
    def _extract_python_imports(self, content: str) -> List[str]:
        imports = []
        for match in re.finditer(r'(?:from\\s+(\\S+)\\s+)?import\\s+(.+)', content):
            if match.group(1):
                imports.append(match.group(1).split('.')[0])
            else:
                for imp in match.group(2).split(','):
                    imports.append(imp.strip().split()[0])
        return list(set(imports))
    
    def _extract_js_imports(self, content: str) -> List[str]:
        imports = []
        for match in re.finditer(r'(?:import|require)\\s*\\(?[\\'"]([^\\'\"\\)]+)[\\'"]', content):
            imp = match.group(1)
            if not imp.startswith('.'):
                imports.append(imp.split('/')[0])
        return list(set(imports))
    
    def _extract_python_exports(self, content: str) -> List[str]:
        exports = []
        
        for match in re.finditer(r'class\\s+(\\w+)', content):
            exports.append(match.group(1))
        
        for match in re.finditer(r'def\\s+(\\w+)', content):
            func_name = match.group(1)
            if not func_name.startswith('_'):
                exports.append(func_name)
        
        if '__all__' in content:
            match = re.search(r'__all__\\s*=\\s*\\[(.*?)\\]', content, re.DOTALL)
            if match:
                for item in match.group(1).split(','):
                    item = item.strip().strip('"\\\'')
                    if item:
                        exports.append(item)
        
        return list(set(exports))
    
    def _extract_js_exports(self, content: str) -> List[str]:
        exports = []
        
        for match in re.finditer(r'export\\s+(?:default\\s+)?(?:class|function|const|let|var)\\s+(\\w+)', content):
            exports.append(match.group(1))
        
        if 'export default' in content and 'default' not in exports:
            exports.append('default')
        
        for match in re.finditer(r'module\\.exports\\s*=\\s*{([^}]+)}', content):
            for item in match.group(1).split(','):
                if ':' in item:
                    exports.append(item.split(':')[0].strip())
        
        return list(set(exports))

class ContextManager:
    def __init__(self):
        self.root = Path.cwd()
        self.parser = ContextLLMParser()
        self.generator = ContextLLMGenerator()
        
    def scan(self):
        """Find modules without CONTEXT.llm"""
        skipped_dirs = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', 
                       'node_modules', '.claude', 'dist', 'build', '.tox'}
        
        # Find all directories with Python files but no CONTEXT.llm
        missing_dirs = set()
        for py_file in self.root.rglob('*.py'):
            # Skip if in ignored directory
            if any(skip in py_file.parts for skip in skipped_dirs):
                continue
            if py_file.name.startswith('__') or py_file.name.startswith('.'):
                continue
            
            # Check if directory has CONTEXT.llm
            if not (py_file.parent / 'CONTEXT.llm').exists():
                missing_dirs.add(py_file.parent)
        
        if missing_dirs:
            print(f"Found {len(missing_dirs)} directories without CONTEXT.llm:")
            sorted_dirs = sorted(missing_dirs, key=lambda x: str(x))
            for path in sorted_dirs[:10]:
                print(f"  {path.relative_to(self.root)}/")
            if len(missing_dirs) > 10:
                print(f"  ... and {len(missing_dirs) - 10} more")
            print(f"\\nRun 'ctx init' to create CONTEXT.llm for all directories")
        else:
            print("✅ All modules have CONTEXT.llm files!")
    
    def generate(self, filepath: Optional[str] = None, auto: bool = False):
        """Generate CONTEXT.llm for modules"""
        if filepath:
            file_path = self.root / filepath
            if not file_path.exists():
                print(f"❌ File not found: {filepath}")
                return
                
            context_data = self.generator.from_code_analysis(file_path)
            context_content = self.generator.from_dict(context_data)
            
            print(f"\\nGenerated CONTEXT.llm for {filepath}:")
            print("-" * 40)
            print(context_content)
            print("-" * 40)
            
            if not auto:
                response = input("\\nSave this file? (y/n): ")
                if response.lower() != 'y':
                    return
            
            context_path = file_path.parent / 'CONTEXT.llm'
            context_path.write_text(context_content)
            print(f"✅ Saved to {context_path}")
        else:
            # Auto-generate for all missing
            suggestions = []
            scan_dirs = ['src', 'lib', 'components', 'services', 'api', 'models', 'utils']
            
            for dir_name in scan_dirs:
                dir_path = self.root / dir_name
                if dir_path.exists():
                    for file_path in dir_path.rglob('*.py'):
                        if not (file_path.parent / 'CONTEXT.llm').exists():
                            context_data = self.generator.from_code_analysis(file_path)
                            if context_data['deps'] or context_data['exports']:
                                suggestions.append({
                                    'file': file_path,
                                    'data': context_data
                                })
            
            if not suggestions:
                print("✅ All modules already have CONTEXT.llm files!")
                return
            
            print(f"\\nFound {len(suggestions)} modules without CONTEXT.llm")
            
            for suggestion in suggestions:
                file_path = suggestion['file']
                context_content = self.generator.from_dict(suggestion['data'])
                
                if not auto:
                    print(f"\\n{'='*60}")
                    print(f"Generate for {file_path.relative_to(self.root)}?")
                    print("-" * 40)
                    print(context_content[:200] + '...' if len(context_content) > 200 else context_content)
                    print("-" * 40)
                    
                    response = input("Generate? (y/n/q): ")
                    if response.lower() == 'q':
                        break
                    if response.lower() != 'y':
                        continue
                
                context_path = file_path.parent / 'CONTEXT.llm'
                context_path.write_text(context_content)
                print(f"✅ Generated: {context_path.relative_to(self.root)}")
    
    def parse(self, filepath: str, format: str = 'json'):
        """Parse CONTEXT.llm file"""
        file_path = self.root / filepath
        if not file_path.exists():
            print(f"❌ File not found: {filepath}")
            return
            
        parsed = self.parser.parse_file(file_path)
        
        if format == 'json':
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        elif format == 'yaml':
            try:
                import yaml
                print(yaml.dump(parsed, allow_unicode=True, default_flow_style=False))
            except ImportError:
                print("❌ PyYAML not installed. Use 'pip3 install pyyaml'")
        else:
            # Markdown format
            lines = []
            if 'component' in parsed:
                lines.append(f"# {parsed['component']}")
            for key, value in parsed.items():
                if key != 'component':
                    lines.append(f"\\n## {key.title()}")
                    if isinstance(value, list):
                        for item in value:
                            lines.append(f"- {item}")
                    elif isinstance(value, dict):
                        for k, v in value.items():
                            lines.append(f"- **{k}**: {v}")
                    else:
                        lines.append(str(value))
            print('\\n'.join(lines))
    
    def graph(self):
        """Show dependency graph"""
        contexts = {}
        
        for context_file in self.root.rglob('CONTEXT.llm'):
            try:
                parsed = self.parser.parse_file(context_file)
                relative_path = context_file.parent.relative_to(self.root)
                contexts[str(relative_path)] = parsed
            except Exception as e:
                print(f"Error parsing {context_file}: {e}")
        
        if not contexts:
            print("No CONTEXT.llm files found")
            return
        
        print("\\n📊 Component Dependency Graph\\n")
        
        for path, context in contexts.items():
            component = context.get('component', path)
            deps = context.get('deps', [])
            
            if deps:
                print(f"{component}")
                for dep in deps:
                    # Check if dep is another component
                    is_internal = any(
                        other.get('component') == dep 
                        for other in contexts.values()
                    )
                    marker = "└── " if deps[-1] == dep else "├── "
                    if is_internal:
                        print(f"  {marker}📦 {dep} (internal)")
                    else:
                        print(f"  {marker}📚 {dep}")
                print()
    
    def init(self, auto: bool = False):
        """Initialize CONTEXT.llm for all modules in project"""
        print("🔍 Scanning project for modules...")
        
        initialized = 0
        skipped_dirs = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', 
                       'node_modules', '.claude', 'dist', 'build', '.tox'}
        
        # Find all directories with Python files
        py_dirs = set()
        for py_file in self.root.rglob('*.py'):
            # Skip if in ignored directory
            if any(skip in py_file.parts for skip in skipped_dirs):
                continue
            if py_file.name.startswith('__') or py_file.name.startswith('.'):
                continue
            py_dirs.add(py_file.parent)
        
        print(f"Found {len(py_dirs)} directories with Python files")
        
        for dir_path in sorted(py_dirs):
            # Skip if CONTEXT.llm already exists
            context_path = dir_path / 'CONTEXT.llm'
            if context_path.exists():
                continue
            
            # Find main Python file in directory
            py_files = list(dir_path.glob('*.py'))
            if not py_files:
                continue
            
            # Choose the main file
            main_file = None
            dir_name = dir_path.name
            
            # Priority: same name as dir, main.py, __init__.py, or first file
            for py_file in py_files:
                if py_file.stem == dir_name:
                    main_file = py_file
                    break
                elif py_file.name == 'main.py':
                    main_file = py_file
                    break
                elif py_file.name == '__init__.py' and len(py_files) > 1:
                    # Use __init__.py only if there are other files
                    main_file = py_file
            
            if not main_file:
                main_file = py_files[0]
            
            # Generate context
            context_data = self.generator.from_code_analysis(main_file)
            
            # Always create CONTEXT.llm, even if no deps/exports
            if not context_data['purpose']:
                context_data['purpose'] = f"Module in {dir_path.relative_to(self.root)}"
                
            context_content = self.generator.from_dict(context_data)
            
            if not auto:
                print(f"\\nCreate CONTEXT.llm for {dir_path.relative_to(self.root)}/?")
                print("-" * 40)
                print(context_content[:150] + '...' if len(context_content) > 150 else context_content)
                print("-" * 40)
                
                response = input("Create? (y/n/a/q): ")
                if response.lower() == 'q':
                    break
                elif response.lower() == 'a':
                    auto = True
                elif response.lower() != 'y':
                    continue
            
            context_path.write_text(context_content)
            print(f"✅ Created: {context_path.relative_to(self.root)}/CONTEXT.llm")
            initialized += 1
        
        print(f"\\n✅ Initialized {initialized} CONTEXT.llm files")
        if initialized > 0:
            print("💡 Run 'update' to refresh project context")
    
    def update_contexts(self):
        """Update existing CONTEXT.llm files based on code changes"""
        print("🔄 Updating CONTEXT.llm files...")
        
        updated = 0
        for context_file in self.root.rglob('CONTEXT.llm'):
            # Find corresponding Python file
            py_files = list(context_file.parent.glob('*.py'))
            if not py_files:
                continue
                
            # Use the main file (same name as directory or the first one)
            main_file = None
            dir_name = context_file.parent.name
            for py_file in py_files:
                if py_file.stem == dir_name or py_file.stem == 'main':
                    main_file = py_file
                    break
            
            if not main_file:
                main_file = py_files[0]
            
            # Parse existing CONTEXT.llm
            old_context = self.parser.parse_file(context_file)
            
            # Generate new context from code
            new_context = self.generator.from_code_analysis(main_file)
            
            # Preserve manual edits (purpose, behavior, notes)
            if 'purpose' in old_context and old_context['purpose']:
                new_context['purpose'] = old_context['purpose']
            if 'behavior' in old_context:
                new_context['behavior'] = old_context['behavior']
            if 'notes' in old_context:
                new_context['notes'] = old_context['notes']
            
            # Check if anything changed
            if (set(new_context.get('deps', [])) != set(old_context.get('deps', [])) or
                set(new_context.get('exports', [])) != set(old_context.get('exports', []))):
                
                new_content = self.generator.from_dict(new_context)
                context_file.write_text(new_content)
                print(f"✅ Updated: {context_file.relative_to(self.root)}")
                updated += 1
        
        print(f"\\n✅ Updated {updated} CONTEXT.llm files")
    
    def help(self):
        """Show CONTEXT.llm format help"""
        print("""
# CONTEXT.llm Format Reference

## Basic Structure
```
@component: ComponentName
@type: service|module|api|ui|data|util
@deps: [dep1, dep2, dep3]
@exports: [export1, export2]

@purpose:
Single line description of component purpose

@interface:
- method1(param1: type) -> returnType
- method2() -> void
- property1: type

@behavior:
- Key behavior or business rule
- Error handling approach
- Performance characteristic

@errors:
- ERROR_CODE: description

@config:
- CONFIG_KEY: type | default | description
```

## Component Types
- **service**: Business logic services
- **module**: General purpose modules  
- **api**: REST/GraphQL endpoints
- **ui**: React/Vue components
- **data**: Models, schemas, DB layers
- **util**: Helper functions, utilities

## Benefits
✅ 50-70% fewer tokens than Markdown
✅ Structured & machine-readable
✅ Auto-generated from code
✅ Integrated with project context

## Commands
- `context init` - Initialize CONTEXT.llm for ALL modules
- `context update` - Update existing CONTEXT.llm files
- `context scan` - Find modules without documentation
- `context generate [file]` - Generate CONTEXT.llm for one file
- `context parse <file>` - View parsed content
- `context graph` - Show dependency graph
- `context help` - This help message

## Workflow
1. `context init --auto` - Create CONTEXT.llm for all modules
2. `update` - Include all CONTEXT.llm in project context
3. Work on code...
4. `context update` - Update CONTEXT.llm when code changes
5. `update` - Refresh project context
""")

def main():
    parser = argparse.ArgumentParser(description='CONTEXT.llm management')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize CONTEXT.llm for all modules')
    init_parser.add_argument('--auto', action='store_true', help='Auto-confirm all')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update existing CONTEXT.llm files')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Find modules without CONTEXT.llm')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate CONTEXT.llm files')
    gen_parser.add_argument('file', nargs='?', help='Specific file to generate for')
    gen_parser.add_argument('--auto', action='store_true', help='Auto-confirm generation')
    
    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse CONTEXT.llm file')
    parse_parser.add_argument('file', help='CONTEXT.llm file to parse')
    parse_parser.add_argument('--format', choices=['json', 'yaml', 'md'], default='json')
    
    # Graph command
    graph_parser = subparsers.add_parser('graph', help='Show dependency graph')
    
    # Help command
    help_parser = subparsers.add_parser('help', help='Show format documentation')
    
    args = parser.parse_args()
    
    manager = ContextManager()
    
    if args.command == 'init':
        manager.init(args.auto)
    elif args.command == 'update':
        manager.update_contexts()
    elif args.command == 'scan':
        manager.scan()
    elif args.command == 'generate':
        manager.generate(args.file, args.auto)
    elif args.command == 'parse':
        manager.parse(args.file, args.format)
    elif args.command == 'graph':
        manager.graph()
    elif args.command == 'help':
        manager.help()
    else:
        # Default action
        manager.help()

if __name__ == '__main__':
    main()
'''
        
        context_path = self.claude_dir / 'context.py'
        context_path.write_text(content)
        context_path.chmod(context_path.stat().st_mode | stat.S_IEXEC)
    
    def create_gitignore(self):
        """Create .gitignore for .claude directory"""
        content = '''context.json
format.md
reports/

!update.py
!check.py
!setup.sh
!help.py
!cleancode.py
!context.py
!.gitignore
'''
        
        gitignore_path = self.claude_dir / '.gitignore'
        gitignore_path.write_text(content)
    
    def extract_user_content(self, content):
        """Extract only user-added content from existing CLAUDE.md"""
        if not content:
            return ""
        
        # Look for the separator that marks user content
        separators = [
            "\n---\n\n# Previous Project Documentation",
            "\n---\n\n# Project Documentation",
            "\n---\n"
        ]
        
        for sep in separators:
            if sep in content:
                # Return only the part after separator
                user_part = content.split(sep, 1)[1].strip()
                # Clean up escaped newlines if present
                if '\\n' in user_part:
                    user_part = user_part.replace('\\n', '\n')
                # Check if this is garbled content from previous bad merge
                if user_part.startswith('# FIRST update context') or 'update context\\n' in user_part:
                    print("⚠️  Detected corrupted user content, skipping...")
                    return ""
                return user_part
        
        # If no separator found, check if it's our standard content
        standard_markers = [
            "# Project Context Protocol",
            "## Automatic project context",
            "## 💡 QUICK COMMANDS",
            "### Command mappings:",
            "When I type `update` or `u`, you MUST run:"
        ]
        
        # Count how many standard markers are present
        marker_count = sum(1 for marker in standard_markers if marker in content)
        
        # If most markers are present, it's likely our standard content
        if marker_count >= 3:
            # Try to find where user content might start
            # Look for common user documentation patterns
            user_sections = [
                "\n## Project Description",
                "\n## Overview",
                "\n## About",
                "\n## Documentation",
                "\n# Documentation",
                "\n## Additional"
            ]
            
            for section in user_sections:
                if section in content:
                    return content.split(section, 1)[1]
            
            # If nothing found, return empty (it's all standard content)
            return ""
        else:
            # This seems to be mostly user content, return all
            return content
    
    def create_or_update_claude_md(self):
        """Create or update CLAUDE.md with instructions"""
        claude_md_path = self.root / 'CLAUDE.md'
        
        # Extract user content if file exists
        user_content = ""
        if claude_md_path.exists():
            existing_content = claude_md_path.read_text()
            # Create backup
            backup_path = self.root / f'CLAUDE_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            backup_path.write_text(existing_content)
            print(f"💾 Backup created: {backup_path.name}")
            
            # Extract only user-added content
            user_content = self.extract_user_content(existing_content)
            if user_content:
                print("📝 Extracted user documentation from existing CLAUDE.md")
        
        lines = ["# Project Context Protocol", ""]
        
        # Check if parent CLAUDE.md exists
        parent_claude = self.root.parent / 'CLAUDE.md'
        if parent_claude.exists():
            lines.extend([
                "## Import parent context",
                "@../CLAUDE.md",
                ""
            ])
            
        lines.extend([
            "## Automatic project context",
            "@.claude/format.md",
            "",
            "## 💡 QUICK COMMANDS",
            "Just type these commands and I'll execute them:",
            "- `update` or `u` - Update project context",
            "- `check` or `c` - Quick conflict check",
            "- `structure` or `s` - Show full project structure",
            "- `conflicts` or `cf` - Show only conflicts",
            "- `venv` or `v` - Setup/check Python environment",
            "- `help` or `h` - Show all commands",
            "- `deps` or `d` - Show dependencies",
            "- `cleancode` or `cc` - Interactive dead code cleanup",
            "- `ctx init` - Initialize CONTEXT.llm for ALL modules",
            "- `ctx update` - Update existing CONTEXT.llm files",
            "- `scan` - Find components without documentation",
            "- `graph` - Show component dependency graph",
            "",
            "## ⚠️ CRITICAL RULES",
            "",
            "### Code style",
            "- **NO COMMENTS** in code files",
            "- Use **ENGLISH ONLY** for all code, variables, functions, and documentation",
            "- Self-documenting code with clear naming",
            "",
            "### Python environment",
            "- ALWAYS use `python3` instead of `python`",
            "- ALWAYS use `pip3` instead of `pip`",
            "- ALWAYS work in virtual environment `venv`",
            "- Activate venv: `source venv/bin/activate` (Linux/Mac) or `venv\\Scripts\\activate` (Windows)",
            "",
            "### Directory structure",
            "- ALWAYS check existing directories before creating new ones",
            "- Use `python3 .claude/update.py` to update context",
            "- DO NOT create new config*/test*/src* directories without checking",
            "",
            "### Code unification principle",
            "- **AVOID DUPLICATION**: Before creating new functionality, check existing code",
            "- **EXTEND, DON'T DUPLICATE**: Build on existing solutions rather than creating parallel implementations",
            "- **UNIFIED APPROACH**: If similar functionality exists, refactor to create a single, flexible solution",
            "- Examples:",
            "  - Don't create `user_validator.py` if `validators.py` exists - extend it",
            "  - Don't create `config2/` if `config/` exists - reorganize existing",
            "  - Don't create `new_utils.py` if `utils.py` exists - add to existing",
            "",
            "### Component documentation (AUTOMATIC)",
            "- **ALWAYS create CONTEXT.llm** when creating new directories with code",
            "- **ALWAYS update CONTEXT.llm** when modifying files in a directory",
            "- **ALWAYS read CONTEXT.llm** before working with files in a directory",
            "- Format: compact, LLM-optimized, 50-70% fewer tokens",
            "",
            "### CONTEXT.llm automation rules",
            "When creating a new module/directory:",
            "1. Create the directory and files",
            "2. Immediately create CONTEXT.llm with component info",
            "3. Run `update` to include in project context",
            "",
            "When modifying existing modules:",
            "1. Read existing CONTEXT.llm first",
            "2. Update code as needed", 
            "3. Update CONTEXT.llm to reflect changes",
            "4. Run `update` if structure changed significantly",
            "",
            "### ⚠️ IMPORTANT UPDATE RULE",
            "If I make structural changes (create/delete directories, add new modules),",
            "you MUST suggest running:",
            "```bash",
            "source venv/bin/activate  # First activate venv",
            "python3 .claude/update.py",
            "```",
            "",
            "### Automatic checks",
            "- **Before creating new directories** → first run: `python3 .claude/update.py`",
            "- **Before creating similar functionality** → check existing code structure",
            "- **After refactoring structure** → must run: `python3 .claude/update.py`",
            "- **When unsure about structure** → update context before continuing",
            "",
            "### Context update workflow",
            "1. Ensure venv is activated",
            "2. Run: `python3 .claude/update.py`",
            "3. Check updated context: `cat .claude/format.md`",
            "4. Continue work with current context",
            "",
            "## Typical scenarios requiring update",
            "",
            "### 1. Creating new functionality",
            "```bash",
            "# FIRST update context",
            "python3 .claude/update.py",
            "# THEN create files/folders",
            "```",
            "",
            "### 2. Structure refactoring",
            "```bash",
            "# Before refactoring - check current structure",
            "python3 .claude/update.py",
            "# After refactoring - update context",
            "python3 .claude/update.py",
            "```",
            "",
            "### 3. Resolving conflicts",
            "If I say something like:",
            "- \"put in configs\" (but config exists)",
            "- \"create tests\" (but test exists)",
            "- \"add to src\" (but source exists)",
            "",
            "YOU MUST:",
            "1. Stop",
            "2. Suggest running `python3 .claude/update.py`",
            "3. Show existing directories from context",
            "4. Ask which one to use",
            "",
            "## Python-specific rules",
            "",
            "### Installing dependencies",
            "```bash",
            "# ALWAYS in venv",
            "source venv/bin/activate  # or venv\\Scripts\\activate on Windows",
            "pip3 install -r requirements.txt",
            "```",
            "",
            "### Creating venv if missing",
            "```bash",
            "python3 -m venv venv",
            "source venv/bin/activate",
            "pip3 install --upgrade pip",
            "```",
            "",
            "### Adding new packages",
            "```bash",
            "# In activated venv",
            "pip3 install package_name",
            "pip3 freeze > requirements.txt",
            "python3 .claude/update.py  # Update context!",
            "```",
            "",
            "## Project commands",
            "",
            "### Quick commands (just type these):",
            "- `update` or `u` → Update project context",
            "- `check` or `c` → Quick conflict check",
            "- `structure` or `s` → Show project structure",
            "- `conflicts` or `cf` → Show current conflicts",
            "- `venv` or `v` → Setup Python environment",
            "- `help` or `h` → Show all commands",
            "- `deps` or `d` → Show dependencies",
            "- `cleancode` or `cc` → Interactive dead code cleanup",
            "",
            "### Command mappings:",
            "When I type `update` or `u`, you MUST run: `python3 .claude/update.py`",
            "When I type `check` or `c`, you MUST run: `python3 .claude/check.py`",
            "When I type `structure` or `s`, you MUST run: `cat .claude/context.json | python3 -m json.tool`",
            "When I type `conflicts` or `cf`, you MUST run: `cat .claude/format.md | grep -A20 \"WARNINGS\"`",
            "When I type `venv` or `v`, you MUST run: `bash .claude/setup.sh`",
            "When I type `help` or `h`, you MUST run: `python3 .claude/help.py`",
            "When I type `deps` or `d`, you MUST run: `cat .claude/format.md | grep -A10 \"Dependencies\"`",
            "When I type `cleancode` or `cc`, you MUST run: `python3 .claude/cleancode.py --interactive`",
            "When I type `ctx init`, you MUST run: `python3 .claude/context.py init`",
            "When I type `ctx update`, you MUST run: `python3 .claude/context.py update`",
            "When I type `scan`, you MUST run: `python3 .claude/context.py scan`",
            "When I type `graph`, you MUST run: `python3 .claude/context.py graph`",
            "",
            "## CONTEXT.llm Format & Examples",
            "",
            "### Basic format (auto-create when making directories):",
            "```",
            "@component: ComponentName",
            "@type: service|module|api|ui|data|util",
            "@deps: [dep1, dep2]",
            "@purpose: Single line description",
            "",
            "@interface:",
            "- method(param: type) -> return",
            "- property: type",
            "",
            "@behavior:",
            "- Key behavior",
            "- Error handling",
            "```",
            "",
            "### Example workflow:",
            "User: \"Create an auth service\"",
            "You MUST:",
            "1. Create `services/auth/` directory",
            "2. Create `services/auth/auth_service.py`", 
            "3. Create `services/auth/CONTEXT.llm`:",
            "```",
            "@component: AuthService",
            "@type: service",
            "@deps: [bcrypt, jwt, models.User]",
            "@purpose: Handle user authentication and token management",
            "",
            "@interface:",
            "- authenticate(email: str, password: str) -> dict",
            "- create_token(user_id: str) -> str",
            "- verify_token(token: str) -> bool",
            "",
            "@behavior:",
            "- Passwords hashed with bcrypt",
            "- JWT tokens expire in 24h",
            "- Failed auth rate limited",
            "```",
            "4. Run `update` to refresh context",
            "",
            "Run `context help` for full format documentation.",
            "",
            "## Initial setup (if not done yet)",
            "```bash",
            "# 1. Create virtual environment",
            "python3 -m venv venv",
            "",
            "# 2. Activate venv",
            "source venv/bin/activate  # Linux/Mac",
            "# or",
            "venv\\Scripts\\activate     # Windows",
            "",
            "# 3. Update context",
            "python3 .claude/update.py",
            "```"
        ])
        
        content = '\n'.join(lines)
        
        # If there was user content, append it at the end
        if user_content:
            # Add separator and user content
            content += "\n\n---\n\n# Project Documentation\n\n"
            content += user_content
            print("📝 Preserved user documentation at the end")
        
        claude_md_path.write_text(content)
        print(f"✅ CLAUDE.md created/updated ({len(content.splitlines())} lines)")
    
    def run_initial_update(self):
        """Run initial context update"""
        try:
            result = subprocess.run([sys.executable, str(self.claude_dir / 'update.py')], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"❌ Error during initial scan: {result.stderr}")
        except Exception as e:
            print(f"❌ Failed to run initial update: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Claude Context Box Installer')
    parser.add_argument('-y', '--yes', action='store_true',
                       help='Auto-confirm updates (non-interactive mode)')
    
    args = parser.parse_args()
    
    installer = ClaudeContextInstaller()
    installer.install(auto_yes=args.yes)