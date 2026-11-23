"""
Pawer Packaging Script — Compiles Pawer into a standalone, single-file Windows executable (Pawer.exe).
Run with: python scripts/build_exe.py
"""

import os
import subprocess
import sys
from pathlib import Path


def build():
    root = Path(__file__).parent.parent.resolve()
    os.chdir(root)

    print("🐾 Pawer Standalone Binary Builder")
    print(f"Target directory: {root}")

    # Check if pyinstaller is installed
    try:
        import PyInstaller
        print(f"✓ Found PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not found. Please install with: pip install pyinstaller")
        return False

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=Pawer",
        "--icon=pawer.ico",
        "--add-data=pawer/assets;pawer/assets",
        "--hidden-import=clr",
        "--hidden-import=webview.platforms.edgechromium",
        "--hidden-import=pawer.security",
        "--hidden-import=pawer.services",
        "--hidden-import=pawer.ui",
        "pawer.py",
    ]

    print("Running build:", " ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\n✅ Build successful! Standalone executable located at: dist/Pawer/Pawer.exe")
        return True
    else:
        print("\n❌ Build failed with error code:", res.returncode)
        return False


if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
