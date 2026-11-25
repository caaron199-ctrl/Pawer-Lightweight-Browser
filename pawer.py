"""
Pawer — Entry point.
Run with: python pawer.py
"""

import os
import sys

# Configure Python.NET for frozen PyInstaller environments
if getattr(sys, "frozen", False):
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    py_ver = f"python{sys.version_info.major}{sys.version_info.minor}.dll"
    candidates = [
        os.path.join(base_dir, py_ver),
        os.path.join(base_dir, "_internal", py_ver),
        os.path.join(os.path.dirname(sys.executable), py_ver),
        os.path.join(os.path.dirname(sys.executable), "_internal", py_ver),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            os.environ["PYTHONNET_PYDLL"] = candidate
            break
    os.environ.setdefault("PYTHONNET_RUNTIME", "netfx")

from pawer.cli import main

if __name__ == "__main__":
    main()
