"""
Pawer Status Bar — Bottom information bar showing local security status and tabs.
"""

import clr

try:
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Windows.Forms")
except Exception:
    pass

from System.Drawing import Color, ContentAlignment, Point, Size
from System.Windows.Forms import DockStyle, Label, Panel

from .theme import PawerTheme


class PawerStatusBar:
    """Bottom status bar displaying environment details and local security state."""

    def __init__(self, parent_panel: Panel):
        self.bar_panel = Panel()
        self.bar_panel.Dock = DockStyle.Bottom
        self.bar_panel.Height = 24
        self.bar_panel.BackColor = PawerTheme.BG_BASE

        # Security Status Label
        self.lbl_security = Label()
        self.lbl_security.Text = "🟢 Local Isolation Active (Internet Blocked)"
        self.lbl_security.Font = PawerTheme.get_font(8.5)
        self.lbl_security.ForeColor = PawerTheme.EMERALD
        self.lbl_security.Location = Point(12, 4)
        self.lbl_security.Size = Size(300, 18)
        self.bar_panel.Controls.Add(self.lbl_security)

        # Active tab / URL info
        self.lbl_tab_info = Label()
        self.lbl_tab_info.Text = "Pawer Hub"
        self.lbl_tab_info.Font = PawerTheme.get_font(8.5)
        self.lbl_tab_info.ForeColor = PawerTheme.TEXT_MUTED
        self.lbl_tab_info.Location = Point(320, 4)
        self.lbl_tab_info.Size = Size(400, 18)
        self.lbl_tab_info.AutoEllipsis = True
        self.bar_panel.Controls.Add(self.lbl_tab_info)

        # Engine & Version info (Right side)
        self.lbl_engine = Label()
        self.lbl_engine.Text = "System WebView2 Chromium • Super Lightweight"
        self.lbl_engine.Font = PawerTheme.get_font(8.0)
        self.lbl_engine.ForeColor = PawerTheme.TEXT_SUB
        self.lbl_engine.Dock = DockStyle.Right
        self.lbl_engine.Width = 300
        self.lbl_engine.TextAlign = ContentAlignment.MiddleRight
        self.bar_panel.Controls.Add(self.lbl_engine)

        parent_panel.Controls.Add(self.bar_panel)

    def set_status(self, text: str, is_warning: bool = False):
        self.lbl_security.Text = text
        self.lbl_security.ForeColor = PawerTheme.ROSE if is_warning else PawerTheme.EMERALD

    def set_tab_info(self, info: str):
        self.lbl_tab_info.Text = info

    def set_session_stats(self, stats: dict):
        """Updates the right-side engine label with live session anonymity stats."""
        blocked = stats.get("blocked", 0)
        allowed = stats.get("allowed", 0)
        sid = stats.get("session_id", "?")
        self.lbl_engine.Text = (
            f"🔒 Ephemeral • Session {sid} • "
            f"{blocked} blocked / {allowed} allowed"
        )
        self.lbl_security.Text = "🟢 Ephemeral Session • Internet Blocked • UserAgent Spoofed"
        self.lbl_security.ForeColor = PawerTheme.EMERALD
