"""
Pawer UI Theme — Color palettes, fonts, and styling primitives for the browser chrome.
"""

import clr

try:
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Windows.Forms")
except Exception:
    pass

from System.Drawing import Color, Font, FontStyle


class PawerTheme:
    # Backgrounds
    BG_BASE = Color.FromArgb(17, 17, 27)         # #11111b
    BG_SURFACE = Color.FromArgb(24, 24, 37)      # #181825
    BG_CARD = Color.FromArgb(30, 30, 46)         # #1e1e2e
    BG_CARD_HOVER = Color.FromArgb(45, 47, 65)   # #2d2f41
    BG_ACTIVE_TAB = Color.FromArgb(49, 50, 68)   # #313244
    BG_INACTIVE_TAB = Color.FromArgb(24, 24, 37) # #181825

    # Foregrounds / Text
    TEXT_MAIN = Color.FromArgb(205, 214, 244)    # #cdd6f4
    TEXT_MUTED = Color.FromArgb(166, 173, 200)   # #a6adc8
    TEXT_SUB = Color.FromArgb(108, 112, 134)     # #6c7086
    TEXT_WHITE = Color.FromArgb(255, 255, 255)

    # Accent and status colors
    ACCENT = Color.FromArgb(203, 166, 247)       # #cba6f7 (Mauve)
    ACCENT_BLUE = Color.FromArgb(137, 180, 250)  # #89b4fa (Blue)
    EMERALD = Color.FromArgb(166, 227, 161)      # #a6e3a1 (Green)
    ROSE = Color.FromArgb(243, 139, 168)         # #f38ba8 (Red)
    AMBER = Color.FromArgb(249, 226, 175)        # #f9e2af (Yellow)

    # Borders
    BORDER = Color.FromArgb(49, 50, 68)          # #313244
    BORDER_LIGHT = Color.FromArgb(69, 71, 90)    # #45475a

    @staticmethod
    def get_font(size: float = 9.5, bold: bool = False) -> Font:
        style = FontStyle.Bold if bold else FontStyle.Regular
        for font_name in ("Segoe UI Variable Display", "Segoe UI", "Tahoma"):
            try:
                return Font(font_name, size, style)
            except Exception:
                continue
        return Font("Arial", size, style)

    @staticmethod
    def get_code_font(size: float = 9.0) -> Font:
        try:
            return Font("Consolas", size, FontStyle.Regular)
        except Exception:
            return Font("Courier New", size, FontStyle.Regular)
