#!/usr/bin/env python3
"""
Verification Script for Autonomous Agent System
Checks all components are properly installed
"""

import os
import sys
from datetime import datetime

def check_file_exists(filepath, name):
    """Check if file exists"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {name}: {filepath}")
    return exists

def check_import(module_name, description):
    """Check if module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name} - {e}")
        return False

def check_database():
    """Check if database table exists"""
    try:
        from memory import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_actions_log'")
            result = cursor.fetchone()
            if result:
                print("✅ Database: agent_actions_log table exists")
                return True
            else:
                print("❌ Database: agent_actions_log table NOT found")
                print("   → Run: python migrate_agent_engine.py")
                return False
    except Exception as e:
        print(f"❌ Database: Error checking table - {e}")
        return False

def check_scheduler_integration():
    """Check if scheduler imports the agent"""
    try:
        with open('ai_task_scheduler.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            has_import = 'from agent_engine import' in content
            has_job = 'run_autonomous_agent_job' in content or 'run_autonomous_agent_for_all_users' in content
            
            if has_import and has_job:
                print("✅ Scheduler: Agent integration present")
                return True
            else:
                print(f"❌ Scheduler: Integration missing (import: {has_import}, job: {has_job})")
                return False
    except Exception as e:
        print(f"❌ Scheduler: Error checking integration - {e}")
        return False

def check_chat_fixes():
    """Check if chat.html has the fixes"""
    try:
        with open('web/templates/chat.html', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            has_loadFreshHistory = 'loadFreshHistory' in content
            has_rlhf_header = 'X-RLHF-Strategy' in content
            
            issues = []
            if not has_loadFreshHistory:
                issues.append("loadFreshHistory function")
            if not has_rlhf_header:
                issues.append("RLHF strategy header handling")
            
            if not issues:
                print("✅ Chat: History persistence & RLHF fixes applied")
                return True
            else:
                print(f"❌ Chat: Missing fixes - {', '.join(issues)}")
                return False
    except Exception as e:
        print(f"❌ Chat: Error checking fixes - {e}")
        return False

def check_app_rlhf():
    """Check if app.py has RLHF header"""
    try:
        with open('web/app.py', 'r') as f:
            content = f.read()
            has_header = "response.headers['X-RLHF-Strategy']" in content
            
            if has_header:
                print("✅ App.py: RLHF strategy header added")
                return True
            else:
                print("❌ App.py: RLHF strategy header NOT found")
                return False
    except Exception as e:
        print(f"❌ App.py: Error checking RLHF - {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 70)
    print("AUTONOMOUS AGENT SYSTEM - VERIFICATION")
    print("=" * 70)
    print(f"\nChecking at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    results = {}
    
    # 1. Check files exist
    print("1. CHECKING FILES")
    print("-" * 70)
    results['agent_engine.py'] = check_file_exists('agent_engine.py', 'Agent Engine Module')
    results['migrate_script'] = check_file_exists('migrate_agent_engine.py', 'Migration Script')
    results['agent_tests'] = check_file_exists('tests/test_agent_engine.py', 'Test Suite')
    results['agent_docs'] = check_file_exists('AGENT_ENGINE_DOCS.md', 'Technical Docs')
    results['setup_docs'] = check_file_exists('AGENT_ENGINE_SETUP.md', 'Setup Guide')
    results['quick_ref'] = check_file_exists('AGENT_ENGINE_QUICK_REF.md', 'Quick Reference')
    print()
    
    # 2. Check imports
    print("2. CHECKING IMPORTS")
    print("-" * 70)
    results['agent_import'] = check_import('agent_engine', 'Agent Engine')
    results['memory_import'] = check_import('memory', 'Memory Module')
    print()
    
    # 3. Check database
    print("3. CHECKING DATABASE")
    print("-" * 70)
    results['database'] = check_database()
    print()
    
    # 4. Check integrations
    print("4. CHECKING INTEGRATIONS")
    print("-" * 70)
    results['scheduler'] = check_scheduler_integration()
    results['chat'] = check_chat_fixes()
    results['app_rlhf'] = check_app_rlhf()
    print()
    
    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    print()
    print(f"Total: {passed}/{total} checks passed")
    print()
    
    if passed == total:
        print("🎉 ALL CHECKS PASSED!")
        print()
        print("NEXT STEPS:")
        print("1. Start Flask: python web/app.py")
        print("2. Monitor logs: tail -f agent_engine.log")
        print("3. Check actions: sqlite3 partnerai.db 'SELECT * FROM agent_actions_log;'")
        print("4. Run tests: python tests/test_agent_engine.py")
        print()
        print("The agent will run automatically every 30 minutes!")
        return 0
    else:
        print("⚠️  SOME CHECKS FAILED")
        print()
        
        if not results.get('database'):
            print("ACTION REQUIRED:")
            print("  Run: python migrate_agent_engine.py")
        
        if not results.get('agent_import'):
            print("ACTION REQUIRED:")
            print("  Check that agent_engine.py exists in root directory")
            print("  Check Python path includes root directory")
        
        if not results.get('scheduler'):
            print("ACTION REQUIRED:")
            print("  Check ai_task_scheduler.py has been updated")
        
        if not results.get('chat'):
            print("ACTION REQUIRED:")
            print("  Check web/templates/chat.html has been updated")
        
        print()
        print("See AGENT_ENGINE_SETUP.md for detailed setup instructions")
        return 1

if __name__ == "__main__":
    sys.exit(main())
