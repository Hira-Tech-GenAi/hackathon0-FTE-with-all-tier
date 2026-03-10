"""
Agent Skills for Personal AI Employee - Bronze Tier

This module contains all the modular skills that the AI Employee can use.
Each skill is a standalone function that can be called by the agent_loop.

Skills:
1. move_file(source, destination) - Move files between folders
2. read_file(path) - Read file contents
3. write_to_file(path, content) - Create or update files
4. update_dashboard(status) - Update status in Dashboard.md
5. summarize_and_plan(file_path) - Analyze content and create action plan
6. mark_as_done(file_path) - Complete a task and archive
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


# =============================================================================
# Configuration
# =============================================================================

BASE_DIR = Path(__file__).parent.absolute()
VAULT_DIR = BASE_DIR / "ai-employee-vault"

INBOX_DIR = VAULT_DIR / "Inbox"
NEEDS_ACTION_DIR = VAULT_DIR / "Needs_Action"
DONE_DIR = VAULT_DIR / "Done"

DASHBOARD_PATH = VAULT_DIR / "Dashboard.md"

# Ensure directories exist
for directory in [VAULT_DIR, INBOX_DIR, NEEDS_ACTION_DIR, DONE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Skill 1: move_file
# =============================================================================

def move_file(source: str, destination: str) -> Dict[str, Any]:
    """
    Move a file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path (can be directory or full path)
    
    Returns:
        Dictionary with result status and details
    
    Example:
        >>> move_file("Inbox/task.txt", "Needs_Action/task.txt")
        {"success": True, "message": "File moved successfully", "source": "...", "destination": "..."}
    """
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        # Validate source exists
        if not source_path.exists():
            return {
                "success": False,
                "error": f"Source file not found: {source}",
                "source": str(source),
                "destination": str(destination)
            }
        
        # If destination is a directory, append filename
        if dest_path.is_dir():
            dest_path = dest_path / source_path.name
        
        # Create destination directory if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move the file
        shutil.move(str(source_path), str(dest_path))
        
        return {
            "success": True,
            "message": f"File moved successfully",
            "source": str(source_path),
            "destination": str(dest_path),
            "filename": source_path.name
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "source": str(source),
            "destination": str(destination)
        }


# =============================================================================
# Skill 2: read_file
# =============================================================================

def read_file(path: str) -> Dict[str, Any]:
    """
    Read the contents of a file.
    
    Args:
        path: Path to the file to read
    
    Returns:
        Dictionary with file contents or error message
    
    Example:
        >>> read_file("Needs_Action/task.txt")
        {"success": True, "content": "File contents here...", "path": "..."}
    """
    try:
        file_path = Path(path)
        
        # Validate file exists
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}",
                "path": str(path)
            }
        
        # Validate it's a file (not directory)
        if file_path.is_dir():
            return {
                "success": False,
                "error": f"Path is a directory, not a file: {path}",
                "path": str(path)
            }
        
        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "path": str(file_path),
            "filename": file_path.name,
            "size_bytes": len(content.encode("utf-8"))
        }
    
    except UnicodeDecodeError:
        # Try binary read for non-text files
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return {
                "success": True,
                "content": content.decode("latin-1"),  # Fallback encoding
                "path": str(file_path),
                "filename": file_path.name,
                "encoding": "latin-1 (fallback)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Could not read file (binary): {e}",
                "path": str(path)
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "path": str(path)
        }


# =============================================================================
# Skill 3: write_to_file
# =============================================================================

def write_to_file(path: str, content: str, append: bool = False) -> Dict[str, Any]:
    """
    Write content to a file. Creates the file if it doesn't exist.
    
    Args:
        path: Path to the file to write
        content: Content to write to the file
        append: If True, append to existing file; if False, overwrite
    
    Returns:
        Dictionary with result status and details
    
    Example:
        >>> write_to_file("Notes/task.md", "# Task\n\nDetails here...")
        {"success": True, "message": "File written successfully", "path": "..."}
    """
    try:
        file_path = Path(path)
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine write mode
        mode = "a" if append else "w"
        
        # Write content
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)
        
        action = "appended to" if append else "written to"
        return {
            "success": True,
            "message": f"Content {action} file successfully",
            "path": str(file_path),
            "filename": file_path.name,
            "bytes_written": len(content.encode("utf-8")),
            "appended": append
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "path": str(path)
        }


# =============================================================================
# Skill 4: update_dashboard
# =============================================================================

def update_dashboard(status: str, action: str = "", file_name: str = "", 
                     human_attention: bool = False, human_attention_reason: str = "") -> Dict[str, Any]:
    """
    Update the Dashboard.md with current status and recent actions.
    
    Args:
        status: Current system status (e.g., "Ready", "Processing", "Error")
        action: Description of the action taken
        file_name: Name of the file being processed
        human_attention: Whether human attention is needed
        human_attention_reason: Reason for human attention if applicable
    
    Returns:
        Dictionary with result status and details
    
    Example:
        >>> update_dashboard("Ready", "Processed file", "task.txt")
        {"success": True, "message": "Dashboard updated successfully"}
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_emoji = {"Ready": "🟢", "Processing": "🟡", "Error": "🔴"}.get(status, "⚪")
        
        # Read current dashboard
        dashboard_result = read_file(str(DASHBOARD_PATH))
        
        if not dashboard_result["success"]:
            # Create new dashboard if it doesn't exist
            dashboard_content = f"""# 📊 Personal AI Employee Dashboard

**Last Updated:** {datetime.now().strftime("%Y-%m-%d")}  
**Status:** {status_emoji} {status}

---

## Current Status

| Metric | Value |
|--------|-------|
| System State | {status} |
| Last Action | {action or "System initialized"} |

---

## Today's Tasks

- [ ] Monitor Inbox folder for new files
- [ ] Process incoming files using agent_loop
- [ ] Update dashboard after each action

---

## Recent Actions

| Timestamp | Action | File | Status |
|-----------|--------|------|--------|
| {timestamp} | {action} | {file_name} | Completed |

---

## Human Attention Needed

> 📌 **No items requiring human attention at this time.**

"""
        else:
            dashboard_content = dashboard_result["content"]
        
        # Update status line
        dashboard_content = _update_dashboard_status(dashboard_content, status, status_emoji)
        
        # Update last updated timestamp
        dashboard_content = _update_dashboard_timestamp(dashboard_content)
        
        # Add recent action
        dashboard_content = _add_recent_action(dashboard_content, timestamp, action, file_name)
        
        # Update human attention section if needed
        if human_attention:
            dashboard_content = _add_human_attention_item(
                dashboard_content, timestamp, file_name, human_attention_reason
            )
        
        # Write updated dashboard
        write_result = write_to_file(str(DASHBOARD_PATH), dashboard_content)
        
        return {
            "success": write_result["success"],
            "message": "Dashboard updated successfully" if write_result["success"] else write_result.get("error", "Unknown error"),
            "status": status,
            "timestamp": timestamp
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _update_dashboard_status(content: str, status: str, emoji: str) -> str:
    """Update the status line in dashboard."""
    import re
    pattern = r"\*\*Status:\*\* .*"
    replacement = f"**Status:** {emoji} {status}"
    return re.sub(pattern, replacement, content)


def _update_dashboard_timestamp(content: str) -> str:
    """Update the last updated timestamp in dashboard."""
    import re
    today = datetime.now().strftime("%Y-%m-%d")
    pattern = r"\*\*Last Updated:\*\* .*"
    replacement = f"**Last Updated:** {today}"
    return re.sub(pattern, replacement, content)


def _add_recent_action(content: str, timestamp: str, action: str, file_name: str) -> str:
    """Add a new row to the recent actions table."""
    import re
    
    # Find the recent actions table and add a new row
    pattern = r"(\| Timestamp \| Action \| File \| Status \|\n\|-+\|)?"
    new_row = f"| {timestamp} | {action} | {file_name} | Completed |\n"
    
    # Insert after the header
    match = re.search(pattern, content)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + "\n" + new_row + content[insert_pos:]
    
    return content


def _add_human_attention_item(content: str, timestamp: str, file_name: str, reason: str) -> str:
    """Add an item to the human attention section."""
    import re
    
    pattern = r"(> 📌 \*\*No items requiring human attention at this time\.\*\*)"
    replacement = f"""> 📌 **Items requiring human attention:**
>
> - **{timestamp}** - {file_name}: {reason}"""
    
    return re.sub(pattern, replacement, content)


# =============================================================================
# Skill 5: summarize_and_plan
# =============================================================================

def summarize_and_plan(file_path: str) -> Dict[str, Any]:
    """
    Read a file and create a summary with an action plan.
    
    This skill analyzes the content and generates:
    - A brief summary of the content
    - Suggested actions to take
    - Priority level (high/medium/low)
    
    Args:
        file_path: Path to the file to analyze
    
    Returns:
        Dictionary with summary, action plan, and priority
    
    Example:
        >>> summarize_and_plan("Needs_Action/task.txt")
        {"success": True, "summary": "...", "action_plan": ["...", "..."], "priority": "medium"}
    """
    try:
        # Read the file
        read_result = read_file(file_path)
        
        if not read_result["success"]:
            return {
                "success": False,
                "error": read_result.get("error", "Could not read file"),
                "file_path": file_path
            }
        
        content = read_result["content"]
        filename = read_result["filename"]
        
        # Generate summary (basic implementation - can be enhanced with AI)
        summary = _generate_summary(content, filename)
        
        # Generate action plan
        action_plan = _generate_action_plan(content, filename)
        
        # Determine priority
        priority = _determine_priority(content, filename)
        
        # Create metadata file with summary
        metadata_content = f"""---
original_file: {filename}
analyzed_date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
priority: {priority}
status: analyzed
---

# Summary & Action Plan

## Summary
{summary}

## Action Plan
{chr(10).join(f"- [ ] {action}" for action in action_plan)}

## Notes
- File analyzed by Personal AI Employee (Bronze Tier)
- Priority: {priority}
"""
        
        # Write summary to metadata file
        metadata_path = Path(file_path).parent / f".{Path(file_path).stem}_summary.md"
        write_to_file(str(metadata_path), metadata_content)
        
        return {
            "success": True,
            "file_path": file_path,
            "filename": filename,
            "summary": summary,
            "action_plan": action_plan,
            "priority": priority,
            "metadata_path": str(metadata_path)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }


def _generate_summary(content: str, filename: str) -> str:
    """Generate a brief summary of the file content."""
    # Basic summary generation
    lines = content.strip().split("\n")
    word_count = len(content.split())
    line_count = len(lines)
    
    # Try to extract first meaningful paragraph
    first_lines = [line.strip() for line in lines[:5] if line.strip()]
    preview = " ".join(first_lines)[:200]
    
    return f"This file ({filename}) contains {word_count} words across {line_count} lines. Preview: {preview}..."


def _generate_action_plan(content: str, filename: str) -> list:
    """Generate suggested actions based on content."""
    actions = []
    content_lower = content.lower()
    
    # Detect common patterns
    if "todo" in content_lower or "task" in content_lower:
        actions.append("Identify and list all tasks mentioned")
        actions.append("Prioritize tasks by urgency")
    
    if "meeting" in content_lower:
        actions.append("Extract meeting details (date, time, attendees)")
        actions.append("Add to calendar if applicable")
    
    if "deadline" in content_lower or "due" in content_lower:
        actions.append("Note deadline and set reminder")
    
    if "question" in content_lower or "?" in content:
        actions.append("Identify questions that need answers")
    
    # Default actions
    if not actions:
        actions.append("Review content thoroughly")
        actions.append("Determine if action is required")
    
    actions.append("Move to Done folder after processing")
    
    return actions


def _determine_priority(content: str, filename: str) -> str:
    """Determine priority level based on content."""
    content_lower = content.lower()
    
    high_priority_keywords = ["urgent", "asap", "emergency", "critical", "immediately", "today"]
    medium_priority_keywords = ["soon", "this week", "important", "deadline", "reminder"]
    
    for keyword in high_priority_keywords:
        if keyword in content_lower:
            return "high"
    
    for keyword in medium_priority_keywords:
        if keyword in content_lower:
            return "medium"
    
    return "low"


# =============================================================================
# Skill 6: mark_as_done
# =============================================================================

def mark_as_done(file_path: str, summary: str = "") -> Dict[str, Any]:
    """
    Mark a task as complete by moving it to the Done folder.
    
    Args:
        file_path: Path to the file to mark as done
        summary: Optional summary of what was accomplished
    
    Returns:
        Dictionary with result status and details
    
    Example:
        >>> mark_as_done("Needs_Action/task.txt", "Processed and categorized")
        {"success": True, "message": "File moved to Done", "destination": "..."}
    """
    try:
        source_path = Path(file_path)
        
        # Validate source exists
        if not source_path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }
        
        # Generate destination path in Done folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = source_path.stem
        suffix = source_path.suffix
        dest_filename = f"{stem}_done_{timestamp}{suffix}"
        dest_path = DONE_DIR / dest_filename
        
        # Move file to Done folder
        shutil.move(str(source_path), str(dest_path))
        
        # Create completion note if summary provided
        if summary:
            note_path = DONE_DIR / f".{stem}_completion_note.md"
            note_content = f"""---
completed_date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
original_file: {source_path.name}
---

# Completion Note

**Summary:** {summary}

**Completed At:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

"""
            write_to_file(str(note_path), note_content)
        
        # Also move any associated metadata files
        meta_pattern = source_path.parent / f".{stem}_*"
        for meta_file in source_path.parent.glob(f".{stem}_*"):
            if meta_file != source_path:
                try:
                    shutil.move(str(meta_file), str(DONE_DIR / meta_file.name))
                except Exception:
                    pass  # Skip if metadata file doesn't exist or can't be moved
        
        return {
            "success": True,
            "message": "File marked as done and moved to Done folder",
            "original_path": str(source_path),
            "destination": str(dest_path),
            "filename": dest_filename,
            "summary": summary
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }


# =============================================================================
# Skill Registry
# =============================================================================

# Dictionary mapping skill names to functions
SKILLS = {
    "move_file": move_file,
    "read_file": read_file,
    "write_to_file": write_to_file,
    "update_dashboard": update_dashboard,
    "summarize_and_plan": summarize_and_plan,
    "mark_as_done": mark_as_done,
}


def get_skill(skill_name: str):
    """
    Get a skill function by name.
    
    Args:
        skill_name: Name of the skill to retrieve
    
    Returns:
        The skill function, or None if not found
    """
    return SKILLS.get(skill_name)


def list_skills() -> list:
    """
    List all available skills.
    
    Returns:
        List of skill names
    """
    return list(SKILLS.keys())


# =============================================================================
# Entry Point (for testing)
# =============================================================================

if __name__ == "__main__":
    print("Available Skills:")
    for skill_name in list_skills():
        print(f"  - {skill_name}")
    
    print("\nTesting read_file skill...")
    result = read_file(str(DASHBOARD_PATH))
    if result["success"]:
        print(f"[OK] Dashboard read successfully ({result.get('size_bytes', 0)} bytes)")
    else:
        print(f"[ERROR] {result.get('error', 'Unknown error')}")
