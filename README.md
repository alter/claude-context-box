# Claude Context Box

A smart project context management system for Claude Code that automatically maintains project structure awareness and prevents common development conflicts.

## 🚀 Features

- **Automatic Project Scanning** - Analyzes your entire project structure and creates a compact context
- **Conflict Detection** - Identifies naming conflicts (e.g., `config` vs `configs` directories)
- **Python Environment Awareness** - Tracks virtual environment status and dependencies
- **Token-Efficient** - Compresses project context to ~200-400 tokens instead of 50,000+
- **Quick Commands** - Simple shortcuts like `u` for update, `c` for check
- **Multi-Language Support** - Detects Python, Node.js, Ruby, Go, Rust, Java, and more
- **Hierarchical Context** - Supports parent/child project relationships

## 📦 Installation

1. Download the installer:
```bash
curl -O https://raw.githubusercontent.com/yourusername/claude-context-box/main/install-claude-context.py)
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

After installation, when you start Claude Code in your project:

1. Claude automatically loads the project context
2. You can use these commands:
   - `u` or `update` - Update project context
   - `c` or `check` - Quick conflict check
   - `s` or `structure` - Show project structure
   - `cf` or `conflicts` - Show naming conflicts
   - `v` or `venv` - Setup Python environment
   - `h` or `help` - Show all commands

## 💡 How It Works

The system creates a `.claude/` directory in your project containing:

```
.claude/
├── update.py      # Main context scanner
├── check.py       # Quick conflict checker
├── setup.sh       # Python environment setup
├── context.json   # Raw context data
└── format.md      # Formatted context for Claude
```

Your `CLAUDE.md` file imports the dynamic context:
```markdown
## Automatic project context
@.claude/format.md
```

This gives Claude real-time awareness of:
- Directory structure and organization
- File types and counts
- Naming conflicts and issues
- Python environment status
- Project dependencies
- Entry points (main.py, app.py, etc.)

## 🔧 Usage Examples

### Update context after structural changes:
```
You: u
Claude: [Runs python3 .claude/update.py and updates context]
```

### Check for conflicts before refactoring:
```
You: c
Claude: [Shows any naming conflicts or warnings]
```

### View current project structure:
```
You: s
Claude: [Displays formatted project tree]
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

1. Run `u` before starting any refactoring
2. Use `c` to quickly check environment status
3. Add `.claude/context.json` and `.claude/format.md` to `.gitignore`
4. Keep `CLAUDE.md` in version control for team sharing
5. Run `v` to quickly set up Python environment

---

Made with ❤️ for developers who want Claude to truly understand their projects.
