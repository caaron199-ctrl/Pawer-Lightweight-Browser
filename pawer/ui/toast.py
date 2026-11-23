"""
Pawer Toast Alert — Non-intrusive floating notification toast for blocked outbound requests
and security alerts, automatically positioned in the bottom-right corner.
"""

import clr
from urllib.parse import urlparse

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
    DockStyle,
    Label,
    Panel,
    Timer,
)

from .theme import PawerTheme


class PawerToast:
    """Floating alert toast that notifies the user when an external request is blocked."""

    def __init__(self, parent_form):
        self.parent = parent_form

        self.panel = Panel()
        self.panel.Size = Size(340, 50)
        self.panel.BackColor = PawerTheme.BG_CARD
        self.panel.BorderStyle = getattr(BorderStyle, "None")
        self.panel.Visible = False
        self.panel.Anchor = AnchorStyles.Bottom | AnchorStyles.Right

        # Accent border stripe (left edge)
        self.stripe = Panel()
        self.stripe.Dock = DockStyle.Left if hasattr(AnchorStyles, "Left") else None
        self.stripe.Width = 4
        self.stripe.BackColor = PawerTheme.ROSE
        self.panel.Controls.Add(self.stripe)

        # Header Title
        self.lbl_title = Label()
        self.lbl_title.Text = "🛡️ External Connection Blocked"
        self.lbl_title.Font = PawerTheme.get_font(8.5, bold=True)
        self.lbl_title.ForeColor = PawerTheme.ROSE
        self.lbl_title.Location = Point(12, 6)
        self.lbl_title.Size = Size(320, 18)
        self.panel.Controls.Add(self.lbl_title)

        # Detail text (host/domain)
        self.lbl_detail = Label()
        self.lbl_detail.Text = "Airgap isolation prevented outbound traffic"
        self.lbl_detail.Font = PawerTheme.get_font(8.0)
        self.lbl_detail.ForeColor = PawerTheme.TEXT_MUTED
        self.lbl_detail.Location = Point(12, 26)
        self.lbl_detail.Size = Size(320, 18)
        self.lbl_detail.AutoEllipsis = True
        self.panel.Controls.Add(self.lbl_detail)

        # Auto-hide timer
        self.timer = Timer()
        self.timer.Interval = 3000
        self.timer.Tick += self._on_timer_tick

        parent_form.Controls.Add(self.panel)

    def show_blocked_alert(self, blocked_url: str):
        """Displays the toast with details about the blocked host."""
        try:
            parsed = urlparse(blocked_url)
            host = parsed.netloc or parsed.path or blocked_url
        except Exception:
            host = blocked_url

        def _do_show():
            try:
                self.lbl_detail.Text = f"Blocked: {host} (Airgap Active)"
                # Position in bottom-right corner just above status bar
                x = max(10, self.parent.ClientSize.Width - self.panel.Width - 16)
                y = max(10, self.parent.ClientSize.Height - self.panel.Height - 34)
                self.panel.Location = Point(x, y)
                self.panel.Visible = True
                self.panel.BringToFront()
                self.timer.Stop()
                self.timer.Start()
            except Exception:
                pass

        if self.panel.InvokeRequired:
            self.panel.Invoke(Action(_do_show))
        else:
            _do_show()

    def _on_timer_tick(self, sender, args):
        self.timer.Stop()
        self.panel.Visible = False
