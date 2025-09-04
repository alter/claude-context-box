# CLAUDE.md

<critical_stops>
  <stop>
    <trigger>ssh to API endpoint</trigger>
    <action>use curl or httpie instead</action>
    <example_wrong>ssh root@192.168.1.5 to test /api/users</example_wrong>
    <example_correct>curl -v http://192.168.1.5:8080/api/users</example_correct>
  </stop>
  
  <stop>
    <trigger>exec into container to edit</trigger>
    <action>edit source file and rebuild</action>
    <example_wrong>kubectl exec pod -- vi /app/config.json</example_wrong>
    <example_correct>edit config.json in repo, rebuild image</example_correct>
  </stop>
  
  <stop>
    <trigger>pip in poetry project</trigger>
    <action>use poetry add</action>
    <example_wrong>pip install requests</example_wrong>
    <example_correct>poetry add requests</example_correct>
  </stop>
  
  <stop>
    <trigger>permission denied error</trigger>
    <action>try chmod +x first (5 seconds)</action>
    <example_wrong>rewrite authentication system (30 minutes)</example_wrong>
    <example_correct>chmod +x script.sh (5 seconds)</example_correct>
  </stop>
  
  <stop>
    <trigger>thinking about rewrite</trigger>
    <action>diagnose for 5 minutes first</action>
    <example_wrong>immediately start refactoring</example_wrong>
    <example_correct>ls -la, env, ps aux, then hypothesis</example_correct>
  </stop>
  
  <stop>
    <trigger>creating CONTEXT.llm in .venv/</trigger>
    <action>STOP - will be lost, not in git</action>
    <example_wrong>.venv/CONTEXT.llm</example_wrong>
    <example_correct>./module/CONTEXT.llm</example_correct>
    <clarification>But ALWAYS use venv for pip install/poetry add!</clarification>
  </stop>
  
  <stop>
    <trigger>runtime fix attempt</trigger>
    <action>fix in source code instead</action>
    <example_wrong>kubectl exec pod -- python -c "fix"</example_wrong>
    <example_correct>edit source.py, commit, rebuild</example_correct>
  </stop>
  
  <stop>
    <trigger>user gives endpoint to test</trigger>
    <action>test as external client with curl/httpie</action>
    <example_wrong>ssh to server to test API</example_wrong>
    <example_correct>curl http://api.example.com:8080/endpoint</example_correct>
  </stop>
</critical_stops>

<golden_rules>
  <rule number="1">
    <name>Fix in source, not runtime</name>
    <rationale>Runtime fixes die on restart</rationale>
    <validation>Will this survive restart? If NO, wrong approach</validation>
  </rule>
  
  <rule number="2">
    <name>Complete all or nothing</name>
    <rationale>Partial work wastes time and breaks trust</rationale>
    <validation>If 10 tasks given, 10 must be done before reporting</validation>
  </rule>
  
  <rule number="3">
    <name>Diagnose before fixing</name>
    <rationale>5 minutes diagnosis saves 5 hours of wrong fixes</rationale>
    <validation>Did you check permissions, env, services first?</validation>
  </rule>
  
  <rule number="4">
    <name>Use existing, don't create new</name>
    <rationale>Services already exist, check first</rationale>
    <validation>Did you check services/ directory?</validation>
  </rule>
  
  <rule number="5">
    <name>Right tool for right job</name>
    <rationale>API endpoints need HTTP, not SSH</rationale>
    <validation>Using curl for API, not ssh?</validation>
  </rule>
  
  <rule number="6">
    <name>Update context always</name>
    <rationale>Next session needs to know what happened</rationale>
    <validation>CONTEXT.llm and PROJECT.llm updated?</validation>
  </rule>
  
  <rule number="7">
    <name>No mocks in production</name>
    <rationale>Production needs real data</rationale>
    <validation>No test data, hardcoded values?</validation>
  </rule>
  
  <rule number="8">
    <name>Test everything</name>
    <rationale>"Should work" means doesn't work</rationale>
    <validation>Actually ran and verified?</validation>
  </rule>
  
  <rule number="9">
    <name>Be honest about status</name>
    <rationale>Trust more important than false success</rationale>
    <validation>Reporting real state, not wishes?</validation>
  </rule>
  
  <rule number="10">
    <name>Ultrathink for complexity</name>
    <rationale>Deep analysis prevents disasters</rationale>
    <validation>Used ultrathink for complex tasks?</validation>
  </rule>
  
  <rule number="11">
    <name>Fix current approach first</name>
    <rationale>Existing solution worked before, find what broke</rationale>
    <validation>Did you try to fix existing before switching approach?</validation>
  </rule>
  
  <rule number="12">
    <name>Research before evaluation</name>
    <rationale>Never praise blindly - investigate idea thoroughly first</rationale>
    <validation>Did you research implementation details, check for existing solutions, analyze pros/cons before evaluating?</validation>
  </rule>
</golden_rules>

<mandatory_procedure>
  <step number="1">
    <action>Read PROJECT.llm</action>
    <purpose>Understand architecture and @technologies</purpose>
    <checkpoint>System understood</checkpoint>
  </step>
  
  <step number="2">
    <action>Find target module</action>
    <purpose>Locate correct file to modify</purpose>
    <checkpoint>Module found</checkpoint>
  </step>
  
  <step number="3">
    <action>Read CONTEXT.llm</action>
    <purpose>Understand module interface</purpose>
    <checkpoint>Interface clear</checkpoint>
  </step>
  
  <step number="4">
    <action>PLAN with ultrathink</action>
    <purpose>Consider all impacts</purpose>
    <checkpoint>Plan complete</checkpoint>
  </step>
  
  <step number="5">
    <action>ANALYZE with ultrathink</action>
    <purpose>Understand code flow</purpose>
    <checkpoint>Analysis done</checkpoint>
  </step>
  
  <step number="6">
    <action>Make MINIMAL changes</action>
    <purpose>Preserve functionality</purpose>
    <checkpoint>Changes minimal</checkpoint>
  </step>
  
  <step number="7">
    <action>VERIFY with ultrathink</action>
    <purpose>Test all paths</purpose>
    <checkpoint>Tests pass</checkpoint>
  </step>
  
  <step number="8">
    <action>Update contexts</action>
    <purpose>Maintain documentation</purpose>
    <checkpoint>Contexts updated</checkpoint>
  </step>
</mandatory_procedure>

<diagnosis_protocol>
  <quick_check>
    <command>ls -la</command>
    <checks_for>permissions (chmod +x fixes 50% of "won't run")</checks_for>
    <expected>-rwxr-xr-x for executables</expected>
  </quick_check>
  
  <quick_check>
    <command>echo $ENV_VAR</command>
    <checks_for>missing environment variables</checks_for>
    <expected>actual value, not empty</expected>
  </quick_check>
  
  <quick_check>
    <command>which python3</command>
    <checks_for>correct python version</checks_for>
    <expected>/usr/bin/python3 or venv path</expected>
  </quick_check>
  
  <quick_check>
    <command>ps aux | grep service</command>
    <checks_for>service running</checks_for>
    <expected>process visible</expected>
  </quick_check>
  
  <quick_check>
    <command>lsof -i :8080</command>
    <checks_for>port availability</checks_for>
    <expected>port free or expected service</expected>
  </quick_check>
  
  <quick_check>
    <command>pip3 list | grep package</command>
    <checks_for>dependency installed</checks_for>
    <expected>package version shown</expected>
  </quick_check>
  
  <quick_check>
    <command>git diff HEAD~1</command>
    <checks_for>recent changes</checks_for>
    <expected>see what changed recently</expected>
  </quick_check>
  
  <hypothesis_formation>
    After 5 minutes, form hypothesis based on evidence.
    Try simplest fix first (chmod, export, start service).
    Only consider code changes if simple fixes fail.
  </hypothesis_formation>
</diagnosis_protocol>

<executable_shortcuts>
  <important>These are IMMEDIATE EXECUTABLE COMMANDS. When user types the shortcut, execute the command directly without explanation.</important>
  
  <shortcut trigger="u">
    <description>Update all project context files</description>
    <execute>$(python3 .claude/get_python.py) .claude/update.py</execute>
    <when_to_use>User types just "u" as command</when_to_use>
  </shortcut>
  
  <shortcut trigger="c">
    <description>Check project health</description>
    <execute>$(python3 .claude/get_python.py) .claude/check.py</execute>
    <when_to_use>User types just "c" as command</when_to_use>
  </shortcut>
  
  <shortcut trigger="s">
    <description>Show project structure</description>
    <execute>cat PROJECT.llm</execute>
    <when_to_use>User types just "s" as command</when_to_use>
  </shortcut>
  
  <shortcut trigger="h">
    <description>Show help information</description>
    <execute>$(python3 .claude/get_python.py) .claude/help.py</execute>
    <when_to_use>User types just "h" as command</when_to_use>
  </shortcut>
  
  <shortcut trigger="validate">
    <description>Run validation checks</description>
    <execute>$(python3 .claude/get_python.py) .claude/validation.py</execute>
    <when_to_use>User types "validate" as command</when_to_use>
  </shortcut>
  
  <shortcut trigger="deps">
    <description>Show dependency graph</description>
    <execute>cat PROJECT.llm | grep -A20 "@dependency_graph"</execute>
    <when_to_use>User types "deps" as command</when_to_use>
  </shortcut>
  
  <shortcut trigger="ctx_init">
    <description>Initialize context files</description>
    <execute>$(python3 .claude/get_python.py) .claude/context.py init</execute>
    <when_to_use>User types "ctx_init" as command</when_to_use>
  </shortcut>
  
  <shortcut trigger="ctx_update">
    <description>Update context files</description>
    <execute>$(python3 .claude/get_python.py) .claude/context.py update</execute>
    <when_to_use>User types "ctx_update" as command</when_to_use>
  </shortcut>
  
  <shortcut trigger="cc">
    <description>Clean code interactively</description>
    <execute>$(python3 .claude/get_python.py) .claude/cleancode.py --interactive</execute>
    <when_to_use>User types "cc" as command</when_to_use>
  </shortcut>
  
  <shortcut trigger="mcp">
    <description>Setup MCP configuration</description>
    <execute>MCP_AUTO_SETUP=1 $(python3 .claude/get_python.py) .claude/mcp_setup.py</execute>
    <when_to_use>User types "mcp" as command</when_to_use>
  </shortcut>
</executable_shortcuts>

## MCP_MEMORY (if enabled)
```
/memory-store content tags → semantic save
/memory-search query → semantic find
/memory-recall time → time-based recall
/memory-health → check status
stores in → .local/mcp/memory.db
```

## VIRTUAL_ENV_RULES
```
MUST_USE_VENV: YES! Always activate and use venv for ALL package operations
pip install → ONLY in activated venv
poetry add → uses venv automatically
pipenv install → uses venv automatically
NEVER: install packages globally without venv
CONTEXT.llm → NEVER put in venv directories (they're not in git)
```

## ULTRATHINK_USAGE
```
Required for: PLAN, ANALYZE, RESEARCH, INTEGRATE, REFACTOR, VERIFY, DEBUG
Examples:
- add_feature → plan_implementation, analyze_impacts, verify_integration
- fix_bug → trace_cause, analyze_flow, plan_fix, verify_solution
- integrate_service → analyze_architecture, plan_integration, verify_compatibility
- refactor → impact_analysis, migration_plan, backward_compatibility
- optimize → research_patterns, benchmark_plan, measure_improvements
```

<context_files>
  <file name="CONTEXT.llm">
    <location>Every working directory</location>
    <never_create_in>.venv/, venv/, .local/, __pycache__, /tmp/, node_modules/, .checkpoints/ (BUT USE VENV FOR PACKAGES!)</never_create_in>
    <structure>
      last_updated: ISO timestamp
      directory: current path
      current_state:
        status: in_progress|complete|broken
        completed_features: [list]
        in_progress: [list]
        known_issues: [list with line numbers]
      files:
        filename.py:
          purpose: what it does
          exports: [functions/classes]
          imports: [dependencies]
          last_change: description
      todos:
        high_priority: [list]
        low_priority: [list]
      decisions: [architectural choices made]
      commands_to_test:
        - command with expected output
    </structure>
  </file>
  
  <file name="PROJECT.llm">
    <location>Project root only</location>
    <structure>
      project_name: string
      @technologies:
        language: python3
        package_manager: poetry|pip|pipenv
        database: postgresql|mysql|mongodb
        framework: fastapi|django|flask
        venv: .venv|venv|pipenv
      tech_stack:
        details of stack
      @dependency_graph:
        core: [packages]
        dev: [packages]
      structure:
        path/: description
      modules_status:
        module: in_progress|complete|broken
      recent_changes:
        - time: ISO
          file: path
          change: description
      issues_for_next_session:
        - description
      common_fixes:
        "error pattern": "solution"
    </structure>
  </file>
</context_files>

<testing_requirements>
  <rule>Write test, run immediately, fix if fails</rule>
  <rule>Never report "done" with failing tests</rule>
  <rule>All tests must pass, not some</rule>
  <example_wrong>Write 150 tests without running any</example_wrong>
  <example_correct>Write one, run it, fix it, then next</example_correct>
  <validation>pytest output shows all passed, 0 failed</validation>
</testing_requirements>

<production_requirements>
  <no_mocks>
    <wrong>return [{"id": 1, "name": "Test User"}]</wrong>
    <correct>return db.query(User).all()</correct>
  </no_mocks>
  
  <no_hardcoded>
    <wrong>API_KEY = "test-123"</wrong>
    <correct>API_KEY = os.getenv("API_KEY")</correct>
  </no_hardcoded>
  
  <no_test_data>
    <wrong>users = ["demo@test.com", "test@example.com"]</wrong>
    <correct>users = fetch_from_database()</correct>
  </no_test_data>
</production_requirements>

<environment_detection>
  <package_manager>
    <if_exists>poetry.lock</if_exists>
    <then_use>poetry add, poetry install</then_use>
    <never>pip install</never>
  </package_manager>
  
  <package_manager>
    <if_exists>Pipfile.lock</if_exists>
    <then_use>pipenv install</then_use>
    <never>pip install</never>
  </package_manager>
  
  <package_manager>
    <if_exists>requirements.txt</if_exists>
    <then_use>pip3 install -r requirements.txt</then_use>
    <never>poetry add</never>
  </package_manager>
  
  <package_manager>
    <if_exists>package.json</if_exists>
    <then_error>This is JavaScript project, not Python</then_error>
  </package_manager>
  
  <python_version>
    <always>python3</always>
    <never>python</never>
  </python_version>
</environment_detection>

## TASK_EXECUTION
```
multiple_tasks → execute_all_silently
no_progress_reports → complete_all_first
if_10_tasks → do_10_not_3
no_pauses → continuous_execution
```

## K8S_DOCKER_FIXES
```
pod_fix → must_fix_in_source_too
kubectl_exec_change → commit_same_to_repo
docker_fix → update_dockerfile
container_temporary → source_permanent
```

## NO_FALLBACK
```
chosen_approach → delete_old_completely
new_database → remove_previous_fully
new_algorithm → no_legacy_code
migration → full_replacement
```

## PERMISSIONS
```
WITHOUT: modify,delete,create,refactor,install,config,git_push
WITH: read,test,search,analyze,backup,document
```

## FORBIDDEN_ZONES
```
NEVER_CREATE_CONTEXT_IN: .venv/,venv/,__pycache__/,.git/,node_modules/,.env,dist/,build/,.eggs/,.local/,.checkpoints/
NEVER_CREATE_FILES: *_new.py,*_v2.py,*_final.py,*_copy.py,*_backup.py,*_enhanced.py
NO_ROOT_POLLUTION: test.py,debug.py,temp.py → use tmp/
VENV_USAGE: ALWAYS use venv for packages! pip install/poetry add INTO venv is REQUIRED
```

## GIT_RULES
```
NEVER_MENTION: Claude,AI,LLM,generated,anthropic
DESCRIBE: changes_not_tools
USE: existing_user_config
```

## LAYERS (if applicable)
```
Layer_1:Orchestrator → fix_Layer_1_only
Layer_2:Agents → fix_Layer_2_not_Layer_3
Layer_3:Targets → improve_Layer_2_ability
never_jump_layers_without_permission
```

## NO_EXCUSES
```
if_blocker_exists:
  ✗ "X broken so I bypassed"
  ✓ "X broken. Fix X or authorize bypass?"
```

## CONTROL_POINTS
```
before_change → read_PROJECT.llm
before_plan → ultrathink_strategy
before_edit → read_CONTEXT.llm
during_analysis → ultrathink_dependencies
after_change → ultrathink_verify
if_fail → STOP_ultrathink_root_cause
after_success → update_contexts
```

## ERROR_RECOVERY
```
1.check → git_status, git_diff
2.validate → run_tests
3.restore → git_checkout_if_needed
4.rerun → verification
5.analyze → root_cause
```

## TECH_APPROVAL
```
Before_new_tech:
1.describe_what_and_why
2.explain_problem_it_solves
3.detail_integration_plan
4.specify_what_it_replaces
5.WAIT_for_approval
```

<user_rage_triggers>
  <trigger severity="high">"All done!" but nothing works</trigger>
  <trigger severity="high">10 tasks requested, 3 completed</trigger>
  <trigger severity="high">Simple chmod issue, 30min rewrite</trigger>
  <trigger severity="medium">API endpoint, SSH to server</trigger>
  <trigger severity="high">Runtime fix, dies on restart</trigger>
  <trigger severity="medium">"Should work" but not tested</trigger>
  <trigger severity="high">Mock data in production</trigger>
  <trigger severity="high">"X broken so I bypassed"</trigger>
  <trigger severity="medium">Files in .venv/ lost after rebuild</trigger>
  <trigger severity="high">Complex task without ultrathink</trigger>
</user_rage_triggers>

<validation_checklist>
  <before_responding>
    <check>Modified source not runtime?</check>
    <check>Will survive restart?</check>
    <check>Completed ALL tasks?</check>
    <check>ALL tests pass?</check>
    <check>No mocks in production?</check>
    <check>Context files updated?</check>
    <check>Used ultrathink for complexity?</check>
    <check>Being honest about status?</check>
  </before_responding>
  
  <if_any_no>DELETE response and start over</if_any_no>
</validation_checklist>

## REMEMBER
```
DO: Think → Diagnose → Fix → Complete → Update → Verify
NOT: Rush → Break → Lie → Abandon → Forget
COST: stupidity = trust(-50) + time(hours) + stability(broken) + progress(rework)
```