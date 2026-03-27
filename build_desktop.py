"""
PyInstaller build script for Cards 4 Sale desktop application.

Usage:
    pip install pyinstaller
    python build_desktop.py

Produces:
    dist/Cards4Sale          (Linux)
    dist/Cards4Sale.exe      (Windows)
    dist/Cards4Sale.app      (macOS)
"""

import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

# Path separator differs between platforms
SEP = ";" if sys.platform == "win32" else ":"

# Icon format is platform-specific:
#   Windows requires .ico, macOS requires .icns, Linux accepts .png
if sys.platform == "win32":
    ICON = os.path.join(ROOT, "assets", "icon.ico")
elif sys.platform == "darwin":
    ICON = os.path.join(ROOT, "assets", "icon.icns")
else:
    ICON = os.path.join(ROOT, "assets", "icon.png")

args = [
    sys.executable, "-m", "PyInstaller",
    "--name", "Cards4Sale",
    "--onefile",
    "--windowed",
    # Bundle templates and static files
    "--add-data", f"{ROOT}/src/templates{SEP}src/templates",
    "--add-data", f"{ROOT}/src/static{SEP}src/static",
    # App icon (platform-specific path set above)
    "--icon", ICON,
    # Entry point
    os.path.join(ROOT, "src", "desktop.py"),
]

if not os.path.exists(ICON):
    print(f"WARNING: Icon file not found at {ICON}.")
    print("  - For Windows: create assets/icon.ico from assets/icon-512.png")
    print("  - For macOS:   create assets/icon.icns from assets/icon-512.png")
    print("  - Proceeding without icon...")
    # Remove the --icon flag and its argument
    icon_idx = args.index("--icon")
    args = args[:icon_idx] + args[icon_idx + 2:]

print("Running PyInstaller with args:")
print(" ".join(args))
subprocess.check_call(args)
