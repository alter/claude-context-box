#!/usr/bin/env python3
"""
Claude Context Box - Main installer module
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

class ClaudeContextInstaller:
    """Main installer class"""
    
    def __init__(self):
        self.base_url = os.environ.get('CLAUDE_BASE_URL', '')
        self.version = os.environ.get('CLAUDE_VERSION', '0.1.0')
        self.install_dir = Path(os.environ.get('CLAUDE_HOME', os.getcwd()))
        self.force = os.environ.get('CLAUDE_FORCE', '').lower() in ('1', 'true', 'yes')
        self.no_venv = os.environ.get('CLAUDE_NO_VENV', '').lower() in ('1', 'true', 'yes')
        
        # Paths
        self.claude_dir = self.install_dir / '.claude'
        self.backup_dir = None
        
    def run(self):
        """Main installation process"""
        print(f"\n🚀 Installing Claude Context Box v{self.version}")
        print(f"   Directory: {self.install_dir}")
        
        try:
            # Check for existing installation
            if self.check_existing_installation():
                if not self.force:
                    print("\n⚠️  Existing installation detected!")
                    print("   Use CLAUDE_FORCE=1 to override")
                    return False
                self.backup_existing()
            
            # Setup virtual environment
            if not self.no_venv:
                self.setup_venv()
            
            # Install core files
            self.install_core_files()
            
            # Create CLAUDE.md
            self.create_claude_md()
            
            # Create initial PROJECT.llm
            self.create_initial_project_llm()
            
            # Run initial update
            self.run_initial_update()
            
            print(f"\n✅ Installation complete!")
            return True
            
        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
            if self.backup_dir and self.backup_dir.exists():
                print(f"   Backup available at: {self.backup_dir}")
            return False
    
    def check_existing_installation(self):
        """Check if Claude Context Box is already installed"""
        markers = [
            self.claude_dir,
            self.install_dir / 'CLAUDE.md',
            self.install_dir / 'PROJECT.llm'
        ]
        return any(path.exists() for path in markers)
    
    def backup_existing(self):
        """Backup existing installation"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.install_dir / f'.claude_backup_{timestamp}'
        
        print(f"\n📦 Creating backup at {self.backup_dir}")
        
        # Backup .claude directory
        if self.claude_dir.exists():
            shutil.copytree(self.claude_dir, self.backup_dir / '.claude')
        
        # Backup root files
        for file in ['CLAUDE.md', 'PROJECT.llm']:
            src = self.install_dir / file
            if src.exists():
                dst = self.backup_dir / file
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    
    def find_existing_venvs(self):
        """Find all existing virtual environments in the project"""
        venvs = []
        
        # Find all activate scripts
        activate_scripts = []
        for root, dirs, files in os.walk(self.install_dir):
            if 'activate' in files:
                activate_path = Path(root) / 'activate'
                if activate_path.is_file():
                    activate_scripts.append(activate_path)
        
        for activate_script in activate_scripts:
            venv_path = activate_script.parent.parent  # bin/activate -> venv/
            python_exe = venv_path / 'bin' / 'python3'
            if not python_exe.exists():
                python_exe = venv_path / 'Scripts' / 'python.exe'
            
            if python_exe.exists():
                # Test if it's a valid Python environment
                try:
                    result = subprocess.run(
                        [str(python_exe), '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        venvs.append({
                            'path': venv_path,
                            'python': python_exe,
                            'activate': activate_script,
                            'version': result.stdout.strip()
                        })
                except:
                    continue
        
        return venvs

    def detect_project_type(self):
        """Detect project type and dependency management"""
        project_info = {
            'type': 'standard',
            'has_poetry': False,
            'has_requirements': False,
            'has_pyproject': False
        }
        
        # Check for Poetry
        if (self.install_dir / 'pyproject.toml').exists():
            project_info['has_pyproject'] = True
            try:
                with open(self.install_dir / 'pyproject.toml', 'r') as f:
                    content = f.read()
                    if '[tool.poetry]' in content:
                        project_info['type'] = 'poetry'
                        project_info['has_poetry'] = True
            except:
                pass
        
        # Check for requirements.txt
        if (self.install_dir / 'requirements.txt').exists():
            project_info['has_requirements'] = True
        
        return project_info

    def setup_venv(self):
        """Setup Python virtual environment - use existing or create new"""
        print("🔍 Scanning for existing virtual environments...")
        
        # Find existing venvs
        existing_venvs = self.find_existing_venvs()
        project_info = self.detect_project_type()
        
        if existing_venvs:
            print(f"📦 Found {len(existing_venvs)} existing virtual environment(s):")
            for i, venv in enumerate(existing_venvs):
                rel_path = venv['path'].relative_to(self.install_dir)
                print(f"  {i+1}. {rel_path} ({venv['version']})")
            
            # Prefer .venv over venv for Poetry projects
            selected_venv = existing_venvs[0]
            if project_info['has_poetry']:
                for venv in existing_venvs:
                    if venv['path'].name == '.venv':
                        selected_venv = venv
                        break
            
            # Save venv info for other scripts
            venv_info = {
                'path': str(selected_venv['path']),
                'python': str(selected_venv['python']),
                'activate': str(selected_venv['activate']),
                'type': project_info['type']
            }
            
            # Create .claude directory and save venv info
            self.claude_dir.mkdir(exist_ok=True)
            with open(self.claude_dir / 'venv_info.json', 'w') as f:
                json.dump(venv_info, f, indent=2)
            
            rel_path = selected_venv['path'].relative_to(self.install_dir)
            print(f"✅ Using existing virtual environment: {rel_path}")
            
            # Install packages in existing venv
            self.install_packages_in_venv(selected_venv, project_info)
            
        else:
            # Create new venv
            print("📦 Creating new virtual environment...")
            if project_info['has_poetry']:
                venv_path = self.install_dir / '.venv'
                print("  🎭 Poetry project detected - creating .venv/")
            else:
                venv_path = self.install_dir / 'venv'
                print("  📦 Standard project - creating venv/")
            
            result = subprocess.run(
                [sys.executable, '-m', 'venv', str(venv_path)],
                cwd=self.install_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ✅ Virtual environment created")
                
                # Find python executable in new venv
                python_exe = venv_path / 'bin' / 'python3'
                if not python_exe.exists():
                    python_exe = venv_path / 'Scripts' / 'python.exe'
                
                # Save venv info
                venv_info = {
                    'path': str(venv_path),
                    'python': str(python_exe),
                    'activate': str(venv_path / 'bin' / 'activate'),
                    'type': project_info['type']
                }
                
                self.claude_dir.mkdir(exist_ok=True)
                with open(self.claude_dir / 'venv_info.json', 'w') as f:
                    json.dump(venv_info, f, indent=2)
                
                # Install packages
                fake_venv = {
                    'path': venv_path,
                    'python': python_exe,
                    'activate': venv_path / 'bin' / 'activate'
                }
                self.install_packages_in_venv(fake_venv, project_info)
                
            else:
                print(f"  ⚠️  Failed to create venv: {result.stderr}")

    def install_packages_in_venv(self, venv, project_info):
        """Install packages in the virtual environment"""
        if project_info['has_poetry']:
            print("  🎭 Poetry project detected - using poetry install")
            # Try to install with poetry
            try:
                result = subprocess.run(
                    ['poetry', 'install'],
                    cwd=self.install_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    print("  ✅ Poetry packages installed")
                    
                    # Add pytest if not in pyproject.toml
                    result = subprocess.run(
                        ['poetry', 'add', '--group', 'dev', 'pytest'],
                        cwd=self.install_dir,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        print("  ✅ Added pytest to dev dependencies")
                    
                    return
                else:
                    print(f"  ⚠️  Poetry install failed: {result.stderr}")
            except:
                print("  ⚠️  Poetry not available or failed")
        
        # Fallback to pip
        pip_cmd = str(venv['python']).replace('python3', 'pip3').replace('python.exe', 'pip.exe')
        if not Path(pip_cmd).exists():
            pip_cmd = str(venv['path'] / 'bin' / 'pip')
            if not Path(pip_cmd).exists():
                pip_cmd = str(venv['path'] / 'Scripts' / 'pip.exe')
        
        if Path(pip_cmd).exists():
            print("  📦 Installing packages with pip...")
            subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], capture_output=True)
            subprocess.run([pip_cmd, 'install', 'pytest'], capture_output=True)
            
            # Install from requirements.txt if exists
            if project_info['has_requirements']:
                print("  📋 Installing from requirements.txt...")
                subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], 
                             capture_output=True, cwd=self.install_dir)
            
            print("  ✅ Packages installed")
        else:
            print("  ⚠️  Could not find pip executable")
    
    def download_template(self, template_name):
        """Download a template file"""
        if self.base_url:
            url = f"{self.base_url}/claude_context/templates/{template_name}"
            try:
                with urllib.request.urlopen(url) as response:
                    return response.read().decode('utf-8')
            except:
                pass
        
        # Fallback to embedded templates
        template_path = Path(__file__).parent / 'templates' / template_name
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        
        return None
    
    def install_core_files(self):
        """Install core script files"""
        print("\n📝 Installing core files...")
        
        # Create directories
        self.claude_dir.mkdir(exist_ok=True)
        (self.claude_dir / 'core').mkdir(exist_ok=True)
        (self.claude_dir / 'templates').mkdir(exist_ok=True)
        
        # Get prompt.md template
        prompt_content = self.download_template('prompt.md')
        if not prompt_content:
            # Use embedded content from old installer
            prompt_content = self.get_embedded_prompt()
        
        with open(self.claude_dir / 'prompt.md', 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        print("  ✅ Created prompt.md")
        
        # Install Python scripts
        scripts = self.get_embedded_scripts()
        for script_name, content in scripts.items():
            script_path = self.claude_dir / script_name
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            script_path.chmod(0o755)
            print(f"  ✅ Created {script_name}")
    
    def create_claude_md(self):
        """Create CLAUDE.md with all critical rules included"""
        print("\n📝 Creating CLAUDE.md...")
        
        # Get template
        template = self.download_template('claude.md')
        if not template:
            # Fallback to basic template
            template = self.get_basic_claude_template()
        
        # Replace variables
        content = template.replace('{{ version }}', self.version)
        content = content.replace('{{ timestamp }}', datetime.now().isoformat())
        
        # Check for existing user content
        claude_md_path = self.install_dir / 'CLAUDE.md'
        if claude_md_path.exists():
            try:
                existing = claude_md_path.read_text(encoding='utf-8')
                if '# Previous User Documentation' in existing:
                    user_content = existing.split('# Previous User Documentation')[1].strip()
                    content += f"\n\n---\n\n# Previous User Documentation\n\n{user_content}"
            except:
                pass
        
        # Write file
        with open(claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  ✅ Created CLAUDE.md")
    
    def create_initial_project_llm(self):
        """Create initial PROJECT.llm if it doesn't exist"""
        project_llm_path = self.install_dir / 'PROJECT.llm'
        if project_llm_path.exists():
            return
        
        print("\n📝 Creating initial PROJECT.llm...")
        
        content = f"""@project: {self.install_dir.name}
@version: 0.1.0
@updated: {datetime.now().isoformat()}

@architecture:
# Modules will be added automatically by update.py

@dependency_graph:
# Dependencies will be mapped by update.py

@test_coverage:
# Test coverage will be tracked here

@recent_changes:
- {datetime.now().isoformat()}: Initial Claude Context Box installation
"""
        
        with open(project_llm_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  ✅ Created PROJECT.llm")
    
    def run_initial_update(self):
        """Run initial context update"""
        print("\n🔄 Running initial update...")
        
        # Get Python executable from saved venv info
        python_exe = sys.executable  # fallback
        
        venv_info_file = self.claude_dir / 'venv_info.json'
        if venv_info_file.exists():
            try:
                with open(venv_info_file, 'r') as f:
                    venv_info = json.load(f)
                    python_exe = venv_info['python']
                    print(f"  🐍 Using Python from: {venv_info['path']}")
            except:
                print("  ⚠️  Could not read venv info, using system Python")
        
        # Run update.py
        update_script = self.claude_dir / 'update.py'
        if update_script.exists():
            result = subprocess.run(
                [python_exe, str(update_script)],
                cwd=self.install_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ✅ Context updated successfully")
            else:
                print(f"  ⚠️  Update completed with warnings")
                if result.stderr:
                    print(f"     {result.stderr}")
    
    def get_basic_claude_template(self):
        """Get basic CLAUDE.md template if download fails"""
        return """# Claude Context Box Project

## 🚨 КРИТИЧЕСКИЕ ПРАВИЛА (HIGHEST PRIORITY)

1. Priorities: Stability First → Clean Code → DRY → KISS → SOLID
2. NEVER modify without reading
3. ALWAYS test before and after
4. MUST follow 9-step procedure

## ⚡ КОМАНДЫ

- `u` or `update` → Universal update
- `c` or `check` → Health check
- `s` or `structure` → Show structure

## 📋 9-STEP PROCEDURE

1. Read PROJECT.llm
2. Find target module
3. Read module CONTEXT.llm
4. Analyze current code
5. Create baseline tests
6. Run baseline tests
7. Make minimal changes
8. Test again (STOP if fails)
9. Update contexts

@.claude/prompt.md
@.claude/format.md

---
Claude Context Box v{{ version }} - {{ timestamp }}"""
    
    def get_embedded_prompt(self):
        """Get embedded prompt content"""
        # Try local file first
        local_path = Path(__file__).parent / 'templates' / 'prompt.md'
        if local_path.exists():
            return local_path.read_text(encoding='utf-8')
        
        # Fallback to basic version
        return """# CLAUDE CONTEXT BOX SYSTEM PROMPT

## ROLE AND GOAL

You are a senior developer who:
1. Priorities: Stability First → Clean Code → DRY → KISS → SOLID
2. Creates resilient, maintainable systems
3. Respects existing codebase structure
4. Minimizes breaking changes

## CRITICAL SAFETY RULES

**Understand Before Modifying**
- NEVER modify code you haven't read and understood
- ALWAYS backup before any changes (create *.backup files)
- ALWAYS test after modifications

**Surgical Fixes Only**
- Make MINIMUM changes to fix the issue
- Preserve existing functionality
- Only refactor with explicit permission
- Test edge cases after any change

## MANDATORY 9-STEP PROCEDURE

For ANY code modification, follow these steps EXACTLY..."""
    
    def get_embedded_scripts(self):
        """Get embedded Python scripts"""
        scripts = {}
        
        # Try to load from local files first
        script_names = ['update.py', 'check.py', 'help.py', 'context.py', 
                       'baseline.py', 'validation.py', 'cleancode.py']
        
        for script_name in script_names:
            # Try local file
            local_path = Path(__file__).parent / 'scripts' / script_name
            if local_path.exists():
                scripts[script_name] = local_path.read_text(encoding='utf-8')
                continue
            
            # Try downloading
            if self.base_url:
                url = f"{self.base_url}/claude_context/scripts/{script_name}"
                try:
                    with urllib.request.urlopen(url) as response:
                        scripts[script_name] = response.read().decode('utf-8')
                        continue
                except:
                    pass
            
            # Fallback stub
            scripts[script_name] = f'#!/usr/bin/env python3\n# {script_name} stub\nprint("{script_name} not found")'
        
        return scripts

def main():
    """Entry point"""
    installer = ClaudeContextInstaller()
    success = installer.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()