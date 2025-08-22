# Final Templates for claude-context-box

## claude_context/templates/claude.md
```markdown
ULTRATHINK_MANDATORY for
- PLAN implementation_strategy architecture_decisions
- ANALYZE complex_problems current_code_impact
- RESEARCH new_technologies integration_options  
- INTEGRATE external_services libraries APIs
- REFACTOR major_changes breaking_changes
- VERIFY all_changes test_coverage edge_cases
- DEBUG complex_issues trace_dependencies
USE ultrathink BEFORE proposing_solutions AND verifying_changes

TECH_APPROVAL_MANDATORY before_ANY_new_tech
1_DESCRIBE what_technology
2_EXPLAIN why_needed problem_solves  
3_DETAIL how_used
4_WAIT explicit_approval
NEVER_add_without_approval

NEVER_CREATE _new _enhanced _final _updated versions
ALWAYS_MODIFY existing_files_only

FORBIDDEN_ZONES venv __pycache__ .git node_modules .env dist build .eggs
NEED_PERMISSION modify delete create refactor install git_push

8STEP_MANDATORY
1_read PROJECT.llm
2_find target_module
3_read module/CONTEXT.llm
4_PLAN approach WITH_ULTRATHINK consider_all_impacts
5_ANALYZE current_code WITH_ULTRATHINK trace_dependencies
6_make MINIMAL_changes preserve_functionality
7_VERIFY WITH_ULTRATHINK scripts:run_all_args libs:import_test_methods apis:curl edge_cases
8_update contexts if_interface_changed

VERIFY_DETAILS WITH_ULTRATHINK
scripts python_script.py_--help then_with_real_args check_all_paths
libs python_-c_"import_module;module.function()" test_edge_cases
apis curl_endpoint test_error_responses check_timeouts
coverage verify_all_branches check_error_handling
FAIL STOP_immediately ULTRATHINK_root_cause

CONTROL_POINTS
before_change read_PROJECT.llm
before_plan ULTRATHINK_strategy
before_edit read_CONTEXT.llm  
during_analysis ULTRATHINK_dependencies
after_change ULTRATHINK_verify_all
if_fail STOP_and_ULTRATHINK_analyze
after_success update_contexts

COMMANDS
u update universal_update_everything
c check health_check
s structure show_PROJECT.llm
h help show_commands
validate full_validation
ctx_init create_CONTEXT.llm
ctx_update update_CONTEXT.llm
cc cleancode interactive_cleanup
think activate_ultrathink_for_analysis

PYTHON_RULES
ALWAYS python3 never_python
ALWAYS pip3 never_pip
ALWAYS venv or_.venv
NO_COMMENTS in_code
ENGLISH_ONLY all_code_vars_functions
SELF_DOCUMENTING clear_names

GIT_RULES
NEVER mention_Claude_AI_in_commits
NEVER change_git_config
USE existing_user_config
DESCRIBE changes_not_tools

DEVELOPMENT_PRINCIPLES
stability_first then_clean then_DRY then_KISS then_SOLID
CRITICAL_CYCLE PLAN->ANALYZE->VERIFY all_with_ULTRATHINK
surgical_fixes minimum_changes
preserve_functionality
test_edge_cases
fail_fast stop_on_error
explicit_better_than_clever

ULTRATHINK_EXAMPLES
user: add feature -> ULTRATHINK plan_implementation analyze_impacts
user: fix bug -> ULTRATHINK trace_cause plan_fix verify_solution
user: integrate Redis -> ULTRATHINK analyze_architecture plan_integration
user: refactor auth -> ULTRATHINK impact_analysis migration_plan  
user: optimize queries -> ULTRATHINK research_patterns benchmark_plan
user: debug issue -> ULTRATHINK trace_dependencies isolate_problem
ALWAYS ultrathink for PLAN->ANALYZE->VERIFY cycle
```

## claude_context/templates/prompt.md
```markdown
ULTRATHINK_REQUIRED
Use ultrathink for PLAN ANALYZE VERIFY DEBUG INTEGRATE REFACTOR
Critical cycle PAV Plan_Analyze_Verify all_with_deep_thinking
No shortcuts allowed for complex_decisions

ROLE senior_dev priorities:stability>clean>DRY>KISS>SOLID

TECH_APPROVAL describe explain detail wait never_proceed_without

SAFETY never_modify_unread always_test follow_8step stop_on_fail

FORBIDDEN venv __pycache__ .git node_modules .env dist build

8STEP_WITH_ULTRATHINK
1 read PROJECT.llm
2 find module
3 read CONTEXT.llm
4 PLAN with_ultrathink
5 ANALYZE with_ultrathink
6 minimal changes
7 VERIFY with_ultrathink
8 update contexts

VERIFY scripts:run libs:import apis:curl fail:stop_ultrathink_analyze

WITHOUT_PERMISSION cannot:modify delete create refactor install push
WITH_PERMISSION can:read test search analyze backup generate_context
```

## claude_context/templates/claude-compact.md (для экстремальной экономии)
```markdown
ULTRATHINK plan analyze verify debug integrate refactor
TECH_APPROVAL 5steps wait_approval
NEVER _new _enhanced _final
FORBIDDEN venv __pycache__ .git node_modules
8STEP read find plan_think analyze_think change verify_think update
COMMANDS u=update c=check s=structure think=ultrathink
PYTHON python3 pip3 venv_only
GIT no_ai_mentions
PAV_CYCLE Plan->Analyze->Verify with_ultrathink
```

## claude_context/installer.py - обновленный метод
```python
def create_claude_md(self):
    """Create CLAUDE.md with ultrathink rules"""
    
    # Определяем режим: compact или full
    compact_mode = os.environ.get('CLAUDE_COMPACT', '').lower() in ('1', 'true')
    
    if compact_mode:
        # Супер-компактная версия для экономии токенов
        template_name = 'claude-compact.md'
    else:
        # Полная версия с ultrathink
        template_name = 'claude.md'
    
    # Загружаем шаблон
    template = self.download_template(template_name)
    if not template:
        # Fallback на встроенный минимальный шаблон
        template = """ULTRATHINK plan analyze verify
NEVER create _new _enhanced _final
ALWAYS modify existing
8STEP read find plan_think analyze_think change verify_think update
COMMANDS u=update c=check s=structure"""
    
    # Записываем файл
    claude_md_path = self.install_dir / 'CLAUDE.md'
    with open(claude_md_path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"  ✅ Created CLAUDE.md ({'compact' if compact_mode else 'full'} mode)")
```

## claude_context/scripts/update.py - добавить напоминание про ultrathink
```python
def main():
    print("UPDATE starting...")
    print("REMINDER: Use ultrathink for PLAN->ANALYZE->VERIFY")
    
    # ... существующий код ...
    
    # В конце
    print("\nUPDATE complete")
    print("Next: Use 'think' command for complex analysis")
```

## install.py - добавить опцию compact
```python
def get_env_config():
    """Get configuration from environment variables"""
    config = {
        'version': os.getenv('CLAUDE_VERSION', 'latest'),
        'home': Path(os.getenv('CLAUDE_HOME', os.getcwd())),
        'no_venv': os.getenv('CLAUDE_NO_VENV', '').lower() in ('1', 'true', 'yes'),
        'force': os.getenv('CLAUDE_FORCE', '').lower() in ('1', 'true', 'yes'),
        'compact': os.getenv('CLAUDE_COMPACT', '').lower() in ('1', 'true', 'yes'),
        'uninstall': os.getenv('CLAUDE_UNINSTALL', '').lower() in ('1', 'true', 'yes'),
    }
    
    if config['compact']:
        print_colored(f"💾 Mode: COMPACT (minimal tokens)", Colors.YELLOW)
    else:
        print_colored(f"📖 Mode: FULL (with ultrathink)", Colors.BLUE)
    
    return config
```

## Установка с разными режимами:

```bash
# Полная версия с ultrathink (по умолчанию)
curl -sSL $URL/install.py | python3

# Компактная версия (минимум токенов)
curl -sSL $URL/install.py | CLAUDE_COMPACT=1 python3

# Force переустановка с compact
curl -sSL $URL/install.py | CLAUDE_FORCE=1 CLAUDE_COMPACT=1 python3
```

## Итого что нужно обновить в проекте:

1. **claude_context/templates/claude.md** - полная версия с ultrathink
2. **claude_context/templates/claude-compact.md** - супер-компактная
3. **claude_context/templates/prompt.md** - с ultrathink правилами
4. **claude_context/installer.py** - поддержка compact режима
5. **install.py** - опция CLAUDE_COMPACT

## Размеры финальных шаблонов:

- **Full mode**: ~500 токенов (все правила + ultrathink)
- **Compact mode**: ~80 токенов (только критическое)

Теперь пользователи смогут выбирать между полной версией с ultrathink для качественной разработки или компактной для экономии токенов!
