# Claude Context Box Project

## 🚨 КРИТИЧЕСКИЕ ПРАВИЛА (HIGHEST PRIORITY - OVERRIDE ALL)

### Core Priorities
1. **Stability First** → **Clean Code** → **DRY** → **KISS** → **SOLID**
2. Creates resilient, maintainable systems
3. Respects existing codebase structure
4. Minimizes breaking changes

### Mandatory Safety Rules
- **NEVER** modify code you haven't read and understood
- **ALWAYS** backup before any changes (create *.backup files)
- **ALWAYS** test after modifications
- **MUST** follow 9-step procedure for ANY code change
- **STOP** immediately when tests fail

### Surgical Fixes Only
- Make MINIMUM changes to fix the issue
- Preserve existing functionality
- Only refactor with explicit permission
- Test edge cases after any change

## ⛔ СТРОГО ЗАПРЕЩЕНО

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

## 📋 ОБЯЗАТЕЛЬНАЯ 9-ШАГОВАЯ ПРОЦЕДУРА

For ANY code modification, follow these steps EXACTLY:

1. **Read PROJECT.llm** → `cat PROJECT.llm`
2. **Find target module** → Use efficient search
3. **Read module CONTEXT.llm** → `cat path/to/module/CONTEXT.llm`
4. **Analyze current code** → Read and understand
5. **Create baseline tests** → `python .claude/baseline.py module_name`
6. **Run baseline tests** → Must see "✅ Baseline established"
7. **Make minimal changes** → Edit ONLY what's needed
8. **Test again** → If failed: STOP and wait for user
9. **Update contexts** → Run update if needed

## ⚡ БЫСТРЫЕ КОМАНДЫ

Type exactly (case-sensitive):
- `u` or `update` → 🚀 Universal update (does EVERYTHING)
- `c` or `check` → Quick health check
- `s` or `structure` → Show PROJECT.llm structure
- `h` or `help` → Show all commands
- `validate` → Run full validation
- `baseline <module>` → Create baseline tests
- `test-all` → Run all baseline tests
- `deps` → Show dependency graph
- `ctx init` → Initialize CONTEXT.llm files
- `ctx update` → Update existing CONTEXT.llm
- `cc` or `cleancode` → Interactive dead code cleanup

## 🔧 ПРАВИЛА ОКРУЖЕНИЯ

### Python Environment
- **ALWAYS** use `python3` (never `python`)
- **ALWAYS** use `pip3` (never `pip`)
- **ALWAYS** work in virtual environment `venv`

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

## 📍 КОНТРОЛЬНЫЕ ТОЧКИ

✓ Before ANY code change → Read PROJECT.llm
✓ Before module edit → Read module's CONTEXT.llm
✓ Before making changes → Create baseline tests
✓ After changes → Run ALL tests
✓ If tests fail → STOP and show options
✓ After completion → Update all contexts

## 🎯 ПРИНЦИПЫ РАЗРАБОТКИ

1. **English only** - All code, variables, functions, documentation
2. **No comments** in code - Use descriptive names and CONTEXT.llm
3. **Test before change** - Baseline tests are mandatory
4. **Small commits** - One logical change at a time
5. **Update contexts** - Keep CONTEXT.llm and PROJECT.llm current
6. **Fail fast** - Stop immediately when tests fail
7. **Explicit is better** - Clear function names over clever code

## 📊 COMMAND MAPPINGS

All commands check for venv and use it if available:

```bash
# When user types exactly:
h, help     → venv/bin/python3 .claude/help.py
u, update   → venv/bin/python3 .claude/update.py
c, check    → venv/bin/python3 .claude/check.py
s, structure → cat PROJECT.llm
validate    → venv/bin/python3 .claude/validation.py
procedure   → venv/bin/python3 .claude/validation.py --check-procedure
baseline X  → venv/bin/python3 .claude/baseline.py X
test-all    → venv/bin/python3 -m pytest test_baseline_*.py -v
deps        → cat PROJECT.llm | grep -A20 "@dependency_graph"
project     → cat PROJECT.llm
ctx init    → venv/bin/python3 .claude/context.py init
ctx update  → venv/bin/python3 .claude/context.py update
ctx scan    → venv/bin/python3 .claude/context.py scan
cc, cleancode → venv/bin/python3 .claude/cleancode.py --interactive
```

## 🔄 ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ

@.claude/prompt.md  # Detailed system prompt
@.claude/format.md  # Project-specific format

---
*Claude Context Box v{{ version }} - Updated: {{ timestamp }}*