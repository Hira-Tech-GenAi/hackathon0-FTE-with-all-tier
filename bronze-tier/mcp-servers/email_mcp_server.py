#!/usr/bin/env python3
"""
Email MCP Server for Personal AI Employee - Silver Tier

Model Context Protocol (MCP) server for sending emails.
This server exposes email capabilities to Claude Code.

Usage:
    python email_mcp_server.py

Configuration:
    Set in .env:
    - SMTP_SERVER: SMTP server address (default: smtp.gmail.com)
    - SMTP_PORT: SMTP port (default: 587)
    - EMAIL_ADDRESS: Your email address
    - EMAIL_PASSWORD: Your email password or app password
"""

import os
import sys
import json
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =============================================================================
# Configuration
# =============================================================================

BASE_DIR = Path(__file__).parent.parent.absolute()
VAULT_DIR = BASE_DIR / "ai-employee-vault"
LOGS_DIR = VAULT_DIR / "Logs"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# SMTP Settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Dry run mode (log but don't send)
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


# =============================================================================
# Email Functions
# =============================================================================

def send_email(to: str, subject: str, body: str, 
               from_addr: Optional[str] = None,
               cc: Optional[List[str]] = None,
               bcc: Optional[List[str]] = None,
               attachments: Optional[List[str]] = None,
               html: bool = False) -> Dict[str, Any]:
    """
    Send an email via SMTP.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        from_addr: Sender email (defaults to EMAIL_ADDRESS)
        cc: List of CC email addresses
        bcc: List of BCC email addresses
        attachments: List of file paths to attach
        html: Whether body is HTML content
    
    Returns:
        Dictionary with send status and details
    """
    try:
        from_addr = from_addr or EMAIL_ADDRESS
        
        if not from_addr or not EMAIL_PASSWORD:
            return {
                "success": False,
                "error": "Email credentials not configured",
                "config_hint": "Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env"
            }
        
        # Create message
        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = to
        msg["Subject"] = subject
        
        if cc:
            msg["Cc"] = ", ".join(cc)
        
        # Add body
        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type))
        
        # Add attachments
        if attachments:
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={Path(file_path).name}"
                    )
                    msg.attach(part)
                except Exception as e:
                    print(f"Warning: Could not attach {file_path}: {e}")
        
        # Dry run mode
        if DRY_RUN:
            print(f"[EMAIL MCP] DRY RUN: Would send email to {to}")
            print(f"[EMAIL MCP] Subject: {subject}")
            print(f"[EMAIL MCP] Body: {body[:200]}...")
            
            # Log the email
            log_email_action(to, subject, "dry_run")
            
            return {
                "success": True,
                "message": "Email logged (dry run mode)",
                "dry_run": True,
                "to": to,
                "subject": subject
            }
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        recipients = [to]
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)
        
        server.sendmail(from_addr, recipients, msg.as_string())
        server.quit()
        
        print(f"[EMAIL MCP] ✓ Email sent to {to}")
        
        # Log the action
        log_email_action(to, subject, "sent")
        
        return {
            "success": True,
            "message": f"Email sent to {to}",
            "to": to,
            "subject": subject,
            "attachments": attachments or []
        }
        
    except smtplib.SMTPAuthenticationError:
        error_msg = "SMTP authentication failed. Check email credentials."
        print(f"[EMAIL MCP] ✗ {error_msg}")
        log_email_action(to, subject, "failed", error_msg)
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Failed to send email: {e}"
        print(f"[EMAIL MCP] ✗ {error_msg}")
        log_email_action(to, subject, "failed", error_msg)
        return {
            "success": False,
            "error": error_msg
        }


def log_email_action(to: str, subject: str, status: str, error: str = ""):
    """Log email action to audit log."""
    log_date = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"email_{log_date}.json"
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "email_send",
        "actor": "email_mcp_server",
        "to": to,
        "subject": subject,
        "status": status,
        "error": error
    }
    
    # Load existing log
    log_data = {"date": log_date, "emails": []}
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except:
            pass
    
    log_data["emails"].append(log_entry)
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)


# =============================================================================
# MCP Server Protocol
# =============================================================================

class EmailMCPServer:
    """
    Model Context Protocol server for email operations.
    
    This implements the MCP specification for exposing email capabilities
    to Claude Code.
    """
    
    def __init__(self):
        self.name = "email-mcp"
        self.version = "1.0.0"
        self.capabilities = {
            "tools": {
                "send_email": {
                    "description": "Send an email via SMTP",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Recipient email address"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body content"
                            },
                            "cc": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "CC recipients"
                            },
                            "bcc": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "BCC recipients"
                            },
                            "attachments": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File paths to attach"
                            },
                            "html": {
                                "type": "boolean",
                                "description": "Whether body is HTML"
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                },
                "test_connection": {
                    "description": "Test email server connection",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP request.
        
        Args:
            request: MCP request dictionary
        
        Returns:
            MCP response dictionary
        """
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        # Handle different methods
        if method == "initialize":
            return self._response(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": self.capabilities,
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                }
            })
        
        elif method == "tools/list":
            return self._response(request_id, {
                "tools": [
                    {
                        "name": tool_name,
                        "description": tool_info["description"],
                        "inputSchema": tool_info["inputSchema"]
                    }
                    for tool_name, tool_info in self.capabilities["tools"].items()
                ]
            })
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            
            if tool_name == "send_email":
                result = send_email(**tool_args)
                return self._response(request_id, {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                })
            
            elif tool_name == "test_connection":
                result = self._test_connection()
                return self._response(request_id, {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                })
        
        elif method == "notifications/initialized":
            # No response needed for notifications
            return None
        
        # Unknown method
        return self._error(request_id, -32601, f"Method not found: {method}")
    
    def _response(self, request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a success response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    def _error(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    def _test_connection(self) -> Dict[str, Any]:
        """Test the email server connection."""
        try:
            if DRY_RUN:
                return {
                    "success": True,
                    "message": "Connection test (dry run mode)",
                    "smtp_server": SMTP_SERVER,
                    "smtp_port": SMTP_PORT,
                    "email_address": EMAIL_ADDRESS or "(not configured)"
                }
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.quit()
            
            return {
                "success": True,
                "message": "Connection successful",
                "smtp_server": SMTP_SERVER,
                "smtp_port": SMTP_PORT,
                "email_address": EMAIL_ADDRESS
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "smtp_server": SMTP_SERVER,
                "smtp_port": SMTP_PORT
            }


# =============================================================================
# Main Server Loop
# =============================================================================

def run_stdio_server():
    """
    Run the MCP server using stdio transport.
    
    This is the primary mode for Claude Code integration.
    """
    print(f"[EMAIL MCP] Starting Email MCP Server v1.0.0", file=sys.stderr)
    print(f"[EMAIL MCP] SMTP Server: {SMTP_SERVER}:{SMTP_PORT}", file=sys.stderr)
    print(f"[EMAIL MCP] Email: {EMAIL_ADDRESS or '(not configured)'}", file=sys.stderr)
    print(f"[EMAIL MCP] Dry Run: {DRY_RUN}", file=sys.stderr)
    print(f"[EMAIL MCP] Ready for requests...\n", file=sys.stderr)
    
    server = EmailMCPServer()
    
    # Read requests from stdin
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            
            if response:
                # Write response to stdout
                print(json.dumps(response), flush=True)
        
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {e}"
                }
            }
            print(json.dumps(error_response), flush=True)
        
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {e}"
                }
            }
            print(json.dumps(error_response), flush=True)


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    run_stdio_server()
