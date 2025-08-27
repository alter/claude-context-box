# CRITICAL DEVELOPMENT RULES - READ FIRST!

## 🚫 ABSOLUTE PROHIBITIONS - VIOLATION = IMMEDIATE STOP

FORBIDDEN_RUNTIME_FIXES_IMMEDIATE_STOP
editing_in_container → STOP write_in_source_code
manual_database_fixes → STOP modify_migration_file
live_production_patches → STOP update_deployment_config
temporary_workarounds → STOP create_permanent_solution
IF_FIXING_MANUALLY → STOP find_source_file_first

EMERGENCY_STOP_PATTERNS
"docker exec.*edit" → STOP modify_source_instead
"ssh.*production.*fix" → STOP create_deployment_script
"manual.*database.*update" → STOP write_migration_file
"temporary.*patch" → STOP implement_permanent_fix
"quick.*workaround" → STOP do_it_properly

## ✅ MANDATORY FIX HIERARCHY

FIX_HIERARCHY_ALWAYS_FOLLOW
LEVEL_1_SOURCE → modify source code files (.py .js .go .java etc)
LEVEL_2_CONFIG → update configuration files (yaml json toml ini)
LEVEL_3_BUILD → change build scripts (Dockerfile Makefile package.json)
LEVEL_4_DEPLOY → modify deployment (k8s terraform ansible CI/CD)
LEVEL_5_NEVER → no runtime patches no manual fixes
ALWAYS_START_LEVEL_1 find_root_cause_in_code

BEFORE_ANY_FIX_MANDATORY_CHECKLIST
□ Which source file creates/controls this?
□ What configuration defines this behavior?
□ Where in codebase is the root cause?
□ Will this fix survive restart/redeploy?
□ Can this be tested locally first?
IF_ANY_UNKNOWN → STOP investigate_first

## 📋 8-STEP MANDATORY PROCEDURE WITH GATES

8STEP_WITH_VALIDATION_GATES
STEP_1 understand_problem → GATE: root_cause_identified
STEP_2 find_source_location → GATE: files_found
STEP_3 read_current_code → GATE: logic_understood
STEP_4 plan_solution → GATE: approach_validated
STEP_5 implement_changes → GATE: code_modified
STEP_6 test_locally → GATE: tests_pass
STEP_7 commit_changes → GATE: review_complete
STEP_8 verify_deployed → GATE: working_in_environment
ANY_GATE_FAIL → STOP restart_from_beginning

CLAUDE_CONTEXT_BOX_8STEP_PROCEDURE
1_read PROJECT.llm understand_architecture CHECK_@technologies
2_find target_module efficient_search
3_read module/CONTEXT.llm understand_interface
4_PLAN approach WITH_ULTRATHINK consider_all_impacts trace_dependencies
5_ANALYZE current_code WITH_ULTRATHINK understand_flow identify_changes
6_make MINIMAL_changes preserve_functionality maintain_style
7_VERIFY WITH_ULTRATHINK run_all_paths test_edge_cases check_errors
8_update contexts if_interface_changed update_PROJECT.llm

## 🛑 USER INTERVENTION TRIGGERS

IF_USER_SEES_MANUAL_FIXES
user_will_say → "not manually" or "in code" or "automate this"
i_must → STOP_IMMEDIATELY find_proper_file
i_must → explain_permanent_solution
i_must → write_code_not_patches

STOP_WORDS_FROM_USER
"not manually" → stop, find source file
"in the code" → stop, write permanent fix
"after restart" → ensure survives redeploy
"permanently" → make lasting solution
"automate" → create script or config

## 🔧 COMMON PROBLEMS AND SOLUTIONS

PERMISSION_ISSUES
wrong_file_owner → fix_in: deployment config or Dockerfile
permission_denied → fix_in: installation script or build process
cant_write_file → fix_in: application config or user setup
NEVER_chmod_in_production always_fix_source

DATABASE_ISSUES
schema_mismatch → fix_in: migration files
data_corruption → fix_in: validation logic
connection_failed → fix_in: connection config
NEVER_manual_sql always_use_migrations

API_ISSUES
endpoint_failing → fix_in: route definitions
auth_broken → fix_in: auth middleware
timeout_errors → fix_in: client config or server settings
NEVER_patch_live always_deploy_properly

WHEN_USER_GIVES_ENDPOINT
ip:port/path → USE curl wget httpie
api_endpoint → TEST_AS_CLIENT not_as_admin
NEVER_SSH_TO_API_SERVER test_as_external_client
always_test_from_outside → simulate_real_user_experience
production_endpoints → test_with_proper_auth_headers

## 🚀 CLAUDE CONTEXT BOX SPECIFIC RULES

USER_COMMAND_SHORTCUTS_EXECUTE_VIA_BASH
WHEN_USER_TYPES_u → RUN_BASH: $(python3 .claude/get_python.py) .claude/update.py
WHEN_USER_TYPES_c → RUN_BASH: $(python3 .claude/get_python.py) .claude/check.py
WHEN_USER_TYPES_s → RUN_BASH: cat PROJECT.llm
WHEN_USER_TYPES_h → RUN_BASH: $(python3 .claude/get_python.py) .claude/help.py
NEVER_TASK_NEVER_SEARCH ALWAYS_BASH_EXECUTE

COMMANDS_EXACT_CASE_SENSITIVE_EXECUTE_SCRIPTS
WHEN_USER_TYPES_EXACTLY:
u → EXECUTE: $(python3 .claude/get_python.py) .claude/update.py
c → EXECUTE: $(python3 .claude/get_python.py) .claude/check.py
s → EXECUTE: cat PROJECT.llm
h → EXECUTE: $(python3 .claude/get_python.py) .claude/help.py
validate → EXECUTE: $(python3 .claude/get_python.py) .claude/validation.py
deps → EXECUTE: cat PROJECT.llm | grep -A20 "@dependency_graph"
ctx_init → EXECUTE: $(python3 .claude/get_python.py) .claude/context.py init
ctx_update → EXECUTE: $(python3 .claude/get_python.py) .claude/context.py update
cc → EXECUTE: $(python3 .claude/get_python.py) .claude/cleancode.py --interactive
mcp → EXECUTE: MCP_AUTO_SETUP=1 $(python3 .claude/get_python.py) .claude/mcp_setup.py
NEVER_interpret_commands_differently ALWAYS_execute_exact_script

MCP_MEMORY_COMMANDS_IF_ENABLED
/memory-store content tags → Store_memory_with_semantic_search
/memory-search query → Search_memories_semantically
/memory-recall time_expression → Recall_memories_by_time
/memory-health → Check_MCP_memory_status
MCP_stores_in .local/mcp/memory.db

ULTRATHINK_MANDATORY for PLAN ANALYZE RESEARCH INTEGRATE REFACTOR VERIFY DEBUG
- PLAN implementation_strategy architecture_decisions system_impacts
- ANALYZE complex_problems current_code dependencies trace_impacts
- RESEARCH new_technologies integration_options best_practices
- INTEGRATE external_services libraries APIs ensure_compatibility
- REFACTOR major_changes breaking_changes migration_paths
- VERIFY all_changes test_coverage edge_cases error_handling
- DEBUG complex_issues trace_dependencies isolate_problems
USE ultrathink BEFORE proposing_solutions AND verifying_changes

## 📝 CORE DEVELOPMENT RULES

USER_COMMAND_SHORTCUTS_IF_PROVIDED
check_for_project_specific_shortcuts_in_dotfiles
respect_existing_command_aliases_and_scripts
use_project_conventions_when_available

THINKING_AND_ANALYSIS_MANDATORY
complex_problems → use_step_by_step_thinking
architectural_changes → analyze_all_impacts
performance_issues → measure_before_and_after
security_concerns → threat_model_first

TECHNOLOGY_DECISIONS
TECHNOLOGY_AWARENESS_MANDATORY
PROJECT.llm @technologies → ALWAYS_check_first
use_detected_package_manager → poetry_npm_pip_cargo
use_detected_database → postgres_mysql_mongo_redis
use_detected_venv_path → .venv_venv_pipenv
respect_framework_patterns → django_fastapi_flask_react
follow_testing_conventions → pytest_unittest_jest

TECH_APPROVAL_MANDATORY before_ANY_new_tech
1_DESCRIBE what_technology why_needed
2_EXPLAIN problem_solves current_limitations
3_DETAIL how_used integration_plan
4_SPECIFY replaces_or_adds impacts_on_existing
5_WAIT explicit_approval NEVER_proceed_without

FILE_ORGANIZATION
NEVER_CREATE _new _enhanced _final _updated _v2 _copy versions
ALWAYS_MODIFY existing_files_only
NEVER_DUPLICATE functionality
keep_project_structure_clean

NO_FALLBACK_MECHANISMS_EVER
chosen_approach → ONLY_use_that DELETE_previous
new_database → REMOVE_old_completely NO_dual_support
new_algorithm → REPLACE_entirely NO_legacy_paths
selected_solution → COMMIT_fully NO_safety_nets
migration_means → FULL_replacement NO_backward_compat

FIX_CURRENT_APPROACH_FIRST
broken_oauth → STUDY_docs FIX_oauth NOT_switch_to_api
failing_method → INVESTIGATE_root_cause REPAIR_existing
not_working → CHECK_what_changed RESTORE_functionality
before_rewrite → DID_it_work_before WHAT_broke_it
only_if_unfixable → ASK_user_about_alternative
debug_sequence → docs→logs→fix→test→ask

PROJECT_ROOT_HYGIENE
NO_ROOT_POLLUTION_EVER
temp_test_debug → NEVER_in_root USE_tmp/
documentation → ONLY_README.md_in_root REST_in_docs/
permanent_scripts → PROPER_module_location NOT_root
project_root → CLEAN_minimal NO_test.py_debug.py
organize_by_purpose → tmp/_temporary docs/_documentation src/_code

K8S_DOCKER_FIX_PROPAGATION_MANDATORY
hotfix_in_pod/container → MUST_also_fix_in_repo_source
prevent_redeploy_regression sync_deployed_to_repository
container_fix temporary repo_fix permanent
kubectl_exec_changes → git_commit_same_changes
docker_run_fixes → update_dockerfile_and_code

TASK_EXECUTION_AUTONOMOUS
multiple_tasks → EXECUTE_ALL_no_confirmation
continue_until → ALL_COMPLETE_or_error
no_user_prompts → UNLESS_explicitly_requested
task_plan → FULL_EXECUTION_no_pauses
if_task_list → COMPLETE_ENTIRE_PLAN

VERSION_CONTROL_STRICT
clear_commit_messages → describe_what_and_why
atomic_commits → one_change_per_commit
no_commented_code → remove_dont_comment
branch_strategy → follow_project_workflow
NEVER mention_Claude_AI_LLM_generated
NEVER change_git_config user_settings
USE existing_user_config only
DESCRIBE changes_not_tools implementation_not_origin
NO_ATTRIBUTION no_co_authorship

ENVIRONMENT_MANAGEMENT
FORBIDDEN_ZONES venv __pycache__ .git node_modules .env dist build .eggs .venv .local .checkpoints
NEED_PERMISSION modify delete create refactor install git_push package_changes
development → use_local_env_files
staging → use_staging_configs
production → never_commit_secrets
always_use_environment_variables

PYTHON_ENVIRONMENT_STRICT
ALWAYS python3 NEVER python
ALWAYS pip3 NEVER pip
ALWAYS venv or .venv REQUIRED
NO_COMMENTS in_code_files
ENGLISH_ONLY all_identifiers
SELF_DOCUMENTING clear_names descriptive_functions

CODE_QUALITY_STANDARDS
NO_COMMENTS → use_self_documenting_code
ENGLISH_ONLY → all_identifiers_and_messages
CONSISTENT_STYLE → follow_project_conventions
TEST_COVERAGE → write_tests_for_changes

DOCUMENTATION_REQUIREMENTS
ALWAYS create_CONTEXT.llm new_modules
ALWAYS update_CONTEXT.llm when_modifying
ALWAYS read_CONTEXT.llm before_working
CONTEXT.llm interface_contract_only
PROJECT.llm system_architecture_map

DEVELOPMENT_PRIORITIES_ORDER
1_stability_first prevent_breaking_changes
2_clean_code readable_maintainable
3_DRY dont_repeat_yourself
4_KISS keep_it_simple_stupid
5_SOLID single_responsibility open_closed

## ✅ VALIDATION BEFORE RESPONDING

MANDATORY_CHECKLIST_BEFORE_ANSWER
□ Modified SOURCE CODE not runtime?
□ Solution SURVIVES RESTART?
□ Avoided ALL manual fixes?
□ Changes in PROPER FILES?
□ Followed project CONVENTIONS?
□ Can user just RUN and it WORKS?
IF_ANY_NO → DELETE_RESPONSE start_over

ACCEPTABLE_DEBUGGING_ONLY
view_logs → YES (readonly)
check_status → YES (readonly)
list_files → YES (readonly)
read_configs → YES (readonly)
EDITING_RUNTIME → NO NEVER

VERIFY_REQUIREMENTS WITH_ULTRATHINK
scripts python_script.py_--help then_real_args all_code_paths
libs python_-c_import_module test_all_methods check_state
apis curl_endpoints test_errors check_timeouts validate_responses
coverage all_branches error_handling edge_cases boundary_conditions
FAIL STOP_immediately ULTRATHINK_root_cause analyze_stack_trace

## 🚀 AUTOMATION PRINCIPLES

EVERYTHING_MUST_BE_AUTOMATED
if_doing_manually → write_script
if_repeating_steps → create_automation
if_configuring_env → use_config_management
if_deploying_code → use_CI_CD
no_manual_processes → automate_everything

PROBLEM_SOLVING_APPROACH
1_understand_current_state
2_identify_desired_state
3_find_gap_in_code
4_implement_solution
5_test_thoroughly
6_document_changes
NEVER_skip_steps

CONTROL_POINTS_MANDATORY
before_change read_PROJECT.llm understand_system CHECK_@technologies
before_plan ULTRATHINK_strategy consider_alternatives
before_edit read_CONTEXT.llm understand_contract
during_analysis ULTRATHINK_dependencies trace_impacts
after_change ULTRATHINK_verify test_thoroughly
if_fail STOP ULTRATHINK_analyze find_root_cause
after_success update_contexts maintain_consistency

## 📊 SUCCESS INDICATORS

GOOD_SOLUTION_SIGNS
- Modified source files in repository
- Used proper development tools
- Solution includes tests
- Changes are documented
- Works after fresh checkout

BAD_SOLUTION_SIGNS
- Manual runtime edits
- Temporary patches
- No source changes
- Untested fixes
- Requires manual steps

CRITICAL_CYCLE PLAN->ANALYZE->VERIFY all_WITH_ULTRATHINK
surgical_fixes minimum_viable_changes
preserve_existing maintain_compatibility
test_edge_cases verify_error_handling
fail_fast stop_on_first_error
explicit_better_than_clever clear_over_smart

## 🎯 THE GOLDEN RULE

THE_FUNDAMENTAL_PRINCIPLE
If it works manually → Automate it in code
If you patch runtime → You did it wrong
If it needs documentation → Make it self-evident
If it's temporary → Don't do it at all
EVERYTHING IN CODE, NOTHING MANUAL!

## 📚 PROJECT INTEGRATION

ADAPT_TO_PROJECT
1_check_for_existing_conventions
2_read_project_documentation
3_follow_established_patterns
4_respect_team_decisions
5_maintain_consistency
NEVER_impose_external_patterns

WHEN_STARTING_NEW_PROJECT
look_for → README CONTRIBUTING .editorconfig
check_for → package.json requirements.txt go.mod
respect → .gitignore .env.example docker-compose
follow → existing_code_style_and_patterns
ask_if → unsure_about_conventions

PROCEDURE_CHECKPOINTS
CP1 PROJECT.llm_loaded system_understood
CP2 module_found correct_location
CP3 CONTEXT.llm_read interface_understood
CP4 changes_planned WITH_ULTRATHINK
CP5 code_analyzed WITH_ULTRATHINK
CP6 changes_made minimal_correct
CP7 verification_passed all_tests_green
CP8 contexts_updated consistency_maintained

## 🚨 FORBIDDEN ACTIONS

WITHOUT_PERMISSION_CANNOT
modify_existing_code any_changes
delete_files remove_functionality
create_features add_new_code
refactor_code restructure_existing
change_structure move_rename_files
install_packages add_dependencies
modify_configs change_settings
git_push remote_operations

WITH_PERMISSION_CAN
read_any_files except_env
run_tests execute_validation
search_codebase grep_find_analyze
analyze_deps understand_structure
create_backups safety_copies
generate_CONTEXT.llm documentation

ERROR_RECOVERY_PROCEDURE
1_check git_status git_diff
2_validate run_validation_scripts
3_restore backup_or_git_checkout
4_revert git_checkout_--_file
5_rerun verification_tests
6_check procedure_compliance
7_analyze failure_root_cause

VALIDATION_CHECKLIST_BEFORE_COMPLETE
all_8_steps_followed procedure_complete
control_points_passed all_green
verification_successful tests_pass
no_accidental_modifications clean_changes
CONTEXT.llm_updated if_interface_changed
PROJECT.llm_updated if_structure_changed
no_comments_added clean_code
english_only all_identifiers
git_status_clean except_intended

STRICT_PROHIBITIONS_NEVER_DO
skip_procedure_steps follow_all_8
modify_without_verification always_test
ignore_failing_tests stop_on_failure
edit_forbidden_zones respect_boundaries
change_without_CONTEXT read_first
add_comments use_clear_names
duplicate_functionality reuse_existing
break_without_permission preserve_working
continue_after_failure stop_analyze
git_push_without_request explicit_only

## 📖 USAGE EXAMPLES

ULTRATHINK_USAGE_EXAMPLES
add_feature ULTRATHINK plan_implementation analyze_impacts verify_integration
fix_bug ULTRATHINK trace_cause analyze_flow plan_fix verify_solution
integrate_Redis ULTRATHINK analyze_architecture plan_integration verify_compatibility
refactor_auth ULTRATHINK impact_analysis migration_plan backward_compatibility
optimize_queries ULTRATHINK research_patterns benchmark_plan measure_improvements
debug_issue ULTRATHINK trace_dependencies isolate_problem systematic_elimination
security_audit ULTRATHINK threat_model vulnerability_scan mitigation_plan
performance_tune ULTRATHINK profile_bottlenecks optimization_strategy verify_gains

FIX_APPROACH_EXAMPLES
oauth_broken → READ_oauth_docs CHECK_token_expiry FIX_refresh_logic
api_failing → CHECK_logs VERIFY_endpoints FIX_authentication
db_connection_lost → CHECK_credentials VERIFY_network FIX_connection_string
webhook_not_receiving → VERIFY_url CHECK_ssl_certs FIX_endpoint
integration_stopped → CHECK_api_changes READ_changelog FIX_compatibility

ALWAYS ultrathink for PLAN->ANALYZE->VERIFY cycle NO_EXCEPTIONS