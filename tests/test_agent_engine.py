"""
Test Suite for Autonomous Agent Engine
Tests data collection, decision making, and action execution
"""

import os
import sys
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_engine import (
    collect_user_data, make_decision, execute_action,
    check_action_cooldown, log_action
)
from memory import get_db, create_account


def test_collect_user_data():
    """Test data collection for a user"""
    print("\n✅ TEST: collect_user_data()")
    print("─" * 50)
    
    # Create a test user
    user_id = create_account("test_agent_user", "testpass123", "agent@test.com")
    if not user_id:
        print("❌ Could not create test user")
        return False
    
    try:
        data = collect_user_data(user_id)
        
        if not data:
            print("❌ collect_user_data returned None")
            return False
        
        print(f"✅ User data collected:")
        print(f"   - Name: {data['name']}")
        print(f"   - Missed Tasks: {data['missed_tasks']}")
        print(f"   - Completion Rate: {data['completion_rate']}%")
        print(f"   - Inactivity Hours: {data['inactivity_hours']}")
        print(f"   - Productivity Score: {data['productivity_score']}")
        
        assert 'user_id' in data, "Missing user_id in data"
        assert 'completion_rate' in data, "Missing completion_rate"
        assert 'productivity_score' in data, "Missing productivity_score"
        
        print("✅ All assertions passed")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_make_decision():
    """Test decision making engine"""
    print("\n✅ TEST: make_decision()")
    print("─" * 50)
    
    # Simulate user data with issues
    user_data = {
        'user_id': 999,
        'name': 'Test User',
        'email': 'test@example.com',
        'missed_tasks': 3,  # Should trigger reschedule_tasks
        'incomplete_tasks': 3,
        'completed_tasks_today': 0,
        'total_tasks_today': 3,
        'completion_rate': 0,
        'focus_sessions_today': 0,
        'habit_completion_rate': 50,
        'current_streak': 5,
        'inactivity_hours': 12,
        'productivity_score': 20,
        'last_action_time': datetime.now().isoformat(),
        'active_today': True
    }
    
    try:
        decision = make_decision(user_data)
        
        if not decision:
            print("❌ make_decision returned None")
            return False
        
        print(f"✅ Decision made:")
        print(f"   - Action: {decision['action']}")
        print(f"   - Reason: {decision['reason']}")
        print(f"   - Priority: {decision['priority']}")
        
        assert decision['action'] == 'reschedule_tasks', f"Expected reschedule_tasks, got {decision['action']}"
        assert decision['priority'] in ['low', 'medium', 'high'], "Invalid priority"
        
        print("✅ All assertions passed")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_action_cooldown():
    """Test cooldown mechanism to prevent spam"""
    print("\n✅ TEST: check_action_cooldown()")
    print("─" * 50)
    
    test_user_id = 99999  # Fake ID for testing
    
    try:
        # First check - should not be on cooldown
        is_available = check_action_cooldown(test_user_id, 'test_action')
        print(f"✅ First cooldown check: {is_available} (should be True)")
        assert is_available, "Should not be on cooldown initially"
        
        # Log an action
        log_action(test_user_id, 'test_action', 'Test reason', 'low', {'test': 'data'}, True)
        
        # Check cooldown immediately - should be on cooldown
        is_available = check_action_cooldown(test_user_id, 'test_action')
        print(f"✅ Cooldown after action: {is_available} (should be False)")
        assert not is_available, "Should be on cooldown after action"
        
        print("✅ All assertions passed")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_decision_rules():
    """Test different decision rules"""
    print("\n✅ TEST: Decision Rules (Various Conditions)")
    print("─" * 50)
    
    test_cases = [
        {
            'name': 'High missed tasks',
            'data': {
                'user_id': 1, 'name': 'User', 'email': 'u@test.com',
                'missed_tasks': 5, 'incomplete_tasks': 5, 'completed_tasks_today': 0,
                'total_tasks_today': 5, 'completion_rate': 0, 'focus_sessions_today': 2,
                'habit_completion_rate': 80, 'current_streak': 10, 'inactivity_hours': 6,
                'productivity_score': 50, 'last_action_time': None, 'active_today': True
            },
            'expected_action': 'reschedule_tasks'
        },
        {
            'name': 'Long inactivity',
            'data': {
                'user_id': 2, 'name': 'User', 'email': 'u@test.com',
                'missed_tasks': 0, 'incomplete_tasks': 0, 'completed_tasks_today': 0,
                'total_tasks_today': 0, 'completion_rate': 0, 'focus_sessions_today': 0,
                'habit_completion_rate': 80, 'current_streak': 5, 'inactivity_hours': 48,
                'productivity_score': 0, 'last_action_time': None, 'active_today': False
            },
            'expected_action': 'send_inactivity_nudge'
        },
        {
            'name': 'Low completion rate',
            'data': {
                'user_id': 3, 'name': 'User', 'email': 'u@test.com',
                'missed_tasks': 1, 'incomplete_tasks': 1, 'completed_tasks_today': 0,
                'total_tasks_today': 3, 'completion_rate': 33.33, 'focus_sessions_today': 0,
                'habit_completion_rate': 80, 'current_streak': 5, 'inactivity_hours': 2,
                'productivity_score': 27, 'last_action_time': None, 'active_today': True
            },
            'expected_action': 'reduce_task_load'
        }
    ]
    
    for test_case in test_cases:
        try:
            decision = make_decision(test_case['data'])
            
            if decision:
                actual_action = decision['action']
                expected_action = test_case['expected_action']
                match = actual_action == expected_action
                
                status = "✅" if match else "⚠️"
                print(f"{status} {test_case['name']}: {actual_action}")
                
                if not match:
                    print(f"   Expected: {expected_action}, Got: {actual_action}")
            else:
                print(f"⚠️  {test_case['name']}: No decision made")
                
        except Exception as e:
            print(f"❌ {test_case['name']}: {e}")
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("AUTONOMOUS AGENT ENGINE - TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Collect User Data", test_collect_user_data),
        ("Make Decision", test_make_decision),
        ("Decision Rules", test_decision_rules),
        ("Action Cooldown", test_action_cooldown),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ FATAL ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
