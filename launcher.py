"""
One-click launcher for Auto Check-in.
Compiled to .exe via: pyinstaller --onefile --name "Auto Check-in" launcher.py
"""
import os
import sys
import shutil
import subprocess
import time


def find_python() -> str:
    """Find the system Python executable (even when called from a compiled .exe)."""
    # shutil.which searches the live system PATH at runtime
    for name in ("python", "python3"):
        p = shutil.which(name)
        if p:
            return p
    # Fallback: common Windows install locations
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
    return "python"  # last resort


def main():
    # Directory where this .exe (or .py) lives
    base = os.path.dirname(
        sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
    )

    python = find_python()

    print("╔══════════════════════════════╗")
    print("║     Auto Check-in Launcher   ║")
    print("╚══════════════════════════════╝")
    print(f"\nPython : {python}")
    print(f"Folder : {base}\n")

    # ── Install / verify dependencies ────────────────────────────────────────
    req = os.path.join(base, "requirements.txt")
    print("Checking dependencies...")
    result = subprocess.run(
        [python, "-m", "pip", "install", "-r", req, "-q"],
        cwd=base, capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("Dependencies OK.\n")
    else:
        print(f"pip warning: {result.stderr.strip()}\n")

    # ── Check if server is already running ───────────────────────────────────
    import socket
    already_running = False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        already_running = s.connect_ex(("127.0.0.1", 8080)) == 0

    if already_running:
        print("Server already running — opening browser...")
    else:
        print("Starting server...")
        main_py = os.path.join(base, "main.py")
        subprocess.Popen(
            [python, main_py],
            cwd=base,
            creationflags=0x08000000,  # CREATE_NO_WINDOW (Windows)
        )
        print("Server started.")

    print("\nBrowser will open at http://localhost:8080")
    print("This window closes in 3 seconds...")
    time.sleep(3)


if __name__ == "__main__":
    main()
