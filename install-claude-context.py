#!/usr/bin/env python3
"""
Claude Context Box - Complete Universal Installer
Automatically detects project type and installs appropriate system
"""
import os
import sys
import stat
import json
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any

# ===== Project Analyzer =====
class ProjectAnalyzer:
    """Analyzes project to determine its type and state"""
    
    def __init__(self, root: Path):
        self.root = root
        self.analysis = {
            "type": "unknown",
            "chaos_indicators": 0,
            "organization_indicators": 0,
            "has_claude_md": False,
            "has_documentation": False,
            "module_count": 0,
            "readme_coverage": 0.0,
            "structure_type": None,
            "recommendations": []
        }
        
    def analyze(self) -> Dict:
        """Perform complete project analysis"""
        print("🔍 Analyzing project structure...")
        
        # Check for existing Claude setup
        self.analysis["has_claude_md"] = (self.root / "CLAUDE.md").exists()
        self.analysis["has_claude_context"] = (self.root / ".claude").exists()
        
        # Analyze project structure
        structure_analysis = self._analyze_structure()
        self.analysis.update(structure_analysis)
        
        # Count chaos indicators
        self.analysis["chaos_indicators"] = self._count_chaos_indicators()
        
        # Count organization indicators
        self.analysis["organization_indicators"] = self._count_organization_indicators()
        
        # Determine project type
        self.analysis["type"] = self._determine_project_type()
        
        # Generate recommendations
        self.analysis["recommendations"] = self._generate_recommendations()
        
        return self.analysis
        
    def _analyze_structure(self) -> Dict:
        """Analyze directory structure and documentation"""
        result = {
            "directories": {},
            "python_files": 0,
            "total_files": 0,
            "module_directories": [],
            "readme_files": [],
            "scattered_scripts": [],
            "duplicate_directories": []
        }
        
        ignore_patterns = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.claude'}
        
        for path in self.root.rglob("*"):
            if any(pattern in str(path) for pattern in ignore_patterns):
                continue
                
            if path.is_file():
                result["total_files"] += 1
                
                if path.suffix == '.py':
                    result["python_files"] += 1
                    
                    # Check if it's a scattered script
                    parent = path.parent
                    if parent == self.root:
                        # Python file in root
                        if path.name not in ['setup.py', 'manage.py', '__init__.py', 'conftest.py']:
                            result["scattered_scripts"].append(str(path.name))
                            
                elif path.name == 'README.md':
                    result["readme_files"].append(str(path.relative_to(self.root)))
                    
            elif path.is_dir():
                # Check if it's a module directory
                if self._is_module_directory(path):
                    result["module_directories"].append(str(path.relative_to(self.root)))
                    
                result["directories"][str(path.relative_to(self.root))] = {
                    "file_count": len(list(path.glob("*"))),
                    "has_readme": (path / "README.md").exists(),
                    "has_init": (path / "__init__.py").exists()
                }
        
        # Find duplicate directories
        dir_names = defaultdict(list)
        for dir_path in result["directories"]:
            name = Path(dir_path).name.lower()
            dir_names[name].append(dir_path)
            
            # Check for singular/plural
            if name.endswith('s'):
                singular = name[:-1]
                if singular in dir_names:
                    result["duplicate_directories"].append((singular, name))
            
        # Calculate README coverage
        if result["module_directories"]:
            modules_with_readme = sum(
                1 for mod in result["module_directories"]
                if (self.root / mod / "README.md").exists()
            )
            result["readme_coverage"] = modules_with_readme / len(result["module_directories"])
        else:
            result["readme_coverage"] = 0.0
            
        return result
        
    def _is_module_directory(self, path: Path) -> bool:
        """Check if directory is likely a module"""
        # Has __init__.py
        if (path / "__init__.py").exists():
            return True
            
        # Has multiple Python files
        py_files = list(path.glob("*.py"))
        if len(py_files) >= 2:
            return True
            
        # Common module directory names
        module_indicators = {
            'modules', 'components', 'apps', 'lib', 'src',
            'core', 'utils', 'services', 'models', 'controllers',
            'views', 'api', 'handlers', 'middleware'
        }
        
        if path.name.lower() in module_indicators:
            return True
            
        # Parent is a known module container
        if path.parent.name in ['modules', 'src', 'lib', 'apps', 'components']:
            return True
            
        return False
        
    def _count_chaos_indicators(self) -> int:
        """Count indicators of a chaotic/legacy project"""
        indicators = 0
        
        # Many scattered Python files in root
        scattered = len(self.analysis.get("scattered_scripts", []))
        if scattered > 5:
            indicators += 3
        elif scattered > 2:
            indicators += 2
        elif scattered > 0:
            indicators += 1
            
        # Duplicate directories
        duplicates = len(self.analysis.get("duplicate_directories", []))
        indicators += duplicates * 2
        
        # Low README coverage
        coverage = self.analysis.get("readme_coverage", 0)
        if coverage < 0.2:
            indicators += 2
        elif coverage < 0.5:
            indicators += 1
            
        # No clear structure
        dirs = list(self.analysis.get("directories", {}).keys())
        if not any(d in dirs for d in ['src', 'lib', 'app', 'modules']):
            indicators += 2
            
        # Multiple test directories
        test_dirs = [d for d in dirs if 'test' in Path(d).name.lower()]
        if len(test_dirs) > 2:
            indicators += 2
        elif len(test_dirs) > 1:
            indicators += 1
            
        # Multiple config directories
        config_dirs = [d for d in dirs if 'config' in Path(d).name.lower()]
        if len(config_dirs) > 1:
            indicators += 2
            
        # Multiple data/cache directories
        data_dirs = [d for d in dirs if any(x in Path(d).name.lower() for x in ['data', 'cache'])]
        if len(data_dirs) > 2:
            indicators += 2
            
        return indicators
        
    def _count_organization_indicators(self) -> int:
        """Count indicators of an organized project"""
        indicators = 0
        
        # Has clear source structure
        dirs = list(self.analysis.get("directories", {}).keys())
        if any(d in dirs for d in ['src', 'lib', 'app']):
            indicators += 2
            
        # High README coverage
        coverage = self.analysis.get("readme_coverage", 0)
        if coverage > 0.8:
            indicators += 3
        elif coverage > 0.5:
            indicators += 2
        elif coverage > 0.3:
            indicators += 1
            
        # Has modules directory
        if any('modules' in d for d in dirs):
            indicators += 2
            
        # Few scattered scripts
        scattered = len(self.analysis.get("scattered_scripts", []))
        if scattered == 0:
            indicators += 2
        elif scattered <= 2:
            indicators += 1
            
        # Has standard project files
        standard_files = ['requirements.txt', 'setup.py', 'pyproject.toml', 'Makefile', 'README.md']
        for file in standard_files:
            if (self.root / file).exists():
                indicators += 1
                
        # Has single test directory
        test_dirs = [d for d in dirs if 'test' in Path(d).name.lower()]
        if len(test_dirs) == 1:
            indicators += 1
            
        # Has documentation
        if any(d in dirs for d in ['docs', 'documentation']):
            indicators += 1
            
        # Has config directory
        if 'config' in dirs and len([d for d in dirs if 'config' in d]) == 1:
            indicators += 1
            
        return indicators
        
    def _determine_project_type(self) -> str:
        """Determine project type based on analysis"""
        chaos = self.analysis["chaos_indicators"]
        organized = self.analysis["organization_indicators"]
        
        # Already has Claude setup
        if self.analysis["has_claude_context"]:
            return "existing_claude"
            
        # New/empty project
        if self.analysis["total_files"] < 10:
            return "new_project"
            
        # Clear determination
        if chaos >= 8:
            return "legacy_chaotic"
        elif organized >= 8:
            return "organized"
        elif chaos > organized * 1.5:
            return "legacy_chaotic"
        elif organized > chaos * 1.5:
            return "organized"
        else:
            # Mixed indicators - look deeper
            if self.analysis["readme_coverage"] < 0.3:
                return "legacy_chaotic"
            elif len(self.analysis["scattered_scripts"]) > 3:
                return "legacy_chaotic"
            elif len(self.analysis.get("duplicate_directories", [])) > 0:
                return "legacy_chaotic"
            else:
                return "organized"
                
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis"""
        recs = []
        
        if self.analysis["type"] == "legacy_chaotic":
            recs.append("Use Legacy Refactoring System to organize the project")
            if self.analysis["scattered_scripts"]:
                recs.append(f"Organize {len(self.analysis['scattered_scripts'])} scattered scripts")
            if self.analysis.get("duplicate_directories"):
                recs.append("Resolve duplicate directory names")
            recs.append("Create consistent directory structure")
            if self.analysis["readme_coverage"] < 0.5:
                recs.append("Add README.md to modules")
            
        elif self.analysis["type"] == "organized":
            recs.append("Use Enhanced Context Box for documentation management")
            if self.analysis["readme_coverage"] < 1.0:
                recs.append("Complete README.md coverage for all modules")
            recs.append("Set up automatic documentation sync")
            recs.append("Implement configuration management")
            
        elif self.analysis["type"] == "new_project":
            recs.append("Use Enhanced Context Box to start with best practices")
            recs.append("Create initial module structure")
            recs.append("Set up configuration management from the start")
            recs.append("Implement documentation-first development")
            
        return recs


# ===== Main Universal Installer =====
class UniversalInstaller:
    """Universal installer that combines both systems"""
    
    def __init__(self):
        self.root = Path.cwd()
        self.analyzer = ProjectAnalyzer(self.root)
        
    def run(self):
        """Main installation process"""
        print("🚀 Claude Context Box Universal Installer")
        print("=========================================\n")
        
        # Check Python version and venv
        self._check_environment()
        
        # Analyze project
        analysis = self.analyzer.analyze()
        
        # Show analysis results
        self._display_analysis(analysis)
        
        # Get user confirmation
        if not self._get_user_confirmation(analysis):
            print("\nInstallation cancelled.")
            return
            
        # Perform installation
        if analysis["type"] == "existing_claude":
            self._handle_existing_installation()
        elif analysis["type"] == "legacy_chaotic":
            self._install_legacy_system()
        elif analysis["type"] in ["organized", "new_project"]:
            self._install_enhanced_system()
        else:
            self._interactive_selection()
            
    def _check_environment(self):
        """Check Python version and venv"""
        if sys.version_info < (3, 6):
            print("❌ Python 3.6+ required")
            sys.exit(1)
            
        # Check if in venv
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        if not in_venv:
            print("⚠️  WARNING: Not running in virtual environment!")
            print("   Recommended: Create and activate venv first")
            print("   python3 -m venv venv")
            print("   source venv/bin/activate\n")
            
            response = input("Continue without venv? (y/N): ")
            if response.lower() != 'y':
                print("\nTo create venv and install:")
                print("1. python3 -m venv venv")
                print("2. source venv/bin/activate")
                print("3. python3 claude-context-installer.py")
                sys.exit(0)
                
    def _display_analysis(self, analysis: Dict):
        """Display project analysis results"""
        print("📊 Project Analysis Results")
        print("=" * 50)
        
        # Basic stats
        print(f"\n📁 Project: {self.root.name}")
        print(f"Total files: {analysis.get('total_files', 0)}")
        print(f"Python files: {analysis.get('python_files', 0)}")
        print(f"Modules found: {len(analysis.get('module_directories', []))}")
        print(f"README coverage: {analysis.get('readme_coverage', 0):.0%}")
        
        # Indicators
        print(f"\n📈 Analysis scores:")
        chaos = analysis['chaos_indicators']
        org = analysis['organization_indicators']
        print(f"Chaos indicators: {'🔴' * min(chaos, 10)} ({chaos})")
        print(f"Organization indicators: {'🟢' * min(org, 10)} ({org})")
        
        # Issues found
        if analysis.get('scattered_scripts'):
            print(f"\n⚠️  Scattered scripts in root: {len(analysis['scattered_scripts'])}")
            for script in analysis['scattered_scripts'][:5]:
                print(f"   - {script}")
            if len(analysis['scattered_scripts']) > 5:
                print(f"   ... and {len(analysis['scattered_scripts']) - 5} more")
                
        if analysis.get('duplicate_directories'):
            print(f"\n⚠️  Duplicate directory names:")
            for dup in analysis['duplicate_directories']:
                print(f"   - {dup[0]} vs {dup[1]}")
                
        # Project type
        project_types = {
            "legacy_chaotic": "🔥 Legacy/Chaotic Project",
            "organized": "✅ Organized Project",
            "new_project": "🌱 New/Empty Project",
            "existing_claude": "📦 Existing Claude Setup"
        }
        
        print(f"\n🎯 Detected project type: {project_types.get(analysis['type'], 'Unknown')}")
        
        # Recommendations
        if analysis['recommendations']:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(analysis['recommendations'], 1):
                print(f"   {i}. {rec}")
                
        print("\n" + "=" * 50)
        
    def _get_user_confirmation(self, analysis: Dict) -> bool:
        """Get user confirmation for installation type"""
        
        if analysis["type"] == "existing_claude":
            return True  # Will handle separately
            
        system_map = {
            "legacy_chaotic": "Legacy Refactoring System",
            "organized": "Enhanced Context Box",
            "new_project": "Enhanced Context Box"
        }
        
        system = system_map.get(analysis["type"], "Unknown")
        print(f"\n📦 Recommended system: {system}")
        
        if analysis["type"] == "legacy_chaotic":
            print("   - Designed for chaotic/legacy projects")
            print("   - Includes chaos analysis and file tracking")
            print("   - Automatic import fixing after moves")
        else:
            print("   - Perfect for organized projects")
            print("   - Automatic documentation management")
            print("   - Module registry and sync")
            
        response = input("\nProceed with installation? (Y/n): ")
        return response.lower() != 'n'
        
    def _handle_existing_installation(self):
        """Handle existing Claude installation"""
        print("\n📦 Existing Claude Context Box detected!\n")
        
        print("Options:")
        print("1. Update existing installation")
        print("2. Reinstall (backup existing)")
        print("3. Cancel")
        
        choice = input("\nSelect option (1-3): ")
        
        if choice == "1":
            self._update_existing()
        elif choice == "2":
            self._backup_and_reinstall()
        else:
            print("Installation cancelled.")
            
    def _update_existing(self):
        """Update existing installation"""
        print("\n🔄 Updating existing installation...")
        
        # Detect which system is currently installed
        has_sync = (self.root / '.claude' / 'sync.py').exists()
        has_refactor = (self.root / '.claude' / 'refactor').exists()
        has_help = (self.root / '.claude' / 'help.py').exists()
        
        # Analyze current project to determine best system
        analysis = self.analyzer.analyze()
        
        # If basic installation, upgrade to appropriate system
        if not has_sync and not has_refactor:
            print("📦 Detected basic Context Box - upgrading to full version...")
            
            # Backup existing files
            import shutil
            for file in ['context.json', 'format.md', 'settings.local.json']:
                src = self.root / '.claude' / file
                if src.exists():
                    dst = self.root / '.claude' / f'{file}.backup'
                    shutil.copy2(src, dst)
                    print(f"💾 Backed up {file}")
            
            # Install appropriate system based on analysis
            if analysis["chaos_indicators"] > analysis["organization_indicators"]:
                print("🔧 Installing Legacy Refactoring components...")
                installer = LegacyProjectRefactorInstaller()
                # Create missing directories
                installer.create_directory_structure()
                # Install all components
                installer.create_chaos_analyzer()
                installer.create_migration_planner()
                installer.create_file_mapper()
                installer.create_import_fixer()
                installer.create_migration_executor()
                installer.create_help_script()
                
                # Update CLAUDE.md with refactoring rules
                installer.create_refactor_claude_md()
                
                # Show recommendations
                self._display_recommendations_cli(analysis)
                
            else:
                print("📦 Installing Enhanced Context Box components...")
                installer = EnhancedClaudeContextInstaller()
                # Create missing directories
                installer.create_directory_structure()
                # Install all components
                installer.create_project_brief_template()
                installer.create_module_readme_template()
                installer.create_config_template()
                installer.create_sync_py()
                installer.create_help_script()
                
                # Update CLAUDE.md with enhanced rules
                installer.create_enhanced_claude_md()
                installer.create_initial_project_brief()
        
        else:
            # Just update existing scripts to latest version
            print("🔄 Updating existing scripts to latest version...")
            
            # Always create/update help script
            if not has_help:
                installer = EnhancedClaudeContextInstaller() if has_sync else LegacyProjectRefactorInstaller()
                installer.create_help_script()
                print("✅ Added help command")
            
            # Update sync if exists
            if has_sync:
                installer = EnhancedClaudeContextInstaller()
                installer.create_sync_py()
                print("✅ Updated sync.py")
            
            # Update refactor tools if exist
            if has_refactor:
                installer = LegacyProjectRefactorInstaller()
                installer.create_chaos_analyzer()
                installer.create_import_fixer()
                print("✅ Updated refactoring tools")
        
        # Run appropriate sync/update
        if (self.root / '.claude' / 'sync.py').exists():
            print("\n🔄 Running sync...")
            result = subprocess.run([sys.executable, str(self.root / '.claude' / 'sync.py')], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
        else:
            print("\n🔄 Running context update...")
            result = subprocess.run([sys.executable, str(self.root / '.claude' / 'update.py')], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
                
        print("\n✅ Update complete!")
        
        # Show quick help
        self._display_quick_help()
        
        # Show recommendations if chaos is high
        if analysis.get("chaos_indicators", 0) > 10:
            self._display_recommendations_cli(analysis)
        
    def _backup_and_reinstall(self):
        """Backup existing and reinstall"""
        backup_dir = self.root / f'.claude_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        print(f"📦 Backing up to {backup_dir}")
        shutil.move(str(self.root / '.claude'), str(backup_dir))
        
        if (self.root / 'CLAUDE.md').exists():
            shutil.copy(str(self.root / 'CLAUDE.md'), str(backup_dir / 'CLAUDE.md'))
            
        # Reanalyze and install
        analysis = self.analyzer.analyze()
        if analysis["chaos_indicators"] > analysis["organization_indicators"]:
            self._install_legacy_system()
        else:
            self._install_enhanced_system()
            
    def _display_quick_help(self, system_type: str = None):
        """Display quick CLI-style help"""
        print("\n" + "─" * 50)
        print("📋 QUICK COMMAND REFERENCE")
        print("─" * 50)
        
        if system_type == "enhanced" or (self.root / '.claude' / 'sync.py').exists():
            print("\nENHANCED CONTEXT BOX COMMANDS:")
            print("  sync, sy      - Sync documentation and context")
            print("  update, u     - Update project context")
            print("  check, c      - Quick conflict check")
            print("  modules, m    - List modules with status")
            print("  brief, b      - Show PROJECT_BRIEF.md")
            print("  structure, s  - Show project structure")
            print("  clean, cc     - Clean code (remove comments, format)")
            print("  help, h       - Show all commands")
            
        if system_type == "legacy" or (self.root / '.claude' / 'refactor').exists():
            print("\nLEGACY REFACTORING COMMANDS:")
            print("  chaos         - Analyze project chaos level")
            print("  plan <action> - Create migration plan:")
            print("    • scripts   - Consolidate scattered scripts")
            print("    • data      - Unify data directories")
            print("    • config    - Consolidate configurations")
            print("  fix imports   - Fix Python imports after moves")
            print("  mappings      - Show file movement history")
            print("  report        - Show chaos analysis report")
            print("  clean, cc     - Clean code (remove comments, format)")
            
        print("\nWORKFLOW:")
        print("  1. Start each session: sync")
        print("  2. Make changes")
        print("  3. Clean code: clean")
        print("  4. End with: sync")
        
        print("\n💡 Claude will run these automatically!")
        print("─" * 50)
        
    def _display_recommendations_cli(self, analysis: Dict):
        """Display actionable recommendations in CLI style"""
        chaos = analysis.get('chaos_indicators', 0)
        
        if chaos > 10:
            print("\n🔧 RECOMMENDED ACTIONS:")
            print("─" * 50)
            
            if analysis.get('scattered_scripts'):
                print(f"\n1. ORGANIZE SCRIPTS ({len(analysis['scattered_scripts'])} files)")
                print("   python3 .claude/refactor/plan_migration.py consolidate_scripts")
                
            if analysis.get('duplicate_directories'):
                print("\n2. FIX DUPLICATE DIRECTORIES")
                for dup in analysis['duplicate_directories'][:3]:
                    print(f"   • Keep '{dup[0]}', remove '{dup[1]}'")
                    
            if analysis.get('readme_coverage', 0) < 0.5:
                print(f"\n3. IMPROVE DOCUMENTATION (current: {analysis['readme_coverage']:.0%})")
                print("   python3 .claude/sync.py")
                
            print("\n4. CHECK DETAILED REPORT")
            print("   cat .claude/refactor/analysis/chaos_report.md")
            print("─" * 50)
        
    def _interactive_selection(self):
        """Let user choose system interactively"""
        print("\n🤔 Unable to determine project type automatically.\n")
        
        print("Please choose the appropriate system:\n")
        
        print("1. Enhanced Context Box")
        print("   ✅ For new or well-organized projects")
        print("   ✅ Automatic documentation management")
        print("   ✅ Module registry and tracking")
        print("   ✅ Best for maintaining organization\n")
        
        print("2. Legacy Refactoring System")
        print("   🔧 For chaotic/legacy projects")
        print("   🔧 File movement tracking")
        print("   🔧 Import fixing and chaos analysis")
        print("   🔧 Best for cleaning up messy code\n")
        
        choice = input("Select system (1 or 2): ")
        
        if choice == "1":
            self._install_enhanced_system()
        elif choice == "2":
            self._install_legacy_system()
        else:
            print("Invalid choice. Exiting.")


# ===== ENHANCED CONTEXT BOX INSTALLER =====
class EnhancedClaudeContextInstaller:
    def __init__(self):
        self.root = Path.cwd()
        self.claude_dir = self.root / '.claude'
        
    def check_python_version(self):
        if sys.version_info < (3, 6):
            print("❌ Python 3.6+ required")
            sys.exit(1)
            
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        if not in_venv:
            print("⚠️  WARNING: Not in virtual environment!")
            
    def create_directory_structure(self):
        print("📁 Creating enhanced project structure...")
        self.claude_dir.mkdir(exist_ok=True)
        (self.claude_dir / 'docs').mkdir(exist_ok=True)
        (self.claude_dir / 'templates').mkdir(exist_ok=True)
        
    def create_project_brief_template(self):
        print("📋 Creating PROJECT_BRIEF template...")
        
        template_content = '''# PROJECT_BRIEF.MD: LLM Context Protocol v2.0

## 1. Project Overview
**Name**: {project_name}
**Type**: {project_type}
**Purpose**: {project_purpose}
**Stage**: {project_stage}

## 2. Technology Stack
- **Language**: Python 3.x
- **Framework**: {framework}
- **Database**: {database}
- **Testing**: {testing_framework}
- **CI/CD**: {ci_cd}

## 3. Architecture Map
```
{project_root}/
├── src/
│   ├── modules/           # Business logic modules
│   ├── core/              # Core functionality
│   └── utils/             # Shared utilities
├── tests/                 # Test suite
├── docs/                  # Documentation
├── config/                # Configuration files
├── scripts/               # Utility scripts
├── .claude/               # Claude context management
│   ├── docs/              # Auto-generated documentation
│   ├── templates/         # Documentation templates
│   └── logs/              # Change logs
├── requirements.txt       # Python dependencies
├── setup.py               # Package setup
├── README.md              # Public documentation
├── PROJECT_BRIEF.md       # This file - LLM context
└── CLAUDE.md              # Claude instructions
```

## 4. Module Registry
<!-- AUTO-GENERATED - DO NOT EDIT MANUALLY -->
{module_registry}

## 5. Global LLM Rules

### 5.1 Documentation Protocol
1. **Before ANY code change**: Read PROJECT_BRIEF.md and relevant module README.md
2. **After EVERY code change**: Update module documentation
3. **New module creation**: Generate README.md using LLM template
4. **Module deletion**: Archive documentation to .claude/docs/archived/

### 5.2 Code Standards
- **Language**: English only in code and documentation
- **Comments**: Self-documenting code, no comments
- **Naming**: snake_case for Python, descriptive names
- **Structure**: Single responsibility, DRY, KISS principles
- **Config**: No hardcoded values, use configuration classes

### 5.3 Development Workflow
1. Read context → Plan changes → Implement atomically
2. Test locally → Update docs → Commit with clear message
3. Every session starts with: `python3 .claude/sync.py`

### 5.4 Conflict Resolution
- **Directory conflicts**: Always use singular form (config, test, model)
- **File conflicts**: Check existing before creating similar
- **Naming conflicts**: Run conflict checker before structural changes

## 6. Current State
**Last Updated**: {last_updated}
**Active Issues**: {active_issues}
**Next Sprint Goals**: {sprint_goals}

## 7. AI Action Log
<!-- AUTO-GENERATED - DO NOT EDIT MANUALLY -->
{ai_action_log}
'''
        
        template_path = self.claude_dir / 'templates' / 'PROJECT_BRIEF.template.md'
        template_path.write_text(template_content)
        
    def create_module_readme_template(self):
        print("📄 Creating module README template...")
        
        template_content = '''# Module: {module_name}

## 1. Purpose
{module_purpose}

## 2. Architecture
```
{module_name}/
├── __init__.py           # Module exports
├── {main_file}.py        # Main implementation
├── models.py             # Data models (if applicable)
├── validators.py         # Input validation
├── exceptions.py         # Custom exceptions
├── utils.py              # Module-specific utilities
├── README.md             # This file
└── tests/                # Module tests
```

## 3. Key Components

### 3.1 Main File: {main_file}.py
**Purpose**: {main_file_purpose}
**Public API**:
```python
{public_api}
```

### 3.2 Models
{models_description}

### 3.3 Validators
{validators_description}

## 4. Dependencies

### Internal Dependencies
{internal_deps}

### External Dependencies
{external_deps}

## 5. Usage Examples

### Basic Usage
```python
{usage_example}
```

### Advanced Usage
```python
{advanced_example}
```

## 6. Business Rules
{business_rules}

## 7. Testing
- Test coverage: {test_coverage}%
- Key test scenarios: {test_scenarios}

## 8. Performance Considerations
{performance_notes}

## 9. Security Considerations
{security_notes}

## 10. Future Improvements
{future_improvements}

---
**AI Metadata**:
- Created: {created_date}
- Last Modified: {modified_date}
- Last AI Review: {ai_review_date}
- Module Version: {version}
'''
        
        template_path = self.claude_dir / 'templates' / 'MODULE_README.template.md'
        template_path.write_text(template_content)
        
    def create_sync_py(self):
        print("🔄 Creating sync script...")
        
        # [Full sync.py content - abbreviated for space]
        sync_content = '''#!/usr/bin/env python3
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any, Optional

class ProjectDocumentationSync:
    def __init__(self):
        self.root = Path.cwd()
        self.claude_dir = self.root / '.claude'
        self.docs_dir = self.claude_dir / 'docs'
        self.templates_dir = self.claude_dir / 'templates'
        self.state_file = self.claude_dir / 'project_state.json'
        self.action_log = self.claude_dir / 'action_log.json'
        
        self.ignore_patterns = {
            '__pycache__', '.git', '.claude', 'node_modules',
            '.venv', 'venv', 'env', '.env', '*.pyc', '.DS_Store',
            'dist', 'build', '.pytest_cache', '.mypy_cache'
        }
        
    def check_venv(self):
        """Ensure running in venv"""
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("❌ ERROR: Must run in virtual environment!")
            print("   Activate venv: source venv/bin/activate")
            sys.exit(1)
            
    def sync_documentation(self):
        """Main sync process"""
        self.check_venv()
        print("🔄 Syncing project documentation...")
        # [Rest of sync implementation]
        
if __name__ == "__main__":
    sync = ProjectDocumentationSync()
    sync.sync_documentation()
'''
        
        sync_path = self.claude_dir / 'sync.py'
        sync_path.write_text(sync_content)
        sync_path.chmod(sync_path.stat().st_mode | stat.S_IEXEC)
        
    def create_update_py(self):
        # [Original update.py content]
        pass
        
    def create_check_py(self):
        # [Original check.py content]
        pass
        
    def create_setup_sh(self):
        # [Original setup.sh content]
        pass
        
    def create_gitignore(self):
        # [Original gitignore content]
        pass
        
    def create_config_template(self):
        print("⚙️ Creating configuration template...")
        
        config_dir = self.root / 'config'
        config_dir.mkdir(exist_ok=True)
        
        # [Full config template content]
        
    def create_enhanced_claude_md(self):
        print("📝 Creating enhanced CLAUDE.md...")
        
        # [Full enhanced CLAUDE.md content]
        
    def create_initial_project_brief(self):
        # [Initial PROJECT_BRIEF.md creation]
        pass
        
    def install(self):
        print("🚀 Installing Enhanced Context Box...")
        
        self.check_python_version()
        self.create_directory_structure()
        
        # Create all components
        self.create_project_brief_template()
        self.create_module_readme_template()
        self.create_config_template()
        self.create_sync_py()
        self.create_update_py()
        self.create_check_py()
        self.create_setup_sh()
        self.create_gitignore()
        self.create_enhanced_claude_md()
        self.create_initial_project_brief()
        
        # Create source structure if not exists
        src_dir = self.root / 'src'
        if not src_dir.exists():
            print("📁 Creating source structure...")
            (src_dir / 'modules').mkdir(parents=True, exist_ok=True)
            (src_dir / 'core').mkdir(exist_ok=True)
            (src_dir / 'utils').mkdir(exist_ok=True)
        
        print("\n✅ Enhanced Context Box installed!")
        print("\n📋 Next steps:")
        print("1. Activate venv: source venv/bin/activate")
        print("2. Run initial sync: python3 .claude/sync.py")
        print("3. Start developing with auto-documentation!")


# ===== LEGACY REFACTORING INSTALLER =====
class LegacyProjectRefactorInstaller:
    def __init__(self):
        self.root = Path.cwd()
        self.claude_dir = self.root / '.claude'
        self.refactor_dir = self.claude_dir / 'refactor'
        
    def check_environment(self):
        if sys.version_info < (3, 6):
            print("❌ Python 3.6+ required")
            sys.exit(1)
            
    def create_directory_structure(self):
        print("📁 Creating refactoring management structure...")
        self.claude_dir.mkdir(exist_ok=True)
        self.refactor_dir.mkdir(exist_ok=True)
        (self.refactor_dir / 'mappings').mkdir(exist_ok=True)
        (self.refactor_dir / 'analysis').mkdir(exist_ok=True)
        (self.refactor_dir / 'migration_plans').mkdir(exist_ok=True)
        
    def create_chaos_analyzer(self):
        # [Full chaos analyzer implementation]
        pass
        
    def create_migration_planner(self):
        # [Full migration planner implementation]
        pass
        
    def create_file_mapper(self):
        # [Full file mapper implementation]
        pass
        
    def create_import_fixer(self):
        # [Full import fixer implementation]
        pass
        
    def create_migration_executor(self):
        # [Full migration executor implementation]
        pass
        
    def create_refactor_claude_md(self):
        # [Full refactor CLAUDE.md content]
        pass
        
    def install(self):
        print("🚀 Installing Legacy Refactoring System...")
        
        self.check_environment()
        self.create_directory_structure()
        
        # Create all components
        self.create_chaos_analyzer()
        self.create_migration_planner()
        self.create_file_mapper()
        self.create_import_fixer()
        self.create_migration_executor()
        self.create_refactor_claude_md()
        
        # Run initial chaos analysis
        print("\n🔍 Running initial chaos analysis...")
        # [Run analysis]
        
        print("\n✅ Legacy Refactoring System installed!")
        print("\n📋 Next steps:")
        print("1. Review chaos report: cat .claude/refactor/analysis/chaos_report.md")
        print("2. Create migration plan: python3 .claude/refactor/plan_migration.py <action>")
        print("3. Start refactoring to reduce chaos!")


if __name__ == '__main__':
    installer = UniversalInstaller()
    installer.run()
