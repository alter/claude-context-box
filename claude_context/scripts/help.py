#!/usr/bin/env python3
"""
Claude Context Box Help System
"""

import os
import sys

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

def main():
    """Display help information"""
    
    help_text = """
🎯 Claude Context Box - Quick Commands

📋 BASIC COMMANDS:
  u, update     - Update PROJECT.llm and all contexts
  c, check      - Quick health check of project
  s, structure  - Show PROJECT.llm structure
  h, help       - Show this help

🔒 PROCEDURE VALIDATION:
  validate      - Full validation (procedure + tests + structure)
  procedure     - Check 9-step procedure compliance
  project       - Display full PROJECT.llm content
  deps          - Show module dependency graph

📁 CONTEXT MANAGEMENT:
  ctx init      - Create CONTEXT.llm for all modules
  ctx update    - Update existing CONTEXT.llm files
  ctx scan      - Find modules without CONTEXT.llm
  
🧪 TESTING:
  baseline <module>  - Create baseline tests for specific module
  test-all          - Run all baseline tests
  
🧹 MAINTENANCE:
  cleancode, cc     - Interactive dead code cleanup
  v, venv          - Setup/check Python environment

📝 MANDATORY WORKFLOW (9 Steps):
  1. Read PROJECT.llm
  2. Find target module
  3. Read module CONTEXT.llm
  4. Analyze current code
  5. Create baseline tests ('baseline <module>')
  6. Run baseline tests
  7. Make minimal changes
  8. Test again (STOP if fails)
  9. Update contexts ('u')

⚠️  CRITICAL RULES:
  - ALWAYS follow the 9-step procedure
  - NEVER modify code without baseline tests
  - STOP immediately when tests fail
  - NO COMMENTS in code
  - ENGLISH ONLY

💡 TIPS:
  - Run 'validate' before ANY code changes
  - Use 'procedure' to check compliance
  - Create baseline tests BEFORE modifications
  - Update contexts AFTER changes

🔗 MORE INFO:
  - .claude/prompt.md - Full system rules & procedure
  - PROJECT.llm - Architecture & dependencies
  - CLAUDE.md - Quick command reference
"""
    
    print(help_text)
    
    if not venv_check():
        print("\\n⚠️  WARNING: Not in virtual environment!")
        print("   Run: source venv/bin/activate")

if __name__ == "__main__":
    main()
