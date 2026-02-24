"""
Filesystem Watcher for Personal AI Employee - Bronze Tier

Monitors the Inbox folder for new or modified files using Watchdog.
When a file is detected, it moves the file to Needs_Action, creates
a metadata note, and triggers the agent_loop() function.

Uses PollingObserver for Windows compatibility.
"""

import os
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path

from watchdog.observers import PollingObserver
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent


# =============================================================================
# Configuration
# =============================================================================

# Base paths - adjust these based on your setup
BASE_DIR = Path(__file__).parent.absolute()
VAULT_DIR = BASE_DIR / "ai-employee-vault"

# Folder paths
INBOX_DIR = VAULT_DIR / "Inbox"
NEEDS_ACTION_DIR = VAULT_DIR / "Needs_Action"
DONE_DIR = VAULT_DIR / "Done"

# Ensure directories exist
for directory in [VAULT_DIR, INBOX_DIR, NEEDS_ACTION_DIR, DONE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# File extensions to monitor (None = all files)
MONITORED_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".log", ""}

# Limits configuration (can be overridden via environment variables)
MAX_FILE_SIZE_MB = int(os.getenv("WATCHER_MAX_FILE_SIZE_MB", "10"))  # Max file size in MB
MAX_FILES_PER_BATCH = int(os.getenv("WATCHER_MAX_FILES_PER_BATCH", "5"))  # Max files to process at once
MIN_CHECK_INTERVAL_SECONDS = float(os.getenv("WATCHER_MIN_CHECK_INTERVAL", "0.5"))  # Min time between checks


# =============================================================================
# Event Handler
# =============================================================================

class InboxEventHandler(FileSystemEventHandler):
    """
    Handles file system events in the Inbox folder.
    
    When a new or modified file is detected:
    1. Move the file to Needs_Action folder
    2. Create a metadata note
    3. Call agent_loop() to process the file
    """
    
    def __init__(self):
        super().__init__()
        self.processing_lock = set()  # Track files being processed
    
    def on_created(self, event):
        """Handle file creation events."""
        if isinstance(event, FileCreatedEvent):
            self._handle_file_event(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if isinstance(event, FileModifiedEvent):
            self._handle_file_event(event.src_path)
    
    def _handle_file_event(self, file_path: str):
        """
        Process a file event (created or modified).
        
        Args:
            file_path: Path to the file that triggered the event
        """
        file_path = Path(file_path)
        
        # Skip directories
        if file_path.is_dir():
            return
        
        # Skip hidden files and temporary files
        if file_path.name.startswith(".") or file_path.name.startswith("~"):
            return
        
        # Check file extension
        if MONITORED_EXTENSIONS and file_path.suffix not in MONITORED_EXTENSIONS:
            print(f"[WATCHER] Ignoring file with unsupported extension: {file_path.name}")
            return
        
        # Skip if already processing
        if str(file_path) in self.processing_lock:
            print(f"[WATCHER] File already being processed: {file_path.name}")
            return
        
        # Add to processing lock
        self.processing_lock.add(str(file_path))
        
        try:
            print(f"[WATCHER] Detected file: {file_path.name}")
            self._process_file(file_path)
        except Exception as e:
            print(f"[WATCHER] Error processing file {file_path.name}: {e}")
        finally:
            # Remove from processing lock
            self.processing_lock.discard(str(file_path))
    
    def _process_file(self, source_path: Path):
        """
        Process a file: move to Needs_Action, create metadata, trigger agent.
        
        Args:
            source_path: Path to the source file in Inbox
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = source_path.name
        
        # Generate destination path
        dest_path = NEEDS_ACTION_DIR / filename
        
        # Handle duplicate filenames
        if dest_path.exists():
            stem = source_path.stem
            suffix = source_path.suffix
            dest_path = NEEDS_ACTION_DIR / f"{stem}_{timestamp}{suffix}"
        
        # Step 1: Move file to Needs_Action
        print(f"[WATCHER] Moving {filename} to Needs_Action...")
        shutil.move(str(source_path), str(dest_path))
        print(f"[WATCHER] File moved to: {dest_path}")
        
        # Step 2: Create metadata note
        metadata_path = self._create_metadata_note(filename, dest_path, timestamp)
        print(f"[WATCHER] Metadata note created: {metadata_path}")
        
        # Step 3: Call agent_loop
        print(f"[WATCHER] Triggering agent_loop for: {filename}")
        try:
            from main_agent import agent_loop
            agent_loop(str(dest_path))
            print(f"[WATCHER] agent_loop completed for: {filename}")
        except ImportError:
            print(f"[WATCHER] Warning: main_agent.py not found. Skipping agent_loop.")
        except Exception as e:
            print(f"[WATCHER] Error in agent_loop: {e}")
    
    def _create_metadata_note(self, original_filename: str, file_path: Path, timestamp: str) -> Path:
        """
        Create a metadata note for the processed file.
        
        Args:
            original_filename: Original name of the file
            file_path: Path where the file was moved
            timestamp: Timestamp of the operation
        
        Returns:
            Path to the created metadata note
        """
        metadata_filename = f".{Path(original_filename).stem}_meta.md"
        metadata_path = NEEDS_ACTION_DIR / metadata_filename
        
        metadata_content = f"""---
original_file: {original_filename}
processed_date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
action_taken: File moved from Inbox to Needs_Action
status: pending_processing
file_path: {file_path}
---

# Metadata Note

This file was automatically detected and moved by the Personal AI Employee system.

- **Original Location:** Inbox/{original_filename}
- **Current Location:** Needs_Action/{file_path.name}
- **Detected At:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Processing Status:** Awaiting agent processing

"""
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(metadata_content)
        
        return metadata_path


# =============================================================================
# Main Watcher Function
# =============================================================================

def start_watcher():
    """
    Start the filesystem watcher on the Inbox folder.
    
    Uses PollingObserver for Windows compatibility.
    """
    print("=" * 60)
    print("🤖 Personal AI Employee - Filesystem Watcher")
    print("=" * 60)
    print(f"[WATCHER] Vault Directory: {VAULT_DIR}")
    print(f"[WATCHER] Monitoring Inbox: {INBOX_DIR}")
    print(f"[WATCHER] Using PollingObserver (Windows compatible)")
    print("=" * 60)
    print("[WATCHER] Starting watcher... Press Ctrl+C to stop.\n")
    
    # Create observer with PollingObserver for Windows compatibility
    observer = PollingObserver(timeout=1.0)  # 1 second polling interval
    
    # Set up event handler
    event_handler = InboxEventHandler()
    
    # Schedule watcher on Inbox directory
    observer.schedule(event_handler, str(INBOX_DIR), recursive=False)
    
    # Start the observer
    observer.start()
    print("[WATCHER] ✓ Watcher started successfully!")
    print("[WATCHER] Waiting for files in Inbox...\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[WATCHER] Stopping watcher...")
        observer.stop()
    
    observer.join()
    print("[WATCHER] Watcher stopped.")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    start_watcher()
