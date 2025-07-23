# Claude Context Box v2

## What's New in v0.2.0

- **Simplified 7-step procedure** - Removed baseline tests in favor of practical verification
- **Enhanced exclusion rules** - Better handling of virtual environments (.venv, venv, env, etc.)
- **Git best practices** - No AI/Claude mentions in commits, respects user git config
- **Practical verification** - Test scripts by running them, libraries by importing them
- **Auto venv detection** - Commands automatically find and use correct Python from venv/.venv/env
- **PostCompact hook** - Automatically refreshes context after /compact command

A modern context management system for Claude AI that enforces coding standards and maintains deep project understanding.

## 🚀 Quick Install

### Method 1: One-Command Install (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -
```

### Method 2: pip Install
```bash
pip install claude-context-box
```

### Method 3: From Source
```bash
git clone https://github.com/alter/claude-context-box.git
cd claude-context-box
pip install .
```

## 📦 Installation Options

Customize installation with environment variables:

```bash
# Install specific version
curl -sSL ... | CLAUDE_VERSION=v0.1.0 python3 -

# Custom installation directory
curl -sSL ... | CLAUDE_HOME=/path/to/project python3 -

# Skip virtual environment creation
curl -sSL ... | CLAUDE_NO_VENV=1 python3 -

# Force reinstall
curl -sSL ... | CLAUDE_FORCE=1 python3 -

# Uninstall
curl -sSL ... | CLAUDE_UNINSTALL=1 python3 -
```

The installer automatically:
- Creates virtual environment
- Installs claude-context-box package
- Initializes project structure
- Creates `.claude/` tools directory

## ⚡ Quick Commands

After installation, use these commands in Claude:

| Command | Description |
|---------|-------------|
| `u` | Universal update (does EVERYTHING!) |
| `c` | Quick health check |
| `s` | Show project structure |
| `h` | Help with all commands |
| `ctx init` | Initialize CONTEXT.llm files |
| `ctx update` | Update existing CONTEXT.llm |
| `cc` | Interactive dead code cleanup |
| `validate` | Check procedure compliance |
| `deps` | Show dependency graph |

## 🎯 Core Features

### 🛡️ 7-Step Safety Procedure
Mandatory procedure for ANY code changes:
1. Read PROJECT.llm
2. Find target module
3. Read module CONTEXT.llm
4. Analyze current code
5. Make minimal changes
6. Verify changes (run scripts, import libraries, test endpoints)
7. Update contexts

### 📋 Context Management
- **CONTEXT.llm** - Automatic documentation for every module
- **PROJECT.llm** - Architecture and dependency tracking
- **CLAUDE.md** - Project rules and instructions for Claude

### 🎪 Claude Code Hooks (New!)
Automatic actions with `.claude-hooks.toml`:
- **PostCompact** - Auto-updates context after /compact
- **PostToolUse** - Auto-format Python files
- **PreToolUse** - Remind about CONTEXT.llm
See `claude_context/templates/claude-hooks.toml` for examples

## 🏗️ Project Structure

After installation:
```
your-project/
├── .claude/           # Core scripts and tools
│   ├── update.py      # Universal updater
│   ├── check.py       # Health checker
│   ├── context.py     # CONTEXT.llm manager
│   ├── baseline.py    # Baseline test creator
│   └── ...
├── CLAUDE.md          # Project rules for Claude
├── PROJECT.llm        # Project architecture
└── venv/              # Virtual environment
```

## 🔄 Typical Workflow

1. **Start work**: Type `u` to update everything
2. **Before changes**: Claude automatically follows the 9-step procedure
3. **Code changes**: Make edits (Claude creates/updates CONTEXT.llm)
4. **Cleanup**: Type `cc` for dead code cleanup
5. **Check**: Type `c` to verify project health

## 🎯 Core Principles

1. **Priorities**: Stability First → Clean Code → DRY → KISS → SOLID
2. Never modify without understanding
3. Always test before and after changes
4. Minimal changes only
5. English-only, self-documenting code
6. NO comments in code (use CONTEXT.llm instead)

## 📚 CONTEXT.llm Files

Each module gets a CONTEXT.llm file describing:
- Component purpose and interface
- Dependencies and state
- Expected behavior and errors
- Performance characteristics

Example:
```
@component: UserAuthService
@type: service
@version: 2.1.0
@deps: [models.User, utils.crypto]
@purpose: Handle user authentication

@interface:
- authenticate(email: str, password: str) -> dict
- create_session(user_id: str) -> str
- validate_token(token: str) -> bool

@behavior:
- Passwords hashed with bcrypt
- Sessions stored in Redis
- Rate limiting on failed attempts
```

## 🔄 Updating

```bash
# Update to latest version
curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | CLAUDE_FORCE=1 python3 -
```

## ⚠️ Important Rules

### ❌ FORBIDDEN without permission:
- Modify existing code
- Delete any files
- Create new features
- Refactor existing code
- Change project structure
- Install new packages

### ✅ ALLOWED without permission:
- Read any files
- Create baseline tests
- Run existing tests
- Search codebase
- Create backup files
- Generate CONTEXT.llm files

## 🐍 Python Environment

The system automatically:
- Creates virtual environment
- Installs pytest
- Tracks venv activation
- Uses only python3 and pip3

## 🧹 Dead Code Cleanup (Skylos)

Integrated analyzer finds:
- 🔗 Unused imports
- 🔧 Unused functions
- 🏗️ Unused classes
- 📦 Unused variables

```bash
# In Claude, just type:
cc

# Or run directly:
python3 .claude/cleancode.py --interactive
```

## 📋 Requirements

- Python 3.7+
- macOS, Linux, or Windows
- Git (for some features)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Follow the 9-step procedure
4. Submit a pull request

## 📄 License

MIT License - use freely!

## 🔗 Links

- [GitHub Repository](https://github.com/alter/claude-context-box)
- [Issue Tracker](https://github.com/alter/claude-context-box/issues)
- [Discussions](https://github.com/alter/claude-context-box/discussions)

---

Made with ❤️ for developers who want Claude to truly understand their projects.