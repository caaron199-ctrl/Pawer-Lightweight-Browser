"""
Pawer Tab Bar — Custom modern tab strip for managing multiple browser tabs.
"""

import clr

try:
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Windows.Forms")
except Exception:
    pass

from typing import Callable, Dict

from System.Drawing import Color, Point, Size
from System.Windows.Forms import (
    Button,
    DockStyle,
    FlatStyle,
    FlowLayoutPanel,
    Label,
    MouseButtons,
    MouseEventArgs,
    Padding,
    Panel,
)

from .theme import PawerTheme


class TabButtonWidget:
    """Widget representing an individual tab item in the tab bar."""

    def __init__(
        self,
        tab_id: str,
        title: str,
        on_select: Callable[[str], None],
        on_close: Callable[[str], None],
    ):
        self.tab_id = tab_id
        self.title = title
        self.on_select = on_select
        self.on_close = on_close
        self.is_active = False

        # Container panel for the tab
        self.container = Panel()
        self.container.Size = Size(180, 32)
        self.container.Margin = Padding(2, 2, 2, 0)
        self.container.BackColor = PawerTheme.BG_INACTIVE_TAB

        # Title label
        self.lbl_title = Label()
        self.lbl_title.Text = self._format_title(title)
        self.lbl_title.Font = PawerTheme.get_font(9.0)
        self.lbl_title.ForeColor = PawerTheme.TEXT_MUTED
        self.lbl_title.Location = Point(10, 7)
        self.lbl_title.Size = Size(142, 20)
        self.lbl_title.AutoEllipsis = True

        # Close button (x)
        self.btn_close = Button()
        self.btn_close.Text = "×"
        self.btn_close.Font = PawerTheme.get_font(10.0, bold=True)
        self.btn_close.ForeColor = PawerTheme.TEXT_SUB
        self.btn_close.BackColor = Color.Transparent
        self.btn_close.FlatStyle = FlatStyle.Flat
        self.btn_close.FlatAppearance.BorderSize = 0
        self.btn_close.FlatAppearance.MouseOverBackColor = PawerTheme.ROSE
        self.btn_close.Size = Size(20, 20)
        self.btn_close.Location = Point(155, 6)

        # Wire click and hover events
        self.lbl_title.Click += lambda s, e: self.on_select(self.tab_id)
        self.container.Click += lambda s, e: self.on_select(self.tab_id)
        self.btn_close.Click += lambda s, e: self.on_close(self.tab_id)

        self.container.MouseEnter += self._on_mouse_enter
        self.container.MouseLeave += self._on_mouse_leave
        self.lbl_title.MouseEnter += self._on_mouse_enter
        self.lbl_title.MouseLeave += self._on_mouse_leave

        self.container.Controls.Add(self.lbl_title)
        self.container.Controls.Add(self.btn_close)

    def _format_title(self, text: str) -> str:
        """Formats and prefixes friendly icons for common local apps."""
        clean = (text or "Pawer Hub").strip()
        lower = clean.lower()
        if "streamlit" in lower:
            return f"🎈 {clean}"
        if "fastapi" in lower or "swagger" in lower:
            return f"⚡ {clean}"
        if "react" in lower or "vite" in lower or "next" in lower:
            return f"⚛️ {clean}"
        if "flask" in lower:
            return f"🧪 {clean}"
        if "pawer" in lower or "home" in lower:
            return f"🐾 {clean}"
        if "offline" in lower:
            return f"🔌 {clean}"
        if "blocked" in lower:
            return f"🛡️ {clean}"
        return clean

    def set_title(self, new_title: str):
        self.title = new_title
        self.lbl_title.Text = self._format_title(new_title)

    def set_active(self, active: bool):
        self.is_active = active
        if active:
            self.container.BackColor = PawerTheme.BG_ACTIVE_TAB
            self.lbl_title.ForeColor = PawerTheme.TEXT_MAIN
            self.lbl_title.Font = PawerTheme.get_font(9.0, bold=True)
            self.btn_close.ForeColor = PawerTheme.TEXT_MUTED
        else:
            self.container.BackColor = PawerTheme.BG_INACTIVE_TAB
            self.lbl_title.ForeColor = PawerTheme.TEXT_MUTED
            self.lbl_title.Font = PawerTheme.get_font(9.0, bold=False)
            self.btn_close.ForeColor = PawerTheme.TEXT_SUB

    def _on_mouse_enter(self, sender, args):
        if not self.is_active:
            self.container.BackColor = PawerTheme.BG_CARD_HOVER

    def _on_mouse_leave(self, sender, args):
        if not self.is_active:
            self.container.BackColor = PawerTheme.BG_INACTIVE_TAB


class PawerTabBar:
    """Horizontal tab strip managing all open tabs."""

    def __init__(
        self,
        parent_panel: Panel,
        on_select_tab: Callable[[str], None],
        on_close_tab: Callable[[str], None],
        on_new_tab: Callable[[], None],
    ):
        self.parent_panel = parent_panel
        self.on_select_tab = on_select_tab
        self.on_close_tab = on_close_tab
        self.on_new_tab = on_new_tab
        self.tab_widgets: Dict[str, TabButtonWidget] = {}

        # Main TabBar container
        self.bar_panel = Panel()
        self.bar_panel.Dock = DockStyle.Top
        self.bar_panel.Height = 36
        self.bar_panel.BackColor = PawerTheme.BG_BASE

        # Brand / Logo Button on the far left
        self.lbl_brand = Label()
        self.lbl_brand.Text = "🐾 PAWER"
        self.lbl_brand.Font = PawerTheme.get_font(10.0, bold=True)
        self.lbl_brand.ForeColor = PawerTheme.ACCENT
        self.lbl_brand.Location = Point(14, 8)
        self.lbl_brand.Size = Size(90, 22)
        self.bar_panel.Controls.Add(self.lbl_brand)

        # FlowLayoutPanel for dynamically placed tabs
        self.tabs_flow = FlowLayoutPanel()
        self.tabs_flow.Location = Point(110, 2)
        self.tabs_flow.Height = 34
        self.tabs_flow.Width = 850
        self.tabs_flow.AutoScroll = False
        self.tabs_flow.WrapContents = False
        self.tabs_flow.BackColor = Color.Transparent
        self.bar_panel.Controls.Add(self.tabs_flow)

        # New Tab (+) button right beside tabs
        self.btn_add_tab = Button()
        self.btn_add_tab.Text = "+"
        self.btn_add_tab.Font = PawerTheme.get_font(13.0, bold=True)
        self.btn_add_tab.ForeColor = PawerTheme.TEXT_MUTED
        self.btn_add_tab.BackColor = Color.Transparent
        self.btn_add_tab.FlatStyle = FlatStyle.Flat
        self.btn_add_tab.FlatAppearance.BorderSize = 0
        self.btn_add_tab.FlatAppearance.MouseOverBackColor = PawerTheme.BG_CARD_HOVER
        self.btn_add_tab.Size = Size(32, 28)
        self.btn_add_tab.Margin = Padding(4, 3, 0, 0)
        self.btn_add_tab.Click += lambda s, e: self.on_new_tab()
        self.tabs_flow.Controls.Add(self.btn_add_tab)

        self.parent_panel.Controls.Add(self.bar_panel)

    def add_tab(self, tab_id: str, title: str):
        """Adds a new tab widget to the tab strip."""
        widget = TabButtonWidget(
            tab_id=tab_id,
            title=title,
            on_select=self.on_select_tab,
            on_close=self.on_close_tab,
        )
        self.tab_widgets[tab_id] = widget

        # Insert before the '+' button
        self.tabs_flow.Controls.Remove(self.btn_add_tab)
        self.tabs_flow.Controls.Add(widget.container)
        self.tabs_flow.Controls.Add(self.btn_add_tab)

    def set_active_tab(self, tab_id: str):
        """Highlights the active tab and unhighlights the others."""
        for tid, widget in self.tab_widgets.items():
            widget.set_active(tid == tab_id)

    def update_tab_title(self, tab_id: str, new_title: str):
        """Updates the text displayed on a specific tab."""
        if tab_id in self.tab_widgets:
            self.tab_widgets[tab_id].set_title(new_title)

    def remove_tab(self, tab_id: str):
        """Removes a tab widget from the tab strip."""
        if tab_id in self.tab_widgets:
            widget = self.tab_widgets.pop(tab_id)
            self.tabs_flow.Controls.Remove(widget.container)
            widget.container.Dispose()
