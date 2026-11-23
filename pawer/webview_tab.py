"""
Pawer Tab Controller — Encapsulates an individual tab running a high-performance
Chromium WebView2 instance, wired to local network isolation policies and
the full security hardening stack.
"""

import os
import urllib.parse
import webbrowser
from typing import TYPE_CHECKING, Optional

import clr
from System import Action, Uri
from System.Drawing import Color
from System.Windows.Forms import DockStyle, Panel

import webview.platforms.edgechromium as ec

from .security.guardian import extract_port, is_local_url, normalize_url
from .security.hardener import BROWSER_ARGUMENTS, apply_core_settings, configure_private_mode
from .security.session_manager import current_session
from .security.request_interceptor import RequestInterceptor
from .services.pages import get_blocked_html, get_error_html, get_home_html, get_security_html
from .services.port_scanner import scan_known_ports

if TYPE_CHECKING:
    from .app import PawerApp


class PawerTab:
    """Represents a single browser tab running a WebView2 Chromium instance."""

    def __init__(self, tab_id: str, app: "PawerApp", initial_url: str = "pawer://home"):
        self.tab_id = tab_id
        self.app = app
        self.title = "Pawer Hub"
        self.current_url = initial_url
        self.is_ready = False
        self._pending_url = initial_url
        self._interceptor = RequestInterceptor(current_session, on_blocked_callback=self._on_resource_blocked)

        # Tab container panel docked inside the main viewport
        self.panel = Panel()
        self.panel.Dock = DockStyle.Fill
        self.panel.BackColor = Color.FromArgb(17, 17, 27)

        # Create Chromium WebView2
        self.webview = ec.WebView2()
        self.webview.Dock = DockStyle.Fill

        # -------------------------------------------------------------------
        # Hardened creation properties:
        #   - Unique per-session ephemeral temp directory (not shared/persisted)
        #   - Privacy Chromium flags from hardener.py (28 flags)
        #   - InPrivate mode: no cookie/history/localStorage persistence
        # -------------------------------------------------------------------
        props = ec.CoreWebView2CreationProperties()
        props.UserDataFolder = current_session.data_dir   # ephemeral dir, wiped on close
        props.AdditionalBrowserArguments = BROWSER_ARGUMENTS  # all privacy flags
        configure_private_mode(props)                          # IsInPrivateModeEnabled = True
        self.webview.CreationProperties = props

        # Wire up events
        self.webview.CoreWebView2InitializationCompleted += self._on_init_completed
        self.webview.NavigationStarting += self._on_navigation_starting
        self.webview.NavigationCompleted += self._on_navigation_completed
        self.webview.WebMessageReceived += self._on_web_message_received

        self.panel.Controls.Add(self.webview)

        # Start asynchronous Chromium engine initialization
        self.webview.EnsureCoreWebView2Async(None)

    def _on_resource_blocked(self, uri: str):
        """Notifies the main app toast of an external network block."""
        if hasattr(self.app, "toast") and self.app.toast:
            self.app.toast.show_blocked_alert(uri)

    def _on_init_completed(self, sender, args):
        """Called when the underlying Edge Chromium engine is ready."""
        try:
            if not args.IsSuccess:
                return

            self.is_ready = True
            core = self.webview.CoreWebView2
            if core:
                # Apply hardened settings (UA spoof, disable accel keys, etc.)
                apply_core_settings(core.Settings)

                # Wire request interceptor — blocks non-local resources + strips headers
                try:
                    core.AddWebResourceRequestedFilter(
                        "*", ec.CoreWebView2WebResourceContext.All
                    )
                    core.WebResourceRequested += self._interceptor.handle
                except Exception as ex:
                    print(f"[PawerTab] WebResourceRequested wire error: {ex}")

                # Handle new window requests (target="_blank" or window.open)
                core.NewWindowRequested += self._on_new_window_requested
                core.DocumentTitleChanged += self._on_document_title_changed

            # If an initial URL was waiting for the engine to boot, navigate now
            if self._pending_url:
                url_to_load = self._pending_url
                self._pending_url = None
                self.navigate(url_to_load)
        except Exception as ex:
            print(f"[PawerTab] Init error: {ex}")

    def _on_new_window_requested(self, sender, args):
        """Intercepts popup/target=_blank links to open them in a new Pawer tab instead."""
        try:
            args.Handled = True
            dest_url = args.Uri
            if dest_url:
                self.app.invoke_on_ui(lambda: self.app.create_tab(dest_url))
        except Exception as ex:
            print(f"[PawerTab] NewWindowRequested error: {ex}")

    def _on_document_title_changed(self, sender, args):
        """Updates tab title when web document title changes."""
        try:
            if self.webview.CoreWebView2:
                raw_title = self.webview.CoreWebView2.DocumentTitle
                if raw_title and raw_title.strip():
                    self.title = raw_title.strip()
                elif self.current_url.startswith("pawer://"):
                    self.title = "Pawer Hub"
                else:
                    self.title = self.current_url

                self.app.invoke_on_ui(lambda: self.app.on_tab_title_changed(self))
        except Exception:
            pass

    def _on_navigation_starting(self, sender, args):
        """Enforces Pawer's local-only security boundary."""
        dest_url = str(args.Uri) if args.Uri else ""

        # Allow internal pawer:// scheme pages always
        if dest_url.startswith("pawer://"):
            self.current_url = dest_url
            self.app.invoke_on_ui(lambda: self.app.on_tab_navigating(self, dest_url))
            return

        # Validate against local access guardian
        if not is_local_url(dest_url):
            # Block external internet navigation
            args.Cancel = True
            current_session.record_blocked()
            self.current_url = dest_url
            self.title = "Blocked — Pawer"
            self.webview.NavigateToString(get_blocked_html(dest_url))
            self.app.invoke_on_ui(lambda: self.app.on_navigation_blocked(self, dest_url))
            return

        current_session.record_allowed()
        self.current_url = dest_url
        self.app.invoke_on_ui(lambda: self.app.on_tab_navigating(self, dest_url))

    def _on_navigation_completed(self, sender, args):
        """Handles completion and local connection errors."""
        try:
            if not args.IsSuccess:
                # Connection refused / server offline
                port = extract_port(self.current_url)
                self.webview.NavigateToString(get_error_html(self.current_url, port))
                self.title = f"Offline (Port {port})" if port else "Offline"
                self.app.invoke_on_ui(lambda: self.app.on_tab_title_changed(self))
            else:
                if self.webview.Source:
                    self.current_url = str(self.webview.Source)
                self.app.invoke_on_ui(lambda: self.app.on_tab_navigated(self, self.current_url))
        except Exception:
            pass

    def _on_web_message_received(self, sender, args):
        """Processes messages sent via window.chrome.webview.postMessage(...)."""
        try:
            msg = args.TryGetWebMessageAsString()
            if not msg:
                return

            if msg.startswith("open:"):
                dest = msg[5:].strip()
                self.app.invoke_on_ui(lambda: self.navigate(dest))

            elif msg.startswith("open_external:"):
                dest = msg[14:].strip()
                unquoted = urllib.parse.unquote_plus(dest)
                webbrowser.open(unquoted)

            elif msg == "launch_streamlit_picker":
                self.app.invoke_on_ui(lambda: self.app.launch_streamlit_dialog())

            elif msg == "rescan_ports":
                self.app.invoke_on_ui(lambda: self.navigate("pawer://home"))

            elif msg.startswith("kill_port:"):
                port_str = msg[10:].strip()
                try:
                    from .services.port_scanner import kill_process_on_port
                    kill_process_on_port(int(port_str))
                    self.app.invoke_on_ui(lambda: self.navigate("pawer://home"))
                except Exception:
                    pass

            elif msg.startswith("launch_favorite:"):
                target = msg[16:].strip()
                self.app.invoke_on_ui(lambda: self.app.launch_streamlit_script(target))

            elif msg.startswith("remove_favorite:"):
                fav_id = msg[16:].strip()
                try:
                    from .services.favorites import remove_favorite
                    remove_favorite(fav_id)
                    self.app.invoke_on_ui(lambda: self.navigate("pawer://home"))
                except Exception:
                    pass

            elif msg == "pin_current_or_picker":
                self.app.invoke_on_ui(lambda: self.app.pin_favorite_dialog())

            elif msg == "toggle_isolation":
                self.app.invoke_on_ui(lambda: self.app.on_toggle_isolation_mode())
                if self.current_url == "pawer://security":
                    self.app.invoke_on_ui(lambda: self.navigate("pawer://security"))

            elif msg == "reload_current":
                self.app.invoke_on_ui(lambda: self.reload())

        except Exception as ex:
            print(f"[PawerTab] Message handler error: {ex}")

    def navigate(self, target_url: str):
        """Navigates this tab to the specified URL or internal page."""
        normalized = normalize_url(target_url)
        self.current_url = normalized

        if not self.is_ready:
            self._pending_url = normalized
            return

        if normalized in ("pawer://home", "pawer://ports"):
            services = scan_known_ports()
            self.title = "Pawer Hub"
            self.webview.NavigateToString(get_home_html(services))
            self.app.invoke_on_ui(lambda: self.app.on_tab_navigated(self, normalized))

        elif normalized == "pawer://security":
            self.title = "Security — Pawer"
            self.webview.NavigateToString(get_security_html(current_session.stats))
            self.app.invoke_on_ui(lambda: self.app.on_tab_navigated(self, normalized))

        elif normalized.startswith("pawer://blocked"):
            self.webview.NavigateToString(get_blocked_html(normalized))

        else:
            try:
                self.webview.Source = Uri(normalized)
            except Exception:
                try:
                    self.webview.CoreWebView2.Navigate(normalized)
                except Exception as ex:
                    print(f"[PawerTab] Navigate error: {ex}")

    def reload(self):
        """Reloads the current page."""
        if not self.is_ready:
            return
        if self.current_url.startswith("pawer://"):
            self.navigate(self.current_url)
        else:
            self.webview.Reload()

    def go_back(self):
        """Navigates back in history if possible."""
        if self.is_ready and self.webview.CanGoBack:
            self.webview.GoBack()

    def go_forward(self):
        """Navigates forward in history if possible."""
        if self.is_ready and self.webview.CanGoForward:
            self.webview.GoForward()

    def open_devtools(self):
        """Opens Chromium Developer Tools for this tab."""
        if self.is_ready and self.webview.CoreWebView2:
            self.webview.CoreWebView2.OpenDevToolsWindow()

    def dispose(self):
        """Disposes and cleans up resources for this tab."""
        try:
            self.panel.Controls.Clear()
            self.webview.Dispose()
            self.panel.Dispose()
        except Exception:
            pass
