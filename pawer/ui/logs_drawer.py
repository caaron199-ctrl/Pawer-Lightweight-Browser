"""
Pawer Live Server Logs Drawer — Collapsible bottom terminal console for real-time
server logs, exception tracebacks, and stdout/stderr debugging.
"""

import clr

try:
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Windows.Forms")
except Exception:
    pass

from System import Action
from System.Drawing import Color, Point, Size
from System.Windows.Forms import (
    AnchorStyles,
    BorderStyle,
    Button,
    Clipboard,
    DockStyle,
    FlatStyle,
    Label,
    Panel,
    ScrollBars,
    TextBox,
)

from .theme import PawerTheme


class PawerLogsDrawer:
    """Collapsible terminal drawer showing real-time logs from launched servers."""

    def __init__(self, parent_form):
        self.parent = parent_form
        self.is_open = False
        self._default_height = 220

        # Container panel docked at bottom
        self.drawer_panel = Panel()
        self.drawer_panel.Dock = DockStyle.Bottom
        self.drawer_panel.Height = self._default_height
        self.drawer_panel.BackColor = PawerTheme.BG_SURFACE
        self.drawer_panel.Visible = False

        # Top Control Bar
        self.bar_panel = Panel()
        self.bar_panel.Dock = DockStyle.Top
        self.bar_panel.Height = 30
        self.bar_panel.BackColor = PawerTheme.BG_SURFACE

        # Title Label
        self.lbl_title = Label()
        self.lbl_title.Text = "📄 Live Server Console"
        self.lbl_title.Font = PawerTheme.get_font(8.5, bold=True)
        self.lbl_title.ForeColor = PawerTheme.ACCENT
        self.lbl_title.Location = Point(12, 6)
        self.lbl_title.Size = Size(180, 20)
        self.bar_panel.Controls.Add(self.lbl_title)

        # Action Buttons (Clear, Copy, Close)
        x_offset = 200

        self.btn_clear = self._create_btn("🧹 Clear", x_offset, 55, self.clear_logs)
        x_offset += 62
        self.btn_copy = self._create_btn("📋 Copy", x_offset, 55, self.copy_logs)
        x_offset += 62

        # Right-side Close Button (✕)
        self.btn_close = Button()
        self.btn_close.Text = "✕"
        self.btn_close.Font = PawerTheme.get_font(9.0, bold=True)
        self.btn_close.ForeColor = PawerTheme.TEXT_MUTED
        self.btn_close.BackColor = Color.Transparent
        self.btn_close.FlatStyle = FlatStyle.Flat
        self.btn_close.FlatAppearance.BorderSize = 0
        self.btn_close.Size = Size(28, 24)
        self.btn_close.Dock = DockStyle.Right
        self.btn_close.Click += lambda s, e: self.hide_drawer()
        self.bar_panel.Controls.Add(self.btn_close)

        self.drawer_panel.Controls.Add(self.bar_panel)

        # Monospace Log TextBox
        self.txt_logs = TextBox()
        self.txt_logs.Multiline = True
        self.txt_logs.ReadOnly = True
        self.txt_logs.ScrollBars = ScrollBars.Vertical
        self.txt_logs.WordWrap = False
        self.txt_logs.Dock = DockStyle.Fill
        self.txt_logs.BackColor = PawerTheme.BG_CARD
        self.txt_logs.ForeColor = PawerTheme.TEXT_MAIN
        self.txt_logs.Font = PawerTheme.get_code_font(9.0)
        self.txt_logs.BorderStyle = getattr(BorderStyle, "None")
        self.txt_logs.Text = "[Pawer] Console ready. Logs from Streamlit and local servers stream here.\r\n"

        self.drawer_panel.Controls.Add(self.txt_logs)
        parent_form.Controls.Add(self.drawer_panel)

    def _create_btn(self, text: str, x: int, width: int, on_click) -> Button:
        btn = Button()
        btn.Text = text
        btn.Font = PawerTheme.get_font(8.0)
        btn.ForeColor = PawerTheme.TEXT_MUTED
        btn.BackColor = PawerTheme.BG_CARD
        btn.FlatStyle = FlatStyle.Flat
        btn.FlatAppearance.BorderSize = 0
        btn.Size = Size(width, 22)
        btn.Location = Point(x, 4)
        btn.Click += lambda s, e: on_click()
        self.bar_panel.Controls.Add(btn)
        return btn

    def append_log(self, port: int, line: str):
        """Appends a new log line thread-safely."""
        formatted = f"[{port}] {line}\r\n"

        def _do_append():
            try:
                # Keep log buffer from ballooning indefinitely
                if len(self.txt_logs.Text) > 100000:
                    self.txt_logs.Text = self.txt_logs.Text[-50000:]
                self.txt_logs.AppendText(formatted)
            except Exception:
                pass

        if self.txt_logs.InvokeRequired:
            self.txt_logs.Invoke(Action(_do_append))
        else:
            _do_append()

    def clear_logs(self):
        self.txt_logs.Clear()

    def copy_logs(self):
        try:
            Clipboard.SetText(self.txt_logs.Text)
        except Exception:
            pass

    def toggle_drawer(self):
        if self.is_open:
            self.hide_drawer()
        else:
            self.show_drawer()

    def show_drawer(self):
        self.is_open = True
        self.drawer_panel.Visible = True
        self.drawer_panel.BringToFront()

    def hide_drawer(self):
        self.is_open = False
        self.drawer_panel.Visible = False
