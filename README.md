# MMU Auto Scan Attendance

An automated attendance check-in tool for **Multimedia University (MMU)** students. It monitors your screen for QR codes displayed during class, automatically opens the sign-in page, and fills in your credentials — so you never miss a check-in.

---

## Background

MMU uses a QR-code-based attendance system (`osc.mmu.edu.my`). During each class, a QR code is displayed (on screen, projector, etc.) for a limited time. Students must scan it and submit their credentials to register attendance.

This tool automates the entire process: it watches your screen in the background, detects the QR code the moment it appears, launches a browser, and submits the attendance form — all without manual input.

---

## Features

- 🖥️ **Full-screen monitoring** — captures the entire desktop (all monitors), not just the browser
- 🔍 **Multi-engine QR detection** — uses OpenCV + zxing-cpp with multiple preprocessing passes for reliable detection
- 🤖 **Auto form fill & submit** — opens the sign-in URL in Chromium and fills in your Student ID and password automatically
- 🔁 **Duplicate prevention** — same QR code won't trigger twice within 5 minutes
- 🛑 **Auto-stop** — monitoring stops automatically after a configured number of successful check-ins per session (default: 2)
- 🌐 **Web UI** — control panel accessible at `http://localhost:8080`
- 🔑 **Persistent browser session** — logs in once; cookies are saved for future sessions
- ⚙️ **Configurable** — URL keyword filter, scan interval, custom CSS selectors for form fields

---

## Requirements

> ⚠️ **Python 3.10 or higher must be installed before running.**
>
> Download from: https://www.python.org/downloads/
>
> During installation, check **"Add Python to PATH"**.

All other dependencies (FastAPI, OpenCV, Playwright, etc.) are installed automatically on first launch.

---

## Quick Start

1. **Download** this repository as a ZIP and extract it, or clone it:
   ```
   git clone https://github.com/ericwong28/mmu-autoscan-attendance.git
   ```

2. **Double-click** `Auto Check-in.exe`

   The launcher will:
   - Install all pip dependencies
   - Download the Playwright Chromium browser (~180 MB, first run only)
   - Start the local server
   - Open `http://localhost:8080` in your browser

   > First-run setup may take a few minutes depending on your internet speed.

3. **Configure** your credentials in the Settings panel:
   - Student ID
   - Password
   - URL Keyword Filter: `osc.mmu.edu.my`
   - Max check-ins per session: `2` (adjust as needed)

4. **Click Start** — the tool will monitor your screen and check in automatically when a QR code appears.

---

## How It Works

```
Screen capture (mss)
      ↓
QR code detection (OpenCV → zxing-cpp fallback)
      ↓
URL keyword filter check
      ↓
Duplicate / cooldown check (5 min)
      ↓
Open URL in Playwright Chromium browser
      ↓
Auto-fill Student ID + Password
      ↓
Click Submit → Attendance recorded
      ↓
Session counter +1 → auto-stop when limit reached
```

---

## Configuration

| Field | Description |
|-------|-------------|
| **Student ID** | Your MMU student ID |
| **Password** | Your MMU portal password |
| **URL Keyword Filter** | Only trigger on QR codes containing this string (e.g. `osc.mmu.edu.my`) |
| **Scan Interval** | How often the screen is captured, in seconds (default: 1) |
| **Max check-ins per session** | Auto-stops monitoring after this many successful submissions (default: 2) |

### Advanced — custom form selectors

If auto-fill doesn't work, expand the **Advanced** section and enter the CSS selectors for your sign-in form fields. For MMU's OSC system:

| Field | Selector |
|-------|----------|
| Student ID input | `input[name="N_QRCODE_DRV_USERID"]` |
| Password input | `input[name="N_QRCODE_DRV_PASSWORD"]` |
| Submit button | `input[name="N_QRCODE_DRV_BUTTON1"]` |

---

## Project Structure

```
mmu-autoscan-attendance/
├── Auto Check-in.exe   # One-click launcher (requires Python in PATH)
├── main.py             # FastAPI server + monitor thread + WebSocket
├── monitor.py          # Screen capture + QR code detection
├── checkin.py          # Browser automation (Playwright)
├── config.py           # SQLite config read/write
├── database.py         # SQLite log management
├── launcher.py         # Source for the .exe launcher
├── requirements.txt    # Python dependencies
└── static/
    └── index.html      # Web UI
```

---

## Building the .exe yourself

```bash
pip install pyinstaller
pyinstaller --onefile --name "Auto Check-in" launcher.py
```

The output will be in `dist/Auto Check-in.exe`.

---

## Disclaimer

> **This tool is intended for personal convenience only.**
>
> - Use it only for your own attendance and only for classes you are genuinely attending.
> - The authors take **no responsibility** for any academic penalties, account suspensions, or other consequences arising from misuse of this tool.
> - This project is not affiliated with, endorsed by, or connected to Multimedia University (MMU) in any way.
> - Use of automated tools may violate your institution's academic integrity policy. **You are solely responsible** for ensuring your use complies with MMU's rules and regulations.
> - Credentials (Student ID and password) are stored **locally** in a SQLite database on your own machine. They are never transmitted to any third-party server.

---

## License

MIT License — free to use, modify, and distribute.
