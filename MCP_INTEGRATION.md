# MCP Memory Service Integration

Claude Context Box now includes optional integration with the doobidoo MCP Memory Service, providing persistent semantic memory for Claude Desktop and other AI assistants.

## Features

- **Semantic Memory Storage**: Store and retrieve memories using natural language
- **Persistent Storage**: SQLite-vec backend for fast, lightweight storage
- **Auto-consolidation**: Dream-inspired memory organization system
- **Multi-client Support**: Works with Claude Desktop, VS Code, Cursor, and more

## Installation

### With MCP Support

```bash
# Install with MCP enabled
MCP_ENABLE=1 curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3

# Or with force reinstall
CLAUDE_FORCE=1 MCP_ENABLE=1 curl -sSL https://raw.githubusercontent.com/alter/claude-context-box/main/install.py | python3
```

### Manual Setup

If you already have Claude Context Box installed:

```bash
# Run MCP setup
python3 .claude/mcp_setup.py

# Check MCP status
python3 .claude/mcp_check.py
```

## Commands

### Setup Commands (in terminal)
- `mcp` - Setup MCP Memory Service
- `mcp check` - Check MCP status and configuration

### Memory Commands (in Claude)
- `/memory-store "content" --tags work,important` - Store memory with tags
- `/memory-search --query "database decisions"` - Search memories
- `/memory-recall "what did we decide last week?"` - Recall by time
- `/memory-health` - Check memory system status

## Data Storage

MCP stores data in `.local/mcp/`:
- `memory.db` - SQLite database with vector embeddings
- `backups/` - Automatic backups

## Configuration

The installer automatically configures Claude Desktop with MCP. The configuration is stored in:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

## Requirements

- Python 3.8+
- Claude Desktop (for memory commands)
- uv package manager (installed automatically)

## Troubleshooting

### MCP not working in Claude
1. Restart Claude Desktop after installation
2. Check status: `python3 .claude/mcp_check.py`
3. Verify config exists in Claude's config directory

### Installation fails
1. Ensure Python 3.8+ is installed
2. Try manual installation:
   ```bash
   pip install uv
   uvx --from git+https://github.com/doobidoo/mcp-memory-service.git mcp-memory-service
   ```

### Memory commands not available
1. Check MCP is enabled in CLAUDE.md
2. Verify MCP service is running
3. Look for errors in Claude's developer console

## Uninstalling

To remove MCP integration:
1. Edit Claude Desktop config and remove the "memory" section from "mcpServers"
2. Delete `.local/mcp/` directory
3. MCP commands will no longer appear in Claude

## Privacy Note

All memories are stored locally in your project's `.local/mcp/memory.db` file. No data is sent to external servers unless you explicitly configure cloud backends.