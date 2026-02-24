"""
Main Agent for Personal AI Employee - Bronze Tier

This module contains the core agent_loop function that:
1. Reads Dashboard, Handbook, and trigger file
2. Sends context to Claude with ReAct-style system prompt
3. Parses Claude's JSON response
4. Executes the specified skill
5. Loops until task is complete
6. Moves file to Done and updates Dashboard

The agent uses a ReAct (Reason + Act) pattern where Claude thinks,
decides on an action, and the system executes it.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import skills module
from skills import (
    SKILLS,
    read_file,
    write_to_file,
    update_dashboard,
    summarize_and_plan,
    mark_as_done,
    move_file,
    list_skills,
    # Silver Tier skills
    create_plan,
    request_approval,
    check_approval_status,
    log_action,
    send_email_draft,
    update_plan_step,
)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional


# =============================================================================
# Configuration
# =============================================================================

BASE_DIR = Path(__file__).parent.absolute()
VAULT_DIR = BASE_DIR / "ai-employee-vault"

DASHBOARD_PATH = VAULT_DIR / "Dashboard.md"
HANDBOOK_PATH = VAULT_DIR / "Company_Handbook.md"

# OpenAI API configuration
# Set OPENAI_API_KEY environment variable before running
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default to gpt-4o-mini for cost efficiency
MAX_ITERATIONS = 10  # Maximum loop iterations per task
MAX_TOKENS = 2048  # Max tokens for OpenAI response


# =============================================================================
# System Prompt
# =============================================================================

SYSTEM_PROMPT = """You are a Personal AI Employee working in the Silver Tier system.
Your job is to process files that arrive in the Inbox folder and take appropriate actions.

## Your Capabilities (Skills)

You have access to these skills. Respond with JSON to use them:

### Core Skills
1. **read_file** - Read contents of a file
   Parameters: {{"path": "path/to/file.txt"}}

2. **write_to_file** - Write content to a file
   Parameters: {{"path": "path/to/file.txt", "content": "text to write"}}

3. **move_file** - Move a file from source to destination
   Parameters: {{"source": "path/from", "destination": "path/to"}}

4. **update_dashboard** - Update the Dashboard.md with status
   Parameters: {{"status": "Ready|Processing|Error", "action": "what you did", "file_name": "filename"}}

5. **summarize_and_plan** - Analyze a file and create summary + action plan
   Parameters: {{"file_path": "path/to/file.txt"}}

6. **mark_as_done** - Mark a task as complete and move to Done folder
   Parameters: {{"file_path": "path/to/file.txt", "summary": "brief summary of what was done"}}

### Silver Tier Skills
7. **create_plan** - Create a Plan.md with objective and action steps
   Parameters: {{"objective": "what to achieve", "file_path": "path/to/trigger.txt"}}

8. **request_approval** - Request human approval for sensitive actions
   Parameters: {{"action_type": "email_send|payment|etc", "details": {{"key": "value"}}, "reason": "why approval needed"}}

9. **check_approval_status** - Check status of an approval request
   Parameters: {{"approval_id": "approval request ID"}}

10. **log_action** - Log an action to the audit log
    Parameters: {{"action_type": "type of action", "details": {{"key": "value"}}, "result": "success|failed"}}

11. **send_email_draft** - Create an email draft (requires approval to send)
    Parameters: {{"to": "email@example.com", "subject": "subject", "body": "email content"}}

12. **update_plan_step** - Update a step in a plan file
    Parameters: {{"plan_path": "path/to/plan.md", "step_number": 1, "completed": true}}

## Response Format

You MUST respond with valid JSON in this exact format:

```json
{{
    "thinking": "Your reasoning about what to do next",
    "skill_to_use": "name_of_skill",
    "parameters": {{
        "param1": "value1",
        "param2": 123
    }}
}}
```

## Rules

1. **Always think first** - Explain your reasoning in the "thinking" field
2. **One skill at a time** - Only call one skill per response
3. **Read before acting** - Always read a file before processing it
4. **Create plans for complex tasks** - Use create_plan for multi-step tasks
5. **Request approval for sensitive actions** - Email sends, payments, external actions
6. **Follow the Handbook** - Refer to Company_Handbook.md for guidance
7. **Update Dashboard** - Keep Dashboard.md updated after significant actions
8. **Log all actions** - Use log_action for audit trail
9. **Complete the task** - Continue until the file is processed and moved to Done
10. **Ask for help** - If unsure, set status to require human attention

## Workflow

1. Read the trigger file to understand what needs to be done
2. Analyze the content and determine appropriate actions
3. For complex tasks: create a Plan.md first
4. Use skills to process the file
5. Request approval for sensitive actions (email, payments, etc.)
6. When complete, use mark_as_done to move it to Done folder
7. Update the Dashboard with final status
8. Log the action for audit

## Example Response

```json
{{
    "thinking": "I need to first read the file to understand what task is being requested.",
    "skill_to_use": "read_file",
    "parameters": {{
        "path": "Needs_Action/example.txt"
    }}
}}
```

Remember: Respond ONLY with valid JSON. No additional text outside the JSON."""


# =============================================================================
# OpenAI API Integration
# =============================================================================

def call_openai(messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """
    Call OpenAI API with messages and get response.

    Args:
        messages: List of message dictionaries with 'role' and 'content'

    Returns:
        Parsed JSON response from OpenAI, or None if error
    """
    try:
        # Try to import openai
        import openai
    except ImportError:
        print("[AGENT] Warning: openai package not installed.")
        print("[AGENT] Install with: uv add openai")
        return None

    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[AGENT] Error: OPENAI_API_KEY environment variable not set.")
        print("[AGENT] Please set your API key and try again.")
        return None

    try:
        # Create client
        client = openai.OpenAI(api_key=api_key)

        # Prepare messages - add system message as first
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        full_messages.extend(messages)

        # Make API call
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=MAX_TOKENS,
            messages=full_messages,
            temperature=0.1,  # Low temperature for more consistent JSON output
            response_format={"type": "json_object"}  # Request JSON format
        )

        # Extract response text
        response_text = response.choices[0].message.content

        # Parse JSON from response
        return parse_openai_response(response_text)

    except Exception as e:
        print(f"[AGENT] Error calling OpenAI: {e}")
        return None


def parse_openai_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON response from OpenAI.

    Args:
        response_text: Raw text response from OpenAI

    Returns:
        Parsed JSON dictionary, or None if parsing fails
    """
    try:
        # Try to find JSON in the response (handle markdown code blocks)
        import re

        # Look for JSON block
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to parse the entire response as JSON
            json_str = response_text.strip()

        # Parse JSON
        return json.loads(json_str)

    except json.JSONDecodeError as e:
        print(f"[AGENT] Error parsing JSON response: {e}")
        print(f"[AGENT] Raw response: {response_text[:500]}...")
        return None


# =============================================================================
# Agent Loop
# =============================================================================

def agent_loop(trigger_file: str, max_iterations: int = MAX_ITERATIONS) -> Dict[str, Any]:
    """
    Main agent loop that processes a trigger file.

    This function:
    1. Reads Dashboard, Handbook, and trigger file
    2. Sends context to OpenAI with system prompt
    3. Receives JSON response with skill to execute
    4. Executes the skill
    5. Loops until task is complete or max iterations reached

    Args:
        trigger_file: Path to the file that triggered the agent
        max_iterations: Maximum number of loop iterations

    Returns:
        Dictionary with final status and results
    """
    import sys
    # Enable UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    print("\n" + "=" * 60)
    print("[AI] Personal AI Employee - Agent Loop Started")
    print("=" * 60)
    print(f"[AGENT] Trigger file: {trigger_file}")
    print(f"[AGENT] Max iterations: {max_iterations}")

    # Update dashboard to show processing status
    update_dashboard(
        status="Processing",
        action="Starting agent loop",
        file_name=Path(trigger_file).name
    )

    # Read context files
    dashboard_result = read_file(str(DASHBOARD_PATH))
    handbook_result = read_file(str(HANDBOOK_PATH))
    trigger_result = read_file(trigger_file)

    # Build context
    dashboard_content = dashboard_result.get("content", "Dashboard not found")
    handbook_content = handbook_result.get("content", "Handbook not found")
    trigger_content = trigger_result.get("content", "Could not read trigger file")
    trigger_filename = Path(trigger_file).name

    # Build messages for OpenAI
    messages = [
        {
            "role": "user",
            "content": f"""I need you to process this file that arrived in my Inbox.

## Current Dashboard Status
{dashboard_content[:2000]}...

## Company Handbook (Your Guidelines)
{handbook_content[:3000]}...

## Trigger File to Process
**Filename:** {trigger_filename}
**Path:** {trigger_file}

**Content:**
{trigger_content}

---

Please analyze this file and tell me what skill to use first to process it.
Remember to respond with JSON containing: thinking, skill_to_use, and parameters."""
        }
    ]

    # Main processing loop
    iteration = 0
    task_complete = False
    last_skill_used = None

    while iteration < max_iterations and not task_complete:
        iteration += 1
        print(f"\n[AGENT] Iteration {iteration}/{max_iterations}")

        # Call OpenAI for decision
        print("[AGENT] Consulting OpenAI...")
        openai_response = call_openai(messages)

        if openai_response is None:
            print("[AGENT] Failed to get response from OpenAI.")
            # Fallback: use local processing
            openai_response = fallback_processing(trigger_file, trigger_content)

        # Extract response components
        thinking = openai_response.get("thinking", "No thinking provided")
        skill_name = openai_response.get("skill_to_use", "")
        parameters = openai_response.get("parameters", {})

        print(f"[AGENT] Thinking: {thinking[:200]}...")
        print(f"[AGENT] Skill: {skill_name}")
        print(f"[AGENT] Parameters: {parameters}")

        # Check if task is complete
        if skill_name == "mark_as_done":
            task_complete = True

        # Execute the skill
        skill_result = execute_skill(skill_name, parameters)

        if skill_result is None:
            print(f"[AGENT] Skill '{skill_name}' not found or failed.")
            continue

        print(f"[AGENT] Skill result: {skill_result.get('success', False)}")

        # Add skill result to conversation history
        messages.append({
            "role": "assistant",
            "content": json.dumps({
                "thinking": thinking,
                "skill_to_use": skill_name,
                "parameters": parameters
            })
        })

        messages.append({
            "role": "user",
            "content": f"Skill '{skill_name}' executed. Result: {json.dumps(skill_result, indent=2)}\n\nWhat should I do next?"
        })

        last_skill_used = skill_name

        # Small delay to avoid rate limiting
        time.sleep(0.5)

    # Task complete or max iterations reached
    print("\n" + "=" * 60)
    if task_complete:
        print("[AGENT] ✓ Task completed successfully!")
    else:
        print(f"[AGENT] ⚠ Max iterations ({max_iterations}) reached.")
    print("=" * 60)

    # Final dashboard update
    final_status = "Ready" if task_complete else "Error"
    final_action = f"Processing completed after {iteration} iterations" if task_complete else f"Max iterations reached, last skill: {last_skill_used}"

    update_dashboard(
        status=final_status,
        action=final_action,
        file_name=trigger_filename
    )

    return {
        "success": task_complete,
        "iterations": iteration,
        "trigger_file": trigger_file,
        "final_status": final_status,
        "last_skill": last_skill_used
    }


def execute_skill(skill_name: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Execute a skill with the given parameters.
    
    Args:
        skill_name: Name of the skill to execute
        parameters: Dictionary of parameters for the skill
    
    Returns:
        Result dictionary from the skill, or None if skill not found
    """
    skill_func = SKILLS.get(skill_name)
    
    if skill_func is None:
        print(f"[AGENT] Unknown skill: {skill_name}")
        print(f"[AGENT] Available skills: {list_skills()}")
        return None
    
    try:
        # Execute skill with parameters
        result = skill_func(**parameters)
        return result
    except TypeError as e:
        print(f"[AGENT] Error executing skill '{skill_name}': {e}")
        print(f"[AGENT] Parameters provided: {parameters}")
        return None
    except Exception as e:
        print(f"[AGENT] Unexpected error in skill '{skill_name}': {e}")
        return None


def fallback_processing(trigger_file: str, content: str) -> Dict[str, Any]:
    """
    Fallback processing when Claude API is unavailable.
    
    This provides basic local processing without AI.
    
    Args:
        trigger_file: Path to the trigger file
        content: Content of the trigger file
    
    Returns:
        Fallback response dictionary
    """
    print("[AGENT] Using fallback local processing...")
    
    # Basic analysis
    content_lower = content.lower()
    
    # Determine appropriate action
    if "done" in content_lower or "complete" in content_lower:
        return {
            "thinking": "File appears to be already completed. Moving to Done folder.",
            "skill_to_use": "mark_as_done",
            "parameters": {
                "file_path": trigger_file,
                "summary": "File marked as complete based on content analysis"
            }
        }
    elif "todo" in content_lower or "task" in content_lower:
        return {
            "thinking": "File contains tasks. Creating summary and action plan.",
            "skill_to_use": "summarize_and_plan",
            "parameters": {
                "file_path": trigger_file
            }
        }
    else:
        return {
            "thinking": "Processing file with default actions. Reading and summarizing.",
            "skill_to_use": "summarize_and_plan",
            "parameters": {
                "file_path": trigger_file
            }
        }


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    # Check for command line argument
    if len(sys.argv) < 2:
        print("Usage: python main_agent.py <file_path>")
        print("Example: python main_agent.py ai-employee-vault/Needs_Action/task.txt")
        print("\nOr run the filesystem_watcher.py to automatically process Inbox files.")
        sys.exit(1)
    
    trigger_file_path = sys.argv[1]
    
    # Validate file exists
    if not Path(trigger_file_path).exists():
        print(f"Error: File not found: {trigger_file_path}")
        sys.exit(1)
    
    # Run agent loop
    result = agent_loop(trigger_file_path)
    
    # Print final result
    print("\n" + "=" * 60)
    print("📊 Final Result:")
    print(f"   Success: {result['success']}")
    print(f"   Iterations: {result['iterations']}")
    print(f"   Final Status: {result['final_status']}")
    print("=" * 60)
