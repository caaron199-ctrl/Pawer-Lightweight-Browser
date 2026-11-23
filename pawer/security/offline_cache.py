"""
Pawer Offline CDN Fallback Cache — Intercepts common external CDN assets (fonts, icons,
analytics, CDN stylesheets) during Airgap / Local isolation and provides safe, offline
fallbacks so local dashboards, Plotly charts, and Streamlit components render without breaking.
"""

from typing import Optional, Tuple

# Common CDN domains that local frontend libraries often embed
OFFLINE_CDN_DOMAINS = (
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "cdn.jsdelivr.net",
    "cdnjs.cloudflare.com",
    "unpkg.com",
    "use.fontawesome.com",
    "ka-f.fontawesome.com",
)

# Harmless dummy responses for common asset types
EMPTY_CSS = "/* Pawer Offline Asset Cache: External stylesheet neutralized for local privacy */\n"
EMPTY_JS = "/* Pawer Offline Asset Cache: External script neutralized */\n"
EMPTY_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"/>'
EMPTY_JSON = "{}"


def get_offline_fallback_for_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Checks if a blocked URL is a known external CDN asset and returns a tuple of
    (content_str, content_type) so the WebView can render cleanly without network errors.
    Returns None if no specific fallback is configured.
    """
    lower = url.lower()

    # Font and CSS stylesheets
    if "fonts.googleapis.com" in lower or lower.endswith(".css") or "/css" in lower:
        return (EMPTY_CSS, "text/css")

    # Font binaries (woff2, woff, ttf) - return empty CSS instead
    if any(lower.endswith(ext) for ext in (".woff2", ".woff", ".ttf", ".otf")):
        return ("", "font/woff2")

    # SVG icons
    if lower.endswith(".svg"):
        return (EMPTY_SVG, "image/svg+xml")

    # JSON metadata / telemetry endpoints
    if lower.endswith(".json") or "/telemetry" in lower or "/analytics" in lower:
        return (EMPTY_JSON, "application/json")

    # Generic CDN scripts
    if any(domain in lower for domain in OFFLINE_CDN_DOMAINS) and lower.endswith(".js"):
        return (EMPTY_JS, "application/javascript")

    return None
