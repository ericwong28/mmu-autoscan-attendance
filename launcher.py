"""
One-click launcher for Auto Check-in.
Compiled to .exe via: pyinstaller --onefile --name "Auto Check-in" launcher.py
"""
import os
import sys
import shutil
import subprocess
import time
import socket


def find_python() -> str:
    """Find the system Python executable (even when called from a compiled .exe)."""
    for name in ("python", "python3"):
        p = shutil.which(name)
        if p:
            return p
    for p in [
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python313\python.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python312\python.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python311\python.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python310\python.exe"),
        r"C:\Python313\python.exe",
        r"C:\Python312\python.exe",
        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe",
    ]:
        if os.path.exists(p):
            return p
    return "python"


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def main():
    base = os.path.dirname(
        sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    )
    python = find_python()

    print("╔══════════════════════════════════╗")
    print("║     Auto Check-in  Launcher      ║")
    print("╚══════════════════════════════════╝")
    print(f"\n  Python  : {python}")
    print(f"  Folder  : {base}\n")

    # ── 1. pip dependencies ───────────────────────────────────────────────────
    print("[1/3] Checking pip dependencies...")
    req = os.path.join(base, "requirements.txt")
    r = run([python, "-m", "pip", "install", "-r", req, "-q"], cwd=base)
    if r.returncode == 0:
        print("      OK\n")
    else:
        print(f"      Warning: {r.stderr.strip()}\n")

    # ── 2. Playwright browser ─────────────────────────────────────────────────
    print("[2/3] Checking Playwright browser (may download ~180 MB on first run)...")
    r = subprocess.run(
        [python, "-m", "playwright", "install", "chromium"],
        cwd=base
    )
    if r.returncode == 0:
        print("      OK\n")
    else:
        print("      Warning: playwright install may have failed.\n")

    # ── 3. Start server ───────────────────────────────────────────────────────
    print("[3/3] Starting server...")
    already_running = socket.connect_ex(("127.0.0.1", 8080)) == 0
    if already_running:
        print("      Already running — opening browser...\n")
    else:
        main_py = os.path.join(base, "main.py")
        subprocess.Popen(
            [python, main_py],
            cwd=base,
            creationflags=0x08000000,   # CREATE_NO_WINDOW
        )
        print("      Server started.\n")

    print("  Browser will open at http://localhost:8080")
    print("  This window closes in 3 seconds...")
    time.sleep(3)


if __name__ == "__main__":
    main()
