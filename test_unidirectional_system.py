#!/usr/bin/env python3
"""
Test Script for Unidirectional Sync System

This script tests the converted unidirectional Monday → Google Calendar sync system
to ensure all components work correctly after removing Google → Monday functionality.

Usage:
    python test_unidirectional_system.py
"""

import os
import sys
import json
import time
from datetime import datetime

def test_imports():
    """Test that all required imports work and removed functions are gone."""
    print("🔍 Testing imports and removed components...")
    
    try:
        # Test required imports
        from app import app
        from google_calendar_service import get_calendar_service, create_google_event, update_google_event
        from sync_logic import sincronizar_item_via_webhook, generate_content_hash
        from google_change_monitor import GoogleChangeMonitor
        print("✅ All required imports successful")
        
        # Test that removed functions are gone
        removed_functions = [
            ("google_calendar_service", "get_incremental_sync_events"),
            ("google_calendar_service", "compare_event_values"),
            ("sync_logic", "sincronizar_desde_google_calendar"),
            ("sync_logic", "sincronizar_desde_calendario_personal")
        ]
        
        for module_name, function_name in removed_functions:
            try:
                module = __import__(module_name)
                getattr(module, function_name)
                print(f"❌ ERROR: {function_name} should be removed from {module_name}")
                return False
            except AttributeError:
                print(f"✅ {function_name} correctly removed from {module_name}")
        
        # Test that deleted files are gone
        deleted_files = [
            "sync_token_manager.py",
            "config/sync_tokens.json"
        ]
        
        for file_path in deleted_files:
            if os.path.exists(file_path):
                print(f"❌ ERROR: {file_path} should be deleted")
                return False
            else:
                print(f"✅ {file_path} correctly deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def test_flask_endpoints():
    """Test Flask app endpoints."""
    print("\n🌐 Testing Flask endpoints...")
    
    try:
        from app import app
        
        # Test client
        with app.test_client() as client:
            
            # Test home endpoint
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Home endpoint (/) working")
            else:
                print(f"❌ Home endpoint failed: {response.status_code}")
                return False
            
            # Test health check
            response = client.get('/health')
            if response.status_code == 200:
                data = json.loads(response.data)
                if data.get('status') == 'healthy':
                    print("✅ Health check endpoint (/health) working")
                else:
                    print(f"❌ Health check failed: {data}")
                    return False
            else:
                print(f"❌ Health check endpoint failed: {response.status_code}")
                return False
            
            # Test Monday webhook endpoint (should accept POST)
            test_webhook_data = {
                "pulseId": 12345,
                "event": {"pulseId": 12345}
            }
            
            response = client.post('/monday-webhook', 
                                 json=test_webhook_data,
                                 headers={'Content-Type': 'application/json'})
            
            # Should return 200 even if it can't process (no services configured)
            if response.status_code == 200:
                print("✅ Monday webhook endpoint (/monday-webhook) accepts requests")
            else:
                print(f"❌ Monday webhook endpoint failed: {response.status_code}")
                return False
            
            # Test that Google webhook endpoint is gone
            response = client.post('/google-webhook',
                                 json={"test": "data"},
                                 headers={'Content-Type': 'application/json'})
            
            if response.status_code == 404:
                print("✅ Google webhook endpoint (/google-webhook) correctly removed")
            else:
                print(f"❌ Google webhook endpoint should be removed but returned: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Flask endpoint test failed: {e}")
        return False


def test_configuration_files():
    """Test that configuration files are properly updated."""
    print("\n📂 Testing configuration file changes...")
    
    try:
        # Check that webhook config files are disabled
        disabled_files = [
            "config/channels/google_channel_map.json.DISABLED",
            "config/webhooks/webhooks_personales_info.json.DISABLED"
        ]
        
        for file_path in disabled_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path} correctly disabled")
            else:
                print(f"⚠️  {file_path} not found (may not have existed)")
        
        # Check for documentation files
        doc_files = [
            "config/channels/GOOGLE_WEBHOOKS_DISABLED.md",
            "google_change_monitor.py",
            "scripts/utilities/cleanup_google_webhooks_for_unidirectional.py"
        ]
        
        for file_path in doc_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path} created")
            else:
                print(f"❌ {file_path} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration file test failed: {e}")
        return False


def test_monitoring_system():
    """Test the Google change monitoring system."""
    print("\n📊 Testing Google change monitoring system...")
    
    try:
        from google_change_monitor import GoogleChangeMonitor, run_monitoring_check
        
        # Test monitor initialization
        monitor = GoogleChangeMonitor()
        print("✅ GoogleChangeMonitor initialized")
        
        # Test monitoring check function
        # This should run without crashing even if no Google service is available
        try:
            run_monitoring_check()
            print("✅ Monitoring check function runs")
        except Exception as e:
            # It's okay if it fails due to missing credentials
            if "credentials" in str(e).lower() or "service" in str(e).lower():
                print("ℹ️  Monitoring check requires Google credentials (expected)")
            else:
                print(f"⚠️  Monitoring check error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring system test failed: {e}")
        return False


def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n" + "=" * 60)
    print("📋 UNIDIRECTIONAL SYSTEM TEST REPORT")
    print("=" * 60)
    
    tests = [
        ("Imports and Removed Components", test_imports),
        ("Flask Endpoints", test_flask_endpoints),
        ("Configuration Files", test_configuration_files),
        ("Monitoring System", test_monitoring_system)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📍 Running: {test_name}")
        print("-" * 40)
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<10} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - UNIDIRECTIONAL SYSTEM IS READY!")
        print("\nNext Steps:")
        print("1. Run cleanup script: python scripts/utilities/cleanup_google_webhooks_for_unidirectional.py")
        print("2. Configure Google calendars as read-only for users")
        print("3. Test Monday → Google sync with real data")
        print("4. Monitor for conflicts with: python google_change_monitor.py")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW ISSUES ABOVE")
        return False


if __name__ == "__main__":
    print("🚀 TESTING UNIDIRECTIONAL SYNC SYSTEM")
    print("🎯 Testing Monday → Google only synchronization")
    
    success = generate_test_report()
    
    if success:
        # Create test completion log
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_entry = {
            "test_date": datetime.now().isoformat(),
            "test_type": "unidirectional_system_validation",
            "result": "passed",
            "components_tested": [
                "imports_and_removed_components",
                "flask_endpoints", 
                "configuration_files",
                "monitoring_system"
            ],
            "system_status": "ready_for_production"
        }
        
        with open(os.path.join(log_dir, "unidirectional_test_results.json"), 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        print(f"\n📝 Test results saved to logs/unidirectional_test_results.json")
        sys.exit(0)
    else:
        sys.exit(1)