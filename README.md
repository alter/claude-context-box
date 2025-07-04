# Claude Context Box

A unified project context management system for Claude Code with integrated dead code analysis using Skylos.

## 🚀 Features

- **Unified Management** - Single script for all project context operations
- **Dead Code Analysis** - Integrated Skylos scanner for cleaning unused code
- **Automatic Project Scanning** - Analyzes project structure and creates compact context
- **Conflict Detection** - Identifies naming conflicts and organization issues
- **Python Environment Awareness** - Tracks virtual environment status and dependencies
- **Token-Efficient** - Compresses project context to ~200-400 tokens instead of 50,000+
- **Interactive Cleanup** - Guided removal of dead code with confidence levels
- **Multi-Language Support** - Detects Python, Node.js, Ruby, Go, Rust, Java, and more

## 📦 Installation

1. Download the installer:
```bash
curl -O https://raw.githubusercontent.com/alter/claude-context-box/refs/heads/main/install-claude-context.py
```

2. Run the installer in your project root:
```bash
python3 install-claude-context.py
```

3. The installer will create:
   - `.claude/` directory with context management scripts
   - `CLAUDE.md` file that Claude Code automatically loads
   - Initial project context scan

## 🎯 Quick Start

After installation, use these unified commands:

### Main Commands:
- `sync, sy` - Sync documentation and context
- `update, u` - Update project context
- `check, c` - Quick conflict check
- `modules, m` - List modules with status
- `brief, b` - Show PROJECT_BRIEF.md
- `structure, s` - Show project structure
- `cleancode, cc` - Clean code (using Skylos)
- `help, h` - Show all commands

### Usage Examples:
```bash
# Show help
python3 install-claude-context.py help

# Quick sync
python3 install-claude-context.py sync

# Analyze dead code
python3 install-claude-context.py cleancode

# Interactive cleanup
python3 install-claude-context.py cleancode --interactive

# Preview changes (dry run)
python3 install-claude-context.py cleancode --interactive --dry-run

# High confidence cleanup only
python3 install-claude-context.py cleancode --confidence 80
```

## 💡 How It Works

The unified system provides comprehensive project management through a single script:

### Core Features:
- **Project Analysis** - Automatically detects project type (new, organized, legacy/chaotic)
- **Skylos Integration** - Built-in dead code analysis and cleanup
- **Context Management** - Maintains project documentation and structure awareness
- **Command Shortcuts** - Simple aliases for all operations

### Workflow:
1. **Start session**: `python3 install-claude-context.py sync`
2. **Make changes** to your code
3. **Clean dead code**: `python3 install-claude-context.py cleancode --interactive`
4. **End session**: `python3 install-claude-context.py sync`

### Skylos Dead Code Analysis:
The integrated Skylos scanner identifies:
- 🔗 Unused imports
- 🔧 Unused functions  
- 🏗️ Unused classes
- 📦 Unused variables

### Confidence Levels:
- **High (80-100%)** - Very likely safe to remove
- **Medium (60-80%)** - Needs manual review
- **Low (20-60%)** - Requires careful analysis

## 🧹 Dead Code Cleanup Examples

### Basic analysis:
```bash
python3 install-claude-context.py cleancode
# Shows summary of dead code found
```

### Interactive cleanup:
```bash
python3 install-claude-context.py cleancode --interactive
# Guides you through each item for removal
```

### Safe preview:
```bash
python3 install-claude-context.py cleancode --interactive --dry-run
# Shows what would be removed without making changes
```

### High confidence only:
```bash
python3 install-claude-context.py cleancode --confidence 80
# Only shows items with 80%+ confidence
```

## ⚠️ Conflict Prevention

The system actively prevents common mistakes:

- **Multiple config directories**: Warns if both `config/` and `configs/` exist
- **Test directory conflicts**: Identifies when `test/` and `tests/` coexist  
- **Singular/plural naming**: Detects `model/` vs `models/` conflicts

Example warning:
```
⚠️ CRITICAL WARNINGS - READ FIRST!

### 🔴 Config Conflict
- **Issue**: Multiple config directories found: ['config', 'configs']
- **REQUIRED ACTION**: Use 'config' as primary config directory
- **DO NOT**: Create new directories without resolving this
```

## 🐍 Python Environment Integration

The system tracks your Python environment:

- Detects virtual environment location
- Checks if venv is activated
- Lists installed dependencies
- Warns about missing requirements.txt

## 📋 Requirements

- Python 3.6+
- Works on macOS, Linux, and Windows
- No external dependencies

## 🔄 Updating

To update an existing installation:

1. Copy the `.claude` folder to a new project
2. Run the installer again:
```bash
python3 install-claude-context.py
```

## 🤝 Contributing

Contributions are welcome! The system is designed to be:

- **Language agnostic** - Easy to add support for new languages
- **Extensible** - Simple to add new conflict detection rules
- **Lightweight** - No external dependencies

## 📝 License

MIT License - feel free to use in your projects!

## 🙋 FAQ

**Q: Does this work with all Claude Code features?**  
A: Yes! It uses only official Claude Code mechanisms (CLAUDE.md and @ imports).

**Q: How much context does it use?**  
A: Typically 200-400 tokens, compared to 50,000+ for full code dumps.

**Q: Can I customize what gets scanned?**  
A: Yes! Edit the `ignore_patterns` in `.claude/update.py`.

**Q: Does it work in monorepos?**  
A: Yes! It supports hierarchical contexts and can import parent CLAUDE.md files.

## 🚨 Troubleshooting

If you encounter issues:

1. Ensure Python 3.6+ is installed: `python3 --version`
2. Check file permissions: `ls -la .claude/`
3. Run manual update: `python3 .claude/update.py`
4. Check for errors: `python3 .claude/check.py`

## 🌟 Pro Tips

1. **Always sync first**: Run `sync` before starting any session
2. **Use dry-run**: Preview changes with `--dry-run` before actual cleanup
3. **Start with high confidence**: Use `--confidence 80` for safer removals
4. **Test after cleanup**: Always run tests after removing dead code
5. **Keep documentation**: Add `.claude/reports/` to `.gitignore` but keep `CLAUDE.md`
6. **Regular cleanup**: Use `cleancode` regularly to prevent code bloat
7. **Interactive mode**: Use `--interactive` for guided cleanup experience

## 📋 Command Reference

| Command | Alias | Description |
|---------|-------|-------------|
| `help` | `h` | Show all commands |
| `sync` | `sy` | Sync documentation and context |
| `update` | `u` | Update project context |
| `check` | `c` | Quick conflict check |
| `modules` | `m` | List modules with status |
| `brief` | `b` | Show PROJECT_BRIEF.md |
| `structure` | `s` | Show project structure |
| `cleancode` | `cc` | Clean code using Skylos |
| `install` | - | Install/setup system |

---

Made with ❤️ for developers who want Claude to truly understand their projects.
