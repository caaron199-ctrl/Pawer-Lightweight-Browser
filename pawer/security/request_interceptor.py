"""
Pawer Request Interceptor — WebResourceRequested handler that provides a
second line of defence after NavigationStarting.

Responsibilities:
  1. Block any resource request (image, XHR, fetch, WebSocket, etc.) whose
     host is NOT permitted under the active isolation mode.
  2. Serve safe offline mock responses (empty CSS/SVG/JSON) for common CDN
     assets to ensure airgapped charts and UI components never break.
  3. Strip identifying HTTP request headers (Referer, Origin, X-Forwarded-For,
     Via, X-Real-IP) before they reach local apps.
  4. Inject privacy-signalling headers (DNT, Sec-GPC) on every request.
"""

from __future__ import annotations

import clr
try:
    from System.IO import MemoryStream
    from System.Text import Encoding
except Exception:
    MemoryStream = None
    Encoding = None

from typing import Callable, Optional
from urllib.parse import urlparse

from .guardian import is_local_url
from .offline_cache import get_offline_fallback_for_url
from .session_manager import PawerSession

# Headers to remove from every outbound request (leak identity or route info)
_STRIP_HEADERS = [
    "Referer",
    "Origin",
    "X-Forwarded-For",
    "X-Forwarded-Host",
    "X-Forwarded-Proto",
    "X-Real-IP",
    "Via",
    "Forwarded",
]

# Headers to inject on every outbound request (signal privacy preferences)
_INJECT_HEADERS = {
    "DNT": "1",          # Do Not Track
    "Sec-GPC": "1",      # Global Privacy Control
}


class RequestInterceptor:
    """
    Wraps a PawerSession and provides a WebResourceRequested event handler.
    Thread-safe: each call is independent.
    """

    def __init__(self, session: PawerSession, on_blocked_callback: Optional[Callable[[str], None]] = None):
        self._session = session
        self._on_blocked = on_blocked_callback

    def handle(self, sender, args) -> None:
        """
        WebResourceRequested event handler.

        args.Request  → CoreWebView2WebResourceRequest  (mutable headers)
        args.Response → set to CoreWebView2WebResourceResponse to override
        """
        try:
            req = args.Request
            uri = str(req.Uri) if req.Uri else ""

            # ----------------------------------------------------------------
            # 1. Block non-local requests (second gate after NavigationStarting)
            # ----------------------------------------------------------------
            if uri and not _is_safe_resource_url(uri):
                self._session.record_blocked()
                if self._on_blocked:
                    try:
                        self._on_blocked(uri)
                    except Exception:
                        pass

                try:
                    env = sender.Environment if hasattr(sender, "Environment") else None
                    if env is not None:
                        # Check for safe offline CDN asset fallback
                        fallback = get_offline_fallback_for_url(uri)
                        if fallback and MemoryStream and Encoding:
                            content, content_type = fallback
                            stream = MemoryStream(Encoding.UTF8.GetBytes(content))
                            header_str = f"Content-Type: {content_type}\r\nAccess-Control-Allow-Origin: *\r\n"
                            args.Response = env.CreateWebResourceResponse(stream, 200, "OK", header_str)
                        else:
                            args.Response = env.CreateWebResourceResponse(None, 403, "Blocked by Pawer", "")
                except Exception:
                    pass
                return

            # ----------------------------------------------------------------
            # 2. Strip identifying headers
            # ----------------------------------------------------------------
            headers = req.Headers
            for header_name in _STRIP_HEADERS:
                try:
                    headers.RemoveHeader(header_name)
                except Exception:
                    pass

            # ----------------------------------------------------------------
            # 3. Inject privacy headers
            # ----------------------------------------------------------------
            for name, value in _INJECT_HEADERS.items():
                try:
                    headers.SetHeader(name, value)
                except Exception:
                    pass

            self._session.record_allowed()

        except Exception as ex:
            print(f"[RequestInterceptor] Error: {ex}")


def _is_safe_resource_url(url: str) -> bool:
    """
    Extended local-URL check for resource requests.
    Allows data: URIs for inline assets (Streamlit uses them heavily for fonts/icons).
    Allows blob: URIs for media content served locally.
    Allows internal pawer:// and about: schemes.
    Checks destination against current isolation mode.
    """
    if url.startswith("data:"):
        return True
    if url.startswith("blob:"):
        return True
    if url.startswith("pawer://"):
        return True
    if url.startswith("about:"):
        return True
    return is_local_url(url)
