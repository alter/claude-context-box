# Claude Context Box v2

A modern context management system for Claude AI that helps maintain consistent coding standards and project understanding.

## 🚀 Quick Install

### Method 1: Curl Install (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3 -
```

### Method 2: Pip Install
```bash
pip install claude-context-box
claude-context init
```

### Method 3: Manual Install
```bash
git clone https://github.com/alter/claude-context-box.git
cd claude-context-box
python3 install.py
```

## 🎯 Features

- **9-Step Safety Procedure**: Enforces safe code modifications with mandatory testing
- **Context Management**: Automatic CONTEXT.llm files for every module
- **Project Overview**: PROJECT.llm tracks architecture and dependencies
- **Baseline Testing**: Create snapshot tests before any changes
- **Smart Commands**: Single-letter shortcuts for common operations
- **Virtual Environment**: Automatic venv setup and management

## ⚡ Quick Commands

After installation, use these commands in your project:

- `u` → Universal update (does everything!)
- `c` → Quick health check
- `s` → Show project structure
- `h` → Help
- `baseline <module>` → Create baseline tests
- `ctx init` → Initialize context files
- `cc` → Clean dead code

## 🛡️ Core Principles

1. **Stability First** → **Clean Code** → **DRY** → **KISS** → **SOLID**
2. Never modify without understanding
3. Always test before and after changes
4. Minimal changes only
5. English-only, self-documenting code

## 📦 Installation Options

### Environment Variables

Customize installation with these environment variables:

```bash
# Install specific version
curl -sSL ... | CLAUDE_VERSION=v0.1.0 python3 -

# Custom installation directory
curl -sSL ... | CLAUDE_HOME=/opt/claude python3 -

# Skip virtual environment
curl -sSL ... | CLAUDE_NO_VENV=1 python3 -

# Force reinstall
curl -sSL ... | CLAUDE_FORCE=1 python3 -

# Uninstall
curl -sSL ... | CLAUDE_UNINSTALL=1 python3 -
```

## 🏗️ Project Structure

After installation, your project will have:

```
your-project/
├── .claude/           # Core scripts and tools
│   ├── update.py      # Universal updater
│   ├── check.py       # Health checker
│   ├── context.py     # Context manager
│   └── ...
├── CLAUDE.md          # Project rules for Claude
├── PROJECT.llm        # Project architecture
└── venv/              # Virtual environment
```

## 🔄 Updating

Update to the latest version:

```bash
# If installed via curl
curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | CLAUDE_FORCE=1 python3 -

# If installed via pip
pip install --upgrade claude-context-box
```

## 📚 Documentation

Each module gets a CONTEXT.llm file describing:
- Component purpose and interface
- Dependencies and state
- Expected behavior and errors
- Performance characteristics

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Follow the 9-step procedure for changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- [GitHub Repository](https://github.com/alter/claude-context-box)
- [Issue Tracker](https://github.com/alter/claude-context-box/issues)
- [Discussions](https://github.com/alter/claude-context-box/discussions)