# 🐾 Pawer

> **A super lightweight browsing application designed specifically for Streamlit apps and local web tools.**  
> Built for speed, offline workflows, zero telemetry, and complete local privacy. **Not designed to browse the open internet.**
> Pawer is intentionally designed NOT to browse the open web**

---

## 💡Pawer?

General-purpose browsers like Google Chrome and Mozilla Firefox are built to browse the open web. For local development, running Streamlit dashboards, or viewing internal tools, they come with substantial drawbacks:
- **Massive Resource Bloat**: Modern Chrome or Firefox often consumes 500MB to 1.5GB of RAM just idling with a couple tabs.
- **Unwanted Internet Wandering**: Search engine suggestions, cloud analytics, tracking scripts, and external links distract from local tasks.
- **Broken Local Workflows**: If a local server isn't running yet, standard browsers show generic, dead `ERR_CONNECTION_REFUSED` pages with zero diagnostic help.
- **Lost Process Tracking**: Running `streamlit run app.py` leaves terminal windows cluttering your workspace or orphan python processes hogging ports when the browser is closed.

---

## ✨ Key Features

- 🪶 **Ultra-Lightweight Engine**: Built on top of Microsoft Edge WebView2 (Chromium) natively installed on Windows. Starts in under 200ms, consumes **~50–150 MB RAM** (vs ~500 MB+ in Chrome), and requires **no bulky 200MB bundled Electron/Chromium binaries**.
- 🛡️ **Internet Isolation & Local Guardian**: Strictly accepts local and private LAN traffic (`localhost`, `127.0.0.1`, `[::1]`, `192.168.x.x`, `10.x.x.x`, `file://`, and `pawer://` internal schemes). Navigation to external internet domains (like `google.com`) is **automatically intercepted and blocked**, keeping your work private, distraction-free, and offline.
- 🔒 **Total Anonymity & Privacy Hardening**:
  - **Ephemeral In-Memory Sessions**: Every launch generates a cryptographically random session ID and an isolated temp directory that is completely wiped on exit.
  - **Strict InPrivate Mode**: Prevents cookies, localStorage, browsing history, and autofill from persisting across launches.
  - **Fingerprint Resistance**: User-Agent spoofing (`Pawer/1.0`), battery API blocked, ambient light sensors disabled, canvas color cache disabled, and hardware discovery APIs (WebBluetooth, WebUsb, WebHid) turned off.
  - **Zero Telemetry**: All crash reporting, field trials, background networking, component updates, and phone-home telemetry are hard-disabled via 28+ Chromium process flags.
  - **HTTP Header Scrubber**: Automatically strips identifying outbound headers (`Referer`, `Origin`, `X-Forwarded-For`, `Via`, `X-Real-IP`) and injects privacy headers (`DNT: 1`, `Sec-GPC: 1`).
  - **Security Dashboard (`pawer://security`)**: View live session metrics (blocked/allowed requests, session ID, active privacy flags).
- 🎈 **Streamlit Superpowers**:
  - **1-Click Streamlit Runner**: Click **"🚀 Run App"** or pass a `.py` file to automatically spin up Streamlit headlessly in the background on an available port and open it immediately in a tab.
  - **Zero-Orphan Process Management**: Background processes spawned by Pawer are tracked and cleanly terminated when their tab or Pawer closes.
  - **Persistent WebSockets**: Switching between tabs never drops Streamlit session state or causes websocket reconnection flickers.
- 📑 **Multi-Tab Architecture**: Open multiple local apps side-by-side (e.g. Tab 1: Streamlit Dashboard on `8501`, Tab 2: FastAPI Swagger Docs on `8000`, Tab 3: Vite/React Frontend on `3000`).
- 🛰️ **Active Port Hub (`pawer://home`)**: The built-in offline New Tab page automatically scans common local ports (8501, 8000, 3000, 5000, 5173, 8080, 7860, 8888) in < 15ms and displays live `🟢 ONLINE` badges with 1-click connect buttons.
- ⚡ **Smart Address Bar**:
  - Type just a port number like `8501` or `3000` and press <kbd>Enter</kbd> — Pawer automatically expands it to `http://localhost:8501`.
  - Quick-switch chips for common developer ports right next to the URL bar.
- 🛠️ **Developer Tools & Kiosk Mode**:
  - Press <kbd>F12</kbd> or click **"🛠 DevTools"** to open Chromium DevTools (Inspect Element, Console, Network monitoring).
  - Press <kbd>F11</kbd> to toggle Fullscreen / Kiosk mode — perfect for running Streamlit dashboards as standalone executive displays.
  - Instant cache flushing with the **"🧹"** button.

---

## 🚀 Quick Start

### 1. Requirements
- Windows 10 / 11 (with Microsoft Edge WebView2 runtime, standard on Windows)
- Python 3.9+ (Python 3.14 verified)

### 2. Launching Pawer

You can run Pawer directly using Python or the provided batch script:

```bash
# Launch Pawer Hub (Default New Tab)
python pawer.py
# or using the batch script
.\pawer.bat
```

```bash
# Open directly to a local port
python pawer.py 8501

# Launch a Streamlit script directly
python pawer.py examples/sample_streamlit_app.py

# Open a local URL
python pawer.py localhost:8000

# Serve a local directory statically
python pawer.py --serve ./my_web_folder
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| <kbd>Ctrl</kbd> + <kbd>T</kbd> | Open New Tab (Pawer Hub) |
| <kbd>Ctrl</kbd> + <kbd>W</kbd> | Close Current Tab |
| <kbd>Ctrl</kbd> + <kbd>R</kbd> or <kbd>F5</kbd> | Reload Current Page |
| <kbd>Ctrl</kbd> + <kbd>L</kbd> or <kbd>Alt</kbd> + <kbd>D</kbd> | Focus Address Bar |
| <kbd>F12</kbd> or <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>I</kbd> | Open Chromium DevTools |
| <kbd>Alt</kbd> + <kbd>Left</kbd> | Navigate Back |
| <kbd>Alt</kbd> + <kbd>Right</kbd> | Navigate Forward |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>A</kbd> | Toggle Airgap / Isolation Mode (`Local` ↔ `Airgap` ↔ `Open`) |
| <kbd>Ctrl</kbd> + <kbd>J</kbd> or <kbd>F10</kbd> | Toggle Live Server Console / Logs Drawer |
| <kbd>Alt</kbd> + <kbd>S</kbd> | Toggle Side-by-Side Split View |
| <kbd>F11</kbd> | Toggle Fullscreen / Kiosk Mode |

---

## 📁 Project Structure

```
Pawer/
├── pawer/
│   ├── __init__.py           # Package version & CLR assembly initialization
│   ├── app.py                # Main Pawer Form application & multi-tab coordinator
│   ├── webview_tab.py        # Tab controller wrapping WebView2 with security hooks
│   ├── cli.py                # CLI argument parser and STA runner
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── theme.py          # Modern dark palette (Catppuccin Mocha) & typography
│   │   ├── tab_bar.py        # Dynamic tab strip with close buttons and '+' launcher
│   │   ├── nav_bar.py        # Address bar, quick port chips, logs & split toggles
│   │   ├── status_bar.py     # Local isolation shield and active connection stats
│   │   ├── logs_drawer.py    # Collapsible live server logs & stdout/stderr console
│   │   ├── toast.py          # Auto-fading security alert toast notifications
│   │   └── tray.py           # Windows notification area system tray integration
│   ├── security/
│   │   ├── __init__.py
│   │   ├── guardian.py           # Local IP & CIDR validator, URL normalizer, Airgap toggle
│   │   ├── hardener.py           # Chromium privacy flags, User-Agent spoof, InPrivate mode
│   │   ├── session_manager.py    # Ephemeral sessions, isolated temp dirs, auto-cleanup
│   │   ├── offline_cache.py      # Offline CDN asset fallback cache (fonts/icons/scripts)
│   │   └── request_interceptor.py# WebResourceRequested filter & HTTP header scrubber
│   └── services/
│       ├── __init__.py
│       ├── port_scanner.py   # Multi-threaded port scanner, PID inspector & port killer
│       ├── app_launcher.py   # Streamlit/HTTP runner with live background log streaming
│       ├── favorites.py      # Pinned project workspaces and favorites persistence
│       └── pages.py          # Offline internal pages (pawer://home, blocked, error, security)
├── scripts/
│   └── build_exe.py          # Standalone Windows executable builder
├── build.bat                 # 1-click PyInstaller compiler
├── examples/
│   └── sample_streamlit_app.py # Interactive showcase app with charts & diagnostics
├── tests/
│   └── test_pawer.py         # Unit and integration test suite
├── pawer.py                  # Direct entry point
├── pawer.bat                 # Windows double-click runner
├── pyproject.toml            # Project packaging specification
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation
```

---

## 🧪 Running the Tests

To run the automated unit and integration tests:

```bash
python tests/test_pawer.py
```

All tests run locally in ~1 second, validating security boundaries, URL normalizations, internal HTML pages, and WinForms/WebView2 lifecycle.

---

## 🔒 Security Policy: Local-Only Boundary & Airgap Toggle

Pawer provides a 1-click **Dynamic Network Isolation Switch** (toggleable via the top navigation badge, the `pawer://security` page, or <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>A</kbd>):

| Mode | Behavior | Use Case |
| :--- | :--- | :--- |
| **🟢 Local Isolation** *(Default)* | Loopback (`127.0.0.1`, `localhost`) and local LAN (`192.168.x.x`, `10.x.x.x`, `*.local`) permitted. All external internet strictly blocked. | Running Streamlit apps, local AI models, and communicating with private network test devices. |
| **🔒 Strict Airgap** *(100% Isolated)* | Blocks external internet **AND** cuts off local LAN/Wi-Fi/mDNS. **Only** `127.0.0.1`, `localhost`, `file://`, and `pawer://` can connect. Zero packets leave your physical machine. | Working with sensitive airgapped datasets, proprietary models, or untrusted local scripts that shouldn't probe your LAN. |
| **⚠️ Unrestricted** *(Open)* | External internet temporarily allowed. | Quickly looking up API documentation or external guides when needed. |

When any navigation or sub-resource fetch occurs:
1. **Pawer Guardian & Request Interceptor** evaluate the destination host against the active isolation policy.
2. If unauthorized, requests are blocked immediately with zero network traffic emitted.
3. The security status bar, address bar badge, and live audit stats update instantaneously.

---

## 📄 License

MIT License. Designed with 🐾 for local developers and data scientists.
