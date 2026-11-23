"""
Pawer Security Hardener — Applies defence-in-depth Chromium flags and
CoreWebView2 settings to maximise anonymity and attack surface reduction.

Threat model: local apps that might phone home, inject tracking pixels,
fingerprint the browser, or leak identity through HTTP headers.
"""

from typing import List


# ---------------------------------------------------------------------------
# Chromium Process Flags
# Applied as AdditionalBrowserArguments in CoreWebView2CreationProperties
# ---------------------------------------------------------------------------

PRIVACY_FLAGS: List[str] = [
    # ---- Core Tracking Prevention ----
    # Block 3rd-party tracking storage
    "--disable-third-party-cookies",
    # Hard-disable crash/metrics reporting
    "--metrics-recording-only",
    "--disable-breakpad",
    # Disable field trials & feature experiments (opt-out of A/B data collection)
    "--disable-field-trial-config",
    "--variations-server-url=",
    # ---- Fingerprinting Resistance ----
    # Disable WebRTC local IP leaks (irrelevant for local-only but good hygiene)
    "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
    # Disable battery status API (fingerprinting vector)
    "--disable-features=BatteryStatus",
    # Disable ambient light sensor API
    "--disable-features=SensorExtraClasses",
    # Suppress canvas fingerprinting noise injection by blocking canvas readback
    "--disable-features=CanvasColorCache",
    # Disable high-entropy client hints headers
    "--disable-features=ClientHintsSaveData",
    # ---- Network Anonymity ----
    # Strip Referer headers by default to limit data passed to local apps
    "--no-referrers",
    # Disable network prediction / pre-fetching (would trigger background requests)
    "--no-pings",
    "--disable-preconnect",
    "--dns-prefetch-disable",
    "--disable-features=NetworkPrediction",
    # Disable WebSocket compression (can expose data patterns)
    "--disable-features=WebSocketDeflate",
    # ---- Spectre / Side-Channel Mitigations ----
    "--enable-strict-mixed-content-checking",
    "--disable-features=SharedArrayBuffer",
    # ---- Misc Hardening ----
    # Disable Bluetooth / USB / HID discovery APIs
    "--disable-features=WebBluetooth,WebUsb,WebHid",
    # Disable vibration API
    "--disable-features=Vibration",
    # Disable IDLE detection API
    "--disable-features=IdleDetection",
    # Disable file system access API (apps can still use Pawer file picker)
    "--disable-features=FileSystemAccessAPI",
    # Disable persistent-permissions prompt spam
    "--deny-permission-prompts",
    # Suppress save-password prompts
    "--password-store=basic",
    # No autofill
    "--disable-autofill-keyboard-accessory-view",
    # Suppress cloud policy fetching
    "--disable-background-networking",
    # Disable component updater phone-home
    "--disable-component-update",
    # Suppress Safe Browsing (which phones home to Google)
    "--disable-safe-browsing",
    # Disable WebGL fingerprinting (allow rendering but disable data export)
    # Note: fully disabling WebGL breaks some Streamlit charts; leave enabled
    # but disable the unmasked renderer API
    "--disable-webgl-image-chromium",
    # ---- Local-App Specific Allowances ----
    "--allow-file-access-from-files",
    "--disable-features=ElasticOverscroll",
]

# Join flags for the CreationProperties string
BROWSER_ARGUMENTS = " ".join(PRIVACY_FLAGS)


# ---------------------------------------------------------------------------
# CoreWebView2Settings hardening (applied after engine init)
# ---------------------------------------------------------------------------

def apply_core_settings(settings) -> None:
    """
    Applies privacy-hardened settings to a CoreWebView2Settings object.
    Call this inside the CoreWebView2InitializationCompleted handler.
    """
    # Keep DevTools (useful for local debugging)
    settings.AreDevToolsEnabled = True
    # Disable status bar (leaks URL previews on hover)
    settings.IsStatusBarEnabled = False
    # Keep zoom controls
    settings.IsZoomControlEnabled = True
    # Keep right-click context menu (useful for inspect, copy)
    settings.AreDefaultContextMenusEnabled = True
    # Suppress browser accelerator keys that could bypass our nav (e.g. Ctrl+U view-source)
    settings.AreBrowserAcceleratorKeysEnabled = False
    # Disable swipe-to-navigate (accidental history navigation on touch/trackpad)
    settings.IsSwipeNavigationEnabled = False

    # Spoof the User-Agent to remove local machine OS/version fingerprint
    # Presents as a generic local app without revealing OS or Chromium version
    settings.UserAgent = (
        "Pawer/1.0 (Local App Browser; +https://pawer.local)"
    )


# ---------------------------------------------------------------------------
# Private-Mode Flag (IsInPrivateModeEnabled)
# ---------------------------------------------------------------------------

def configure_private_mode(props) -> None:
    """
    Enables InPrivate mode on CoreWebView2CreationProperties.
    In InPrivate mode the WebView2 engine:
      - Does NOT persist cookies across sessions
      - Does NOT persist localStorage / sessionStorage to disk
      - Does NOT write browsing history to the user data folder
      - Does NOT write form-fill data, passwords, or autofill entries
    """
    props.set_IsInPrivateModeEnabled(True)
