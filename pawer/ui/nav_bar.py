"""
Pawer Navigation Bar — Address bar, navigation buttons, quick port chips, and devtools.
"""

import clr

try:
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Windows.Forms")
except Exception:
    pass

from typing import Callable, Optional

from System.Drawing import Color, Point, Size
from System.Windows.Forms import (
    AnchorStyles,
    BorderStyle,
    Button,
    Cursors,
    DockStyle,
    FlatStyle,
    KeyEventArgs,
    Keys,
    Label,
    Padding,
    Panel,
    TextBox,
)

from .theme import PawerTheme


class PawerNavBar:
    """Navigation and address toolbar."""

    def __init__(
        self,
        parent_panel: Panel,
        on_navigate: Callable[[str], None],
        on_back: Callable[[], None],
        on_forward: Callable[[], None],
        on_reload: Callable[[], None],
        on_home: Callable[[], None],
        on_run_streamlit: Callable[[], None],
        on_devtools: Callable[[], None],
        on_clear_cache: Callable[[], None],
        on_toggle_isolation: Optional[Callable[[], None]] = None,
        on_toggle_logs: Optional[Callable[[], None]] = None,
        on_toggle_split: Optional[Callable[[], None]] = None,
    ):
        self.on_navigate = on_navigate
        self.on_back = on_back
        self.on_forward = on_forward
        self.on_reload = on_reload
        self.on_home = on_home
        self.on_run_streamlit = on_run_streamlit
        self.on_devtools = on_devtools
        self.on_clear_cache = on_clear_cache
        self.on_toggle_isolation = on_toggle_isolation
        self.on_toggle_logs = on_toggle_logs
        self.on_toggle_split = on_toggle_split

        # Main Nav Bar panel
        self.bar_panel = Panel()
        self.bar_panel.Dock = DockStyle.Top
        self.bar_panel.Height = 44
        self.bar_panel.BackColor = PawerTheme.BG_SURFACE

        # Navigation Buttons (Back, Forward, Reload, Home)
        self.btn_back = self._create_icon_btn("◀", 10, self.on_back)
        self.btn_forward = self._create_icon_btn("▶", 42, self.on_forward)
        self.btn_reload = self._create_icon_btn("🔄", 74, self.on_reload)
        self.btn_home = self._create_icon_btn("🏠", 106, self.on_home)

        # Isolation Mode Toggle Badge / Button
        self.btn_isolation = Button()
        self.btn_isolation.Text = "🛡️ Local"
        self.btn_isolation.Font = PawerTheme.get_font(8.0, bold=True)
        self.btn_isolation.ForeColor = PawerTheme.EMERALD
        self.btn_isolation.BackColor = PawerTheme.BG_CARD
        self.btn_isolation.FlatStyle = FlatStyle.Flat
        self.btn_isolation.FlatAppearance.BorderSize = 0
        self.btn_isolation.Location = Point(140, 8)
        self.btn_isolation.Size = Size(76, 28)
        self.btn_isolation.Cursor = Cursors.Hand
        if self.on_toggle_isolation:
            self.btn_isolation.Click += lambda s, e: self.on_toggle_isolation()
        else:
            self.btn_isolation.Click += lambda s, e: self.on_navigate("pawer://security")
        self.bar_panel.Controls.Add(self.btn_isolation)

        # Address Bar Container Panel (for smooth border effect)
        self.address_container = Panel()
        self.address_container.Location = Point(222, 7)
        self.address_container.Size = Size(444, 30)
        self.address_container.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.address_container.BackColor = PawerTheme.BG_CARD

        # Address Bar TextBox
        self.txt_address = TextBox()
        self.txt_address.Font = PawerTheme.get_font(9.5)
        self.txt_address.BackColor = PawerTheme.BG_CARD
        self.txt_address.ForeColor = PawerTheme.TEXT_MAIN
        self.txt_address.BorderStyle = getattr(BorderStyle, "None")
        self.txt_address.Location = Point(10, 6)
        self.txt_address.Size = Size(440, 20)
        self.txt_address.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.txt_address.KeyDown += self._on_address_keydown

        self.address_container.Controls.Add(self.txt_address)
        self.bar_panel.Controls.Add(self.address_container)

        # Quick Port Chips panel (Right side)
        self.right_panel = Panel()
        self.right_panel.Dock = DockStyle.Right
        self.right_panel.Width = 590
        self.right_panel.BackColor = Color.Transparent
        self.bar_panel.Controls.Add(self.right_panel)

        # Quick Port Chips: 8501, 8000, 3000
        x_offset = 6
        for port, label, icon in [
            (8501, "8501", "🎈"),
            (8000, "8000", "⚡"),
            (3000, "3000", "⚛️"),
        ]:
            chip = Button()
            chip.Text = f"{icon} {label}"
            chip.Font = PawerTheme.get_font(8.5, bold=True)
            chip.ForeColor = PawerTheme.TEXT_MUTED
            chip.BackColor = PawerTheme.BG_CARD
            chip.FlatStyle = FlatStyle.Flat
            chip.FlatAppearance.BorderSize = 0
            chip.FlatAppearance.MouseOverBackColor = PawerTheme.BG_CARD_HOVER
            chip.Size = Size(64, 28)
            chip.Location = Point(x_offset, 8)
            chip.Click += self._make_port_click_handler(port)
            self.right_panel.Controls.Add(chip)
            x_offset += 68

        # Split View Button
        self.btn_split = Button()
        self.btn_split.Text = "◫ Split"
        self.btn_split.Font = PawerTheme.get_font(8.5)
        self.btn_split.ForeColor = PawerTheme.TEXT_MUTED
        self.btn_split.BackColor = PawerTheme.BG_CARD
        self.btn_split.FlatStyle = FlatStyle.Flat
        self.btn_split.FlatAppearance.BorderSize = 0
        self.btn_split.FlatAppearance.MouseOverBackColor = PawerTheme.BG_CARD_HOVER
        self.btn_split.Size = Size(64, 28)
        self.btn_split.Location = Point(x_offset, 8)
        if self.on_toggle_split:
            self.btn_split.Click += lambda s, e: self.on_toggle_split()
        self.right_panel.Controls.Add(self.btn_split)
        x_offset += 70

        # Live Console / Server Logs Button
        self.btn_logs = Button()
        self.btn_logs.Text = "📄 Logs"
        self.btn_logs.Font = PawerTheme.get_font(8.5)
        self.btn_logs.ForeColor = PawerTheme.TEXT_MUTED
        self.btn_logs.BackColor = PawerTheme.BG_CARD
        self.btn_logs.FlatStyle = FlatStyle.Flat
        self.btn_logs.FlatAppearance.BorderSize = 0
        self.btn_logs.FlatAppearance.MouseOverBackColor = PawerTheme.BG_CARD_HOVER
        self.btn_logs.Size = Size(66, 28)
        self.btn_logs.Location = Point(x_offset, 8)
        if self.on_toggle_logs:
            self.btn_logs.Click += lambda s, e: self.on_toggle_logs()
        self.right_panel.Controls.Add(self.btn_logs)
        x_offset += 72

        # Action Buttons: Run App, DevTools, Cache
        self.btn_run = Button()
        self.btn_run.Text = "🚀 Run App"
        self.btn_run.Font = PawerTheme.get_font(9.0, bold=True)
        self.btn_run.ForeColor = Color.FromArgb(17, 17, 27)
        self.btn_run.BackColor = PawerTheme.ACCENT
        self.btn_run.FlatStyle = FlatStyle.Flat
        self.btn_run.FlatAppearance.BorderSize = 0
        self.btn_run.FlatAppearance.MouseOverBackColor = PawerTheme.ACCENT_BLUE
        self.btn_run.Size = Size(90, 28)
        self.btn_run.Location = Point(x_offset, 8)
        self.btn_run.Click += lambda s, e: self.on_run_streamlit()
        self.right_panel.Controls.Add(self.btn_run)
        x_offset += 96

        self.btn_devtools = Button()
        self.btn_devtools.Text = "🛠 DevTools"
        self.btn_devtools.Font = PawerTheme.get_font(8.5)
        self.btn_devtools.ForeColor = PawerTheme.TEXT_MUTED
        self.btn_devtools.BackColor = PawerTheme.BG_CARD
        self.btn_devtools.FlatStyle = FlatStyle.Flat
        self.btn_devtools.FlatAppearance.BorderSize = 0
        self.btn_devtools.FlatAppearance.MouseOverBackColor = PawerTheme.BG_CARD_HOVER
        self.btn_devtools.Size = Size(78, 28)
        self.btn_devtools.Location = Point(x_offset, 8)
        self.btn_devtools.Click += lambda s, e: self.on_devtools()
        self.right_panel.Controls.Add(self.btn_devtools)
        x_offset += 84

        self.btn_cache = Button()
        self.btn_cache.Text = "🧹"
        self.btn_cache.Font = PawerTheme.get_font(9.0)
        self.btn_cache.ForeColor = PawerTheme.TEXT_MUTED
        self.btn_cache.BackColor = PawerTheme.BG_CARD
        self.btn_cache.FlatStyle = FlatStyle.Flat
        self.btn_cache.FlatAppearance.BorderSize = 0
        self.btn_cache.FlatAppearance.MouseOverBackColor = PawerTheme.BG_CARD_HOVER
        self.btn_cache.Size = Size(32, 28)
        self.btn_cache.Location = Point(x_offset, 8)
        self.btn_cache.Click += lambda s, e: self.on_clear_cache()
        self.right_panel.Controls.Add(self.btn_cache)

        parent_panel.Controls.Add(self.bar_panel)

    def _create_icon_btn(self, icon: str, x: int, handler: Callable[[], None]) -> Button:
        btn = Button()
        btn.Text = icon
        btn.Font = PawerTheme.get_font(10.0)
        btn.ForeColor = PawerTheme.TEXT_MAIN
        btn.BackColor = Color.Transparent
        btn.FlatStyle = FlatStyle.Flat
        btn.FlatAppearance.BorderSize = 0
        btn.FlatAppearance.MouseOverBackColor = PawerTheme.BG_CARD_HOVER
        btn.Size = Size(30, 28)
        btn.Location = Point(x, 8)
        btn.Click += lambda s, e: handler()
        self.bar_panel.Controls.Add(btn)
        return btn

    def _make_port_click_handler(self, port: int):
        return lambda s, e: self.on_navigate(f"http://localhost:{port}")

    def _on_address_keydown(self, sender, args: KeyEventArgs):
        if args.KeyCode == Keys.Enter:
            args.SuppressKeyPress = True
            text = self.txt_address.Text.strip()
            self.on_navigate(text)

    def set_url(self, url: str):
        """Updates the text in the address bar."""
        self.txt_address.Text = url

    def set_nav_state(self, can_back: bool, can_forward: bool):
        """Enables/disables Back and Forward buttons based on history."""
        self.btn_back.ForeColor = PawerTheme.TEXT_MAIN if can_back else PawerTheme.TEXT_SUB
        self.btn_forward.ForeColor = PawerTheme.TEXT_MAIN if can_forward else PawerTheme.TEXT_SUB

    def update_isolation_badge(self, mode: str):
        """Updates the isolation toggle button label and accent color."""
        mode = mode.lower().strip()
        if mode == "airgap":
            self.btn_isolation.Text = "🔒 Airgap"
            self.btn_isolation.ForeColor = PawerTheme.ACCENT_BLUE
        elif mode == "open":
            self.btn_isolation.Text = "⚠️ Open"
            self.btn_isolation.ForeColor = PawerTheme.ROSE
        else:
            self.btn_isolation.Text = "🛡️ Local"
            self.btn_isolation.ForeColor = PawerTheme.EMERALD
