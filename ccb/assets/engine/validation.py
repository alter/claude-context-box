#!/usr/bin/env python3
"""
Procedure validation system - ensures 9-step procedure compliance
"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

def venv_check():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'prefix'):
        return False
    return os.path.exists(os.path.join(sys.prefix, 'bin', 'activate')) or \
           os.path.exists(os.path.join(sys.prefix, 'Scripts', 'activate'))

class ProcedureValidator:
    """Validates that the 9-step procedure is being followed"""
    
    def __init__(self):
        self.log_file = '.claude/procedure.log'
        self.current_step = 0
        self.steps_completed = []
        self.violations = []
        
    def log_step(self, step_num, status, details=""):
        """Log procedure step completion"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step_num,
            'status': status,
            'details': details
        }
        
        # Ensure directory exists
        os.makedirs('.claude', exist_ok=True)
        
        # Append to log
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\\n')
    
    def check_procedure_compliance(self):
        """Check if all steps were followed in order"""
        if not os.path.exists(self.log_file):
            print("❌ No procedure log found - procedure not started")
            return False
        
        with open(self.log_file, 'r') as f:
            logs = [json.loads(line) for line in f if line.strip()]
        
        if not logs:
            print("❌ Empty procedure log")
            return False
        
        # Get latest session (last 9 entries or less)
        session_logs = logs[-9:]
        
        print("🔍 Checking procedure compliance...\\n")
        
        expected_steps = [
            "Read PROJECT.llm",
            "Find target module", 
            "Read module CONTEXT.llm",
            "Analyze current code",
            "Create baseline tests",
            "Run baseline tests",
            "Make changes",
            "Test again",
            "Update contexts"
        ]
        
        all_good = True
        
        for i, step_name in enumerate(expected_steps, 1):
            # Find log for this step
            step_log = next((log for log in session_logs if log['step'] == i), None)
            
            if not step_log:
                print(f"❌ Step {i}: {step_name} - NOT EXECUTED")
                self.violations.append(f"Step {i} not executed")
                all_good = False
            elif step_log['status'] == 'completed':
                print(f"✅ Step {i}: {step_name} - Completed")
            elif step_log['status'] == 'failed':
                print(f"❌ Step {i}: {step_name} - FAILED: {step_log.get('details', '')}")
                self.violations.append(f"Step {i} failed")
                all_good = False
            else:
                print(f"⚠️  Step {i}: {step_name} - {step_log['status']}")
        
        return all_good
    
    def validate_control_points(self):
        """Check control points"""
        print("\\n📍 Validating control points...\\n")
        
        checks = {
            "PROJECT.llm exists": os.path.exists('PROJECT.llm'),
            "Has CONTEXT.llm files": len(list(Path('.').rglob('CONTEXT.llm'))) > 0,
            "Has baseline tests": len(list(Path('.').glob('test_baseline_*.py'))) > 0,
            "In virtual environment": venv_check()
        }
        
        all_passed = True
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
            if not passed:
                all_passed = False
                self.violations.append(f"Control point failed: {check}")
        
        return all_passed
    
    def check_last_change(self):
        """Validate the last code change followed procedure"""
        print("\\n🔍 Checking last change compliance...\\n")
        
        # Check git status for recent changes
        try:
            import subprocess
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                changed_files = result.stdout.strip().split('\\n')
                print(f"📝 Found {len(changed_files)} changed files")
                
                # Check if baseline tests exist for changed modules
                for file_line in changed_files:
                    if file_line.endswith('.py') and not file_line.startswith('test_'):
                        file_path = file_line.split()[-1]
                        module_name = Path(file_path).stem
                        baseline_test = f"test_baseline_{module_name}.py"
                        
                        if os.path.exists(baseline_test):
                            print(f"✅ Baseline test exists: {baseline_test}")
                        else:
                            print(f"❌ No baseline test for: {file_path}")
                            self.violations.append(f"No baseline test for {file_path}")
        except:
            print("⚠️  Could not check git status")
    
    def generate_report(self):
        """Generate compliance report"""
        print("\\n" + "="*60)
        print("📊 PROCEDURE COMPLIANCE REPORT")
        print("="*60)
        
        if not self.violations:
            print("\\n✅ All checks passed! Procedure followed correctly.")
        else:
            print(f"\\n❌ Found {len(self.violations)} violations:\\n")
            for i, violation in enumerate(self.violations, 1):
                print(f"  {i}. {violation}")
            
            print("\\n💡 Recommendations:")
            print("  - Review the 9-step procedure in .claude/prompt.md")
            print("  - Ensure all steps are followed in order")
            print("  - Create baseline tests before any changes")
            print("  - Run 'validate' regularly during development")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Validate procedure compliance')
    parser.add_argument('--check-procedure', action='store_true',
                       help='Check if procedure was followed')
    parser.add_argument('--check-last-change', action='store_true',
                       help='Validate last code change')
    parser.add_argument('--log-step', type=int,
                       help='Log completion of a procedure step')
    parser.add_argument('--status', choices=['completed', 'failed', 'skipped'],
                       help='Status for --log-step')
    parser.add_argument('--details', help='Details for --log-step')
    
    args = parser.parse_args()
    
    validator = ProcedureValidator()
    
    if args.log_step:
        if not args.status:
            print("❌ --status required with --log-step")
            sys.exit(1)
        validator.log_step(args.log_step, args.status, args.details or "")
        print(f"✅ Logged step {args.log_step} as {args.status}")
    
    elif args.check_procedure:
        validator.check_procedure_compliance()
        validator.generate_report()
    
    elif args.check_last_change:
        validator.check_last_change()
        validator.generate_report()
    
    else:
        # Default: full validation
        print("🎯 Running full validation...\\n")
        
        procedure_ok = validator.check_procedure_compliance()
        control_ok = validator.validate_control_points()
        validator.check_last_change()
        
        validator.generate_report()
        
        if not (procedure_ok and control_ok):
            sys.exit(1)

if __name__ == "__main__":
    main()
