"""
Pawer Main Application Form — Coordinates the multi-tab browser chrome,
keyboard shortcuts, WebView2 lifecycles, and Streamlit execution.
"""

import os
import sys
import uuid
from typing import Callable, Dict, Optional

import clr

try:
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
except Exception:
    pass

import webview.platforms.edgechromium as ec

from System import Action, Uri
from System.Drawing import Color, Icon, Point, Size
from System.Threading import ApartmentState, Thread, ThreadStart
from System.Windows.Forms import (
    Application,
    DockStyle,
    FileDialog,
    Form,
    FormClosingEventArgs,
    FormStartPosition,
    KeyEventArgs,
    Keys,
    MessageBox,
    MessageBoxButtons,
    MessageBoxIcon,
    OpenFileDialog,
    Orientation,
    Panel,
    SplitContainer,
)

from .services.app_launcher import launcher
from .services.favorites import add_favorite, load_favorites
from .security.guardian import IsolationMode, toggle_isolation_mode, get_isolation_mode
from .security.session_manager import current_session, cleanup_stale_sessions
from .ui.logs_drawer import PawerLogsDrawer
from .ui.nav_bar import PawerNavBar
from .ui.status_bar import PawerStatusBar
from .ui.tab_bar import PawerTabBar
from .ui.theme import PawerTheme
from .ui.toast import PawerToast
from .ui.tray import PawerSystemTray
from .webview_tab import PawerTab


class PawerApp(Form):
    """The Pawer Browser main desktop application window."""

    def __init__(self, initial_urls: Optional[list] = None):
        super().__init__()
        self.Text = "Pawer — Local App Browser"
        self.Size = Size(1280, 840)
        self.MinimumSize = Size(800, 600)
        self.StartPosition = FormStartPosition.CenterScreen
        self.BackColor = PawerTheme.BG_BASE
        self.KeyPreview = True

        # Load Window & Taskbar Icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.isfile(icon_path):
            try:
                self.Icon = Icon(icon_path)
            except Exception:
                pass

        # State
        self.tabs: Dict[str, PawerTab] = {}
        self.active_tab_id: Optional[str] = None
        self._is_fullscreen = False

        # Top Control Container (TabBar + NavBar)
        self.pnl_top = Panel()
        self.pnl_top.Dock = DockStyle.Top
        self.pnl_top.Height = 80
        self.pnl_top.BackColor = PawerTheme.BG_BASE
        self.Controls.Add(self.pnl_top)

        # Bottom Status Bar
        self.status_bar = PawerStatusBar(self)

        # Live Server Logs Drawer (docked above status bar)
        self.logs_drawer = PawerLogsDrawer(self)
        launcher.add_log_listener(self.logs_drawer.append_log)

        # Blocked Outbound Traffic Toast Notification
        self.toast = PawerToast(self)

        # Windows Notification Area System Tray
        self.tray = PawerSystemTray(self)

        # Split View State
        self.is_split_view = False
        self.split_container: Optional[SplitContainer] = None
        self.split_tab_id: Optional[str] = None

        # Center Viewport Container for WebViews
        self.pnl_content = Panel()
        self.pnl_content.Dock = DockStyle.Fill
        self.pnl_content.BackColor = PawerTheme.BG_BASE
        self.Controls.Add(self.pnl_content)

        # Initialize Navigation Bar (docked below TabBar)
        self.nav_bar = PawerNavBar(
            parent_panel=self.pnl_top,
            on_navigate=self.on_user_navigate,
            on_back=self.on_nav_back,
            on_forward=self.on_nav_forward,
            on_reload=self.on_nav_reload,
            on_home=self.on_nav_home,
            on_run_streamlit=self.launch_streamlit_dialog,
            on_devtools=self.on_open_devtools,
            on_clear_cache=self.on_clear_cache,
            on_toggle_isolation=self.on_toggle_isolation_mode,
            on_toggle_logs=self.toggle_logs_drawer,
            on_toggle_split=self.toggle_split_view,
        )

        # Initialize Tab Bar (docked at the very top)
        self.tab_bar = PawerTabBar(
            parent_panel=self.pnl_top,
            on_select_tab=self.switch_to_tab,
            on_close_tab=self.close_tab,
            on_new_tab=lambda: self.create_tab("pawer://home"),
        )

        # Hook Window Events
        self.KeyDown += self._on_form_keydown
        self.FormClosing += self._on_form_closing

        # Create initial tabs
        urls = initial_urls if initial_urls else ["pawer://home"]
        for u in urls:
            self.create_tab(u)

    def invoke_on_ui(self, func: Callable[[], None]):
        """Executes a callable on the WinForms UI thread safely."""
        try:
            if self.InvokeRequired:
                self.Invoke(Action(func))
            else:
                func()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Tab Management
    # --------------------------------------------------------------------------

    def create_tab(self, url: str = "pawer://home") -> PawerTab:
        """Creates a new browser tab and activates it."""
        tab_id = f"tab_{uuid.uuid4().hex[:8]}"
        tab = PawerTab(tab_id=tab_id, app=self, initial_url=url)

        self.tabs[tab_id] = tab
        self.pnl_content.Controls.Add(tab.panel)
        self.tab_bar.add_tab(tab_id, tab.title)

        self.switch_to_tab(tab_id)
        return tab

    def switch_to_tab(self, tab_id: str):
        """Switches the active viewport to the requested tab."""
        if tab_id not in self.tabs:
            return

        self.active_tab_id = tab_id
        target_tab = self.tabs[tab_id]

        # Update visibility of tab panels
        for tid, tab in self.tabs.items():
            if tid == tab_id:
                tab.panel.Visible = True
                tab.panel.BringToFront()
            else:
                tab.panel.Visible = False

        # Update Chrome UI
        self.tab_bar.set_active_tab(tab_id)
        self.nav_bar.set_url(target_tab.current_url)
        self.status_bar.set_tab_info(f"Tab: {target_tab.title} ({target_tab.current_url})")
        self.Text = f"{target_tab.title} — Pawer"

    def close_tab(self, tab_id: str):
        """Closes and disposes a tab."""
        if tab_id not in self.tabs:
            return

        tab = self.tabs.pop(tab_id)
        self.tab_bar.remove_tab(tab_id)
        self.pnl_content.Controls.Remove(tab.panel)
        tab.dispose()

        if self.tabs:
            if self.active_tab_id == tab_id:
                # Switch to the first remaining tab
                next_id = next(iter(self.tabs.keys()))
                self.switch_to_tab(next_id)
        else:
            # If all tabs are closed, create a fresh Pawer Hub tab
            self.create_tab("pawer://home")

    def get_active_tab(self) -> Optional[PawerTab]:
        if self.active_tab_id and self.active_tab_id in self.tabs:
            return self.tabs[self.active_tab_id]
        return None

    # --------------------------------------------------------------------------
    # Tab Notifications
    # --------------------------------------------------------------------------

    def on_tab_title_changed(self, tab: PawerTab):
        self.tab_bar.update_tab_title(tab.tab_id, tab.title)
        if self.active_tab_id == tab.tab_id:
            self.Text = f"{tab.title} — Pawer"
            self.status_bar.set_tab_info(f"Tab: {tab.title} ({tab.current_url})")

    def on_tab_navigating(self, tab: PawerTab, url: str):
        if self.active_tab_id == tab.tab_id:
            self.nav_bar.set_url(url)
            self.status_bar.set_status("🟢 Loading Local App...")

    def on_tab_navigated(self, tab: PawerTab, url: str):
        if self.active_tab_id == tab.tab_id:
            self.nav_bar.set_url(url)
            self.status_bar.set_status("🟢 Local Isolation Active (Internet Blocked)")
            # Update live session stats in the engine label
            self.status_bar.set_session_stats(current_session.stats)

    def on_navigation_blocked(self, tab: PawerTab, url: str):
        if self.active_tab_id == tab.tab_id:
            self.nav_bar.set_url(url)
            self.status_bar.set_status("🛡️ Blocked External Internet Request", is_warning=True)

    # --------------------------------------------------------------------------
    # Navigation Actions
    # --------------------------------------------------------------------------

    def on_user_navigate(self, url: str):
        active = self.get_active_tab()
        if active:
            active.navigate(url)

    def on_nav_back(self):
        active = self.get_active_tab()
        if active:
            active.go_back()

    def on_nav_forward(self):
        active = self.get_active_tab()
        if active:
            active.go_forward()

    def on_nav_reload(self):
        active = self.get_active_tab()
        if active:
            active.reload()

    def on_nav_home(self):
        active = self.get_active_tab()
        if active:
            active.navigate("pawer://home")

    def on_open_devtools(self):
        active = self.get_active_tab()
        if active:
            active.open_devtools()

    def on_clear_cache(self):
        """Clears session data by closing the active tab and opening a fresh one."""
        active = self.get_active_tab()
        if active:
            url = active.current_url
            tab_id = active.tab_id
            self.close_tab(tab_id)
            self.create_tab(url)
            self.status_bar.set_status("🧹 Session cleared — fresh tab opened")

    def on_toggle_isolation_mode(self):
        """Toggles between LOCAL, AIRGAP (strict loopback only), and OPEN modes."""
        new_mode = toggle_isolation_mode()
        self.nav_bar.update_isolation_badge(new_mode)
        if new_mode == IsolationMode.AIRGAP:
            self.status_bar.set_status("🔒 Strict Airgap Active — All LAN & External Internet Blocked (Loopback Only)")
        elif new_mode == IsolationMode.LOCAL:
            self.status_bar.set_status("🟢 Local Isolation Active — Loopback & Local LAN Allowed (Internet Blocked)")
        else:
            self.status_bar.set_status("⚠️ Unrestricted Mode — External Internet Access Allowed", is_warning=True)
        self.status_bar.set_session_stats(current_session.stats)

    def toggle_logs_drawer(self):
        """Toggles the visibility of the bottom live server logs drawer."""
        self.logs_drawer.toggle_drawer()

    def toggle_split_view(self):
        """Toggles side-by-side split screen view with another tab."""
        if self.is_split_view:
            # Revert to single view
            self.is_split_view = False
            self.nav_bar.btn_split.Text = "◫ Split"
            if self.split_container:
                self.split_container.Panel1.Controls.Clear()
                self.split_container.Panel2.Controls.Clear()
                self.pnl_content.Controls.Remove(self.split_container)
                self.split_container.Dispose()
                self.split_container = None

            # Re-dock active tab
            active = self.get_active_tab()
            if active:
                self.pnl_content.Controls.Add(active.panel)
                active.panel.Visible = True
                active.panel.BringToFront()
            self.status_bar.set_status("Single view mode")
        else:
            # Enable split view
            if len(self.tabs) < 2:
                # Spawn a secondary hub tab if only one tab exists
                self.create_tab("pawer://home")

            tab_ids = list(self.tabs.keys())
            active_id = self.active_tab_id or tab_ids[0]
            secondary_id = [tid for tid in tab_ids if tid != active_id][0]

            tab1 = self.tabs[active_id]
            tab2 = self.tabs[secondary_id]

            self.pnl_content.Controls.Clear()
            self.split_container = SplitContainer()
            self.split_container.Dock = DockStyle.Fill
            self.split_container.Orientation = Orientation.Vertical
            self.split_container.SplitterDistance = max(300, self.pnl_content.Width // 2)

            tab1.panel.Visible = True
            tab2.panel.Visible = True
            self.split_container.Panel1.Controls.Add(tab1.panel)
            self.split_container.Panel2.Controls.Add(tab2.panel)

            self.pnl_content.Controls.Add(self.split_container)
            self.is_split_view = True
            self.split_tab_id = secondary_id
            self.nav_bar.btn_split.Text = "◫ Merged"
            self.status_bar.set_status("◫ Side-by-Side Split View Active")

    def launch_streamlit_script(self, script_path: str):
        """Launches a Streamlit app by file path and navigates to it."""
        self.status_bar.set_status(f"🚀 Spawning Streamlit for {script_path}...")

        def on_ready(url: str):
            self.invoke_on_ui(lambda: self.create_tab(url))
            self.invoke_on_ui(lambda: self.status_bar.set_status(f"🟢 Streamlit online at {url}"))

        def on_error(err: str):
            self.invoke_on_ui(lambda: MessageBox.Show(err, "Streamlit Error", MessageBoxButtons.OK, MessageBoxIcon.Error))

        launcher.launch_streamlit(script_path, on_ready=on_ready, on_error=on_error)

    def pin_favorite_dialog(self):
        """Opens a file dialog to pin a script to the Home favorites hub."""
        dialog = OpenFileDialog()
        dialog.Title = "Select Python Script to Pin to Pawer Hub"
        dialog.Filter = "Python Scripts (*.py)|*.py|All Files (*.*)|*.*"
        if dialog.ShowDialog() == ec.WinForms.DialogResult.OK:
            path = dialog.FileName
            name = os.path.basename(path).replace(".py", "").replace("_", " ").title()
            add_favorite(name, path, icon="🎈")
            self.status_bar.set_status(f"⭐ Pinned {name} to Pawer Hub")
            active = self.get_active_tab()
            if active and active.current_url.startswith("pawer://home"):
                active.reload()

    def launch_streamlit_dialog(self):
        """Opens a file dialog to pick a Streamlit .py file and runs it."""
        dialog = OpenFileDialog()
        dialog.Title = "Select Streamlit Python Script"
        dialog.Filter = "Python Scripts (*.py)|*.py|All Files (*.*)|*.*"
        dialog.Multiselect = False

        if dialog.ShowDialog() == ec.WinForms.DialogResult.OK:
            script_path = dialog.FileName
            self.status_bar.set_status(f"🚀 Spawning Streamlit for {script_path}...")

            def on_ready(url: str):
                self.invoke_on_ui(lambda: self.create_tab(url))
                self.invoke_on_ui(
                    lambda: self.status_bar.set_status(f"🟢 Streamlit online at {url}")
                )

            def on_error(err: str):
                self.invoke_on_ui(
                    lambda: MessageBox.Show(
                        err, "Streamlit Launch Error", MessageBoxButtons.OK, MessageBoxIcon.Error
                    )
                )

            launcher.launch_streamlit(script_path, on_ready=on_ready, on_error=on_error)

    # --------------------------------------------------------------------------
    # Keyboard Shortcuts & Fullscreen
    # --------------------------------------------------------------------------

    def _on_form_keydown(self, sender, args: KeyEventArgs):
        # Ctrl + T : New Tab
        if args.Control and args.KeyCode == Keys.T:
            args.SuppressKeyPress = True
            self.create_tab("pawer://home")

        # Ctrl + W : Close Active Tab
        elif args.Control and args.KeyCode == Keys.W:
            args.SuppressKeyPress = True
            if self.active_tab_id:
                self.close_tab(self.active_tab_id)

        # Ctrl + R or F5 : Reload
        elif (args.Control and args.KeyCode == Keys.R) or args.KeyCode == Keys.F5:
            args.SuppressKeyPress = True
            self.on_nav_reload()

        # Ctrl + Shift + A : Toggle Airgap / Isolation Mode
        elif args.Control and args.Shift and args.KeyCode == Keys.A:
            args.SuppressKeyPress = True
            self.on_toggle_isolation_mode()

        # Ctrl + J or F10 : Toggle Live Server Logs Drawer
        elif (args.Control and args.KeyCode == Keys.J) or args.KeyCode == Keys.F10:
            args.SuppressKeyPress = True
            self.toggle_logs_drawer()

        # Alt + S : Toggle Split View
        elif args.Alt and args.KeyCode == Keys.S:
            args.SuppressKeyPress = True
            self.toggle_split_view()

        # F12 or Ctrl + Shift + I : DevTools
        elif args.KeyCode == Keys.F12 or (args.Control and args.Shift and args.KeyCode == Keys.I):
            args.SuppressKeyPress = True
            self.on_open_devtools()

        # Ctrl + L or Alt + D : Focus Address Bar
        elif (args.Control and args.KeyCode == Keys.L) or (args.Alt and args.KeyCode == Keys.D):
            args.SuppressKeyPress = True
            self.nav_bar.txt_address.Focus()
            self.nav_bar.txt_address.SelectAll()

        # Alt + Left : Back
        elif args.Alt and args.KeyCode == Keys.Left:
            args.SuppressKeyPress = True
            self.on_nav_back()

        # Alt + Right : Forward
        elif args.Alt and args.KeyCode == Keys.Right:
            args.SuppressKeyPress = True
            self.on_nav_forward()

        # F11 : Toggle Kiosk / Fullscreen
        elif args.KeyCode == Keys.F11:
            args.SuppressKeyPress = True
            self._toggle_fullscreen()

    def _toggle_fullscreen(self):
        if not self._is_fullscreen:
            self._is_fullscreen = True
            self.FormBorderStyle = getattr(ec.WinForms.FormBorderStyle, "None")
            self.WindowState = ec.WinForms.FormWindowState.Maximized
        else:
            self._is_fullscreen = False
            self.FormBorderStyle = ec.WinForms.FormBorderStyle.Sizable
            self.WindowState = ec.WinForms.FormWindowState.Normal

    # --------------------------------------------------------------------------
    # Cleanup & Lifecycle
    # --------------------------------------------------------------------------

    def _on_form_closing(self, sender, args: FormClosingEventArgs):
        """Clean up all tabs, terminate child processes, dispose tray, and wipe the ephemeral session."""
        try:
            if hasattr(self, "tray") and self.tray:
                self.tray.dispose()
            for tab in list(self.tabs.values()):
                tab.dispose()
            self.tabs.clear()
            launcher.stop_all()
            # Wipe ephemeral session data directory
            current_session.cleanup()
            cleanup_stale_sessions()
        except Exception:
            pass


def start_pawer(initial_urls: Optional[list] = None):
    """Main entry point to start the Pawer application on an STA thread."""
    # Clean up any stale session directories from previously crashed instances
    cleanup_stale_sessions()
    Application.EnableVisualStyles()
    Application.SetCompatibleTextRenderingDefault(False)
    app = PawerApp(initial_urls=initial_urls)
    Application.Run(app)
