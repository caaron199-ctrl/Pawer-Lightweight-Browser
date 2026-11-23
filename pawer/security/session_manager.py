"""
Pawer Session Manager — Manages ephemeral (in-memory only) session lifecycle.
Ensures that every Pawer session starts clean: no cookies, no history,
no cached data, no stored credentials bleed across sessions.

Design:
  - Each WebView2 instance uses a per-session temp directory (never the
    same across launches) so residual data is wiped on OS temp cleanup.
  - On close, the session directory is proactively deleted.
  - A session ID is generated per launch (not persistent) so local apps
    cannot correlate sessions.
"""

import os
import secrets
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional


class PawerSession:
    """
    Manages a single ephemeral browser session:
    - Unique temp directory per launch
    - Automatic cleanup on close
    - Session ID generated fresh each launch (non-persistent)
    """

    def __init__(self):
        # Generate a cryptographically random, non-repeating session ID
        # This is NOT stored to disk and is regenerated on every Pawer launch
        self.session_id: str = secrets.token_hex(16)
        self.started_at: float = time.time()

        # Create a unique temp directory for this session's WebView2 user data
        # Named with session ID so it cannot be correlated across launches
        self._base_tmp = Path(tempfile.gettempdir())
        self._session_dir: Optional[Path] = None
        self._data_dir = self._create_session_dir()

        # Track permissions that have been granted this session
        self._granted_permissions: set = set()

        # Request count for the audit log
        self._blocked_request_count = 0
        self._allowed_request_count = 0

    def _create_session_dir(self) -> Path:
        """Creates a fresh, isolated session directory in the OS temp folder."""
        # Use a random suffix so no two sessions share a path
        session_path = self._base_tmp / f"Pawer_session_{self.session_id}"
        session_path.mkdir(parents=True, exist_ok=True)
        self._session_dir = session_path
        return session_path

    @property
    def data_dir(self) -> str:
        """Returns the WebView2 user data directory path for this session."""
        return str(self._data_dir)

    def record_blocked(self):
        self._blocked_request_count += 1

    def record_allowed(self):
        self._allowed_request_count += 1

    @property
    def stats(self) -> dict:
        from .guardian import get_isolation_mode
        return {
            "session_id": self.session_id[:8] + "…",  # truncated for display
            "blocked": self._blocked_request_count,
            "allowed": self._allowed_request_count,
            "uptime_secs": int(time.time() - self.started_at),
            "isolation_mode": get_isolation_mode(),
        }

    def cleanup(self):
        """
        Proactively wipes the session's WebView2 user data directory.
        Called when Pawer closes. Removes cookies, cache, localStorage,
        IndexedDB, service workers, and all persistent engine state.
        """
        if self._session_dir and self._session_dir.exists():
            try:
                # First try to remove the WebView2 EBWebView subdirectory
                # (where most sensitive state lives)
                eb_dir = self._session_dir / "EBWebView"
                if eb_dir.exists():
                    shutil.rmtree(str(eb_dir), ignore_errors=True)

                # Then wipe the whole session directory
                shutil.rmtree(str(self._session_dir), ignore_errors=True)
            except Exception:
                pass  # Best-effort — OS will clean /tmp on reboot anyway


# ---------------------------------------------------------------------------
# Stale Session Cleaner
# ---------------------------------------------------------------------------

def cleanup_stale_sessions(max_age_hours: float = 24.0) -> int:
    """
    Finds and removes orphaned Pawer_session_* directories from previous
    crashed or force-killed Pawer instances.
    Returns the number of stale directories cleaned up.
    """
    tmp = Path(tempfile.gettempdir())
    cleaned = 0
    cutoff = time.time() - (max_age_hours * 3600)

    for entry in tmp.iterdir():
        if entry.is_dir() and entry.name.startswith("Pawer_session_"):
            try:
                mtime = entry.stat().st_mtime
                if mtime < cutoff:
                    shutil.rmtree(str(entry), ignore_errors=True)
                    cleaned += 1
            except Exception:
                pass

    return cleaned


# Global session singleton (one per Pawer process)
current_session = PawerSession()
