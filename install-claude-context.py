#!/usr/bin/env python3
"""
Claude Context Box - Minimal Installer
Creates .claude/ directory with management scripts
"""
import os
import sys
import stat
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class ClaudeContextInstaller:
    def __init__(self):
        self.root = Path.cwd()
        self.claude_dir = self.root / '.claude'
        
    def install(self):
        """Main installation process"""
        print("🚀 Claude Context Box - Installation")
        print("=" * 50)
        
        # Check if already installed
        if (self.root / 'CLAUDE.md').exists():
            print("⚠️  CLAUDE.md already exists!")
            response = input("Update existing installation? (y/n): ")
            if response.lower() != 'y':
                print("Installation cancelled.")
                return
        
        print("📁 Creating directory structure...")
        self.create_directories()
        
        print("📝 Creating/Updating scripts...")
        # Always overwrite scripts to ensure latest version
        self.create_update_script()
        self.create_check_script()
        self.create_setup_script()
        self.create_help_script()
        self.create_cleancode_script()
        self.create_gitignore()
        print("✅ All scripts updated to latest version")
        
        print("📄 Creating/Updating CLAUDE.md...")
        self.create_or_update_claude_md()
        
        print("🔄 Running initial update...")
        self.run_initial_update()
        
        print("\n✅ Installation completed!")
        print("\n📋 Quick commands (type in Claude):")
        print("  u     - Update context")
        print("  c     - Check conflicts")
        print("  cc    - Clean dead code")
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
        update_path.write_text(content)
        update_path.chmod(update_path.stat().st_mode | stat.S_IEXEC)
    
    def create_check_script(self):
        """Create check.py for quick conflict checking"""
        content = '''#!/usr/bin/env python3
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
    
    print("🔧 DIRECT COMMANDS:")
    print("  python3 .claude/update.py    - Update context")
    print("  python3 .claude/check.py     - Quick check")
    print("  python3 .claude/cleancode.py - Clean dead code")
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
            "### ⚠️ IMPORTANT UPDATE RULE",
            "If I make structural changes (create/delete directories, add new modules),",
            "you MUST suggest running:",
            "```bash",
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
    installer = ClaudeContextInstaller()
    installer.install()