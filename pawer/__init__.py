"""
Pawer — A super lightweight browser for Streamlit apps and local apps.
Designed exclusively for local development, local servers, and offline workflows.
"""

import clr

try:
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Threading")
except Exception:
    pass

__version__ = "1.0.0"
__app_name__ = "Pawer"
