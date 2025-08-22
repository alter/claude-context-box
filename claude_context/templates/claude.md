USER_COMMAND_SHORTCUTS_EXECUTE_VIA_BASH
WHEN_USER_TYPES_u → RUN_BASH: $(python3 .claude/get_python.py) .claude/update.py
WHEN_USER_TYPES_c → RUN_BASH: $(python3 .claude/get_python.py) .claude/check.py
WHEN_USER_TYPES_s → RUN_BASH: cat PROJECT.llm
WHEN_USER_TYPES_h → RUN_BASH: $(python3 .claude/get_python.py) .claude/help.py
NEVER_TASK_NEVER_SEARCH ALWAYS_BASH_EXECUTE

ULTRATHINK_MANDATORY for PLAN ANALYZE RESEARCH INTEGRATE REFACTOR VERIFY DEBUG
- PLAN implementation_strategy architecture_decisions system_impacts
- ANALYZE complex_problems current_code dependencies trace_impacts
- RESEARCH new_technologies integration_options best_practices
- INTEGRATE external_services libraries APIs ensure_compatibility
- REFACTOR major_changes breaking_changes migration_paths
- VERIFY all_changes test_coverage edge_cases error_handling
- DEBUG complex_issues trace_dependencies isolate_problems
USE ultrathink BEFORE proposing_solutions AND verifying_changes

TECH_APPROVAL_MANDATORY before_ANY_new_tech
1_DESCRIBE what_technology why_needed
2_EXPLAIN problem_solves current_limitations
3_DETAIL how_used integration_plan
4_SPECIFY replaces_or_adds impacts_on_existing
5_WAIT explicit_approval NEVER_proceed_without

NEVER_CREATE _new _enhanced _final _updated _v2 _copy versions
ALWAYS_MODIFY existing_files_only
NEVER_DUPLICATE functionality

FORBIDDEN_ZONES venv __pycache__ .git node_modules .env dist build .eggs .venv .local
NEED_PERMISSION modify delete create refactor install git_push package_changes

8STEP_MANDATORY_PROCEDURE
1_read PROJECT.llm understand_architecture
2_find target_module efficient_search
3_read module/CONTEXT.llm understand_interface
4_PLAN approach WITH_ULTRATHINK consider_all_impacts trace_dependencies
5_ANALYZE current_code WITH_ULTRATHINK understand_flow identify_changes
6_make MINIMAL_changes preserve_functionality maintain_style
7_VERIFY WITH_ULTRATHINK run_all_paths test_edge_cases check_errors
8_update contexts if_interface_changed update_PROJECT.llm

VERIFY_REQUIREMENTS WITH_ULTRATHINK
scripts python_script.py_--help then_real_args all_code_paths
libs python_-c_import_module test_all_methods check_state
apis curl_endpoints test_errors check_timeouts validate_responses
coverage all_branches error_handling edge_cases boundary_conditions
FAIL STOP_immediately ULTRATHINK_root_cause analyze_stack_trace

CONTROL_POINTS_MANDATORY
before_change read_PROJECT.llm understand_system
before_plan ULTRATHINK_strategy consider_alternatives
before_edit read_CONTEXT.llm understand_contract
during_analysis ULTRATHINK_dependencies trace_impacts
after_change ULTRATHINK_verify test_thoroughly
if_fail STOP ULTRATHINK_analyze find_root_cause
after_success update_contexts maintain_consistency

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
mcp → EXECUTE: $(python3 .claude/get_python.py) .claude/mcp_setup.py
NEVER_interpret_commands_differently ALWAYS_execute_exact_script

MCP_MEMORY_COMMANDS_IF_ENABLED
/memory-store content tags → Store_memory_with_semantic_search
/memory-search query → Search_memories_semantically
/memory-recall time_expression → Recall_memories_by_time
/memory-health → Check_MCP_memory_status
MCP_stores_in .local/mcp/memory.db

PYTHON_ENVIRONMENT_STRICT
ALWAYS python3 NEVER python
ALWAYS pip3 NEVER pip
ALWAYS venv or .venv REQUIRED
NO_COMMENTS in_code_files
ENGLISH_ONLY all_identifiers
SELF_DOCUMENTING clear_names descriptive_functions

GIT_RULES_STRICT
NEVER mention_Claude_AI_LLM_generated
NEVER change_git_config user_settings
USE existing_user_config only
DESCRIBE changes_not_tools implementation_not_origin
NO_ATTRIBUTION no_co_authorship

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

CRITICAL_CYCLE PLAN->ANALYZE->VERIFY all_WITH_ULTRATHINK
surgical_fixes minimum_viable_changes
preserve_existing maintain_compatibility
test_edge_cases verify_error_handling
fail_fast stop_on_first_error
explicit_better_than_clever clear_over_smart

PROCEDURE_CHECKPOINTS
CP1 PROJECT.llm_loaded system_understood
CP2 module_found correct_location
CP3 CONTEXT.llm_read interface_understood
CP4 changes_planned WITH_ULTRATHINK
CP5 code_analyzed WITH_ULTRATHINK
CP6 changes_made minimal_correct
CP7 verification_passed all_tests_green
CP8 contexts_updated consistency_maintained

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

ULTRATHINK_USAGE_EXAMPLES
add_feature ULTRATHINK plan_implementation analyze_impacts verify_integration
fix_bug ULTRATHINK trace_cause analyze_flow plan_fix verify_solution
integrate_Redis ULTRATHINK analyze_architecture plan_integration verify_compatibility
refactor_auth ULTRATHINK impact_analysis migration_plan backward_compatibility
optimize_queries ULTRATHINK research_patterns benchmark_plan measure_improvements
debug_issue ULTRATHINK trace_dependencies isolate_problem systematic_elimination
security_audit ULTRATHINK threat_model vulnerability_scan mitigation_plan
performance_tune ULTRATHINK profile_bottlenecks optimization_strategy verify_gains

ALWAYS ultrathink for PLAN->ANALYZE->VERIFY cycle NO_EXCEPTIONS