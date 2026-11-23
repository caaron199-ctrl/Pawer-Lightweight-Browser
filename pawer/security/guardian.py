"""
Pawer Security Guardian — Network isolation and local-only access control.
Ensures Pawer strictly operates as a local application browser and cannot be
used to wander onto or exfiltrate data to the external internet.
"""

import ipaddress
import re
from typing import Optional
from urllib.parse import urlparse

# Internal Pawer pseudo-schemes and safe offline protocols
ALLOWED_SCHEMES = ("about:", "data:", "blob:", "pawer:", "file:")

# Common loopback and local hostnames
LOOPBACK_HOSTS = {
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
    "::1",
    "[::1]",
    "ip6-localhost",
    "ip6-loopback",
}


class IsolationMode:
    """
    Network Isolation Modes for Pawer:
      - AIRGAP: 100% air-gapped from any network. Strictly loopback & internal files only.
                No packets leave the host machine (blocks local LAN, Wi-Fi, and public internet).
      - LOCAL:  Default local isolation. Loopback + private LAN (192.168.x.x, 10.x.x.x) allowed.
                External public internet strictly blocked.
      - OPEN:   Unrestricted. External internet allowed (e.g. for temporary documentation lookup).
    """
    AIRGAP = "airgap"
    LOCAL = "local"
    OPEN = "open"


# Global active isolation mode (starts in LOCAL mode)
_active_isolation_mode: str = IsolationMode.LOCAL


def get_isolation_mode() -> str:
    """Returns the currently active isolation mode ('airgap', 'local', or 'open')."""
    return _active_isolation_mode


def set_isolation_mode(mode: str) -> str:
    """Sets the active isolation mode and returns the updated mode string."""
    global _active_isolation_mode
    normalized = mode.lower().strip()
    if normalized in (IsolationMode.AIRGAP, IsolationMode.LOCAL, IsolationMode.OPEN):
        _active_isolation_mode = normalized
    return _active_isolation_mode


def toggle_isolation_mode() -> str:
    """
    Cycles between isolation modes:
      LOCAL (Default: Internet blocked, LAN ok) ->
      AIRGAP (Strict: LAN & Internet blocked, Loopback only) ->
      OPEN (Unrestricted: Internet allowed) ->
      LOCAL
    """
    global _active_isolation_mode
    if _active_isolation_mode == IsolationMode.LOCAL:
        _active_isolation_mode = IsolationMode.AIRGAP
    elif _active_isolation_mode == IsolationMode.AIRGAP:
        _active_isolation_mode = IsolationMode.OPEN
    else:
        _active_isolation_mode = IsolationMode.LOCAL
    return _active_isolation_mode


def is_local_url(url_str: str, mode: Optional[str] = None) -> bool:
    """
    Evaluates whether a given URL is permitted under the active (or specified) isolation mode.
    
    Modes:
      - OPEN:   Allows all URLs (internal, local, and external internet).
      - LOCAL:  Allows internal schemes, loopback, and private LAN (RFC 1918 / .local).
                Blocks external internet.
      - AIRGAP: Allows ONLY internal schemes, loopback (127.0.0.1, localhost), and local files.
                Blocks even private LAN (192.168.x.x) and external internet completely.
    """
    if mode is None:
        mode = _active_isolation_mode

    if mode == IsolationMode.OPEN:
        return True

    if not url_str:
        return False

    url_str = url_str.strip()

    # Allow internal and offline schemes
    if any(url_str.lower().startswith(s) for s in ALLOWED_SCHEMES):
        return True

    # Prepend scheme if missing for proper parsing
    if "://" not in url_str:
        url_str = "http://" + url_str

    try:
        parsed = urlparse(url_str)
        host = parsed.hostname
        if not host:
            return False

        host = host.lower().strip()

        # Check standard loopback aliases
        is_loopback = (host in LOOPBACK_HOSTS)

        # Check if the host is an IP address
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_loopback:
                is_loopback = True
            elif mode == IsolationMode.AIRGAP:
                # In AIRGAP mode, block any non-loopback IP (including private LAN)
                return False
            else:
                # In LOCAL mode, allow private LAN and link-local
                return ip.is_private or ip.is_link_local
        except ValueError:
            pass

        if is_loopback:
            return True

        # In strict AIRGAP mode, block mDNS and intranet hostnames
        if mode == IsolationMode.AIRGAP:
            return False

        # In LOCAL mode, allow local mDNS / intranet domains (*.local, *.localhost)
        if host.endswith(".local") or host.endswith(".localhost"):
            return True

        return False
    except Exception:
        return False


def normalize_url(input_text: str) -> str:
    """
    Normalizes user input from the address bar into a well-formed URL.
    Handles:
      - Bare numbers: "8501" -> "http://localhost:8501"
      - "localhost:8501" -> "http://localhost:8501"
      - "127.0.0.1:8000" -> "http://127.0.0.1:8000"
      - "pawer:home", "home", "" -> "pawer://home"
      - file paths -> "file:///..."
    """
    if not input_text:
        return "pawer://home"

    text = input_text.strip()
    lower = text.lower()

    if lower in ("home", "pawer", "pawer://", "pawer://home", "about:blank"):
        return "pawer://home"

    if lower in ("ports", "pawer://ports"):
        return "pawer://ports"

    if lower in ("security", "pawer://security"):
        return "pawer://security"

    if any(lower.startswith(s) for s in ("pawer://", "about:", "file://", "data:", "blob:")):
        return text

    # If user typed just a number (e.g. 8501 or 3000)
    if re.fullmatch(r"\d{2,5}", text):
        port = int(text)
        if 1 <= port <= 65535:
            return f"http://localhost:{port}"

    # If it starts with localhost or 127.0.0.1 or an IP with port
    if re.match(r"^(localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:|\/|$)", text, re.IGNORECASE):
        return f"http://{text}"

    # If already starts with http:// or https://
    if text.startswith(("http://", "https://")):
        return text

    # If it looks like a local file path (e.g., C:\... or /...)
    if (len(text) >= 2 and text[1] == ":" and text[2] in ("\\", "/")) or text.startswith("/"):
        normalized_path = text.replace("\\", "/")
        return f"file:///{normalized_path.lstrip('/')}"

    # Default fallback: treat as http URL
    return f"http://{text}"


def extract_port(url_str: str) -> int | None:
    """Extracts the port number from a URL if present."""
    if not url_str:
        return None
    try:
        parsed = urlparse(url_str if "://" in url_str else "http://" + url_str)
        if parsed.port:
            return parsed.port
        if parsed.scheme == "http":
            return 80
        if parsed.scheme == "https":
            return 443
    except Exception:
        pass
    return None
