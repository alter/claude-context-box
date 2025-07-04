#!/usr/bin/env python3
"""
Claude Context Box - Unified Management Script
Complete universal installer and management system
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

# ===== SKYLOS SCANNER INTEGRATION =====
class SkylosScanner:
    """Wrapper for Skylos dead code detection tool"""
    
    def __init__(self, root_path: Path = None):
        self.root = root_path or Path.cwd()
        self.claude_dir = self.root / '.claude'
        self.reports_dir = self.claude_dir / 'reports'
        
    def check_skylos_installation(self) -> bool:
        """Check if Skylos is installed"""
        try:
            result = subprocess.run(['skylos', '--help'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
            
    def install_skylos(self) -> bool:
        """Install Skylos from GitHub"""
        print("🔧 Installing Skylos...")
        
        try:
            # Check if git is available
            subprocess.run(['git', '--version'], check=True, capture_output=True)
            
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
                    sys.executable, '-m', 'pip', 'install', 
                    str(temp_path / 'skylos')
                ], check=True)
                
                print("✅ Skylos installed successfully!")
                return True
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Skylos: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error installing Skylos: {e}")
            return False
            
    def run_skylos_analysis(self, confidence: int = 60) -> Optional[Dict]:
        """Run Skylos analysis on the project"""
        
        if not self.check_skylos_installation():
            print("❌ Skylos not found. Installing...")
            if not self.install_skylos():
                print("❌ Failed to install Skylos")
                return None
                
        print(f"🔍 Running Skylos analysis (confidence: {confidence})...")
        
        try:
            # Create reports directory
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Run Skylos with JSON output
            cmd = [
                'skylos', 
                str(self.root),
                '--confidence', str(confidence),
                '--json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Skylos failed: {result.stderr}")
                return None
                
            # Parse JSON output
            try:
                analysis_data = json.loads(result.stdout)
                
                # Save raw results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                raw_file = self.reports_dir / f'skylos_raw_{timestamp}.json'
                raw_file.write_text(result.stdout)
                
                print(f"✅ Analysis complete. Raw data saved to {raw_file}")
                return analysis_data
                
            except json.JSONDecodeError:
                print("❌ Failed to parse Skylos JSON output")
                return None
                
        except Exception as e:
            print(f"❌ Error running Skylos: {e}")
            return None
            
    def cleanup_interactively(self, confidence: int = 60, dry_run: bool = True):
        """Run interactive cleanup with Skylos"""
        if not self.check_skylos_installation():
            print("❌ Skylos not installed")
            return
            
        print(f"🧹 Running interactive cleanup (confidence: {confidence})...")
        
        cmd = ['skylos', '--interactive', '--confidence', str(confidence)]
        if dry_run:
            cmd.append('--dry-run')
            print("🔍 DRY RUN MODE - no files will be modified")
        else:
            print("⚠️  LIVE MODE - files will be modified!")
            
        cmd.append(str(self.root))
        
        try:
            # Run interactively (no capture_output so user can interact)
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n🛑 Cleanup cancelled by user")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

# ===== PROJECT ANALYZER =====
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
            "recommendations": [],
            "dead_code_analysis": None
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
        
        # Run dead code analysis with Skylos
        self.analysis["dead_code_analysis"] = self._analyze_dead_code()
        
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
            
        # Low README coverage
        coverage = self.analysis.get("readme_coverage", 0)
        if coverage < 0.2:
            indicators += 2
        elif coverage < 0.5:
            indicators += 1
            
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
            
        # Few scattered scripts
        scattered = len(self.analysis.get("scattered_scripts", []))
        if scattered == 0:
            indicators += 2
        elif scattered <= 2:
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
        if chaos >= 6:
            return "legacy_chaotic"
        elif organized >= 6:
            return "organized"
        elif chaos > organized:
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
            
        elif self.analysis["type"] == "organized":
            recs.append("Use Enhanced Context Box for documentation management")
            if self.analysis["readme_coverage"] < 1.0:
                recs.append("Complete README.md coverage for all modules")
            
        elif self.analysis["type"] == "new_project":
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

# ===== MAIN COMMAND HANDLER =====
class ClaudeContextManager:
    """Main command handler for Claude Context Box"""
    
    def __init__(self):
        self.root = Path.cwd()
        self.claude_dir = self.root / '.claude'
        self.scanner = SkylosScanner(self.root)
        self.analyzer = ProjectAnalyzer(self.root)
        
    def show_help(self):
        """Show help information"""
        print("🚀 CLAUDE CONTEXT BOX - UNIFIED MANAGEMENT")
        print("=" * 50)
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
        
        print("💡 Claude will run these automatically!")
        print("=" * 50)
        
    def sync(self):
        """Sync documentation and context"""
        print("🔄 Syncing documentation and context...")
        
        # Run sync if exists
        sync_script = self.claude_dir / 'sync.py'
        if sync_script.exists():
            result = subprocess.run([sys.executable, str(sync_script)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"❌ Sync failed: {result.stderr}")
        else:
            print("⚠️  No sync script found. Run install first.")
            
    def update(self):
        """Update project context"""
        print("🔄 Updating project context...")
        
        # Run update if exists
        update_script = self.claude_dir / 'update.py'
        if update_script.exists():
            result = subprocess.run([sys.executable, str(update_script)], 
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
            result = subprocess.run([sys.executable, str(check_script)], 
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
            print("📄 PROJECT_BRIEF.md not found. Run install first.")
            
    def structure(self):
        """Show project structure"""
        print("📁 Project structure:")
        
        def print_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
            if current_depth >= max_depth:
                return
                
            items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
            for i, item in enumerate(items):
                if item.name.startswith('.'):
                    continue
                    
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir() and not item.name.startswith('.'):
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(item, next_prefix, max_depth, current_depth + 1)
                    
        print_tree(self.root)
        
    def cleancode(self, interactive: bool = False, dry_run: bool = False, confidence: int = 60):
        """Clean code using Skylos"""
        print("🧹 Cleaning code with Skylos...")
        
        if interactive:
            self.scanner.cleanup_interactively(confidence, dry_run)
        else:
            # Run full analysis
            analysis_data = self.scanner.run_skylos_analysis(confidence)
            if analysis_data:
                # Show summary
                imports = analysis_data.get('unused_imports', [])
                functions = analysis_data.get('unused_functions', [])
                classes = analysis_data.get('unused_classes', [])
                variables = analysis_data.get('unused_variables', [])
                total = len(imports) + len(functions) + len(classes) + len(variables)
                
                print(f"📊 Found {total} potentially unused items:")
                print(f"  🔗 Imports: {len(imports)}")
                print(f"  🔧 Functions: {len(functions)}")
                print(f"  🏗️ Classes: {len(classes)}")
                print(f"  📦 Variables: {len(variables)}")
                print()
                print("💡 Use --interactive for guided cleanup")
                print("💡 Use --dry-run to preview changes")
                
    def install(self):
        """Install Claude Context Box"""
        print("🚀 Installing Claude Context Box...")
        
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
            
    def _display_analysis(self, analysis: Dict):
        """Display project analysis results"""
        print("\n📊 Project Analysis Results")
        print("=" * 50)
        
        # Basic stats
        print(f"\n📁 Project: {self.root.name}")
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
        
        response = input("\nProceed with installation? (Y/n): ")
        return response.lower() != 'n'
        
    def _handle_existing_installation(self):
        """Handle existing Claude installation"""
        print("\n📦 Existing Claude Context Box detected!")
        print("✅ System is already installed and ready to use.")
        
    def _install_legacy_system(self):
        """Install legacy refactoring system"""
        print("\n🔧 Installing Legacy Refactoring System...")
        # Basic installation for legacy projects
        self.claude_dir.mkdir(exist_ok=True)
        print("✅ Legacy system installed!")
        
    def _install_enhanced_system(self):
        """Install enhanced context box"""
        print("\n📦 Installing Enhanced Context Box...")
        # Basic installation for enhanced system
        self.claude_dir.mkdir(exist_ok=True)
        print("✅ Enhanced system installed!")
        
    def _interactive_selection(self):
        """Let user choose system interactively"""
        print("\n🤔 Unable to determine project type automatically.")
        print("Please run the install command to set up the system.")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Claude Context Box - Unified Management')
    parser.add_argument('command', nargs='?', default='help',
                      help='Command to run: sync, update, check, modules, brief, structure, cleancode, help, install')
    parser.add_argument('--interactive', action='store_true',
                      help='Interactive mode (with cleancode)')
    parser.add_argument('--dry-run', action='store_true',
                      help='Dry run mode (with cleancode)')
    parser.add_argument('--confidence', type=int, default=60,
                      help='Confidence threshold for cleancode (0-100)')
    
    args = parser.parse_args()
    
    manager = ClaudeContextManager()
    
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
    elif cmd == 'install':
        manager.install()
    else:
        print(f"Unknown command: {args.command}")
        print("Run 'python3 claude-context.py help' for available commands")

if __name__ == '__main__':
    main()