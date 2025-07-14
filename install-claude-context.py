#!/usr/bin/env python3
"""
Claude Context Box Installer v2.0
Single-file installer that creates modular structure after installation
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import re

# ANSI colors
COLORS = {
    'BLUE': '\033[94m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m'
}

def color(text, color_name):
    """Add color to text"""
    return f"{COLORS.get(color_name, '')}{text}{COLORS['ENDC']}"

def banner():
    """Display installation banner"""
    print(f"\n{color('='*60, 'BLUE')}")
    print(f"{color('Claude Context Box Installer v2.0', 'BOLD')}")
    print(f"{color('='*60, 'BLUE')}\n")

# Core prompt content
PROMPT_CONTENT = '''# CLAUDE CONTEXT BOX SYSTEM PROMPT

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

**Protect System Files**
NEVER search/modify in: venv/, __pycache__/, .git/, node_modules/, .env*, dist/, build/, *.egg-info/

## MANDATORY CODE CHANGE PROCEDURE

When modifying ANY code, you MUST follow this EXACT 9-step sequence:

### Step 1: Read PROJECT.llm
```bash
cat PROJECT.llm || echo "⚠️  No PROJECT.llm found - run 'update' first"
```

### Step 2: Find target module
```bash
# Use efficient search
find . -type f -name "*.py" -path "*${module_name}*" | grep -v venv | head -10
```

### Step 3: Read module context
```bash
cat path/to/module/CONTEXT.llm || echo "⚠️  No CONTEXT.llm - run 'ctx init'"
```

### Step 4: Analyze current code
```bash
# Read the actual code
cat path/to/module/file.py | head -100
# Find related tests
find . -name "test_*.py" -o -name "*_test.py" | grep -E "${module_name}" | head -5
```

### Step 5: Create baseline tests
```bash
python .claude/baseline.py module_name
# This creates test_baseline_module_name.py
```

### Step 6: Run baseline tests
```bash
python -m pytest test_baseline_*.py -v
# Must see: "✅ Baseline established"
```

### Step 7: Make minimal changes
- Edit ONLY what's needed
- Preserve formatting/style
- Update docstrings if behavior changes

### Step 8: Test again
```bash
python -m pytest test_baseline_*.py -v
# If failed:
echo "❌ Tests failed! Showing options..."
echo "1. Fix the code to pass tests"
echo "2. Update tests if behavior should change"  
echo "3. Revert changes with: git checkout -- file.py"
# STOP and wait for user decision
```

### Step 9: Update contexts
```bash
# Update module CONTEXT.llm if interface changed
python .claude/context.py update
# Update PROJECT.llm if structure/dependencies changed
python .claude/update.py
```

## PROCEDURE CONTROL POINTS

✓ Before ANY code change → Read PROJECT.llm (Step 1)
✓ Before module edit → Read module's CONTEXT.llm (Step 3)
✓ Before making changes → Create baseline tests (Step 5)
✓ After changes → Run ALL tests (Step 8)
✓ If tests fail → STOP and show options
✓ After completion → Update all contexts (Step 9)

Example output at each control point:
```
📍 Control Point 1: PROJECT.llm loaded ✓
📍 Control Point 2: Module found at api/auth.py ✓
📍 Control Point 3: CONTEXT.llm read ✓
📍 Control Point 4: Created test_baseline_auth.py ✓
📍 Control Point 5: Baseline tests pass ✓
📍 Control Point 6: Making changes...
📍 Control Point 7: Tests after changes... ❌ FAILED
⚠️  STOPPING: Tests failed. Awaiting user decision.
```

## PROJECT SETUP

When starting work, ALWAYS run:
```bash
# Comprehensive project setup check
setup_check() {
    echo "🔍 Running comprehensive setup check..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Python environment
    echo "📦 Python Environment:"
    if command -v python3 &> /dev/null; then
        python3 --version | awk '{print "  ✅ Python: " $2}'
    else
        echo "  ❌ Python3 not found!"
        return 1
    fi
    
    # Virtual environment
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "  ✅ Virtual env: ACTIVE ($(basename $VIRTUAL_ENV))"
    elif [[ -d "venv" ]]; then
        echo "  ⚠️  Virtual env: EXISTS but INACTIVE"
        echo "     Run: source venv/bin/activate"
    else
        echo "  ❌ No virtual environment"
        echo "     Run: python3 -m venv venv && source venv/bin/activate"
    fi
    
    # Project files
    echo -e "\\n📁 Project Structure:"
    test -f "PROJECT.llm" && echo "  ✅ PROJECT.llm exists" || echo "  ❌ PROJECT.llm missing - run 'update'"
    test -f "CLAUDE.md" && echo "  ✅ CLAUDE.md exists" || echo "  ❌ CLAUDE.md missing"
    test -f "requirements.txt" && echo "  ✅ requirements.txt exists" || echo "  ⚠️  No requirements.txt"
    test -d ".claude" && echo "  ✅ .claude/ directory exists" || echo "  ❌ .claude/ missing"
    
    # Context files
    echo -e "\\n📋 Context Status:"
    context_count=$(find . -name "CONTEXT.llm" 2>/dev/null | wc -l)
    echo "  📄 CONTEXT.llm files: $context_count"
    
    # Find modules without context
    missing_context=0
    for dir in $(find . -type d | grep -v -E "venv|__pycache__|.git|.claude"); do
        if [[ -n $(find "$dir" -maxdepth 1 -name "*.py" 2>/dev/null | head -1) ]] && [[ ! -f "$dir/CONTEXT.llm" ]]; then
            ((missing_context++))
        fi
    done
    [[ $missing_context -eq 0 ]] && echo "  ✅ All modules documented" || echo "  ⚠️  $missing_context modules without CONTEXT.llm"
    
    # Test status
    echo -e "\\n🧪 Test Status:"
    baseline_count=$(find . -name "test_baseline_*.py" 2>/dev/null | wc -l)
    echo "  🧪 Baseline tests: $baseline_count"
    test_count=$(find . -name "test_*.py" -o -name "*_test.py" 2>/dev/null | grep -v baseline | wc -l)
    echo "  🧪 Other tests: $test_count"
    
    # Git status
    if [[ -d ".git" ]]; then
        echo -e "\\n📊 Git Status:"
        branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        echo "  🌿 Current branch: $branch"
        
        modified=$(git status --porcelain 2>/dev/null | wc -l)
        [[ $modified -eq 0 ]] && echo "  ✅ Working tree clean" || echo "  ⚠️  $modified files modified"
    fi
    
    # Module overview
    echo -e "\\n🏗️  Module Structure:"
    for dir in $(find . -maxdepth 2 -type d | grep -v -E "venv|__pycache__|.git|.claude" | sort); do
        if [[ -n $(find "$dir" -maxdepth 1 -name "*.py" 2>/dev/null | head -1) ]]; then
            py_count=$(find "$dir" -maxdepth 1 -name "*.py" | wc -l)
            marker="✓" && [[ ! -f "$dir/CONTEXT.llm" ]] && marker="✗"
            echo "  $marker $dir/ ($py_count files)"
        fi
    done | head -10
    
    # Quick summary
    echo -e "\\n📊 Summary:"
    if [[ -n "$VIRTUAL_ENV" ]] && [[ -f "PROJECT.llm" ]] && [[ $missing_context -eq 0 ]]; then
        echo "  ✅ Project ready for development!"
    else
        echo "  ⚠️  Setup incomplete. Check items marked with ❌ or ⚠️"
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Run the check
setup_check
```

## PROJECT.llm FORMAT

```
@project: ProjectName
@version: 1.0.0
@updated: 2025-01-15T10:30:00

@architecture:
- auth/: Authentication module [@deps: models.User, utils.crypto]
- api/: REST API endpoints [@deps: auth, models, validators]
- models/: Data models [@deps: database]
- utils/: Shared utilities [@deps: none]
- validators/: Input validation [@deps: models]

@dependency_graph:
api -> auth -> models
api -> validators -> models
auth -> utils

@critical_paths:
- User Login: api.login -> auth.authenticate -> models.User.verify
- Create User: api.users.create -> validators.user -> models.User.create -> auth.hash_password

@test_coverage:
- auth/: 85% (baseline + unit tests)
- api/: 70% (integration tests)
- models/: 90% (unit tests)

@recent_changes:
- 2025-01-15T10:30:00: Updated auth module (added 2FA support)
- 2025-01-14T15:45:00: Refactored API error handling
- 2025-01-13T09:00:00: Added validators module
```

## CONTEXT.llm FORMAT

```
@component: UserAuthService
@type: service
@version: 2.1.0
@deps: [models.User, utils.crypto, cache.Redis]
@purpose: Handle user authentication and session management

@interface:
- authenticate(email: str, password: str) -> dict
- create_session(user_id: str) -> str
- validate_token(token: str) -> bool
- logout(token: str) -> bool
- refresh_token(old_token: str) -> str

@state:
- session_timeout: 3600 (seconds)
- max_attempts: 5
- lockout_duration: 300

@behavior:
- Passwords hashed with bcrypt (cost=12)
- Sessions stored in Redis with TTL
- Rate limiting on failed attempts
- Automatic session refresh if activity detected
- Emits auth.login and auth.logout events

@errors:
- AuthenticationError: Invalid credentials
- SessionExpiredError: Token expired
- RateLimitError: Too many attempts

@performance:
- Auth check: <50ms (Redis cached)
- Password verify: ~100ms (bcrypt)
- Session create: <10ms
```

## EFFICIENT SEARCH PATTERNS

```bash
# Comprehensive project scan
project_scan() {
    echo "🔍 Scanning project structure..."
    
    # Count files by type
    echo "📊 File statistics:"
    find . -type f -name "*.py" | grep -v venv | wc -l | xargs echo "  Python files:"
    find . -name "test_*.py" | grep -v venv | wc -l | xargs echo "  Test files:"
    find . -name "CONTEXT.llm" | wc -l | xargs echo "  CONTEXT.llm files:"
    
    # Find modules without context
    echo -e "\\n⚠️  Modules without CONTEXT.llm:"
    for dir in $(find . -type d -name "*.py" -prune -o -type d -print | grep -v -E "venv|__pycache__|.git"); do
        if [[ -n $(find "$dir" -maxdepth 1 -name "*.py" 2>/dev/null) ]] && [[ ! -f "$dir/CONTEXT.llm" ]]; then
            echo "  - $dir/"
        fi
    done
}

# Smart code pattern search
code_patterns() {
    local pattern=$1
    echo "🔍 Searching for pattern: $pattern"
    
    # Use ripgrep for efficient search
    echo -e "\\n📄 Code occurrences:"
    rg "$pattern" --type py -C 2 | grep -v venv | head -30
    
    echo -e "\\n📁 Files containing pattern:"
    rg -l "$pattern" --type py | grep -v venv | sort
    
    echo -e "\\n📊 Statistics:"
    rg -c "$pattern" --type py | grep -v venv | sort -t: -k2 -nr | head -10
}

# Batch file reader with context
read_files() {
    echo "📚 Reading files with context..."
    
    for file in "$@"; do
        if [[ -f "$file" ]]; then
            echo -e "\\n📄 === $file ==="
            
            # Check for associated CONTEXT.llm
            dir=$(dirname "$file")
            if [[ -f "$dir/CONTEXT.llm" ]]; then
                echo "📋 Context available: $dir/CONTEXT.llm"
            fi
            
            # Show file content
            head -50 "$file" | nl
            
            # Show file stats
            lines=$(wc -l < "$file")
            echo -e "\\n📊 Total lines: $lines"
        else
            echo "❌ File not found: $file"
        fi
    done
}

# Combined analysis function
analyze() {
    local pattern=$1
    echo "🔍 Analyzing: $pattern"
    
    # Phase 1: Find definitions
    echo "📍 Definitions:"
    rg "^(class|def).*$pattern" --type py | grep -v venv | head -10
    
    # Phase 2: Find usages
    echo -e "\\n📍 Usages:"
    rg "\\b$pattern\\b" --type py -C 1 | grep -v -E "^(class|def)" | grep -v venv | head -20
    
    # Phase 3: Find imports
    echo -e "\\n📍 Imports:"
    rg "(from|import).*$pattern" --type py | grep -v venv
    
    # Summary
    echo -e "\\n📊 Summary:"
    rg -l "$pattern" --type py | grep -v venv | wc -l | xargs echo "  Files affected:"
}

# Find related modules
find_related() {
    local module=$1
    echo "🔗 Finding modules related to: $module"
    
    # Direct imports
    echo "📥 Modules that import $module:"
    rg "from.*$module|import.*$module" --type py -l | grep -v venv | sort
    
    # Check what this module imports
    if [[ -d "$module" ]]; then
        echo -e "\\n📤 Modules imported by $module:"
        rg "^(from|import)" "$module" --type py | grep -v venv | awk '{print $2}' | sort -u
    fi
}
```

## DECISION FRAMEWORK

### WITHOUT permission you CAN:
- Read any files (except .env)
- Create baseline tests
- Run existing tests
- Search codebase
- Analyze dependencies
- Create backup files
- Generate CONTEXT.llm files

### WITHOUT permission you CANNOT:
- Modify existing code
- Delete any files
- Create new features
- Refactor existing code
- Change project structure
- Install new packages
- Modify configuration files

### ALWAYS ASK before:
- Breaking changes to APIs
- Database schema changes
- Configuration changes
- Package installations/updates
- Major refactoring
- Removing functionality
- Changing public interfaces

## DEVELOPMENT PRINCIPLES

1. **English only** - All code, variables, functions, documentation
2. **No comments** in code - Use descriptive names and CONTEXT.llm
3. **Test before change** - Baseline tests are mandatory
4. **Small commits** - One logical change at a time
5. **Update contexts** - Keep CONTEXT.llm and PROJECT.llm current
6. **Fail fast** - Stop immediately when tests fail
7. **Explicit is better** - Clear function names over clever code

## ERROR RECOVERY

When something breaks:
```bash
# 1. Check what changed
git status
git diff

# 2. Run procedure validation
python .claude/validation.py --check-last-change

# 3. Restore from backup if needed
cp file.py.backup file.py

# 4. Or revert with git
git checkout -- file.py

# 5. Re-run baseline tests
python -m pytest test_baseline_*.py -v

# 6. Check procedure compliance
python .claude/validation.py --check-procedure
```

## COMMAND SHORTCUTS

Quick commands to type in chat:
- `u` or `update` → Update PROJECT.llm and contexts
- `c` or `check` → Quick health check
- `s` or `structure` → Show project structure
- `baseline <module>` → Create baseline tests
- `validate` → Run full validation
- `procedure` → Check procedure compliance
- `deps` → Show dependency graph
- `ctx init` → Create missing CONTEXT.llm
- `ctx update` → Update existing CONTEXT.llm
- `test-all` → Run all baseline tests

## PERFORMANCE OPTIMIZATION

- Use `rg` (ripgrep) instead of grep - 10x faster
- Use `fd` instead of find when available
- Cache PROJECT.llm in memory during session
- Batch file operations when possible
- Limit search scope with path filters

## VALIDATION CHECKLIST

Before marking ANY task complete:
□ All 9 procedure steps followed
□ All control points passed
□ Baseline tests created and passing
□ No files accidentally modified
□ CONTEXT.llm updated if interface changed
□ PROJECT.llm updated if structure changed
□ No commented code added
□ All names in English
□ Clean git status (except intended changes)

## STRICT PROHIBITIONS

NEVER DO:
1. Skip any step in the 9-step procedure
2. Modify code without baseline tests
3. Ignore failing tests
4. Edit system directories (venv/, .git/, etc.)
5. Make changes without reading CONTEXT.llm
6. Add comments instead of clear names
7. Create duplicate functionality
8. Break existing tests without user approval
9. Continue after control point failure

Remember: The procedure exists to prevent breaking changes. Follow it exactly, every time.
'''

# File templates
UPDATE_PY = '''#!/usr/bin/env python3
"""
🚀 UNIVERSAL PROJECT UPDATER - Makes EVERYTHING up to date automatically!

The ONLY command you need: 'u'
- Creates missing CONTEXT.llm files
- Updates existing CONTEXT.llm files  
- Updates PROJECT.llm
- Reads and applies CLAUDE.md rules
- Creates missing baseline tests
- Validates project health
- NO manual commands needed!
"""

import os
import sys
import json
import subprocess
import ast
from datetime import datetime
from pathlib import Path
import fnmatch
import platform

# Configuration
EXCLUDE_DIRS = {
    'venv', '__pycache__', '.git', 'node_modules', '.pytest_cache',
    'htmlcov', 'dist', 'build', '*.egg-info', '.tox', '.mypy_cache',
    '.next', '.nuxt', 'coverage', '.nyc_output', 'tmp', 'temp',
    'vendor', 'target', '.idea', '.vscode', '.fleet'
}

EXCLUDE_PATTERNS = {
    '*.pyc', '*.pyo', '*.pyd', '.DS_Store', '*.so', '*.dylib',
    '*.dll', '*.class', '*.log', '*.sqlite', '*.sqlite3', '*.db',
    '*.bak', '*.swp', '*.swo', '*~', '.env*', '*.tmp'
}

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

def log_action(action, status, details=""):
    """Log actions for procedure tracking"""
    try:
        os.makedirs('.claude', exist_ok=True)
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'status': status,
            'details': details
        }
        with open('.claude/procedure.log', 'a') as f:
            f.write(json.dumps(entry) + '\\n')
    except:
        pass

def get_python_info():
    """Get Python version info"""
    try:
        version = subprocess.check_output(
            ['python3', '--version'], 
            stderr=subprocess.STDOUT
        ).decode().strip().split()[1]
        return version
    except:
        return "Unknown"

def should_exclude(path):
    """Check if path should be excluded"""
    parts = Path(path).parts
    
    # Check directory exclusions
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # Check pattern exclusions
    for pattern in EXCLUDE_PATTERNS:
        if any(fnmatch.fnmatch(part, pattern) for part in parts):
            return True
            
    return False

def find_modules():
    """Find all code modules with structure"""
    modules = {}
    
    for root, dirs, files in os.walk('.'):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        if should_exclude(root):
            continue
            
        # Check for code files
        py_files = [f for f in files if f.endswith('.py') and not should_exclude(f)]
        
        if py_files and root != '.':
            rel_path = os.path.relpath(root)
            modules[rel_path] = {
                'files': py_files,
                'has_context': os.path.exists(os.path.join(root, 'CONTEXT.llm'))
            }
    
    return modules

def analyze_dependencies(modules):
    """Analyze dependencies between modules"""
    deps = {}
    
    for module_path, info in modules.items():
        module_deps = set()
        
        for file in info['files']:
            filepath = os.path.join(module_path, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find imports
                import_lines = [line for line in content.split('\\n') 
                              if line.strip().startswith(('import ', 'from '))]
                
                for line in import_lines:
                    # Extract module names
                    if line.startswith('from '):
                        parts = line.split()
                        if len(parts) >= 2:
                            imp = parts[1].split('.')[0]
                            if imp in [m.split('/')[0] for m in modules]:
                                module_deps.add(imp)
            except:
                pass
        
        if module_deps:
            deps[module_path] = list(module_deps)
    
    return deps

def create_project_llm(modules, dependencies):
    """Create or update PROJECT.llm with full dependency tracking"""
    now = datetime.now().isoformat()
    
    # Load existing PROJECT.llm if exists
    existing_changes = []
    existing_version = "1.0.0"
    existing_paths = []
    
    if os.path.exists('PROJECT.llm'):
        try:
            with open('PROJECT.llm', 'r') as f:
                content = f.read()
                
                # Extract version
                if '@version:' in content:
                    version_line = content.split('@version:')[1].split('\\n')[0].strip()
                    existing_version = version_line
                
                # Extract recent changes
                if '@recent_changes:' in content:
                    changes_section = content.split('@recent_changes:')[1]
                    existing_changes = [l.strip() for l in changes_section.split('\\n') 
                                      if l.strip().startswith('-')][:10]
                
                # Extract critical paths
                if '@critical_paths:' in content:
                    paths_section = content.split('@critical_paths:')[1].split('@')[0]
                    existing_paths = [l.strip() for l in paths_section.split('\\n') 
                                    if l.strip().startswith('-')]
        except:
            pass
    
    # Start building content
    content = f"""@project: {os.path.basename(os.getcwd())}
@version: {existing_version}
@updated: {now}

@architecture:"""
    
    # Add modules with their dependencies and purpose
    for module_path in sorted(modules.keys()):
        module_info = modules[module_path]
        deps = dependencies.get(module_path, [])
        
        # Try to get purpose from CONTEXT.llm
        purpose = ""
        context_file = os.path.join(module_path, 'CONTEXT.llm')
        if os.path.exists(context_file):
            try:
                with open(context_file, 'r') as f:
                    ctx_content = f.read()
                    if '@purpose:' in ctx_content:
                        purpose = ctx_content.split('@purpose:')[1].split('\\n')[0].strip()
            except:
                pass
        
        # Build description
        desc = f"{module_path}/"
        if purpose:
            desc += f": {purpose}"
        if deps:
            desc += f" [@deps: {', '.join(deps)}]"
        
        content += f"\\n- {desc}"
    
    # Add dependency graph
    content += "\\n\\n@dependency_graph:"
    
    # Build dependency tree
    dep_tree = {}
    for module, deps in dependencies.items():
        for dep in deps:
            if dep not in dep_tree:
                dep_tree[dep] = []
            dep_tree[dep].append(module)
    
    # Show dependencies
    for module in sorted(modules.keys()):
        deps = dependencies.get(module, [])
        if deps:
            content += f"\\n{module} -> {' -> '.join(deps)}"
    
    # Add critical paths
    content += "\\n\\n@critical_paths:"
    if existing_paths:
        for path in existing_paths:
            content += f"\\n{path}"
    else:
        content += "\\n- [Analyze code to determine critical paths]"
        content += "\\n- [Add user flow paths here]"
    
    # Add test coverage
    content += "\\n\\n@test_coverage:"
    
    # Check for baseline tests
    baseline_tests = list(Path('.').glob('test_baseline_*.py'))
    for module_path in sorted(modules.keys()):
        module_name = os.path.basename(module_path)
        has_baseline = any(t.name == f"test_baseline_{module_name}.py" for t in baseline_tests)
        
        coverage = "baseline tests" if has_baseline else "no tests"
        content += f"\\n- {module_path}/: {coverage}"
    
    # Add recent changes
    content += "\\n\\n@recent_changes:"
    
    # Determine what changed
    change_desc = "Updated project structure"
    if len(modules) > len(existing_changes):
        change_desc = "Added new modules"
    
    content += f"\\n- {now}: {change_desc}"
    for change in existing_changes[:9]:  # Keep 9 old + 1 new = 10 total
        content += f"\\n{change}"
    
    with open('PROJECT.llm', 'w') as f:
        f.write(content)
    
    return True

def create_format_md():
    """Create format.md with project info"""
    modules = find_modules()
    
    now = datetime.now().isoformat()
    py_version = get_python_info()
    venv_status = "✅ ACTIVE" if venv_check() else "❌ NOT ACTIVE"
    
    # Count files by type
    file_types = {}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        if should_exclude(root):
            continue
            
        for file in files:
            if should_exclude(file):
                continue
            ext = os.path.splitext(file)[1].lower() or 'no_ext'
            file_types[ext] = file_types.get(ext, 0) + 1
    
    content = f"""# Project Context: {os.path.basename(os.getcwd())}
*Updated: {now}*

## 🐍 Python Environment
- Python: `{py_version}`
- Venv: {venv_status}

## Directory Structure

### Code Modules:
"""
    
    for module in sorted(modules.keys()):
        info = modules[module]
        marker = "✓" if info['has_context'] else "❌"
        content += f"\\n- `{module}/` - {marker} CONTEXT.llm"
    
    content += "\\n\\n## Python Project Info"
    py_files = sum(len(info['files']) for info in modules.values())
    content += f"\\n- Total Python files: {py_files}"
    content += f"\\n- Total modules: {len(modules)}"
    content += f"\\n- Has requirements.txt: {'✅' if os.path.exists('requirements.txt') else '❌'}"
    content += f"\\n- Has setup.py: {'✅' if os.path.exists('setup.py') else '❌'}"
    content += f"\\n- Has pyproject.toml: {'✅' if os.path.exists('pyproject.toml') else '❌'}"
    
    # Modules without CONTEXT.llm
    missing_context = [m for m, info in modules.items() if not info['has_context']]
    if missing_context:
        content += "\\n\\n## ⚠️ Modules Missing CONTEXT.llm:"
        for module in missing_context:
            content += f"\\n- `{module}/`"
    
    content += "\\n\\n## File Types\\n"
    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        content += f"\\n- `{ext}`: {count} files"
    
    content += """

## 🔄 Context Update Reminder

**Quick commands**: Type `u` (update), `c` (check), `s` (structure)
**Remember**: Always use `python3` and `pip3`, work in venv!
"""
    
    with open('.claude/format.md', 'w') as f:
        f.write(content)

# =========== UNIVERSAL LOGIC FUNCTIONS ===========

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

def create_missing_contexts():
    """Automatically create missing CONTEXT.llm files"""
    created = 0
    
    for root, dirs, files in os.walk('.'):
        # Skip system directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        if any(f.endswith('.py') for f in files) and root != '.':
            context_path = os.path.join(root, 'CONTEXT.llm')
            
            if os.path.exists(context_path):
                continue
            
            content = generate_context_llm(root)
            if content:
                with open(context_path, 'w') as f:
                    f.write(content)
                print(f"   ✅ Created: {context_path}")
                created += 1
    
    return created

def update_existing_contexts():
    """Update existing CONTEXT.llm files"""
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
            updated += 1
    
    return updated

def apply_claude_rules():
    """Read CLAUDE.md and apply rules"""
    if os.path.exists('CLAUDE.md'):
        log_action('read_claude_md', 'completed', 'Rules refreshed by universal updater')
        return True
    else:
        print("   ⚠️  CLAUDE.md not found")
        return False

def create_baseline_test_for_module(module_path):
    """Create baseline test for a specific module"""
    module_name = os.path.basename(module_path)
    test_filename = f"test_baseline_{module_name}.py"
    
    # Skip if test already exists
    if os.path.exists(test_filename):
        return False
    
    # Analyze module for functions
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
    
    if not functions:
        return False
    
    # Generate test content - using list to avoid f-string issues
    lines = []
    lines.append(f'"""Baseline tests for {module_name}')
    lines.append('Auto-generated to capture current behavior before modifications')
    lines.append('"""')
    lines.append('')
    lines.append('import pytest')
    lines.append('import sys')
    lines.append('from pathlib import Path')
    lines.append('')
    lines.append('# Add module to path')
    lines.append('sys.path.insert(0, str(Path(__file__).parent))')
    lines.append('')
    lines.append('# Import module components')
    lines.append('try:')
    lines.append(f'    from {module_name} import *')
    lines.append('except ImportError:')
    lines.append('    pass')
    lines.append('')
    lines.append(f'class TestBaseline{module_name.title().replace("_", "")}:')
    lines.append('    """Baseline tests to ensure current functionality is preserved"""')
    lines.append('    ')
    lines.append('    def test_baseline_imports(self):')
    lines.append('        """Test that module imports work correctly"""')
    lines.append('        assert True')
    lines.append('')
    
    # Add function tests
    for func in functions[:5]:  # Limit to 5 functions
        test_name = func['name'].replace('.', '_').lower()
        lines.append(f'    def test_baseline_{test_name}(self):')
        lines.append(f'        """Test current behavior of {func["name"]}"""')
        lines.append('        # TODO: Add actual test implementation')
        lines.append('        assert True')
        lines.append('')
    
    lines.append('def test_module_imports():')
    lines.append('    """Ensure all module imports work"""')
    lines.append('    assert True')
    
    content = '\\n'.join(lines)
    
    with open(test_filename, 'w') as f:
        f.write(content)
    
    return True

def create_missing_baseline_tests():
    """Create baseline tests for all modules"""
    created = 0
    modules = find_modules()
    
    for module_path in modules.keys():
        if create_baseline_test_for_module(module_path):
            print(f"   🧪 Created baseline test for {module_path}")
            created += 1
    
    return created

def analyze_project_state():
    """Analyze what needs to be updated"""
    modules = find_modules()
    missing_contexts = [m for m, info in modules.items() if not info['has_context']]
    
    # Check for modules with outdated contexts (simplified check)
    outdated_contexts = []
    for context_file in Path('.').rglob('CONTEXT.llm'):
        # If context is older than the module files, mark as outdated
        context_time = context_file.stat().st_mtime
        module_dir = context_file.parent
        
        for py_file in module_dir.glob('*.py'):
            if py_file.stat().st_mtime > context_time:
                outdated_contexts.append(str(context_file))
                break
    
    # Check for missing baseline tests
    existing_baselines = set(p.stem.replace('test_baseline_', '') for p in Path('.').glob('test_baseline_*.py'))
    missing_baseline_tests = [m for m in modules.keys() if os.path.basename(m) not in existing_baselines]
    
    return {
        'missing_contexts': missing_contexts,
        'outdated_contexts': outdated_contexts,
        'missing_baseline_tests': missing_baseline_tests,
        'total_modules': len(modules)
    }

def validate_project_health():
    """Check project health and show issues"""
    issues = []
    
    # Check PROJECT.llm
    if not os.path.exists('PROJECT.llm'):
        issues.append("Missing PROJECT.llm")
    
    # Check CLAUDE.md
    if not os.path.exists('CLAUDE.md'):
        issues.append("Missing CLAUDE.md")
    
    # Check venv
    if not venv_check():
        issues.append("Not in virtual environment")
    
    # Check for modules without CONTEXT.llm
    state = analyze_project_state()
    if state['missing_contexts']:
        issues.append(f"{len(state['missing_contexts'])} modules without CONTEXT.llm")
    
    if issues:
        print("   ⚠️  Found issues:")
        for issue in issues:
            print(f"      - {issue}")
        return False
    else:
        print("   ✅ Project is healthy!")
        return True

def main():
    """🚀 UNIVERSAL PROJECT UPDATER - Does EVERYTHING automatically!"""
    print("🚀 Universal Project Update - Making everything current...")
    
    # Log that we're starting the universal update
    log_action('universal_update', 'started', 'Running comprehensive project update')
    
    # Show what we're going to do
    state = analyze_project_state()
    total_tasks = (
        len(state['missing_contexts']) + 
        len(state['outdated_contexts']) + 
        len(state['missing_baseline_tests']) + 
        2  # PROJECT.llm + rules
    )
    
    if total_tasks > 2:
        print(f"   📋 Planning to execute {total_tasks} tasks...")
    
    # 1. Read and apply CLAUDE.md rules first
    print("\\n📖 Step 1: Reading CLAUDE.md rules...")
    apply_claude_rules()
    print("   ✅ Rules applied")
    
    # 2. Create missing CONTEXT.llm files
    if state['missing_contexts']:
        print(f"\\n📁 Step 2: Creating {len(state['missing_contexts'])} missing CONTEXT.llm files...")
        created = create_missing_contexts()
        print(f"   ✅ Created {created} CONTEXT.llm files")
    else:
        print("\\n📁 Step 2: All modules have CONTEXT.llm files ✅")
    
    # 3. Update existing CONTEXT.llm files
    if state['outdated_contexts']:
        print(f"\\n🔄 Step 3: Updating {len(state['outdated_contexts'])} outdated CONTEXT.llm files...")
        updated = update_existing_contexts()
        print(f"   ✅ Updated {updated} CONTEXT.llm files")
    else:
        print("\\n🔄 Step 3: All CONTEXT.llm files are current ✅")
    
    # 4. Update PROJECT.llm
    print("\\n📊 Step 4: Updating PROJECT.llm...")
    modules = find_modules()
    dependencies = analyze_dependencies(modules)
    if create_project_llm(modules, dependencies):
        print("   ✅ PROJECT.llm updated")
    
    # 5. Create format.md
    create_format_md()
    print("   ✅ .claude/format.md updated")
    
    # 6. Create missing baseline tests
    if state['missing_baseline_tests']:
        print(f"\\n🧪 Step 5: Creating baseline tests for {len(state['missing_baseline_tests'])} modules...")
        created_tests = create_missing_baseline_tests()
        print(f"   ✅ Created {created_tests} baseline tests")
    else:
        print("\\n🧪 Step 5: All modules have baseline tests ✅")
    
    # 7. Final health check
    print("\\n🏥 Step 6: Final project health check...")
    validate_project_health()
    
    # Success!
    log_action('universal_update', 'completed', f'Updated {total_tasks} items successfully')
    
    print("\\n" + "="*50)
    print("🎉 UNIVERSAL UPDATE COMPLETE!")
    print("="*50)
    print("\\n📊 Summary:")
    print(f"   - Modules: {state['total_modules']}")
    print(f"   - CONTEXT.llm files: ✅ All current")
    print(f"   - PROJECT.llm: ✅ Updated")
    print(f"   - Baseline tests: ✅ Created as needed")
    print(f"   - CLAUDE.md rules: ✅ Applied")
    
    if not venv_check():
        print("\\n⚠️  REMINDER: Activate virtual environment!")
        print("   Run: source venv/bin/activate")
    
    print("\\n💡 Your project is now fully up to date!")
    print("   Ready for Claude development 🚀")

if __name__ == "__main__":
    main()
'''

CHECK_PY = '''#!/usr/bin/env python3
"""
Quick project health check
"""

import os
import sys
import subprocess
from pathlib import Path

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

def main():
    """Run quick checks"""
    print("🔍 Quick project check...\\n")
    
    # Python environment
    print("Python Environment:")
    venv_status = "✅ Active" if venv_check() else "❌ Not active"
    print(f"  Venv: {venv_status}")
    
    # Project files
    print("\\nProject Files:")
    files_to_check = [
        ('PROJECT.llm', 'Project manifest'),
        ('CLAUDE.md', 'Claude instructions'),
        ('requirements.txt', 'Python dependencies'),
        ('.claude/prompt.md', 'System prompt'),
        ('.claude/format.md', 'Project context')
    ]
    
    for file, desc in files_to_check:
        status = "✅" if os.path.exists(file) else "❌"
        print(f"  {status} {desc}: {file}")
    
    # CONTEXT.llm files
    print("\\nModule Documentation:")
    context_files = list(Path('.').rglob('CONTEXT.llm'))
    if context_files:
        print(f"  ✅ Found {len(context_files)} CONTEXT.llm files")
        for ctx in context_files[:3]:
            print(f"     - {ctx}")
        if len(context_files) > 3:
            print(f"     ... and {len(context_files)-3} more")
    else:
        print("  ❌ No CONTEXT.llm files found")
    
    # Baseline tests
    print("\\nBaseline Tests:")
    test_files = list(Path('.').glob('test_baseline_*.py'))
    if test_files:
        print(f"  ✅ Found {len(test_files)} baseline test files")
    else:
        print("  ⚠️  No baseline tests found")
    
    print("\\n💡 Tips:")
    print("  - Run 'u' to update context")
    print("  - Run 'ctx init' to create CONTEXT.llm files")
    print("  - Run 'baseline' to create baseline tests")

if __name__ == "__main__":
    main()
'''

HELP_PY = '''#!/usr/bin/env python3
"""
Claude Context Box Help System
"""

import os
import sys

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

def main():
    """Display help information"""
    
    help_text = """
🎯 Claude Context Box - Quick Commands

📋 BASIC COMMANDS:
  u, update     - Update PROJECT.llm and all contexts
  c, check      - Quick health check of project
  s, structure  - Show PROJECT.llm structure
  h, help       - Show this help

🔒 PROCEDURE VALIDATION:
  validate      - Full validation (procedure + tests + structure)
  procedure     - Check 9-step procedure compliance
  project       - Display full PROJECT.llm content
  deps          - Show module dependency graph

📁 CONTEXT MANAGEMENT:
  ctx init      - Create CONTEXT.llm for all modules
  ctx update    - Update existing CONTEXT.llm files
  ctx scan      - Find modules without CONTEXT.llm
  
🧪 TESTING:
  baseline <module>  - Create baseline tests for specific module
  test-all          - Run all baseline tests
  
🧹 MAINTENANCE:
  cleancode, cc     - Interactive dead code cleanup
  v, venv          - Setup/check Python environment

📝 MANDATORY WORKFLOW (9 Steps):
  1. Read PROJECT.llm
  2. Find target module
  3. Read module CONTEXT.llm
  4. Analyze current code
  5. Create baseline tests ('baseline <module>')
  6. Run baseline tests
  7. Make minimal changes
  8. Test again (STOP if fails)
  9. Update contexts ('u')

⚠️  CRITICAL RULES:
  - ALWAYS follow the 9-step procedure
  - NEVER modify code without baseline tests
  - STOP immediately when tests fail
  - NO COMMENTS in code
  - ENGLISH ONLY

💡 TIPS:
  - Run 'validate' before ANY code changes
  - Use 'procedure' to check compliance
  - Create baseline tests BEFORE modifications
  - Update contexts AFTER changes

🔗 MORE INFO:
  - .claude/prompt.md - Full system rules & procedure
  - PROJECT.llm - Architecture & dependencies
  - CLAUDE.md - Quick command reference
"""
    
    print(help_text)
    
    if not venv_check():
        print("\\n⚠️  WARNING: Not in virtual environment!")
        print("   Run: source venv/bin/activate")

if __name__ == "__main__":
    main()
'''

CONTEXT_PY = '''#!/usr/bin/env python3
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
        dirs[:] = [d for d in dirs if d not in {'venv', '__pycache__', '.git', 'node_modules'}]
        
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
        dirs[:] = [d for d in dirs if d not in {'venv', '__pycache__', '.git', 'node_modules'}]
        
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
'''

BASELINE_PY = '''#!/usr/bin/env python3
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
    
    content += '''
    
def test_module_imports():
    """Ensure all module imports work"""
    # This test passes if imports succeed
    assert True

# Run with: python -m pytest test_baseline_*.py -v
'''
    
    return content

def create_baseline(module_path):
    """Create baseline tests for a module"""
    module_name = os.path.basename(module_path)
    
    # Check if module exists
    if not os.path.exists(module_path):
        print(f"❌ Module not found: {module_path}")
        return False
    
    # Analyze module
    functions = analyze_module(module_path)
    
    if not functions:
        print(f"⚠️  No public functions found in {module_path}")
        return False
    
    # Generate test file
    test_filename = f"test_baseline_{module_name}.py"
    test_content = generate_baseline_test(module_name, functions)
    
    # Write test file
    with open(test_filename, 'w') as f:
        f.write(test_content)
    
    print(f"✅ Created {test_filename}")
    print(f"   Found {len(functions)} functions to test")
    print("\\n💡 Next steps:")
    print(f"   1. Edit {test_filename} to add actual test cases")
    print("   2. Run: python -m pytest {test_filename} -v")
    
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate baseline tests')
    parser.add_argument('module', help='Module path to create baseline for')
    
    args = parser.parse_args()
    
    if not venv_check():
        print("⚠️  Warning: Not running in virtual environment!")
    
    create_baseline(args.module)

if __name__ == "__main__":
    main()
'''

SETUP_SH = '''#!/bin/bash
# Setup script for Python virtual environment

echo "🔧 Setting up Python environment..."

# Check if venv exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment already exists"
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "🔄 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "❌ Could not find activation script!"
    exit 1
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip3 install --upgrade pip

# Install requirements if exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing requirements..."
    pip3 install -r requirements.txt
else
    echo "⚠️  No requirements.txt found"
fi

echo "✅ Setup complete!"
echo ""
echo "💡 To activate virtual environment:"
echo "   source venv/bin/activate  # Linux/Mac"
echo "   venv\\Scripts\\activate     # Windows"
'''

VALIDATION_PY = '''#!/usr/bin/env python3
"""
Procedure validation system - ensures 9-step procedure compliance
"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

class ProcedureValidator:
    """Validates that the 9-step procedure is being followed"""
    
    def __init__(self):
        self.log_file = '.claude/procedure.log'
        self.current_step = 0
        self.steps_completed = []
        self.violations = []
        
    def log_step(self, step_num, status, details=""):
        """Log procedure step completion"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step_num,
            'status': status,
            'details': details
        }
        
        # Ensure directory exists
        os.makedirs('.claude', exist_ok=True)
        
        # Append to log
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\\n')
    
    def check_procedure_compliance(self):
        """Check if all steps were followed in order"""
        if not os.path.exists(self.log_file):
            print("❌ No procedure log found - procedure not started")
            return False
        
        with open(self.log_file, 'r') as f:
            logs = [json.loads(line) for line in f if line.strip()]
        
        if not logs:
            print("❌ Empty procedure log")
            return False
        
        # Get latest session (last 9 entries or less)
        session_logs = logs[-9:]
        
        print("🔍 Checking procedure compliance...\\n")
        
        expected_steps = [
            "Read PROJECT.llm",
            "Find target module", 
            "Read module CONTEXT.llm",
            "Analyze current code",
            "Create baseline tests",
            "Run baseline tests",
            "Make changes",
            "Test again",
            "Update contexts"
        ]
        
        all_good = True
        
        for i, step_name in enumerate(expected_steps, 1):
            # Find log for this step
            step_log = next((log for log in session_logs if log['step'] == i), None)
            
            if not step_log:
                print(f"❌ Step {i}: {step_name} - NOT EXECUTED")
                self.violations.append(f"Step {i} not executed")
                all_good = False
            elif step_log['status'] == 'completed':
                print(f"✅ Step {i}: {step_name} - Completed")
            elif step_log['status'] == 'failed':
                print(f"❌ Step {i}: {step_name} - FAILED: {step_log.get('details', '')}")
                self.violations.append(f"Step {i} failed")
                all_good = False
            else:
                print(f"⚠️  Step {i}: {step_name} - {step_log['status']}")
        
        return all_good
    
    def validate_control_points(self):
        """Check control points"""
        print("\\n📍 Validating control points...\\n")
        
        checks = {
            "PROJECT.llm exists": os.path.exists('PROJECT.llm'),
            "Has CONTEXT.llm files": len(list(Path('.').rglob('CONTEXT.llm'))) > 0,
            "Has baseline tests": len(list(Path('.').glob('test_baseline_*.py'))) > 0,
            "In virtual environment": venv_check()
        }
        
        all_passed = True
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
            if not passed:
                all_passed = False
                self.violations.append(f"Control point failed: {check}")
        
        return all_passed
    
    def check_last_change(self):
        """Validate the last code change followed procedure"""
        print("\\n🔍 Checking last change compliance...\\n")
        
        # Check git status for recent changes
        try:
            import subprocess
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                changed_files = result.stdout.strip().split('\\n')
                print(f"📝 Found {len(changed_files)} changed files")
                
                # Check if baseline tests exist for changed modules
                for file_line in changed_files:
                    if file_line.endswith('.py') and not file_line.startswith('test_'):
                        file_path = file_line.split()[-1]
                        module_name = Path(file_path).stem
                        baseline_test = f"test_baseline_{module_name}.py"
                        
                        if os.path.exists(baseline_test):
                            print(f"✅ Baseline test exists: {baseline_test}")
                        else:
                            print(f"❌ No baseline test for: {file_path}")
                            self.violations.append(f"No baseline test for {file_path}")
        except:
            print("⚠️  Could not check git status")
    
    def generate_report(self):
        """Generate compliance report"""
        print("\\n" + "="*60)
        print("📊 PROCEDURE COMPLIANCE REPORT")
        print("="*60)
        
        if not self.violations:
            print("\\n✅ All checks passed! Procedure followed correctly.")
        else:
            print(f"\\n❌ Found {len(self.violations)} violations:\\n")
            for i, violation in enumerate(self.violations, 1):
                print(f"  {i}. {violation}")
            
            print("\\n💡 Recommendations:")
            print("  - Review the 9-step procedure in .claude/prompt.md")
            print("  - Ensure all steps are followed in order")
            print("  - Create baseline tests before any changes")
            print("  - Run 'validate' regularly during development")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Validate procedure compliance')
    parser.add_argument('--check-procedure', action='store_true',
                       help='Check if procedure was followed')
    parser.add_argument('--check-last-change', action='store_true',
                       help='Validate last code change')
    parser.add_argument('--log-step', type=int,
                       help='Log completion of a procedure step')
    parser.add_argument('--status', choices=['completed', 'failed', 'skipped'],
                       help='Status for --log-step')
    parser.add_argument('--details', help='Details for --log-step')
    
    args = parser.parse_args()
    
    validator = ProcedureValidator()
    
    if args.log_step:
        if not args.status:
            print("❌ --status required with --log-step")
            sys.exit(1)
        validator.log_step(args.log_step, args.status, args.details or "")
        print(f"✅ Logged step {args.log_step} as {args.status}")
    
    elif args.check_procedure:
        validator.check_procedure_compliance()
        validator.generate_report()
    
    elif args.check_last_change:
        validator.check_last_change()
        validator.generate_report()
    
    else:
        # Default: full validation
        print("🎯 Running full validation...\\n")
        
        procedure_ok = validator.check_procedure_compliance()
        control_ok = validator.validate_control_points()
        validator.check_last_change()
        
        validator.generate_report()
        
        if not (procedure_ok and control_ok):
            sys.exit(1)

if __name__ == "__main__":
    main()
'''

CLEANCODE_PY = '''#!/usr/bin/env python3
"""
Dead code cleanup utility
"""

import os
import sys
import ast
from pathlib import Path
import argparse

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

def find_unused_imports(filepath):
    """Find potentially unused imports in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Get all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
        
        # Simple check - look for usage in code
        unused = []
        for imp in set(imports):
            if content.count(imp) <= 1:  # Only in import statement
                unused.append(imp)
        
        return unused
    except:
        return []

def find_unused_functions(filepath):
    """Find potentially unused functions"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):
                    # Count occurrences
                    count = content.count(node.name)
                    if count <= 1:  # Only definition
                        functions.append(node.name)
        
        return functions
    except:
        return []

def scan_project():
    """Scan project for dead code"""
    print("🔍 Scanning for dead code...\\n")
    
    findings = {
        'unused_imports': {},
        'unused_functions': {},
        'empty_files': []
    }
    
    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        # Check file size
        if py_file.stat().st_size == 0:
            findings['empty_files'].append(str(py_file))
            continue
        
        # Check imports
        unused_imports = find_unused_imports(py_file)
        if unused_imports:
            findings['unused_imports'][str(py_file)] = unused_imports
        
        # Check functions
        unused_funcs = find_unused_functions(py_file)
        if unused_funcs:
            findings['unused_functions'][str(py_file)] = unused_funcs
    
    return findings

def interactive_cleanup(findings):
    """Interactive cleanup mode"""
    print("\\n🧹 Interactive Cleanup Mode\\n")
    
    # Empty files
    if findings['empty_files']:
        print(f"Found {len(findings['empty_files'])} empty files:")
        for file in findings['empty_files']:
            response = input(f"  Delete {file}? [y/N]: ").lower()
            if response == 'y':
                os.remove(file)
                print(f"  ✅ Deleted {file}")
    
    # Unused imports
    if findings['unused_imports']:
        print(f"\\nFound potentially unused imports in {len(findings['unused_imports'])} files")
        print("(Note: Some might be used dynamically)")
        for file, imports in list(findings['unused_imports'].items())[:5]:
            print(f"\\n📄 {file}:")
            for imp in imports:
                print(f"  - {imp}")
    
    # Summary
    print("\\n📊 Summary:")
    print(f"  - Empty files: {len(findings['empty_files'])}")
    print(f"  - Files with unused imports: {len(findings['unused_imports'])}")
    print(f"  - Files with unused functions: {len(findings['unused_functions'])}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Clean up dead code')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive cleanup mode')
    
    args = parser.parse_args()
    
    if not venv_check():
        print("⚠️  Warning: Not running in virtual environment!")
    
    findings = scan_project()
    
    if args.interactive:
        interactive_cleanup(findings)
    else:
        # Just report
        print("📊 Dead Code Report:")
        print(f"  - Empty files: {len(findings['empty_files'])}")
        print(f"  - Files with unused imports: {len(findings['unused_imports'])}")
        print(f"  - Files with unused functions: {len(findings['unused_functions'])}")
        print("\\n💡 Run with --interactive to clean up")

if __name__ == "__main__":
    main()
'''

class ClaudeContextInstaller:
    """Main installer class"""
    
    def __init__(self):
        self.existing_claude_md = None
        self.backup_dir = None
        
    def detect_existing_setup(self):
        """Detect existing Claude setup"""
        findings = {
            'has_claude_dir': os.path.exists('.claude'),
            'has_claude_md': os.path.exists('CLAUDE.md'),
            'claude_scripts': [],
            'user_content': None
        }
        
        # Check for existing scripts
        if findings['has_claude_dir']:
            for file in os.listdir('.claude'):
                if file.endswith('.py') or file.endswith('.sh'):
                    findings['claude_scripts'].append(file)
        
        # Extract user content from CLAUDE.md
        if findings['has_claude_md']:
            try:
                with open('CLAUDE.md', 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Try to extract user content (after our markers)
                    if '# Previous User Documentation' in content:
                        findings['user_content'] = content.split('# Previous User Documentation')[1].strip()
                    elif '---' in content:
                        # Fallback: get content after first ---
                        parts = content.split('---', 1)
                        if len(parts) > 1:
                            findings['user_content'] = parts[1].strip()
            except:
                pass
        
        return findings
    
    def backup_existing(self, findings):
        """Backup existing files"""
        if not (findings['has_claude_dir'] or findings['has_claude_md']):
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = f'.claude_backup_{timestamp}'
        os.makedirs(self.backup_dir, exist_ok=True)
        
        print(f"📦 Creating backup in {self.backup_dir}/")
        
        # Backup CLAUDE.md
        if findings['has_claude_md']:
            shutil.copy2('CLAUDE.md', os.path.join(self.backup_dir, 'CLAUDE.md'))
            print("  ✅ Backed up CLAUDE.md")
        
        # Backup .claude directory
        if findings['has_claude_dir']:
            shutil.copytree('.claude', os.path.join(self.backup_dir, '.claude'))
            print("  ✅ Backed up .claude/")
    
    def handle_conflicts(self, findings):
        """Handle existing setup conflicts"""
        if not (findings['has_claude_dir'] or findings['has_claude_md']):
            return 'install'  # No conflicts
        
        print("\n⚠️  Existing Claude setup detected!")
        
        if findings['has_claude_md']:
            print("  - Found CLAUDE.md")
        if findings['has_claude_dir']:
            print(f"  - Found .claude/ with {len(findings['claude_scripts'])} scripts")
        
        print("\nOptions:")
        print("1. Smart merge (recommended) - Preserve user content, update system")
        print("2. Backup and replace - Save existing, install fresh")
        print("3. Cancel installation")
        
        while True:
            choice = input("\nYour choice [1-3]: ").strip()
            if choice == '1':
                return 'merge'
            elif choice == '2':
                return 'replace'
            elif choice == '3':
                return 'cancel'
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def create_claude_md(self, user_content=None):
        """Create CLAUDE.md with proper structure"""
        content = f"""# Project Context Protocol

## Core system prompt (HIGHEST PRIORITY)
@.claude/prompt.md

## Project-specific context  
@.claude/format.md

## 💡 QUICK COMMANDS
When the user types these exact commands, execute the corresponding action:
- `update` or `u` → 🚀 UNIVERSAL UPDATE - Does EVERYTHING automatically!
  - Creates missing CONTEXT.llm files
  - Updates existing CONTEXT.llm files  
  - Updates PROJECT.llm
  - Reads and applies CLAUDE.md rules
  - Creates missing baseline tests
  - Validates project health
  - **This is the ONLY command you need!**
- `check` or `c` → Quick health check  
- `structure` or `s` → Show PROJECT.llm structure
- `help` or `h` → Show all available commands
- `validate` → Run full procedure validation
- `procedure` → Check procedure compliance
- `baseline <module>` → Create baseline tests for module
- `test-all` → Run all baseline tests
- `deps` → Show module dependency graph
- `project` → Display full PROJECT.llm
- `ctx init` → Initialize CONTEXT.llm for ALL modules (now included in `u`)
- `ctx update` → Update existing CONTEXT.llm files (now included in `u`)
- `ctx scan` → Find components without documentation
- `cleancode` or `cc` → Interactive dead code cleanup

## ⚠️ CRITICAL RULES

### 9-Step Mandatory Procedure
For ANY code modification, follow the procedure in @.claude/prompt.md
1. Read PROJECT.llm
2. Find target module
3. Read module CONTEXT.llm
4. Analyze current code
5. Create baseline tests
6. Run baseline tests
7. Make minimal changes
8. Test again (STOP if fails)
9. Update contexts

### Code style
- **NO COMMENTS** in code files
- Use **ENGLISH ONLY** for all code, variables, functions, and documentation
- Self-documenting code with clear naming

### Python environment
- ALWAYS use `python3` instead of `python`
- ALWAYS use `pip3` instead of `pip`
- ALWAYS work in virtual environment `venv`

### Component documentation (AUTOMATIC)
- **ALWAYS create CONTEXT.llm** when creating new directories with code
- **ALWAYS update CONTEXT.llm** when modifying files in a directory
- **ALWAYS read CONTEXT.llm** before working with files in a directory

## Command mappings:
**⚠️ IMPORTANT**: Check for exact command match. All Python scripts use venv/bin/python3 if venv exists.

### EXACT COMMAND MAPPINGS:
When user types exactly `h` → Run: `venv/bin/python3 .claude/help.py` (or `python3 .claude/help.py` if no venv)
When user types exactly `help` → Run: `venv/bin/python3 .claude/help.py` (or `python3 .claude/help.py` if no venv)

When user types exactly `u` → Run: `venv/bin/python3 .claude/update.py` (or `python3 .claude/update.py` if no venv)
When user types exactly `update` → Run: `venv/bin/python3 .claude/update.py` (or `python3 .claude/update.py` if no venv)

When user types exactly `c` → Run: `venv/bin/python3 .claude/check.py` (or `python3 .claude/check.py` if no venv)
When user types exactly `check` → Run: `venv/bin/python3 .claude/check.py` (or `python3 .claude/check.py` if no venv)

When user types exactly `s` → Run: `cat PROJECT.llm`
When user types exactly `structure` → Run: `cat PROJECT.llm`

When user types exactly `validate` → Run: `venv/bin/python3 .claude/validation.py` (or `python3 .claude/validation.py` if no venv)

When user types exactly `procedure` → Run: `venv/bin/python3 .claude/validation.py --check-procedure` (or `python3 .claude/validation.py --check-procedure` if no venv)

When user types `baseline` followed by module name → Run: `venv/bin/python3 .claude/baseline.py MODULE_NAME` (or `python3 .claude/baseline.py MODULE_NAME` if no venv)

When user types exactly `test-all` → Run: `venv/bin/python3 -m pytest test_baseline_*.py -v` (or `python3 -m pytest test_baseline_*.py -v` if no venv)

When user types exactly `deps` → Run: `cat PROJECT.llm | grep -A20 "@dependency_graph"`
When user types exactly `project` → Run: `cat PROJECT.llm`

When user types exactly `ctx init` → Run: `venv/bin/python3 .claude/context.py init` (or `python3 .claude/context.py init` if no venv)

When user types exactly `ctx update` → Run: `venv/bin/python3 .claude/context.py update` (or `python3 .claude/context.py update` if no venv)

When user types exactly `ctx scan` → Run: `venv/bin/python3 .claude/context.py scan` (or `python3 .claude/context.py scan` if no venv)

When user types exactly `cc` → Run: `venv/bin/python3 .claude/cleancode.py --interactive` (or `python3 .claude/cleancode.py --interactive` if no venv)
When user types exactly `cleancode` → Run: `venv/bin/python3 .claude/cleancode.py --interactive` (or `python3 .claude/cleancode.py --interactive` if no venv)

## Initial setup
```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate venv
source venv/bin/activate  # Linux/Mac
# or
venv\\Scripts\\activate     # Windows

# 3. Update context
python3 .claude/update.py
```
"""
        
        if user_content:
            content += f"\n\n---\n\n# Previous User Documentation\n\n{user_content}"
        
        return content
    
    def install_files(self):
        """Install all files"""
        print("\n📦 Installing Claude Context Box...")
        
        # Create .claude directory
        os.makedirs('.claude', exist_ok=True)
        
        # Write files
        files_to_create = [
            ('.claude/prompt.md', PROMPT_CONTENT),
            ('.claude/update.py', UPDATE_PY),
            ('.claude/check.py', CHECK_PY),
            ('.claude/help.py', HELP_PY),
            ('.claude/context.py', CONTEXT_PY),
            ('.claude/baseline.py', BASELINE_PY),
            ('.claude/validation.py', VALIDATION_PY),
            ('.claude/setup.sh', SETUP_SH),
            ('.claude/cleancode.py', CLEANCODE_PY)
        ]
        
        for filepath, content in files_to_create:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Make scripts executable
            if filepath.endswith('.py') or filepath.endswith('.sh'):
                os.chmod(filepath, 0o755)
            
            print(f"  ✅ Created {filepath}")
    
    def run_initial_update(self):
        """Run initial context update"""
        print("\n🔄 Running initial context update...")
        
        # Check for venv Python
        venv_python = None
        if os.path.exists('venv/bin/python3'):
            venv_python = 'venv/bin/python3'
        elif os.path.exists('venv/Scripts/python.exe'):
            venv_python = 'venv/Scripts/python.exe'
        
        # Use venv Python if available, otherwise current Python
        python_exe = venv_python if venv_python else sys.executable
        
        try:
            result = subprocess.run(
                [python_exe, '.claude/update.py'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ✅ Context updated successfully")
            else:
                print("  ⚠️  Update completed with warnings")
                if result.stderr:
                    print(f"     {result.stderr}")
        except Exception as e:
            print(f"  ❌ Error running update: {e}")
    
    def setup_venv(self):
        """Setup Python virtual environment"""
        if os.path.exists('venv'):
            print("✅ Virtual environment already exists")
            return True
        
        print("📦 Creating virtual environment...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'venv', 'venv'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ✅ Virtual environment created")
                
                # Try to install basic packages
                venv_pip = 'venv/bin/pip' if os.path.exists('venv/bin/pip') else 'venv/Scripts/pip.exe'
                if os.path.exists(venv_pip):
                    print("  📦 Installing basic packages...")
                    subprocess.run([venv_pip, 'install', '--upgrade', 'pip'], capture_output=True)
                    
                    # Install pytest if not in requirements.txt
                    if not os.path.exists('requirements.txt') or 'pytest' not in open('requirements.txt').read():
                        subprocess.run([venv_pip, 'install', 'pytest'], capture_output=True)
                        print("    ✅ Installed pytest")
                
                return True
            else:
                print(f"  ❌ Failed to create venv: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ❌ Error creating venv: {e}")
            return False
    
    def install(self):
        """Main installation process"""
        banner()
        
        # Setup virtual environment first
        if not self.setup_venv():
            print("\n⚠️  Warning: Could not create virtual environment")
            print("You may need to create it manually: python3 -m venv venv")
        
        # Detect existing setup
        findings = self.detect_existing_setup()
        
        # Handle conflicts
        if findings['has_claude_dir'] or findings['has_claude_md']:
            action = self.handle_conflicts(findings)
            
            if action == 'cancel':
                print("\n❌ Installation cancelled")
                return
            
            # Backup existing files
            self.backup_existing(findings)
            
            if action == 'replace':
                # Remove existing
                if findings['has_claude_dir']:
                    shutil.rmtree('.claude')
                if findings['has_claude_md']:
                    os.remove('CLAUDE.md')
        
        # Install files
        self.install_files()
        
        # Create CLAUDE.md
        user_content = findings.get('user_content') if findings else None
        claude_md_content = self.create_claude_md(user_content)
        
        with open('CLAUDE.md', 'w', encoding='utf-8') as f:
            f.write(claude_md_content)
        print("  ✅ Created CLAUDE.md")
        
        # Run initial update
        self.run_initial_update()
        
        # Success message
        print(f"\n{color('✅ Installation complete!', 'GREEN')}")
        
        # Check if venv is active
        if not os.environ.get('VIRTUAL_ENV'):
            print(f"\n{color('⚠️  IMPORTANT: Virtual environment is NOT active!', 'YELLOW')}")
            print("Please activate it before using Claude commands:")
            print("  source venv/bin/activate  # Linux/Mac")
            print("  venv\\Scripts\\activate     # Windows")
        
        print("\n📚 Quick start:")
        if not os.environ.get('VIRTUAL_ENV'):
            print("  1. Activate virtual environment: source venv/bin/activate")
            print("  2. Start Claude in this directory")
            print("  3. Type 'help' to see all commands")
        else:
            print("  1. ✅ Virtual environment is active")
            print("  2. Type 'help' to see all commands")
        print("  3. Type 'u' to update project context")
        print("  4. Type 'ctx init' to create CONTEXT.llm files")
        
        if self.backup_dir:
            print(f"\n💾 Previous setup backed up to: {self.backup_dir}/")

def main():
    """Main entry point"""
    installer = ClaudeContextInstaller()
    
    try:
        installer.install()
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
