# Claude Context Box

A powerful development assistant system that helps Claude understand and work with your codebase efficiently. It automatically generates and maintains project documentation, enforces development best practices, and optionally integrates semantic memory capabilities.

## Features

### 🎯 Core Capabilities
- **Automatic Context Generation** - Creates and maintains `PROJECT.llm` and `CONTEXT.llm` files
- **Intelligent Code Analysis** - Understands project structure, dependencies, and architecture
- **Development Guardrails** - Enforces safe coding practices and prevents accidental breaking changes
- **Quick Commands** - Single-letter shortcuts for common operations
- **Virtual Environment Support** - Automatic detection and usage of venv/.venv
- **Dead Code Detection** - Interactive cleanup of unused code

### 🧠 Optional MCP Memory Integration
- **Semantic Memory Storage** - Persistent memory across sessions
- **Natural Language Search** - Find information using concepts, not just keywords
- **Automatic Consolidation** - Dream-inspired memory organization
- **Memory Preservation** - Pre/post compact hooks maintain context

## Installation

### Basic Installation

```bash
# Quick install (without MCP)
curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3

# Force reinstall
CLAUDE_FORCE=1 curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3
```

### Installation with MCP Memory Service (Optional)

MCP provides semantic memory for Claude but requires C++ compilation tools. **Claude Context Box works perfectly without it.**

```bash
# Try to install with MCP (will install Claude Context Box even if MCP fails)
MCP_ENABLE=1 curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3
```

**If MCP installation fails**, Claude Context Box will still be installed. To add MCP later:

1. **Install compilation tools for your OS:**
   - macOS: `xcode-select --install`
   - Ubuntu/Debian: `sudo apt-get install build-essential python3-dev`
   - RHEL/Fedora: `sudo yum groupinstall "Development Tools"`
   - Windows: Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)

2. **Run MCP setup:**
   - In Claude: type `mcp`
   - Or manually: `python3 .claude/mcp_setup.py`

## Quick Commands

Type these exactly (case-sensitive) in Claude:

| Command | Action | Description |
|---------|--------|-------------|
| `u` | Update | Regenerate PROJECT.llm and all contexts |
| `c` | Check | Quick health check of the project |
| `s` | Structure | Display PROJECT.llm structure |
| `h` | Help | Show all available commands |
| `validate` | Validate | Run full validation suite |
| `deps` | Dependencies | Show dependency graph |
| `ctx init` | Context Init | Initialize CONTEXT.llm files |
| `ctx update` | Context Update | Update existing CONTEXT.llm |
| `cc` | Clean Code | Interactive dead code cleanup |
| `mcp` | MCP Setup | Setup MCP Memory Service (if installed with MCP_ENABLE) |
| `mcp check` | MCP Status | Check MCP configuration and health |

## Project Structure

After installation, your project will have:

```
your-project/
├── .claude/                 # Claude Context Box system files
│   ├── update.py           # Main update script
│   ├── check.py            # Health check script
│   ├── validation.py       # Validation framework
│   ├── context.py          # Context management
│   ├── cleancode.py        # Dead code detection
│   ├── mcp_setup.py        # MCP configuration (if enabled)
│   └── ...
├── PROJECT.llm             # Project architecture map
├── CLAUDE.md              # Instructions for Claude
└── module/
    └── CONTEXT.llm        # Module interface documentation
```

## Key Files

### PROJECT.llm
Contains the complete project architecture map:
- Module structure and dependencies
- Critical code paths
- Test coverage information
- Recent changes log

### CONTEXT.llm
Documents module interfaces:
- Public API and methods
- Dependencies and state
- Behavior and error handling
- Performance characteristics

### CLAUDE.md
Instructions and rules for Claude:
- Development procedures
- Safety rules and forbidden zones
- Command mappings
- Environment requirements

## MCP Memory Commands (if enabled)

When MCP is enabled, use these commands in Claude:

- `/memory-store "content" --tags work,important` - Store memory with tags
- `/memory-search --query "database decisions"` - Search memories
- `/memory-recall "what did we decide last week?"` - Time-based recall
- `/memory-health` - Check memory system status

## Development Workflow

### 1. Initial Setup
```bash
# Install Claude Context Box
curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3

# Generate initial contexts
u  # or update
```

### 2. Before Making Changes
```bash
# Check project health
c  # or check

# View structure
s  # or structure
```

### 3. After Changes
```bash
# Update all contexts
u  # or update

# Validate changes
validate
```

## Safety Features

### Protected Zones
Never modifies:
- `venv/`, `.venv/` - Virtual environments
- `__pycache__/` - Python cache
- `.git/` - Git repository
- `node_modules/` - Node dependencies
- `.env*` - Environment files
- `.local/` - Local data

### Mandatory Procedures
- 8-step verification process for code changes
- Control points at each critical step
- Automatic rollback on verification failure
- Context updates after interface changes

### Development Principles
1. **Stability First** - Prevent breaking changes
2. **Clean Code** - Readable and maintainable
3. **DRY** - Don't Repeat Yourself
4. **KISS** - Keep It Simple
5. **SOLID** - Object-oriented design principles

## Configuration

### Environment Variables

```bash
# Force reinstallation
export CLAUDE_FORCE=1

# Enable MCP Memory Service
export MCP_ENABLE=1

# MCP Memory configuration
export MCP_MEMORY_SQLITE_PATH="/path/to/memory.db"
export MCP_MEMORY_BACKUPS_PATH="/path/to/backups"
```

### Hooks System

Create `.claude-hooks.toml` for custom actions:

```toml
[[hooks]]
event = "PreCompact"
command = '''
echo "Running before context compaction..."
'''

[[hooks]]
event = "PostCompact"
command = '''
echo "Running after context compaction..."
'''
```

## Troubleshooting

### Commands Not Working
- Ensure you're typing commands exactly (case-sensitive)
- Check if venv is active: `c` or `check`
- Reinstall with force: `CLAUDE_FORCE=1 curl ... | python3`

### MCP Issues
- Run `mcp check` to diagnose
- Restart Claude Desktop after MCP setup
- Check `.local/mcp/memory.db` exists
- Verify venv Python is being used

### Python Environment
- Always use `python3` (never `python`)
- Always use `pip3` (never `pip`)
- Work in virtual environment (`venv` or `.venv`)

## Advanced Features

### Dead Code Detection
```bash
# Interactive cleanup
cc  # or cleancode

# Automatic cleanup (dangerous!)
python3 .claude/cleancode.py --auto-remove
```

### Custom Validation
Add to `.claude/custom_validators.py`:
```python
def validate_no_todos(file_path, content):
    """Ensure no TODO comments in code"""
    if 'TODO' in content:
        return False, "Found TODO comment"
    return True, None
```

### Multi-Project Support
```bash
# Install in multiple projects
for project in project1 project2 project3; do
    cd $project
    curl -sSL ... | python3
    cd ..
done
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Follow the 8-step procedure for changes
4. Ensure all validations pass
5. Submit pull request

## License

MIT License - See LICENSE file for details

## Support

- Issues: [GitHub Issues](https://github.com/alter/claude-context-box/issues)
- Documentation: Check `.claude/README.md` for detailed system documentation

## Version

Claude Context Box v1.0.0

---

*Remember: The system is designed to help Claude work safely and efficiently with your code. Always use the quick commands and follow the procedures for best results.*