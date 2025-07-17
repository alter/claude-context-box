# Virtual Environment Guide

Claude Context Box v0.1.2 now includes smart virtual environment detection and management.

## How It Works

### 1. Automatic Detection
The installer automatically scans for existing virtual environments by looking for `activate` scripts:
```bash
find . -name 'activate' -type f
```

### 2. Environment Preference
- **Poetry Projects**: Prefers `.venv` over `venv`
- **Standard Projects**: Uses first found environment or creates `venv`
- **Multiple Environments**: Shows all found environments and selects the most appropriate one

### 3. Project Type Detection
- **Poetry**: Detected by `[tool.poetry]` section in `pyproject.toml`
- **Standard**: Regular Python projects with or without `requirements.txt`

## Installation Scenarios

### Scenario 1: Poetry Project with .venv
```bash
# Your project structure:
my-project/
├── .venv/                 # ← Will be detected and used
├── pyproject.toml         # ← Poetry config detected
├── poetry.lock
└── src/

# Installation result:
✅ Using existing virtual environment: .venv
🎭 Poetry project detected - using poetry install
```

### Scenario 2: Standard Project with venv
```bash
# Your project structure:
my-project/
├── venv/                  # ← Will be detected and used
├── requirements.txt       # ← Will be installed
└── src/

# Installation result:
✅ Using existing virtual environment: venv
📋 Installing from requirements.txt...
```

### Scenario 3: Multiple Environments
```bash
# Your project structure:
my-project/
├── venv/                  # ← Available
├── .venv/                 # ← Will be preferred for Poetry
├── pyproject.toml
└── src/

# Installation result:
📦 Found 2 existing virtual environment(s):
  1. venv (Python 3.11.0)
  2. .venv (Python 3.11.0)
✅ Using existing virtual environment: .venv
```

### Scenario 4: No Existing Environment
```bash
# Your project structure:
my-project/
├── pyproject.toml         # ← Poetry detected
└── src/

# Installation result:
📦 Creating new virtual environment...
🎭 Poetry project detected - creating .venv/
```

## Saved Configuration

The installer saves environment information in `.claude/venv_info.json`:
```json
{
  "path": "/project/.venv",
  "python": "/project/.venv/bin/python3",
  "activate": "/project/.venv/bin/activate",
  "type": "poetry"
}
```

## Usage After Installation

All Claude Context Box commands automatically use the detected environment:

```bash
# These commands will use the detected Python environment
claude-context update
claude-context check
u                    # Universal update
c                    # Health check
```

## Benefits

1. **No Conflicts**: Won't create duplicate virtual environments
2. **Consistent**: All scripts use the same Python executable
3. **Smart**: Understands Poetry vs standard Python projects
4. **Flexible**: Works with any virtual environment setup
5. **Automatic**: No manual configuration needed

## Troubleshooting

### Issue: Wrong Environment Selected
Solution: Delete `.claude/venv_info.json` and run installer again

### Issue: Poetry Commands Fail
Solution: Ensure `poetry` is installed and accessible in your PATH

### Issue: Dependencies Not Installed
Solution: Check that your `pyproject.toml` or `requirements.txt` is valid

### Issue: Multiple Python Versions
Solution: The installer will show detected Python versions for each environment

## Migration from v0.1.1

If you're upgrading from v0.1.1, the installer will:
1. Detect your existing setup
2. Create `venv_info.json` with current configuration
3. Continue using your existing virtual environment
4. Install any missing dependencies