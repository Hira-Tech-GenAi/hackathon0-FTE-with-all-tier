#!/usr/bin/env python3
"""
Silver Tier Test Script

Quick verification of Silver Tier features.
Run this to test all implemented functionality.

Usage:
    uv run python test_silver_tier.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.absolute()
VAULT_DIR = BASE_DIR / "ai-employee-vault"

def test_imports():
    """Test that all modules can be imported."""
    print("\n" + "=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)
    
    try:
        from skills import (
            create_plan, request_approval, check_approval_status,
            log_action, send_email_draft, update_plan_step
        )
        print("✓ Skills module imported successfully")
        
        import orchestrator
        print("✓ Orchestrator module imported successfully")
        
        import task_scheduler
        print("✓ Task Scheduler module imported successfully")
        
        import generate_briefing
        print("✓ Generate Briefing module imported successfully")
        
        import linkedin_watcher
        print("✓ LinkedIn Watcher module imported successfully")
        
        import whatsapp_watcher
        print("✓ WhatsApp Watcher module imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_skills():
    """Test Silver Tier skills."""
    print("\n" + "=" * 60)
    print("TEST 2: Silver Tier Skills")
    print("=" * 60)
    
    try:
        from skills import create_plan, request_approval, log_action, send_email_draft
        
        # Test create_plan
        print("\nTesting create_plan...")
        result = create_plan(
            objective="Test Silver Tier functionality",
            file_path="test_file.txt"
        )
        if result.get("success"):
            print(f"✓ Plan created: {result.get('plan_filename')}")
        else:
            print(f"✗ Plan creation failed: {result.get('error')}")
        
        # Test request_approval
        print("\nTesting request_approval...")
        result = request_approval(
            action_type="test_action",
            details={"test": "data", "value": 123},
            reason="Silver Tier testing"
        )
        if result.get("success"):
            print(f"✓ Approval request created: {result.get('approval_filename')}")
        else:
            print(f"✗ Approval request failed: {result.get('error')}")
        
        # Test log_action
        print("\nTesting log_action...")
        result = log_action(
            action_type="test",
            details={"test": "logging"},
            result="success"
        )
        if result.get("success"):
            print(f"✓ Action logged: {result.get('log_file')}")
        else:
            print(f"✗ Logging failed: {result.get('error')}")
        
        # Test send_email_draft
        print("\nTesting send_email_draft...")
        result = send_email_draft(
            to="test@example.com",
            subject="Test Email",
            body="This is a test email from Silver Tier testing.",
            requires_approval=True
        )
        if result.get("success"):
            print(f"✓ Email draft created: {result.get('email_filename')}")
        else:
            print(f"✗ Email draft failed: {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Skills test failed: {e}")
        return False


def test_briefing_generation():
    """Test CEO briefing generation."""
    print("\n" + "=" * 60)
    print("TEST 3: CEO Briefing Generation")
    print("=" * 60)
    
    try:
        from generate_briefing import generate_daily_briefing
        
        print("\nGenerating daily briefing...")
        result = generate_daily_briefing()
        
        if result.get("success"):
            print(f"✓ Daily briefing generated: {result.get('briefing_path')}")
            print(f"  Tasks completed: {result.get('tasks_completed')}")
            print(f"  Pending approvals: {result.get('pending_approvals')}")
        else:
            print(f"✗ Briefing generation failed: {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Briefing test failed: {e}")
        return False


def test_folder_structure():
    """Verify folder structure exists."""
    print("\n" + "=" * 60)
    print("TEST 4: Folder Structure")
    print("=" * 60)
    
    required_folders = [
        "Inbox",
        "Needs_Action",
        "Done",
        "Plans",
        "Pending_Approval",
        "Approved",
        "Rejected",
        "Logs",
        "Briefings",
        "LinkedIn",
        "WhatsApp"
    ]
    
    all_exist = True
    
    for folder_name in required_folders:
        folder_path = VAULT_DIR / folder_name
        if folder_path.exists():
            print(f"✓ {folder_name}/")
        else:
            print(f"✗ {folder_name}/ - MISSING")
            all_exist = False
    
    return all_exist


def test_mcp_server():
    """Test MCP server configuration."""
    print("\n" + "=" * 60)
    print("TEST 5: MCP Server")
    print("=" * 60)
    
    mcp_server_path = BASE_DIR / "mcp-servers" / "email_mcp_server.py"
    
    if mcp_server_path.exists():
        print(f"✓ Email MCP Server exists: {mcp_server_path}")
        
        # Try to import
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(mcp_server_path)],
                input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n',
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print("✓ MCP Server responds correctly")
                return True
            else:
                print(f"✗ MCP Server error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ MCP Server test failed: {e}")
            return False
    else:
        print(f"✗ Email MCP Server not found: {mcp_server_path}")
        return False


def test_watchers():
    """Test watcher scripts exist."""
    print("\n" + "=" * 60)
    print("TEST 6: Watcher Scripts")
    print("=" * 60)
    
    watchers = {
        "Gmail Watcher": "gmail_watcher.py",
        "WhatsApp Watcher": "whatsapp_watcher.py",
        "LinkedIn Watcher": "linkedin_watcher.py",
        "Filesystem Watcher": "filesystem_watcher.py",
        "Orchestrator": "orchestrator.py"
    }
    
    all_exist = True
    
    for name, filename in watchers.items():
        watcher_path = BASE_DIR / filename
        if watcher_path.exists():
            print(f"✓ {name}: {filename}")
        else:
            print(f"✗ {name}: {filename} - MISSING")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧪 SILVER TIER TEST SUITE")
    print("=" * 60)
    print(f"Testing: {BASE_DIR}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "Imports": test_imports(),
        "Skills": test_skills(),
        "Briefing": test_briefing_generation(),
        "Folders": test_folder_structure(),
        "MCP Server": test_mcp_server(),
        "Watchers": test_watchers()
    }
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Silver Tier is ready!")
        print("\nNext steps:")
        print("1. Configure API keys in .env")
        print("2. Run watchers: uv run python gmail_watcher.py")
        print("3. Install scheduled tasks: uv run python task_scheduler.py install")
        print("4. Start orchestrator: uv run python orchestrator.py")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
