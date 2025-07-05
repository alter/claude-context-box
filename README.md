# Claude Context Box - Ultimate Hybrid Installer

A comprehensive project context management system for Claude Code that combines the best of both worlds: advanced project analysis with Skylos dead code detection and robust context management with detailed development guidelines.

## 🚀 Features

### Core Features
- **Hybrid Installation** - Smart merging of existing CLAUDE.md with new command structure
- **Skylos Integration** - Automatic dead code analysis and cleanup
- **Advanced Project Analysis** - Detects project type, chaos indicators, and organization patterns
- **Intelligent Context Management** - Token-efficient project understanding (~200-400 tokens vs 50,000+)
- **Command Mappings** - Single-letter commands for instant actions

### Smart Analysis
- **Project Type Detection** - Identifies new/empty, organized, legacy/chaotic, or existing Claude setups
- **Conflict Detection** - Finds naming conflicts, duplicate directories, scattered scripts
- **Python Environment Tracking** - Virtual environment status, dependencies, pip versions
- **Multi-Language Support** - Python, Node.js, Ruby, Go, Rust, Java, PHP, Dart/Flutter

### Dead Code Cleanup
- **Unused Imports** - Identifies and removes unnecessary imports
- **Unused Functions** - Finds functions that are never called
- **Unused Classes** - Detects orphaned class definitions
- **Unused Variables** - Spots variables that are assigned but never used
- **Confidence Levels** - 60%, 80%, or custom confidence thresholds

## 📦 Installation

### Quick Start
```bash
# Download the installer
curl -O https://raw.githubusercontent.com/yourusername/claude-context-box/main/install-claude-context.py

# Run in your project directory
python3 install-claude-context.py install
```

### Installation Options
When you run the installer, you'll get three options:

1. **🔄 UPDATE** - Update existing installation (recommended)
   - Preserves your existing CLAUDE.md content
   - Adds new command mappings to the top
   - Creates automatic backup

2. **🆕 FRESH** - Complete fresh installation (with backup)
   - Replaces CLAUDE.md with new structure
   - Backs up original content
   - Recommended for major updates

3. **❌ CANCEL** - Exit without changes

### What Gets Created
- `.claude/` directory with management scripts
- `CLAUDE.md` with enhanced command structure
- `.claude/context.json` - Project structure data
- `.claude/format.md` - Human-readable context
- `.claude/reports/` - Skylos analysis reports

## 🎯 Quick Start

### In Claude Code Interface
After installation, just type single letters for instant commands:

```
h              # Show all available commands
u              # Update project context  
c              # Quick conflict check
s              # Show project structure
v              # Setup/check Python environment
cc             # Interactive dead code cleanup
```

### Command Line Usage
```bash
# Project management
python3 claude-context.py help         # Show all commands
python3 claude-context.py update       # Update project context
python3 claude-context.py check        # Quick conflict check
python3 claude-context.py sync         # Sync documentation

# Dead code analysis
python3 claude-context.py cleancode                    # Basic analysis
python3 claude-context.py cleancode --interactive      # Guided cleanup
python3 claude-context.py cleancode --dry-run          # Preview only
python3 claude-context.py cleancode --confidence 80    # High confidence only

# Legacy commands (still work)
python3 .claude/update.py              # Direct context update
python3 .claude/check.py               # Direct conflict check
bash .claude/setup.sh                  # Python environment setup
```

### Typical Workflow
1. **Start session**: Type `u` in Claude Code to update context
2. **Work on code** - make your changes
3. **Clean up**: Type `cc` for interactive dead code cleanup
4. **Check structure**: Type `s` to see project organization
5. **Resolve conflicts**: Type `c` to check for naming conflicts

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

**Q: How does the hybrid installation work?**  
A: It intelligently merges your existing CLAUDE.md with new command mappings, preserving all your project documentation while adding enhanced functionality.

**Q: What's the difference between UPDATE and FRESH installation?**  
A: UPDATE preserves your content and adds new features on top. FRESH replaces everything with the new structure (but creates a backup first).

**Q: Does this work with all Claude Code features?**  
A: Yes! It uses only official Claude Code mechanisms (CLAUDE.md and @ imports) and enhances them with command mappings.

**Q: How much context does it use?**  
A: Typically 200-400 tokens for project structure, compared to 50,000+ for full code dumps. Your existing CLAUDE.md content remains fully accessible.

**Q: Can I customize what gets scanned?**  
A: Yes! Edit the `ignore_patterns` in `.claude/update.py` to exclude specific files or directories.

**Q: Does Skylos work with all Python projects?**  
A: Skylos works with most Python codebases. It automatically installs if missing and provides confidence levels for safe cleanup.

**Q: Does it work in monorepos?**  
A: Yes! It supports hierarchical contexts and can import parent CLAUDE.md files. Each subproject can have its own context.

**Q: What if I already have a complex CLAUDE.md?**  
A: The hybrid installer preserves all your existing content and adds command mappings at the top. Your documentation stays intact.

## 🚨 Troubleshooting

### Common Issues

**Installation fails:**
1. Ensure Python 3.6+ is installed: `python3 --version`
2. Check you're in the project root directory
3. Verify write permissions: `ls -la`

**Commands not working in Claude Code:**
1. Check CLAUDE.md has command mappings at the top
2. Look for "When I type `h` or `help`" section
3. Re-run installer with UPDATE option

**Skylos installation fails:**
1. Check internet connection for git clone
2. Ensure git is installed: `git --version`
3. Try manual installation in virtual environment

**Context not updating:**
1. Run manual update: `python3 .claude/update.py`
2. Check for errors: `python3 .claude/check.py`
3. Verify file permissions: `ls -la .claude/`

**Dead code cleanup removes needed code:**
1. Always use `--dry-run` first to preview
2. Start with `--confidence 80` for safety
3. Use `--interactive` mode for control
4. Test thoroughly after cleanup

## 🌟 Pro Tips

### Installation
1. **Backup first**: Your CLAUDE.md is automatically backed up, but extra safety never hurts
2. **Start with UPDATE**: It's safer and preserves all your existing documentation
3. **Check the merge**: Review the merged CLAUDE.md to ensure everything looks correct

### Daily Usage
4. **Single letters in Claude**: Type `h`, `u`, `c`, `s`, `v`, `cc` for instant commands
5. **Context workflow**: Always run `u` (update) before major coding sessions
6. **Conflict resolution**: Address warnings from `c` (check) before creating new directories

### Dead Code Cleanup
7. **Preview first**: Always use `--dry-run` to see what will be removed
8. **Interactive mode**: Use `--interactive` for guided, safer cleanup
9. **Start conservative**: Begin with `--confidence 80` for high-confidence items only
10. **Test after cleanup**: Run your tests after removing dead code
11. **Regular maintenance**: Use `cc` command weekly to prevent code bloat

### Project Organization
12. **Resolve conflicts early**: Fix directory naming conflicts as soon as they're detected
13. **Keep documentation**: Add `.claude/reports/` to `.gitignore` but commit `CLAUDE.md`
14. **Use in monorepos**: Each subproject can have its own Claude Context Box setup

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
