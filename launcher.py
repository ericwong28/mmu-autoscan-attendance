"""
One-click launcher for Auto Check-in.
Compiled to .exe via: pyinstaller --onefile --name "Auto Check-in" launcher.py
"""
import os
import sys
import shutil
import socket
import subprocess
import time
import webbrowser


def find_python() -> str:
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


def is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for_server(port: int, timeout: int = 15) -> bool:
    print("      Waiting for server", end="", flush=True)
    for _ in range(timeout * 2):
        if is_port_open(port):
            print(" ready!")
            return True
        print(".", end="", flush=True)
        time.sleep(0.5)
    print(" timed out.")
    return False


def main():
    base = os.path.dirname(
        sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    )
    python = find_python()

    print("╔══════════════════════════════════╗")
    print("║     Auto Check-in  Launcher      ║")
    print("╚══════════════════════════════════╝")
    print(f"\n  Python : {python}")
    print(f"  Folder : {base}\n")

    # ── 1. pip dependencies ───────────────────────────────────────────────────
    print("[1/3] Checking pip dependencies...")
    r = subprocess.run(
        [python, "-m", "pip", "install", "-r",
         os.path.join(base, "requirements.txt"), "-q"],
        cwd=base, capture_output=True, text=True,
    )
    print("      OK\n" if r.returncode == 0 else f"      Warning: {r.stderr.strip()}\n")

    # ── 2. Playwright browser ─────────────────────────────────────────────────
    print("[2/3] Checking Playwright browser (may download ~180 MB on first run)...")
    subprocess.run(
        [python, "-m", "playwright", "install", "chromium"],
        cwd=base,
    )
    print()

    # ── 3. Start server ───────────────────────────────────────────────────────
    print("[3/3] Starting server...")
    if is_port_open(8080):
        print("      Already running.\n")
    else:
        subprocess.Popen(
            [python, os.path.join(base, "main.py")],
            cwd=base,
            creationflags=0x08000000,   # CREATE_NO_WINDOW
        )
        if not wait_for_server(8080, timeout=15):
            print("\n  Could not reach server. Please run main.py manually.")
            input("  Press Enter to exit...")
            return

    # ── Open browser ──────────────────────────────────────────────────────────
    print("\n  Opening http://localhost:8080 ...")
    webbrowser.open("http://localhost:8080")
    print("  Done! This window closes in 3 seconds.")
    time.sleep(3)


if __name__ == "__main__":
    main()
