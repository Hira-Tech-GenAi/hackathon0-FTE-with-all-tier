#!/usr/bin/env python3
"""
CEO Briefing Generator for Personal AI Employee - Silver Tier

Generates daily and weekly CEO briefings by analyzing:
- Completed tasks
- Pending approvals
- Business metrics
- System activity logs

Usage:
    python generate_briefing.py           # Daily briefing
    python generate_briefing.py --weekly  # Weekly briefing
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =============================================================================
# Configuration
# =============================================================================

BASE_DIR = Path(__file__).parent.absolute()
VAULT_DIR = BASE_DIR / "ai-employee-vault"

INBOX_DIR = VAULT_DIR / "Inbox"
NEEDS_ACTION_DIR = VAULT_DIR / "Needs_Action"
DONE_DIR = VAULT_DIR / "Done"
PLANS_DIR = VAULT_DIR / "Plans"
PENDING_APPROVAL_DIR = VAULT_DIR / "Pending_Approval"
APPROVED_DIR = VAULT_DIR / "Approved"
REJECTED_DIR = VAULT_DIR / "Rejected"
LOGS_DIR = VAULT_DIR / "Logs"
BRIEFINGS_DIR = VAULT_DIR / "Briefings"

# Ensure directories exist
for directory in [VAULT_DIR, DONE_DIR, PENDING_APPROVAL_DIR, LOGS_DIR, BRIEFINGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

DASHBOARD_PATH = VAULT_DIR / "Dashboard.md"
BUSINESS_GOALS_PATH = VAULT_DIR / "Business_Goals.md"


# =============================================================================
# Data Collection Functions
# =============================================================================

def count_files_in_directory(directory: Path, hours: int = 24) -> int:
    """Count files modified in the last N hours."""
    if not directory.exists():
        return 0
    
    count = 0
    cutoff = datetime.now() - timedelta(hours=hours)
    
    for file_path in directory.glob("*"):
        if file_path.is_file():
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > cutoff:
                    count += 1
            except:
                pass
    
    return count


def get_recent_completed_tasks(hours: int = 24) -> List[Dict[str, Any]]:
    """Get recently completed tasks from Done folder."""
    tasks = []
    cutoff = datetime.now() - timedelta(hours=hours)
    
    if not DONE_DIR.exists():
        return tasks
    
    for file_path in DONE_DIR.glob("*.md"):
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime > cutoff:
                tasks.append({
                    "name": file_path.name,
                    "completed_at": mtime.isoformat(),
                    "path": str(file_path)
                })
        except:
            pass
    
    return tasks


def get_pending_approvals() -> List[Dict[str, Any]]:
    """Get pending approval requests."""
    approvals = []
    
    if not PENDING_APPROVAL_DIR.exists():
        return approvals
    
    for file_path in PENDING_APPROVAL_DIR.glob("*.md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract basic info
            approval_type = "unknown"
            created = "unknown"
            
            for line in content.split("\n"):
                if "action_type:" in line.lower():
                    approval_type = line.split(":")[1].strip()
                elif "created:" in line.lower():
                    created = line.split(":")[1].strip()
            
            approvals.append({
                "name": file_path.name,
                "type": approval_type,
                "created": created,
                "path": str(file_path)
            })
        except:
            pass
    
    return approvals


def get_activity_summary(hours: int = 24) -> Dict[str, Any]:
    """Get summary of system activity."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"orchestrator_{today}.json"
    
    actions = []
    
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                actions = data.get("executions", [])
        except:
            pass
    
    return {
        "total_actions": len(actions),
        "successful": len([a for a in actions if a.get("result") == "success"]),
        "failed": len([a for a in actions if a.get("result") == "failed"]),
        "actions": actions
    }


def load_business_goals() -> Dict[str, Any]:
    """Load business goals from file."""
    if not BUSINESS_GOALS_PATH.exists():
        return {
            "exists": False,
            "goals": []
        }
    
    try:
        with open(BUSINESS_GOALS_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Simple parsing
        goals = {
            "exists": True,
            "content": content,
            "raw": content
        }
        
        return goals
        
    except:
        return {"exists": False, "error": "Could not read business goals"}


# =============================================================================
# Briefing Generation
# =============================================================================

def generate_daily_briefing() -> Dict[str, Any]:
    """Generate daily CEO briefing."""
    timestamp = datetime.now()
    briefing_date = timestamp.strftime("%Y-%m-%d")
    
    # Collect data
    completed_today = count_files_in_directory(DONE_DIR, hours=24)
    pending_count = len(get_pending_approvals())
    activity = get_activity_summary(hours=24)
    
    # Create briefing content
    briefing_content = f"""---
generated: {timestamp.isoformat()}
period: {briefing_date}
type: daily
---

# Daily CEO Briefing

**Generated:** {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
**Period:** {briefing_date}

---

## Executive Summary

Daily briefing generated automatically by AI Employee.

---

## Today's Activity

### Tasks Completed
- **Total:** {completed_today} tasks completed today
- See `/Vault/Done/` folder for details

### Pending Approvals
- **Requiring Attention:** {pending_count} items
- Check `/Vault/Pending_Approval/` folder

### System Activity
- **Total Actions:** {activity['total_actions']}
- **Successful:** {activity['successful']}
- **Failed:** {activity['failed']}

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Tasks Completed | {completed_today} |
| Pending Approvals | {pending_count} |
| System Actions | {activity['total_actions']} |
| Success Rate | {activity['successful']}/{activity['total_actions'] if activity['total_actions'] > 0 else 1} |

---

## Action Items

- [ ] Review pending approvals in `/Vault/Pending_Approval/`
- [ ] Check system health in `Dashboard.md`
- [ ] Process any flagged items

---

## Recent Completed Tasks

"""
    
    # Add recent tasks
    recent_tasks = get_recent_completed_tasks(hours=24)
    if recent_tasks:
        for task in recent_tasks[:10]:  # Show last 10
            briefing_content += f"- {task['name']}\n"
    else:
        briefing_content += "- No tasks completed today\n"
    
    briefing_content += f"""
---

## Notes

This briefing is auto-generated. For detailed information:
- Check `/Vault/Dashboard.md` for system status
- Check `/Vault/Logs/` for audit logs
- Check `/Vault/Pending_Approval/` for items needing attention

---
*Generated by AI Employee v0.2 (Silver Tier)*
"""
    
    # Save briefing
    briefing_filename = f"{briefing_date}_Daily_Briefing.md"
    briefing_path = BRIEFINGS_DIR / briefing_filename
    
    with open(briefing_path, "w", encoding="utf-8") as f:
        f.write(briefing_content)
    
    print(f"[BRIEFING] ✓ Daily briefing generated: {briefing_path}")
    
    return {
        "success": True,
        "briefing_path": str(briefing_path),
        "type": "daily",
        "tasks_completed": completed_today,
        "pending_approvals": pending_count
    }


def generate_weekly_briefing() -> Dict[str, Any]:
    """Generate weekly CEO briefing with business audit."""
    timestamp = datetime.now()
    briefing_date = timestamp.strftime("%Y-%m-%d")
    week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Collect data
    completed_week = count_files_in_directory(DONE_DIR, hours=168)  # 7 days
    pending_count = len(get_pending_approvals())
    activity = get_activity_summary(hours=168)
    business_goals = load_business_goals()
    
    # Create briefing content
    briefing_content = f"""---
generated: {timestamp.isoformat()}
period: {week_start} to {briefing_date}
type: weekly
---

# Weekly CEO Briefing & Business Audit

**Generated:** {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
**Period:** {week_start} to {briefing_date}

---

## Executive Summary

Weekly business audit generated automatically by AI Employee.

---

## This Week's Performance

### Tasks Completed
- **Total:** {completed_week} tasks completed this week
- **Daily Average:** {completed_week / 7:.1f} tasks/day
- See `/Vault/Done/` folder for details

### Pending Approvals
- **Requiring Attention:** {pending_count} items
- Check `/Vault/Pending_Approval/` folder

### System Activity
- **Total Actions:** {activity['total_actions']}
- **Successful:** {activity['successful']}
- **Failed:** {activity['failed']}
- **Success Rate:** {activity['successful']}/{activity['total_actions'] if activity['total_actions'] > 0 else 1}

---

## Key Metrics

| Metric | This Week | Target |
|--------|-----------|--------|
| Tasks Completed | {completed_week} | - |
| Pending Approvals | {pending_count} | 0 |
| System Actions | {activity['total_actions']} | - |
| Success Rate | {activity['successful']}/{activity['total_actions'] if activity['total_actions'] > 0 else 1} | 100% |

---

## Business Goals Progress

"""
    
    if business_goals.get("exists"):
        briefing_content += "*Business goals file detected. Review for alignment.*\n\n"
    else:
        briefing_content += """*No business goals file found. Consider creating `Business_Goals.md` with:*
- Revenue targets
- Key metrics to track
- Active projects
- Subscription audit rules

"""
    
    briefing_content += f"""
## Bottlenecks Identified

"""
    
    if pending_count > 5:
        briefing_content += f"- ⚠️ **High pending approvals:** {pending_count} items awaiting review\n"
    if activity['failed'] > 0:
        briefing_content += f"- ⚠️ **Failed actions:** {activity['failed']} actions failed this week\n"
    if completed_week < 10:
        briefing_content += f"- ⚠️ **Low task completion:** Only {completed_week} tasks completed\n"
    
    if pending_count <= 5 and activity['failed'] == 0 and completed_week >= 10:
        briefing_content += "- ✅ **No major bottlenecks identified**\n"
    
    briefing_content += f"""

## Proactive Suggestions

"""
    
    if pending_count > 0:
        briefing_content += "- **Review Approvals:** Clear pending approvals to unblock workflows\n"
    if activity['failed'] > 0:
        briefing_content += "- **Investigate Failures:** Review logs for failed actions\n"
    
    briefing_content += f"""
## Action Items for This Week

- [ ] Review and clear pending approvals
- [ ] Review system logs for errors
- [ ] Update business goals if needed
- [ ] Plan upcoming week's priorities

---

## Last Week's Completed Tasks (Sample)

"""
    
    # Add recent tasks
    recent_tasks = get_recent_completed_tasks(hours=168)
    if recent_tasks:
        for task in recent_tasks[:20]:  # Show last 20
            briefing_content += f"- {task['name']}\n"
    else:
        briefing_content += "- No tasks completed this week\n"
    
    briefing_content += f"""

---

## Notes

This briefing is auto-generated. For detailed information:
- Check `/Vault/Dashboard.md` for system status
- Check `/Vault/Logs/` for detailed audit logs
- Check `/Vault/Pending_Approval/` for items needing attention
- Review `Business_Goals.md` for strategic alignment

---
*Generated by AI Employee v0.2 (Silver Tier)*
"""
    
    # Save briefing
    briefing_filename = f"{briefing_date}_Weekly_Briefing.md"
    briefing_path = BRIEFINGS_DIR / briefing_filename
    
    with open(briefing_path, "w", encoding="utf-8") as f:
        f.write(briefing_content)
    
    print(f"[BRIEFING] ✓ Weekly briefing generated: {briefing_path}")
    
    return {
        "success": True,
        "briefing_path": str(briefing_path),
        "type": "weekly",
        "tasks_completed": completed_week,
        "pending_approvals": pending_count
    }


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("[AI] Personal AI Employee - CEO Briefing Generator")
    print("=" * 60)
    
    weekly = "--weekly" in sys.argv
    
    if weekly:
        print("[BRIEFING] Generating WEEKLY briefing...")
        result = generate_weekly_briefing()
    else:
        print("[BRIEFING] Generating DAILY briefing...")
        result = generate_daily_briefing()
    
    print("=" * 60)
    
    if result.get("success"):
        print(f"[BRIEFING] Type: {result['type']}")
        print(f"[BRIEFING] Location: {result['briefing_path']}")
    else:
        print(f"[BRIEFING] Failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)
