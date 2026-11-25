"""
Pawer Packaging Script — Compiles Pawer into a standalone Windows executable.
Run with: python scripts/build_exe.py
"""

import os
import shutil
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
        "--collect-all=pythonnet",
        "--collect-all=clr_loader",
        "--add-data=pawer/assets;pawer/assets",
        "--hidden-import=clr",
        "--hidden-import=webview.platforms.edgechromium",
        "--hidden-import=pawer.security",
        "--hidden-import=pawer.services",
        "--hidden-import=pawer.ui",
        "pawer.py",
    ]

    print("Running PyInstaller...")
    # Clean up any leftover build directory
    build_dir = root / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)

    res = subprocess.run(cmd)

    if res.returncode == 0:
        # Copy Pawer.exe.config next to Pawer.exe to allow .NET remote assembly loading
        config_src = root / "Pawer.exe.config"
        config_dst = root / "dist" / "Pawer" / "Pawer.exe.config"
        if config_src.is_file():
            shutil.copy2(config_src, config_dst)
            print("✓ Copied Pawer.exe.config (loadFromRemoteSources enabled for extracted ZIPs)")

        # Clean up temporary intermediate build directory so users don't confuse it with dist
        build_dir = root / "build"
        if build_dir.exists():
            try:
                shutil.rmtree(build_dir, ignore_errors=True)
                print("✓ Removed temporary intermediate build/ directory")
            except Exception:
                pass

        # Create release zip from dist/Pawer (packaged inside a root Pawer/ directory)
        zip_base = root / "dist" / "Pawer-v1.0.0-windows-x64"
        try:
            zip_path = shutil.make_archive(str(zip_base), "zip", root_dir=str(root / "dist"), base_dir="Pawer")
            print(f"✓ Created release ZIP (with root Pawer/ folder): {zip_path}")
        except Exception as ex:
            print(f"Note: Could not create zip archive: {ex}")

        print("\n" + "=" * 60)
        print("✅ BUILD COMPLETE!")
        print("=" * 60)
        print("IMPORTANT: The working executable is inside the 'dist' folder:")
        print(f"  👉 dist\\Pawer\\Pawer.exe")
        print("\nFor GitHub Releases, upload:")
        print(f"  📦 dist\\Pawer-v1.0.0-windows-x64.zip")
        print("=" * 60)
        return True
    else:
        print("\n❌ Build failed with error code:", res.returncode)
        return False


if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
