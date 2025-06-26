#!/usr/bin/env python3
"""
Claude Context Box Installer
Safe installation with proper escaping
"""
import os
import sys
import stat
import json
from pathlib import Path
from datetime import datetime

class ClaudeContextInstaller:
    def __init__(self):
        self.root = Path.cwd()
        self.claude_dir = self.root / '.claude'
        
    def create_directory_structure(self):
        """Create necessary directories"""
        print("📁 Creating project structure...")
        self.claude_dir.mkdir(exist_ok=True)
        
    def create_update_py(self):
        """Create update.py script"""
        print("🐍 Creating update script...")
        
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
    
    def analyze_similar_files(self, structure: Dict) -> Dict[str, List[str]]:
        patterns = {
            "utilities": ["utils", "util", "helpers", "helper", "common", "shared"],
            "validators": ["validator", "validators", "validation", "validate", "checks"],
            "configuration": ["config", "configs", "settings", "configuration", "conf"],
            "database": ["db", "database", "models", "model", "orm"],
            "authentication": ["auth", "authentication", "login", "users", "user"],
            "api": ["api", "endpoints", "routes", "views", "handlers"]
        }
        
        found_patterns = {}
        
        for path in self.root.rglob("*.py"):
            if self.should_ignore(path):
                continue
            
            file_stem = path.stem.lower()
            for pattern_name, keywords in patterns.items():
                for keyword in keywords:
                    if keyword in file_stem:
                        if pattern_name not in found_patterns:
                            found_patterns[pattern_name] = []
                        rel_path = str(path.relative_to(self.root))
                        if rel_path not in found_patterns[pattern_name]:
                            found_patterns[pattern_name].append(rel_path)
                        break
        
        return {k: v for k, v in found_patterns.items() if len(v) > 1}
    
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
        
        dep_files = {
            "Gemfile": "ruby",
            "go.mod": "go", 
            "Cargo.toml": "rust",
            "pom.xml": "java",
            "build.gradle": "java/kotlin",
            "composer.json": "php",
            "pubspec.yaml": "dart/flutter"
        }
        
        for dep_file, lang in dep_files.items():
            if (self.root / dep_file).exists():
                deps[lang] = [dep_file]
        
        return deps
    
    def create_compact_context(self) -> Dict[str, Any]:
        structure = self.scan_directory_structure()
        conflicts = self.analyze_naming_conflicts(structure)
        dependencies = self.extract_dependencies()
        python_env = self.check_python_env()
        
        entry_points = []
        common_entries = ["main.py", "app.py", "index.py", "run.py", "start.py",
                         "manage.py", "__main__.py", "cli.py", "server.py",
                         "index.js", "index.ts", "main.go", "Main.java"]
        
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
        
        parent_claude = self.root.parent / "CLAUDE.md"
        if parent_claude.exists():
            md_lines.extend([
                "## 📁 Subproject Context",
                f"- Parent project: `{self.root.parent.name}`",
                f"- Subproject path: `{self.root.name}/`",
                ""
            ])
        
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
            "If you're about to:",
            "- Create new directories → Run `python3 .claude/update.py` FIRST",
            "- Install new packages → Run `pip3 install` then `python3 .claude/update.py`",
            "- Refactor structure → Run `python3 .claude/update.py` AFTER",
            "- Not sure about structure → Run `python3 .claude/update.py` NOW",
            "",
            "**Quick commands**: Type `u` (update), `c` (check), `s` (structure), `cf` (conflicts), `v` (venv)",
            "**Remember**: Always use `python3` and `pip3`, work in venv!",
            "**Code style**: No comments, English only, self-documenting code"
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
        """Create check.py script"""
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
        """Create setup.sh script"""
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

!update.py
!check.py
!setup.sh
!.gitignore
'''
        
        gitignore_path = self.claude_dir / '.gitignore'
        gitignore_path.write_text(gitignore_content)
        
    def create_claude_md(self):
        """Create or update CLAUDE.md"""
        print("📝 Setting up CLAUDE.md...")
        
        claude_md_path = self.root / 'CLAUDE.md'
        parent_claude = self.root.parent / 'CLAUDE.md'
        
        if claude_md_path.exists():
            print("⚠️  CLAUDE.md already exists!")
            
            # Check if our context import already exists
            content = claude_md_path.read_text()
            if '@.claude/format.md' in content:
                print("✅ Context import already present in CLAUDE.md")
                return
            else:
                print("📝 Adding context import to existing CLAUDE.md...")
                
                # Backup
                backup_path = self.root / 'CLAUDE.md.backup'
                backup_path.write_text(content)
                print(f"💾 Backup saved as {backup_path}")
                
                # Add our rules at the beginning
                additions = self.get_context_rules(parent_claude.exists())
                new_content = additions + "\n\n" + content
                claude_md_path.write_text(new_content)
                
                print("✅ Context rules added to CLAUDE.md")
                print("💡 Your original content is preserved below the new rules")
        else:
            print("📝 Creating new CLAUDE.md...")
            
            # Create new CLAUDE.md
            content = self.get_full_claude_md(parent_claude.exists())
            claude_md_path.write_text(content)
            
            if parent_claude.exists():
                print("📁 Parent CLAUDE.md detected and imported!")
                
    def get_context_rules(self, has_parent: bool) -> str:
        """Get context rules to add to existing CLAUDE.md"""
        rules = ["## ===== Claude Context Box Rules =====", ""]
        
        if has_parent:
            rules.extend([
                "## Import parent context",
                "@../CLAUDE.md",
                ""
            ])
            
        rules.extend([
            "## Automatic project context",
            "@.claude/format.md",
            ""
        ])
        
        return "\n".join(rules)
        
    def get_full_claude_md(self, has_parent: bool) -> str:
        """Get full CLAUDE.md content"""
        lines = ["# Project Context Protocol", ""]
        
        if has_parent:
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
            "",
            "### Command mappings:",
            "When I type `update` or `u`, you MUST run: `python3 .claude/update.py`",
            "When I type `check` or `c`, you MUST run: `python3 .claude/check.py`",
            "When I type `structure` or `s`, you MUST run: `cat .claude/context.json | python3 -m json.tool`",
            "When I type `conflicts` or `cf`, you MUST run: `cat .claude/format.md | grep -A20 \"WARNINGS\"`",
            "When I type `venv` or `v`, you MUST run: `bash .claude/setup.sh`",
            "When I type `help` or `h`, you MUST show: the command list from CLAUDE.md",
            "When I type `deps` or `d`, you MUST run: `cat .claude/format.md | grep -A10 \"Dependencies\"`",
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
        
        return "\n".join(lines)
        
    def run_initial_update(self):
        """Run initial context update"""
        print("")
        print("🔄 Initial project scan...")
        
        import subprocess
        result = subprocess.run([sys.executable, str(self.claude_dir / 'update.py')], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Error during initial scan: {result.stderr}")
            
    def install(self):
        """Main installation process"""
        print("🚀 Claude Context Box Installer")
        print("===============================")
        
        # Check Python
        if sys.version_info < (3, 6):
            print("❌ Python 3.6+ required")
            sys.exit(1)
            
        # Create structure
        self.create_directory_structure()
        
        # Create scripts
        self.create_update_py()
        self.create_check_py()
        self.create_setup_sh()
        self.create_gitignore()
        
        # Create/update CLAUDE.md
        self.create_claude_md()
        
        # Run initial update
        self.run_initial_update()
        
        # Final messages
        print("")
        print("✅ Claude Context Box installed successfully!")
        print("")
        print("📋 Available commands:")
        print("   python3 .claude/update.py  - Update context")
        print("   python3 .claude/check.py   - Quick check")
        print("   bash .claude/setup.sh      - Setup Python environment")
        print("")
        
        if (self.root / 'CLAUDE.md.backup').exists():
            print("⚠️  Your original CLAUDE.md was backed up to CLAUDE.md.backup")
            print("   The context rules were added at the top of CLAUDE.md")
            print("")
            
        print("💡 Now run: claude")
        print("")
        print("📦 To copy to another project:")
        print("   1. Copy .claude folder")
        print("   2. Run: python3 install-claude-context.py in the new project")
        print("")


if __name__ == '__main__':
    installer = ClaudeContextInstaller()
    installer.install()
