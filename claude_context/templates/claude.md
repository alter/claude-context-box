# Claude Context Box Project

## 🚨 CRITICAL RULES (HIGHEST PRIORITY - OVERRIDE ALL)

### Technology Approval Rule (ABSOLUTE HIGHEST PRIORITY)
- **MANDATORY**: Before adding ANY new technology, library, framework, or tool:
  1. **DESCRIBE** what technology you want to add
  2. **EXPLAIN** why it's needed (what problem it solves)
  3. **DETAIL** how it will be used
  4. **SPECIFY** if it replaces something or adds new capability
  5. **WAIT** for explicit approval before proceeding
- **NEVER** add new technologies without this approval process

### Core Priorities
1. **Stability First** → **Clean Code** → **DRY** → **KISS** → **SOLID**
2. Creates resilient, maintainable systems
3. Respects existing codebase structure
4. Minimizes breaking changes

### Mandatory Safety Rules
- **NEVER** modify code you haven't read and understood
- **ALWAYS** test after modifications
- **MUST** follow 7-step procedure for ANY code change
- **STOP** immediately when verification fails

### Surgical Fixes Only
- Make MINIMUM changes to fix the issue
- Preserve existing functionality
- Only refactor with explicit permission
- Test edge cases after any change

## ⛔ STRICTLY FORBIDDEN

### Never Search/Modify In:
- `venv/`, `__pycache__/`, `.git/`
- `node_modules/`, `.env*`, `dist/`
- `build/`, `*.egg-info/`

### Never Do Without Permission:
- Modify existing code
- Delete any files
- Create new features
- Refactor existing code
- Change project structure
- Install new packages
- Modify configuration files
- git push (remote push)

## 📋 MANDATORY 7-STEP PROCEDURE

For ANY code modification, follow these steps EXACTLY:

1. **Read PROJECT.llm** → `cat PROJECT.llm`
2. **Find target module** → Use efficient search
3. **Read module CONTEXT.llm** → `cat path/to/module/CONTEXT.llm`
4. **Analyze current code** → Read and understand
5. **Make minimal changes** → Edit ONLY what's needed
6. **Verify changes** → If script: run with all args; If library: import and test method calls
7. **Update contexts** → Run update if needed

## ⚡ QUICK COMMANDS

Type exactly (case-sensitive):
- `u` or `update` → 🚀 Universal update (does EVERYTHING)
- `c` or `check` → Quick health check
- `s` or `structure` → Show PROJECT.llm structure
- `h` or `help` → Show all commands
- `validate` → Run full validation
- `deps` → Show dependency graph
- `ctx init` → Initialize CONTEXT.llm files
- `ctx update` → Update existing CONTEXT.llm
- `cc` or `cleancode` → Interactive dead code cleanup

## 🔧 ENVIRONMENT RULES

### Python Environment
- **ALWAYS** use `python3` (never `python`)
- **ALWAYS** use `pip3` (never `pip`)
- **ALWAYS** work in virtual environment `venv` or `.venv`

### Code Style
- **NO COMMENTS** in code files
- Use **ENGLISH ONLY** for all code, variables, functions
- Self-documenting code with clear naming

### Documentation
- **ALWAYS** create CONTEXT.llm for new modules
- **ALWAYS** update CONTEXT.llm when modifying
- **ALWAYS** read CONTEXT.llm before working
- **NEVER** add Claude authorship or co-authorship to any files
- **NEVER** use "Generated with Claude Code" or similar attributions

### Git Rules
- **NEVER** mention Claude/AI authorship in commit messages
- **NEVER** change git config (user.name, user.email)
- **ALWAYS** use existing user git configuration
- Commits should describe changes, not tools used

## 📍 CONTROL POINTS

✓ Before ANY code change → Read PROJECT.llm
✓ Before module edit → Read module's CONTEXT.llm
✓ After changes → Verify functionality
✓ If verification fails → STOP and analyze
✓ After completion → Update all contexts

## 🎯 DEVELOPMENT PRINCIPLES

1. **English only** - All code, variables, functions, documentation
2. **No comments** in code - Use descriptive names and CONTEXT.llm
3. **Verify before commit** - Test all changes practically
4. **Small commits** - One logical change at a time
5. **Update contexts** - Keep CONTEXT.llm and PROJECT.llm current
6. **Fail fast** - Stop immediately when verification fails
7. **Explicit is better** - Clear function names over clever code

## 📊 COMMAND MAPPINGS

All commands check for venv and use it if available:

```bash
# When user types exactly:
h, help     → $(python3 .claude/get_python.py) .claude/help.py
u, update   → $(python3 .claude/get_python.py) .claude/update.py
c, check    → $(python3 .claude/get_python.py) .claude/check.py
s, structure → cat PROJECT.llm
validate    → $(python3 .claude/get_python.py) .claude/validation.py
procedure   → $(python3 .claude/get_python.py) .claude/validation.py --check-procedure
deps        → cat PROJECT.llm | grep -A20 "@dependency_graph"
project     → cat PROJECT.llm
ctx init    → $(python3 .claude/get_python.py) .claude/context.py init
ctx update  → $(python3 .claude/get_python.py) .claude/context.py update
ctx scan    → $(python3 .claude/get_python.py) .claude/context.py scan
cc, cleancode → $(python3 .claude/get_python.py) .claude/cleancode.py --interactive
```

## 🔄 ADDITIONAL CONTEXT

@.claude/prompt.md  # Detailed system prompt
@.claude/format.md  # Project-specific format

---
*Claude Context Box v{{ version }} - Updated: {{ timestamp }}*