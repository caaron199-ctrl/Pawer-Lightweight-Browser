"""
Unit and Integration Tests for Pawer.
Run with: python tests/test_pawer.py
"""

import os
import sys
import unittest
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pawer.security.guardian import (
    extract_port,
    is_local_url,
    normalize_url,
    IsolationMode,
    get_isolation_mode,
    set_isolation_mode,
    toggle_isolation_mode,
)
from pawer.security.hardener import BROWSER_ARGUMENTS, PRIVACY_FLAGS
from pawer.security.session_manager import PawerSession, cleanup_stale_sessions
from pawer.security.request_interceptor import _is_safe_resource_url
from pawer.security.offline_cache import get_offline_fallback_for_url
from pawer.services.pages import get_blocked_html, get_error_html, get_home_html, get_security_html
from pawer.services.port_scanner import check_port, find_free_port, scan_known_ports, get_port_pid_map, kill_process_on_port
from pawer.services.favorites import load_favorites, add_favorite, remove_favorite
from pawer.services.app_launcher import launcher


class TestPawerSecurityGuardian(unittest.TestCase):
    def test_local_urls_allowed(self):
        allowed = [
            "http://localhost:8501",
            "http://127.0.0.1:8000",
            "http://0.0.0.0:3000",
            "http://[::1]:8501",
            "http://192.168.1.100:5000",
            "http://10.0.0.5:8080",
            "http://172.16.0.1:8000",
            "http://my-pc.local:8501",
            "file:///C:/Users/app.html",
            "pawer://home",
            "pawer://ports",
            "pawer://security",
            "about:blank",
            "data:text/html,<h1>Test</h1>",
        ]
        for url in allowed:
            self.assertTrue(is_local_url(url), f"Should allow local URL: {url}")

    def test_external_internet_blocked(self):
        blocked = [
            "https://www.google.com",
            "http://github.com",
            "https://streamlit.io",
            "http://8.8.8.8",
            "https://1.1.1.1",
            "http://example.org",
            "https://twitter.com",
            "http://142.250.190.46",
        ]
        for url in blocked:
            self.assertFalse(is_local_url(url), f"Should BLOCK external internet: {url}")

    def test_url_normalization(self):
        self.assertEqual(normalize_url(""), "pawer://home")
        self.assertEqual(normalize_url("home"), "pawer://home")
        self.assertEqual(normalize_url("security"), "pawer://security")
        self.assertEqual(normalize_url("8501"), "http://localhost:8501")
        self.assertEqual(normalize_url("8000"), "http://localhost:8000")
        self.assertEqual(normalize_url("3000"), "http://localhost:3000")
        self.assertEqual(normalize_url("localhost:8501"), "http://localhost:8501")
        self.assertEqual(normalize_url("127.0.0.1:5000"), "http://127.0.0.1:5000")
        self.assertEqual(normalize_url("pawer://home"), "pawer://home")
        self.assertEqual(normalize_url("pawer://security"), "pawer://security")

    def test_extract_port(self):
        self.assertEqual(extract_port("http://localhost:8501"), 8501)
        self.assertEqual(extract_port("http://127.0.0.1:8000/docs"), 8000)
        self.assertEqual(extract_port("http://localhost"), 80)
        self.assertEqual(extract_port("https://localhost"), 443)
        self.assertIsNone(extract_port("pawer://home"))

    def test_airgap_mode_strict_isolation(self):
        prev = get_isolation_mode()
        try:
            set_isolation_mode(IsolationMode.AIRGAP)
            # Loopback & internal schemes MUST still work
            self.assertTrue(is_local_url("http://localhost:8501"))
            self.assertTrue(is_local_url("http://127.0.0.1:8000"))
            self.assertTrue(is_local_url("pawer://home"))
            self.assertTrue(is_local_url("file:///C:/test.html"))

            # Private LAN and mDNS MUST be completely blocked in AIRGAP mode
            self.assertFalse(is_local_url("http://192.168.1.100:5000"))
            self.assertFalse(is_local_url("http://10.0.0.5:8080"))
            self.assertFalse(is_local_url("http://my-pc.local:8501"))

            # External internet must also remain blocked
            self.assertFalse(is_local_url("https://www.google.com"))
        finally:
            set_isolation_mode(prev)

    def test_open_mode_unrestricted(self):
        prev = get_isolation_mode()
        try:
            set_isolation_mode(IsolationMode.OPEN)
            self.assertTrue(is_local_url("https://www.google.com"))
            self.assertTrue(is_local_url("http://localhost:8501"))
        finally:
            set_isolation_mode(prev)

    def test_toggle_isolation_mode_cycle(self):
        prev = get_isolation_mode()
        try:
            set_isolation_mode(IsolationMode.LOCAL)
            self.assertEqual(toggle_isolation_mode(), IsolationMode.AIRGAP)
            self.assertEqual(toggle_isolation_mode(), IsolationMode.OPEN)
            self.assertEqual(toggle_isolation_mode(), IsolationMode.LOCAL)
        finally:
            set_isolation_mode(prev)


class TestPawerSecurityHardening(unittest.TestCase):
    def test_browser_arguments_contain_key_flags(self):
        self.assertIn("--disable-third-party-cookies", BROWSER_ARGUMENTS)
        self.assertIn("--disable-safe-browsing", BROWSER_ARGUMENTS)
        self.assertIn("--disable-features=WebBluetooth,WebUsb,WebHid", BROWSER_ARGUMENTS)
        self.assertIn("--no-referrers", BROWSER_ARGUMENTS)
        # Critical security check: --disable-web-security must NOT be present
        self.assertNotIn("--disable-web-security", BROWSER_ARGUMENTS)

    def test_session_manager_creates_unique_dirs(self):
        s1 = PawerSession()
        s2 = PawerSession()
        self.assertNotEqual(s1.session_id, s2.session_id)
        self.assertNotEqual(s1.data_dir, s2.data_dir)
        self.assertTrue(os.path.exists(s1.data_dir))
        self.assertTrue(os.path.exists(s2.data_dir))
        s1.cleanup()
        s2.cleanup()
        self.assertFalse(os.path.exists(s1.data_dir))
        self.assertFalse(os.path.exists(s2.data_dir))

    def test_session_stats(self):
        s = PawerSession()
        s.record_blocked()
        s.record_blocked()
        s.record_allowed()
        stats = s.stats
        self.assertEqual(stats["blocked"], 2)
        self.assertEqual(stats["allowed"], 1)
        self.assertIn("session_id", stats)
        self.assertIn("uptime_secs", stats)
        s.cleanup()

    def test_cleanup_stale_sessions(self):
        # Should execute cleanly without errors
        cleaned = cleanup_stale_sessions(max_age_hours=0.0)
        self.assertIsInstance(cleaned, int)

    def test_request_interceptor_safe_urls(self):
        self.assertTrue(_is_safe_resource_url("data:image/png;base64,abc"))
        self.assertTrue(_is_safe_resource_url("blob:http://localhost:8501/123"))
        self.assertTrue(_is_safe_resource_url("pawer://home"))
        self.assertTrue(_is_safe_resource_url("http://localhost:8501/static/js/main.js"))
        self.assertFalse(_is_safe_resource_url("https://fonts.googleapis.com/css"))
        self.assertFalse(_is_safe_resource_url("https://analytics.google.com/collect"))

    def test_security_page_rendering(self):
        stats = {"session_id": "test_id_1234", "blocked": 5, "allowed": 12, "uptime_secs": 95}
        html = get_security_html(stats)
        self.assertIn("Pawer Security Dashboard", html)
        self.assertIn("test_id_1234", html)
        self.assertIn("5", html)
        self.assertIn("12", html)
        self.assertIn("1m 35s", html)
        self.assertIn("Active Privacy Flags", html)

    def test_offline_cdn_fallback(self):
        # Fonts / CSS
        css_fb = get_offline_fallback_for_url("https://fonts.googleapis.com/css?family=Roboto")
        self.assertIsNotNone(css_fb)
        self.assertEqual(css_fb[1], "text/css")

        # SVG
        svg_fb = get_offline_fallback_for_url("https://cdn.jsdelivr.net/icon.svg")
        self.assertIsNotNone(svg_fb)
        self.assertEqual(svg_fb[1], "image/svg+xml")

        # Telemetry / JSON
        json_fb = get_offline_fallback_for_url("https://telemetry.streamlit.io/analytics.json")
        self.assertIsNotNone(json_fb)
        self.assertEqual(json_fb[1], "application/json")


class TestPawerServices(unittest.TestCase):
    def test_find_free_port(self):
        port = find_free_port(9000, 9100)
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 9000)

    def test_scan_known_ports(self):
        services = scan_known_ports()
        self.assertIsInstance(services, list)
        self.assertGreater(len(services), 0)
        for s in services:
            self.assertIn("port", s)
            self.assertIn("name", s)
            self.assertIn("online", s)
            self.assertIn("url", s)

    def test_favorites_lifecycle(self):
        fav = add_favorite("Test Dashboard", "examples/sample_streamlit_app.py", icon="🎈")
        self.assertIn("id", fav)
        self.assertEqual(fav["name"], "Test Dashboard")

        favs = load_favorites()
        self.assertTrue(any(f["id"] == fav["id"] for f in favs))

        removed = remove_favorite(fav["id"])
        self.assertTrue(removed)

    def test_port_pid_inspection(self):
        pid_map = get_port_pid_map()
        self.assertIsInstance(pid_map, dict)

    def test_app_launcher_logging(self):
        received = []
        def listener(p, line):
            received.append((p, line))

        launcher.add_log_listener(listener)
        launcher._broadcast_log(8501, "Test log message")
        launcher.remove_log_listener(listener)

        self.assertTrue(any(msg == "Test log message" for _, msg in received))

    def test_html_pages_rendering(self):
        services = scan_known_ports()
        home_html = get_home_html(services)
        self.assertIn("PAWER", home_html)
        self.assertIn("Active Local Services", home_html)
        self.assertIn("Pinned Workspaces & Apps", home_html)

        blocked_html = get_blocked_html("https://google.com")
        self.assertIn("External Internet Access Blocked", blocked_html)
        self.assertIn("https://google.com", blocked_html)

        error_html = get_error_html("http://localhost:8501", 8501)
        self.assertIn("Port 8501 is Offline", error_html)
        self.assertIn("streamlit run", error_html)


class TestPawerEngine(unittest.TestCase):
    def test_winforms_and_webview2_available(self):
        import clr
        import webview.platforms.edgechromium as ec
        from System.Windows.Forms import Form
        form = Form()
        self.assertIsNotNone(form)
        form.Dispose()

    def test_pawer_app_instantiation_and_tabs(self):
        import clr
        from System.Threading import Thread, ThreadStart, ApartmentState
        from pawer.app import PawerApp

        result = {}

        def runner():
            try:
                app = PawerApp(["pawer://home"])
                result["initial_tabs"] = len(app.tabs)
                result["title"] = app.get_active_tab().title
                result["has_icon"] = app.Icon is not None
                app.create_tab("http://localhost:8501")
                result["after_add"] = len(app.tabs)
                app.Dispose()
                result["success"] = True
            except Exception as ex:
                result["error"] = str(ex)

        t = Thread(ThreadStart(runner))
        t.SetApartmentState(ApartmentState.STA)
        t.Start()
        t.Join()

        self.assertTrue(result.get("success"), f"Failed: {result.get('error')}")
        self.assertEqual(result.get("initial_tabs"), 1)
        self.assertEqual(result.get("after_add"), 2)
        self.assertTrue(result.get("has_icon"), "App icon should be loaded and set on Form")


if __name__ == "__main__":
    unittest.main()
