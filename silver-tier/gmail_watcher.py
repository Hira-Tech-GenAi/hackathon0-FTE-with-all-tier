"""
Gmail Watcher for Personal AI Employee - Bronze Tier

Monitors Gmail inbox for new emails using IMAP.
When a new email is detected, it saves the content as a file in Inbox,
then triggers the agent_loop() function to process it.

Uses IMAP IDLE for real-time notifications when available.
"""

import os
import sys
import time
import email
import imaplib
import base64
from datetime import datetime
from pathlib import Path
from email.header import decode_header
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =============================================================================
# Configuration
# =============================================================================

# Base paths
BASE_DIR = Path(__file__).parent.absolute()
VAULT_DIR = BASE_DIR / "ai-employee-vault"
INBOX_DIR = VAULT_DIR / "Inbox"

# Ensure directories exist
for directory in [VAULT_DIR, INBOX_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Gmail IMAP settings
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_IMAP_PORT = 993
CHECK_INTERVAL_SECONDS = 60  # How often to check for new emails

# Limits
DAILY_EMAIL_LIMIT = int(os.getenv("GMAIL_DAILY_LIMIT", "10"))  # Max emails to process per day

# Email filtering - only process emails matching these keywords
FILTER_CATEGORIES = os.getenv("GMAIL_FILTER_CATEGORIES", "help,programming,news,update").split(",")

# Keywords for each category (case-insensitive matching)
FILTER_KEYWORDS = {
    "help": ["help", "support", "assist", "question", "issue", "problem", "error", "bug", "fix"],
    "programming": ["code", "program", "python", "javascript", "java", "c++", "react", "api", 
                    "database", "sql", "git", "github", "gitlab", "devops", "docker", "kubernetes",
                    "software", "development", "developer", "coding", "debug", "algorithm"],
    "news": ["news", "update", "announcement", "release", "changelog", "new feature", "version",
             "launch", "beta", "alpha", "deprecated", "migration"],
    "update": ["update", "upgrade", "patch", "security", "maintenance", "schedule", "downtime"]
}

# Email settings
SEEN_EMAILS_FILE = BASE_DIR / ".seen_emails.txt"  # Track processed email IDs
DAILY_LIMIT_FILE = BASE_DIR / ".gmail_daily_limit.txt"  # Track daily limit reset


# =============================================================================
# Helper Functions
# =============================================================================

def load_seen_emails() -> set:
    """Load set of already processed email IDs."""
    if SEEN_EMAILS_FILE.exists():
        with open(SEEN_EMAILS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_seen_email(email_id: str):
    """Save an email ID as processed."""
    with open(SEEN_EMAILS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{email_id}\n")


def check_daily_limit() -> tuple:
    """
    Check if daily limit has been reached.
    
    Returns:
        Tuple of (limit_reached: bool, count: int)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not DAILY_LIMIT_FILE.exists():
        return False, 0
    
    with open(DAILY_LIMIT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) >= 2:
            file_date = lines[0].strip()
            count = int(lines[1].strip())
            
            if file_date == today:
                return count >= DAILY_EMAIL_LIMIT, count
    
    return False, 0


def get_daily_count() -> int:
    """Get current daily count."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not DAILY_LIMIT_FILE.exists():
        return 0
    
    with open(DAILY_LIMIT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) >= 2 and lines[0].strip() == today:
            return int(lines[1].strip())
    
    return 0


def increment_daily_count():
    """Increment the daily email count."""
    today = datetime.now().strftime("%Y-%m-%d")
    current_count = get_daily_count()
    
    with open(DAILY_LIMIT_FILE, "w", encoding="utf-8") as f:
        f.write(f"{today}\n{current_count + 1}\n")


def reset_daily_count_if_new_day():
    """Reset count if it's a new day."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not DAILY_LIMIT_FILE.exists():
        with open(DAILY_LIMIT_FILE, "w", encoding="utf-8") as f:
            f.write(f"{today}\n0\n")
        return
    
    with open(DAILY_LIMIT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) >= 1:
            file_date = lines[0].strip()
            if file_date != today:
                with open(DAILY_LIMIT_FILE, "w", encoding="utf-8") as f:
                    f.write(f"{today}\n0\n")


def filter_email(subject: str, body: str, sender: str) -> tuple:
    """
    Check if email matches filter criteria.
    
    Args:
        subject: Email subject
        body: Email body
        sender: Email sender
        
    Returns:
        Tuple of (matches: bool, matched_categories: list, matched_keywords: list)
    """
    # Combine text for searching
    text_to_search = f"{subject} {body} {sender}".lower()
    
    matched_categories = []
    matched_keywords = []
    
    # Only check configured categories
    for category in FILTER_CATEGORIES:
        category = category.strip().lower()
        if category in FILTER_KEYWORDS:
            for keyword in FILTER_KEYWORDS[category]:
                if keyword.lower() in text_to_search:
                    if category not in matched_categories:
                        matched_categories.append(category)
                    if keyword not in matched_keywords:
                        matched_keywords.append(keyword)
    
    return len(matched_categories) > 0, matched_categories, matched_keywords


def decode_mime_words(header_value):
    """Decode MIME-encoded header values."""
    if not header_value:
        return ""
    
    decoded_parts = []
    for part, encoding in decode_header(header_value):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
            except (UnicodeDecodeError, LookupError):
                decoded_parts.append(part.decode("latin-1", errors="replace"))
        else:
            decoded_parts.append(part)
    
    return "".join(decoded_parts)


def get_email_body(msg):
    """
    Extract the body content from an email message.
    Prefers HTML body, falls back to plain text.
    
    Args:
        msg: email.message.Message object
        
    Returns:
        Tuple of (body_text, body_type)
    """
    body = ""
    body_type = "text"
    
    if msg.is_multipart():
        # Try to get HTML content first, then plain text
        html_content = None
        text_content = None
        
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
            
            if content_type == "text/html" and html_content is None:
                try:
                    html_content = part.get_payload(decode=True).decode("utf-8", errors="replace")
                except (UnicodeDecodeError, AttributeError):
                    pass
            
            if content_type == "text/plain" and text_content is None:
                try:
                    text_content = part.get_payload(decode=True).decode("utf-8", errors="replace")
                except (UnicodeDecodeError, AttributeError):
                    pass
        
        # Prefer HTML, fall back to text
        if html_content:
            body = html_content
            body_type = "html"
        elif text_content:
            body = text_content
            body_type = "text"
    else:
        # Not multipart
        try:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except (UnicodeDecodeError, AttributeError):
            body = str(msg.get_payload())
    
    return body, body_type


def save_email_as_file(subject: str, sender: str, date: str, body: str, body_type: str = "text") -> Path:
    """
    Save email content as a file in the Inbox folder.
    
    Args:
        subject: Email subject line
        sender: Email sender address
        date: Email date
        body: Email body content
        body_type: Type of body content ('text' or 'html')
        
    Returns:
        Path to the saved file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create safe filename from subject
    safe_subject = "".join(c if c.isalnum() or c in " -_" else "_" for c in subject[:50])
    safe_subject = safe_subject.strip(" _-") or "no_subject"
    
    filename = f"email_{safe_subject}_{timestamp}.{body_type}"
    file_path = INBOX_DIR / filename
    
    # Create email content file
    content = f"""From: {sender}
Date: {date}
Subject: {subject}
Body-Type: {body_type}

---

{body}
"""
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return file_path


# =============================================================================
# Gmail Connection
# =============================================================================

def connect_to_gmail(email_address: str, password: str) -> imaplib.IMAP4_SSL:
    """
    Connect to Gmail IMAP server.
    
    Args:
        email_address: Gmail address
        password: App password or OAuth token
        
    Returns:
        Connected IMAP object
    """
    print(f"[GMAIL] Connecting to {GMAIL_IMAP_SERVER}...")
    
    # Connect with SSL
    mail = imaplib.IMAP4_SSL(GMAIL_IMAP_SERVER, GMAIL_IMAP_PORT)
    
    # Login
    mail.login(email_address, password)
    print(f"[GMAIL] ✓ Logged in as {email_address}")
    
    # Select inbox
    mail.select("inbox")
    print("[GMAIL] ✓ Selected inbox")
    
    return mail


def fetch_new_emails(mail: imaplib.IMAP4_SSL, seen_ids: set) -> list:
    """
    Fetch new (unseen) emails from Gmail.
    
    Args:
        mail: Connected IMAP object
        seen_ids: Set of already processed email IDs
        
    Returns:
        List of tuples (email_id, email_data)
    """
    # Search for unseen emails
    status, messages = mail.search(None, "UNSEEN")
    
    if status != "OK":
        print("[GMAIL] No messages found!")
        return []
    
    email_ids = messages[0].split()
    new_emails = []
    
    for email_id in email_ids:
        email_id_str = email_id.decode()
        
        # Skip if already processed
        if email_id_str in seen_ids:
            continue
        
        # Fetch the email
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        
        if status == "OK":
            new_emails.append((email_id_str, msg_data))
    
    return new_emails


def process_email(msg_data) -> dict:
    """
    Process raw email data and extract information.
    
    Args:
        msg_data: Raw email data from IMAP
        
    Returns:
        Dictionary with email information
    """
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            
            # Extract headers
            subject = decode_mime_words(msg.get("Subject", ""))
            sender = decode_mime_words(msg.get("From", ""))
            date = decode_mime_words(msg.get("Date", ""))
            
            # Extract body
            body, body_type = get_email_body(msg)
            
            return {
                "subject": subject,
                "sender": sender,
                "date": date,
                "body": body,
                "body_type": body_type
            }
    
    return None


# =============================================================================
# Main Gmail Watcher
# =============================================================================

def start_gmail_watcher():
    """
    Start the Gmail watcher.
    
    Monitors the Gmail inbox for new emails and saves them to the Inbox folder.
    """
    import sys
    # Enable UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 60)
    print("[AI] Personal AI Employee - Gmail Watcher")
    print("=" * 60)
    
    # Get credentials from environment
    email_address = os.getenv("GMAIL_ADDRESS")
    email_password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not email_address or not email_password:
        print("[GMAIL] X Error: GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env")
        print("[GMAIL] See README.md for setup instructions")
        return
    
    print(f"[GMAIL] Vault Directory: {VAULT_DIR}")
    print(f"[GMAIL] Monitoring emails for: {email_address}")
    print(f"[GMAIL] Check interval: {CHECK_INTERVAL_SECONDS} seconds")
    print("=" * 60)
    
    # Load seen emails
    seen_emails = load_seen_emails()
    reset_daily_count_if_new_day()
    current_count = get_daily_count()
    print(f"[GMAIL] Loaded {len(seen_emails)} previously processed emails")
    print(f"[GMAIL] Daily limit: {DAILY_EMAIL_LIMIT} emails/day (processed today: {current_count})")
    print("[GMAIL] Starting watcher... Press Ctrl+C to stop.\n")

    try:
        while True:
            # Check daily limit before processing
            limit_reached, count = check_daily_limit()
            if limit_reached:
                print(f"\n[GMAIL] Daily limit reached ({count}/{DAILY_EMAIL_LIMIT} emails processed today)")
                print(f"[GMAIL] Will resume processing at midnight")
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue
            
            try:
                # Connect to Gmail
                mail = connect_to_gmail(email_address, email_password)

                # Fetch new emails
                new_emails = fetch_new_emails(mail, seen_emails)

                if new_emails:
                    print(f"\n[GMAIL] Found {len(new_emails)} new email(s)!")

                    for email_id, msg_data in new_emails:
                        # Check limit again before each email
                        limit_reached, count = check_daily_limit()
                        if limit_reached:
                            print(f"[GMAIL] Daily limit reached ({count}/{DAILY_EMAIL_LIMIT})")
                            break
                        
                        try:
                            # Process email
                            email_info = process_email(msg_data)

                            if email_info:
                                print(f"\n[GMAIL] Received email:")
                                print(f"  From: {email_info['sender']}")
                                print(f"  Subject: {email_info['subject']}")
                                
                                # Apply filter
                                matches, categories, keywords = filter_email(
                                    email_info["subject"],
                                    email_info["body"],
                                    email_info["sender"]
                                )
                                
                                if not matches:
                                    print(f"[GMAIL] ✗ Skipped (no matching keywords)")
                                    print(f"  Categories checked: {', '.join(FILTER_CATEGORIES)}")
                                    # Mark as seen but don't process
                                    mail.store(email_id.encode(), "+FLAGS", "\\Seen")
                                    save_seen_email(email_id)
                                    seen_emails.add(email_id)
                                    continue
                                
                                print(f"[GMAIL] ✓ Matched categories: {', '.join(categories)}")
                                print(f"[GMAIL] ✓ Matched keywords: {', '.join(keywords)}")
                                print(f"[GMAIL] Processing email...")

                                # Save email as file in Inbox
                                file_path = save_email_as_file(
                                    email_info["subject"],
                                    email_info["sender"],
                                    email_info["date"],
                                    email_info["body"],
                                    email_info["body_type"]
                                )
                                print(f"  Saved to: {file_path.name}")
                                
                                # Mark as seen in Gmail
                                mail.store(email_id.encode(), "+FLAGS", "\\Seen")

                                # Track as processed
                                save_seen_email(email_id)
                                seen_emails.add(email_id)
                                
                                # Increment daily count
                                increment_daily_count()
                                new_count = get_daily_count()
                                print(f"[GMAIL] Daily progress: {new_count}/{DAILY_EMAIL_LIMIT} emails")

                                # Trigger agent_loop
                                print(f"[GMAIL] Triggering agent_loop for: {file_path.name}")
                                try:
                                    from main_agent import agent_loop
                                    agent_loop(str(file_path))
                                    print(f"[GMAIL] ✓ agent_loop completed")
                                except ImportError:
                                    print(f"[GMAIL] Warning: main_agent.py not found. Skipping agent_loop.")
                                except Exception as e:
                                    print(f"[GMAIL] Error in agent_loop: {e}")
                            
                        except Exception as e:
                            print(f"[GMAIL] Error processing email {email_id}: {e}")
                
                else:
                    print(f"[GMAIL] No new emails. Checking again in {CHECK_INTERVAL_SECONDS} seconds...")
                
                # Close connection
                mail.close()
                mail.logout()
                
            except imaplib.IMAP4.error as e:
                print(f"[GMAIL] IMAP error: {e}")
            except Exception as e:
                print(f"[GMAIL] Error: {e}")
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\n[GMAIL] Stopping watcher...")
    
    print("[GMAIL] Watcher stopped.")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    start_gmail_watcher()
