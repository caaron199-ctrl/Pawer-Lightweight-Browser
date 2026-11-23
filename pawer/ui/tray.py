"""
Pawer System Tray Integration — Minimizes Pawer to the Windows notification tray
with quick-access controls for isolation mode, server logs, and background processes.
"""

import clr

try:
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Windows.Forms")
except Exception:
    pass

from System.Drawing import Icon, SystemIcons
from System.Windows.Forms import (
    ContextMenuStrip,
    FormWindowState,
    NotifyIcon,
    ToolStripSeparator,
)


class PawerSystemTray:
    """Manages the Windows System Tray (NotifyIcon) icon and context menu for Pawer."""

    def __init__(self, app):
        self.app = app

        self.tray = NotifyIcon()
        self.tray.Text = "Pawer — Local App Browser"

        # Try to use app icon or fallback to default shield icon
        if app.Icon:
            self.tray.Icon = app.Icon
        else:
            self.tray.Icon = SystemIcons.Shield

        # Context Menu
        self.menu = ContextMenuStrip()

        item_open = self.menu.Items.Add("🐾 Open Pawer")
        item_open.Click += lambda s, e: self.restore_window()

        item_airgap = self.menu.Items.Add("🔒 Toggle Airgap Mode")
        item_airgap.Click += lambda s, e: self.app.on_toggle_isolation_mode()

        item_logs = self.menu.Items.Add("📄 Toggle Server Logs")
        item_logs.Click += lambda s, e: self.app.logs_drawer.toggle_drawer()

        self.menu.Items.Add(ToolStripSeparator())

        item_exit = self.menu.Items.Add("✕ Exit Pawer")
        item_exit.Click += lambda s, e: self.app.Close()

        self.tray.ContextMenuStrip = self.menu
        self.tray.DoubleClick += lambda s, e: self.restore_window()
        self.tray.Visible = True

    def restore_window(self):
        """Restores and focuses the main application window."""
        self.app.Show()
        self.app.WindowState = FormWindowState.Normal
        self.app.BringToFront()
        self.app.Activate()

    def show_balloon(self, title: str, text: str):
        """Displays a Windows balloon notification from the tray icon."""
        try:
            from System.Windows.Forms import ToolTipIcon
            self.tray.ShowBalloonTip(3000, title, text, ToolTipIcon.Info)
        except Exception:
            pass

    def dispose(self):
        try:
            self.tray.Visible = False
            self.tray.Dispose()
        except Exception:
            pass
