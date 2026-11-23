"""
Pawer Internal Pages — Ultra-fast, offline, self-contained HTML5 interfaces
for Pawer Home, Blocked Navigation Shield, and Connection Diagnostics.
"""

import json
from typing import Dict, List, Optional
from urllib.parse import quote_plus


def get_base_css() -> str:
    return """
        :root {
            --bg-base: #11111b;
            --bg-surface: #181825;
            --bg-card: #1e1e2e;
            --bg-card-hover: #26263a;
            --accent: #cba6f7;
            --accent-hover: #b4befe;
            --emerald: #a6e3a1;
            --emerald-bg: rgba(166, 227, 161, 0.12);
            --amber: #f9e2af;
            --rose: #f38ba8;
            --rose-bg: rgba(243, 139, 168, 0.12);
            --text-main: #cdd6f4;
            --text-muted: #a6adc8;
            --text-sub: #6c7086;
            --border: #313244;
            --border-highlight: #45475a;
            --font: 'Segoe UI Variable Display', 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: var(--font);
            -webkit-user-select: none;
            user-select: none;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            overflow-y: auto;
        }

        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-base);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--border-highlight);
        }

        .container {
            max-width: 1080px;
            margin: 0 auto;
            padding: 40px 24px 60px;
            width: 100%;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 10px 18px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--bg-card);
            color: var(--text-main);
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
        }
        .btn:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-highlight);
            transform: translateY(-1px);
        }
        .btn-primary {
            background: linear-gradient(135deg, #cba6f7 0%, #89b4fa 100%);
            color: #11111b;
            border: none;
            font-weight: 600;
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #d8b4fe 0%, #93c5fd 100%);
            box-shadow: 0 4px 14px rgba(203, 166, 247, 0.35);
        }
        .btn-success {
            background: var(--emerald-bg);
            color: var(--emerald);
            border-color: rgba(166, 227, 161, 0.3);
        }
        .btn-success:hover {
            background: rgba(166, 227, 161, 0.2);
            border-color: var(--emerald);
        }
        .btn-danger {
            background: var(--rose-bg);
            color: var(--rose);
            border-color: rgba(243, 139, 168, 0.3);
        }
        .btn-danger:hover {
            background: rgba(243, 139, 168, 0.2);
        }
    """


HOME_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pawer Hub</title>
    <style>
        {{BASE_CSS}}

        .header {
            text-align: center;
            margin-bottom: 36px;
        }
        .logo-badge {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            background: rgba(203, 166, 247, 0.1);
            border: 1px solid rgba(203, 166, 247, 0.25);
            padding: 8px 20px;
            border-radius: 9999px;
            margin-bottom: 16px;
        }
        .logo-paw {
            font-size: 26px;
        }
        .logo-title {
            font-size: 24px;
            font-weight: 800;
            background: linear-gradient(135deg, #cba6f7 0%, #89b4fa 50%, #a6e3a1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }
        .subtitle {
            color: var(--text-muted);
            font-size: 15px;
            max-width: 580px;
            margin: 0 auto;
            line-height: 1.5;
        }

        .hero-bar {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 36px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        }
        .quick-launch-group {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
        }
        .quick-input {
            flex: 1;
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 11px 16px;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.15s;
        }
        .quick-input:focus {
            border-color: var(--accent);
        }

        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 18px;
        }
        .section-title {
            font-size: 18px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--text-main);
        }
        .section-badge {
            font-size: 12px;
            padding: 3px 10px;
            border-radius: 9999px;
            background: var(--bg-card);
            color: var(--text-muted);
            border: 1px solid var(--border);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 16px;
            margin-bottom: 36px;
        }

        .card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 14px;
            transition: all 0.18s ease;
        }
        .card:hover {
            background: var(--bg-card);
            border-color: var(--border-highlight);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
        }
        .card.is-online {
            border-color: rgba(166, 227, 161, 0.4);
            background: linear-gradient(180deg, rgba(166, 227, 161, 0.04) 0%, var(--bg-surface) 100%);
        }

        .card-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
        }
        .card-icon-title {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .card-icon {
            font-size: 24px;
            background: var(--bg-card);
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            border: 1px solid var(--border);
        }
        .card-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-main);
        }
        .card-port {
            font-size: 12px;
            color: var(--text-sub);
            font-family: Consolas, monospace;
        }
        .status-pill {
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-online {
            background: var(--emerald-bg);
            color: var(--emerald);
            border: 1px solid rgba(166, 227, 161, 0.3);
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .status-online::before {
            content: '';
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--emerald);
            box-shadow: 0 0 8px var(--emerald);
        }
        .status-offline {
            background: rgba(108, 112, 134, 0.15);
            color: var(--text-sub);
            border: 1px solid var(--border);
        }

        .card-desc {
            font-size: 13px;
            color: var(--text-muted);
            line-height: 1.4;
        }

        .card-bottom {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 10px;
            border-top: 1px solid var(--border);
        }

        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 36px;
        }
        .info-banner {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }
        .info-header {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--accent);
        }
        .info-text {
            font-size: 13px;
            color: var(--text-muted);
            line-height: 1.5;
        }

        .footer {
            text-align: center;
            color: var(--text-sub);
            font-size: 12px;
            padding-top: 24px;
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="logo-badge">
                <span class="logo-paw">🐾</span>
                <span class="logo-title">PAWER</span>
                <span class="section-badge">v1.0 • Local Only</span>
            </div>
            <p class="subtitle">
                Super lightweight, dedicated browser for Streamlit apps, FastAPI docs, React dev servers, and local web tools.
            </p>
        </header>

        <!-- Quick Launch Bar -->
        <div class="hero-bar">
            <div class="quick-launch-group">
                <span style="font-size: 18px;">⚡</span>
                <input type="text" id="customInput" class="quick-input" placeholder="Type port (e.g. 8501, 3000) or URL (e.g. localhost:8000)..." onkeydown="handleKey(event)" />
                <button class="btn btn-primary" onclick="launchCustom()">Open</button>
            </div>
            <div style="display: flex; gap: 8px;">
                <button class="btn btn-success" onclick="sendMessage('launch_streamlit_picker')">
                    <span>🚀</span> Run Streamlit App
                </button>
                <button class="btn" onclick="sendMessage('open:pawer://security')">
                    <span>🛡️</span> Security
                </button>
                <button class="btn" onclick="sendMessage('rescan_ports')">
                    <span>🔄</span> Refresh Status
                </button>
            </div>
        </div>

        <!-- Pinned Favorites & Workspaces -->
        <section id="favoritesSection" style="margin-bottom: 32px;">
            <div class="section-header">
                <h2 class="section-title">
                    <span>⭐</span> Pinned Workspaces & Apps
                </h2>
                <button class="btn" style="padding: 4px 12px; font-size: 12px;" onclick="sendMessage('pin_current_or_picker')">
                    ➕ Pin Script
                </button>
            </div>
            <div class="grid" id="favoritesGrid">
                <!-- Injected via JS from favorites_json -->
            </div>
        </section>

        <!-- Port Hub Grid -->
        <section>
            <div class="section-header">
                <h2 class="section-title">
                    <span>🛰️</span> Active Local Services
                </h2>
                <span class="section-badge" id="onlineCount">Scanning...</span>
            </div>

            <div class="grid" id="servicesGrid">
                <!-- Injected via JavaScript from services_json -->
            </div>
        </section>

        <!-- Info Panels -->
        <div class="info-grid">
            <div class="info-banner">
                <div class="info-header">
                    <span>🛡️</span> Local Isolation Active
                </div>
                <p class="info-text">
                    Pawer blocks external internet navigation by design. Your code, local data, and dashboards run with peak speed and complete privacy without cloud telemetry or ad tracking.
                </p>
            </div>
            <div class="info-banner">
                <div class="info-header">
                    <span>⚡</span> Streamlit Superpowers
                </div>
                <p class="info-text">
                    Zero WebSocket disconnects, built-in Chromium DevTools (F12), 1-click script runner with background process manager, and instant cache flushing.
                </p>
            </div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            <span>🐾 Pawer — The Local App Browser</span>
            <span>Shortcuts: <kbd>Ctrl+T</kbd> New Tab &bull; <kbd>Ctrl+W</kbd> Close &bull; <kbd>F12</kbd> DevTools &bull; <kbd>Ctrl+R</kbd> Reload</span>
        </footer>
    </div>

    <script>
        const services = {{SERVICES_JSON}};
        const favorites = {{FAVORITES_JSON}};

        function sendMessage(msg) {
            if (window.chrome && window.chrome.webview) {
                window.chrome.webview.postMessage(msg);
            } else {
                console.log('Pawer bridge:', msg);
            }
        }

        function openUrl(url) {
            sendMessage('open:' + url);
        }

        function killPort(port) {
            if (confirm('Terminate process on port ' + port + ' to free it?')) {
                sendMessage('kill_port:' + port);
            }
        }

        function launchFavorite(target) {
            if (target.endsWith('.py')) {
                sendMessage('launch_favorite:' + target);
            } else {
                openUrl(target);
            }
        }

        function deleteFavorite(id, e) {
            e.stopPropagation();
            sendMessage('remove_favorite:' + id);
        }

        function launchCustom() {
            const val = document.getElementById('customInput').value.trim();
            if (val) {
                sendMessage('open:' + val);
            }
        }

        function handleKey(e) {
            if (e.key === 'Enter') {
                launchCustom();
            }
        }

        function renderFavorites() {
            const grid = document.getElementById('favoritesGrid');
            if (!grid) return;
            grid.innerHTML = '';
            if (!favorites || favorites.length === 0) {
                grid.innerHTML = '<div style="color:var(--text-sub); font-size:13px; padding:12px;">No pinned apps yet. Click "+ Pin Script" to bookmark favorite dashboards!</div>';
                return;
            }

            favorites.forEach(f => {
                const card = document.createElement('div');
                card.className = 'card';
                card.style.cursor = 'pointer';
                card.onclick = () => launchFavorite(f.target);

                card.innerHTML = `
                    <div class="card-top">
                        <div class="card-icon-title">
                            <div class="card-icon">${f.icon || '⭐'}</div>
                            <div>
                                <div class="card-title">${f.name}</div>
                                <div class="card-port">${f.type === 'streamlit' ? 'Streamlit App' : 'URL Shortcut'}</div>
                            </div>
                        </div>
                        <button class="btn" style="padding:4px 8px; font-size:11px;" onclick="deleteFavorite('${f.id}', event)" title="Remove shortcut">✕</button>
                    </div>
                    <div class="card-desc" style="font-family:monospace; font-size:11px; word-break:break-all;">${f.target}</div>
                    <div class="card-bottom">
                        <span style="font-size:12px; color:var(--accent);">Click to Launch</span>
                        <button class="btn btn-primary" style="padding:6px 14px; font-size:12px;">Launch 🚀</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function renderServices() {
            const grid = document.getElementById('servicesGrid');
            grid.innerHTML = '';
            let onlineCount = 0;

            services.forEach(s => {
                if (s.online) onlineCount++;
                const card = document.createElement('div');
                card.className = 'card' + (s.online ? ' is-online' : '');

                let pidBadge = '';
                let killBtn = '';
                if (s.online && s.pid) {
                    pidBadge = `<span style="font-size:11px; color:#89b4fa; background:#181825; border:1px solid #313244; padding:2px 6px; border-radius:4px; margin-left:6px; font-family:monospace;">PID ${s.pid} (${s.process})</span>`;
                    killBtn = `<button class="btn btn-danger" style="padding:6px 10px; font-size:12px; margin-right:6px;" onclick="killPort(${s.port})" title="Terminate PID ${s.pid} and free port ${s.port}">✕ Free</button>`;
                }

                card.innerHTML = `
                    <div class="card-top">
                        <div class="card-icon-title">
                            <div class="card-icon">${s.icon}</div>
                            <div>
                                <div class="card-title">${s.name} ${pidBadge}</div>
                                <div class="card-port">localhost:${s.port}</div>
                            </div>
                        </div>
                        <span class="status-pill ${s.online ? 'status-online' : 'status-offline'}">
                            ${s.online ? 'Online' : 'Idle'}
                        </span>
                    </div>
                    <div class="card-desc">${s.description}</div>
                    <div class="card-bottom">
                        <span style="font-size: 12px; color: var(--text-sub); font-family: monospace;">${s.url}</span>
                        <div style="display:flex; align-items:center;">
                            ${killBtn}
                            <button class="btn ${s.online ? 'btn-success' : ''}" onclick="openUrl('${s.url}')">
                                ${s.online ? 'Connect →' : 'Open Port'}
                            </button>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });

            const badge = document.getElementById('onlineCount');
            badge.innerText = onlineCount + ' active service' + (onlineCount === 1 ? '' : 's');
            badge.style.color = onlineCount > 0 ? '#a6e3a1' : '#a6adc8';
        }

        document.addEventListener('DOMContentLoaded', () => {
            renderFavorites();
            renderServices();
            document.getElementById('customInput').focus();
        });
    </script>
</body>
</html>
"""


def get_home_html(services_status: List[Dict], favorites: Optional[List[Dict]] = None) -> str:
    """Renders the comprehensive Pawer Home / New Tab interface with PIDs and favorites."""
    if favorites is None:
        try:
            from .favorites import load_favorites
            favorites = load_favorites()
        except Exception:
            favorites = []

    services_json = json.dumps(services_status)
    favorites_json = json.dumps(favorites)
    css = get_base_css()
    return (
        HOME_TEMPLATE.replace("{{BASE_CSS}}", css)
        .replace("{{SERVICES_JSON}}", services_json)
        .replace("{{FAVORITES_JSON}}", favorites_json)
    )


BLOCKED_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>External Navigation Blocked — Pawer</title>
    <style>
        {{BASE_CSS}}
        .center-box {
            max-width: 600px;
            margin: 80px auto;
            background: var(--bg-surface);
            border: 1px solid rgba(243, 139, 168, 0.4);
            border-radius: 16px;
            padding: 36px;
            text-align: center;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.4);
        }
        .shield-icon {
            font-size: 54px;
            margin-bottom: 16px;
            display: inline-block;
        }
        .title {
            font-size: 22px;
            font-weight: 700;
            color: var(--rose);
            margin-bottom: 12px;
        }
        .desc {
            color: var(--text-muted);
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 24px;
        }
        .url-box {
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 12px 16px;
            border-radius: 8px;
            font-family: Consolas, monospace;
            font-size: 13px;
            color: var(--text-main);
            word-break: break-all;
            margin-bottom: 28px;
            user-select: text;
        }
        .action-row {
            display: flex;
            gap: 12px;
            justify-content: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="center-box">
            <div class="shield-icon">🛡️</div>
            <h1 class="title">External Internet Access Blocked</h1>
            <p class="desc">
                Pawer is intentionally designed strictly for local applications and Streamlit development.
                Browsing the external internet is restricted to maintain a lightweight, offline, and distraction-free environment.
            </p>
            <div class="url-box">{{BLOCKED_URL}}</div>
            <div class="action-row">
                <button class="btn btn-primary" onclick="sendMessage('open:pawer://home')">
                    <span>🐾</span> Return to Pawer Home
                </button>
                <button class="btn btn-danger" onclick="sendMessage('open_external:{{ENCODED_URL}}')">
                    <span>🌐</span> Open in System Browser
                </button>
            </div>
        </div>
    </div>
    <script>
        function sendMessage(msg) {
            if (window.chrome && window.chrome.webview) {
                window.chrome.webview.postMessage(msg);
            }
        }
    </script>
</body>
</html>
"""


def get_blocked_html(blocked_url: str) -> str:
    """Renders the safe blocked-navigation page when external internet access is attempted."""
    css = get_base_css()
    escaped_url = blocked_url.replace("<", "&lt;").replace(">", "&gt;")
    encoded_url = quote_plus(blocked_url)
    return (
        BLOCKED_TEMPLATE.replace("{{BASE_CSS}}", css)
        .replace("{{BLOCKED_URL}}", escaped_url)
        .replace("{{ENCODED_URL}}", encoded_url)
    )


ERROR_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Service Not Available — Pawer</title>
    <style>
        {{BASE_CSS}}
        .center-box {
            max-width: 640px;
            margin: 70px auto;
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 36px;
            text-align: center;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.4);
        }
        .err-icon {
            font-size: 50px;
            margin-bottom: 16px;
            display: inline-block;
        }
        .title {
            font-size: 22px;
            font-weight: 700;
            color: var(--amber);
            margin-bottom: 10px;
        }
        .desc {
            color: var(--text-muted);
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        .url-box {
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 10px 14px;
            border-radius: 8px;
            font-family: Consolas, monospace;
            font-size: 13px;
            color: var(--text-main);
            word-break: break-all;
            margin-bottom: 24px;
        }
        .code-box {
            background: #11111b;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            text-align: left;
            font-family: Consolas, monospace;
            font-size: 13px;
            color: #a6e3a1;
            margin-bottom: 24px;
            line-height: 1.5;
            user-select: text;
        }
        .action-row {
            display: flex;
            gap: 12px;
            justify-content: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="center-box">
            <div class="err-icon">🔌</div>
            <h1 class="title">{{PORT_TEXT}} is Offline</h1>
            <p class="desc">
                Pawer cannot connect to <strong>{{ESCAPED_URL}}</strong>. No application is currently listening on this local port.
            </p>
            <div class="url-box">{{ESCAPED_URL}}</div>

            <div class="code-box">
                <span style="color: var(--text-sub);"># Quick Start Command:</span><br>
                streamlit run your_app.py --server.port={{PORT_NUM}}
            </div>

            <div class="action-row">
                <button class="btn btn-primary" onclick="sendMessage('reload_current')">
                    <span>🔄</span> Retry Connection
                </button>
                <button class="btn btn-success" onclick="sendMessage('launch_streamlit_picker')">
                    <span>🚀</span> Run Streamlit App
                </button>
                <button class="btn" onclick="sendMessage('open:pawer://home')">
                    <span>🐾</span> Pawer Home
                </button>
            </div>
        </div>
    </div>
    <script>
        function sendMessage(msg) {
            if (window.chrome && window.chrome.webview) {
                window.chrome.webview.postMessage(msg);
            }
        }
    </script>
</body>
</html>
"""


def get_error_html(url: str, port: Optional[int] = None) -> str:
    """Renders a helpful diagnostic page when a local port is not listening."""
    css = get_base_css()
    escaped_url = url.replace("<", "&lt;").replace(">", "&gt;")
    port_text = f"Port {port}" if port else "Local Service"
    port_num = str(port if port else 8501)

    return (
        ERROR_TEMPLATE.replace("{{BASE_CSS}}", css)
        .replace("{{ESCAPED_URL}}", escaped_url)
        .replace("{{PORT_TEXT}}", port_text)
        .replace("{{PORT_NUM}}", port_num)
    )


# ---------------------------------------------------------------------------
# Security Dashboard Page  —  pawer://security
# ---------------------------------------------------------------------------

SECURITY_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Security — Pawer</title>
<style>
{{BASE_CSS}}
body { display:block; padding:40px 60px; }
.hero { text-align:center; margin-bottom:40px; }
.hero h1 { font-size:2.2rem; color:#a6e3a1; margin-bottom:8px; }
.hero p { color:#9399b2; font-size:1rem; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin-bottom:36px; }
.card { background:#181825; border-radius:14px; padding:22px 24px; border:1px solid #313244; }
.card-title { font-size:0.78rem; color:#9399b2; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px; }
.card-value { font-size:1.9rem; font-weight:700; color:#cdd6f4; }
.card-value.blocked { color:#f38ba8; }
.card-value.allowed { color:#a6e3a1; }
.card-value.session { font-size:1.1rem; font-family:monospace; }
.section-title { font-size:1rem; font-weight:600; color:#cdd6f4; margin:28px 0 12px; }
.flag-list { display:flex; flex-wrap:wrap; gap:8px; }
.flag { background:#1e1e2e; border:1px solid #45475a; border-radius:6px; padding:4px 10px; font-size:0.78rem; color:#89b4fa; font-family:monospace; }
.btn { margin-top:30px; display:inline-block; background:#89b4fa; color:#1e1e2e; padding:10px 24px; border-radius:8px; border:none; cursor:pointer; font-size:0.95rem; font-weight:600; }
.btn:hover { background:#b4befe; }
.badge-row { display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-bottom:28px; }
.badge { background:#1e1e2e; border:1px solid #313244; border-radius:20px; padding:6px 16px; font-size:0.85rem; color:#a6e3a1; display:flex; align-items:center; gap:6px; }
</style>
</head>
<body>
<div class="hero">
  <h1>&#x1F512; Pawer Security Dashboard</h1>
  <p>Session anonymity status and privacy metrics</p>
</div>
<div class="badge-row">
  <div class="badge">&#x1F7E2; Ephemeral Session</div>
  <div class="badge">&#x1F6AB; Internet Blocked</div>
  <div class="badge">&#x1F575; UserAgent Spoofed</div>
  <div class="badge">&#x1F4E1; InPrivate Mode</div>
  <div class="badge">&#x1F9B9; Header Scrubbing</div>
</div>
<div class="grid">
  <div class="card" style="grid-column: 1 / -1; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
    <div>
      <div class="card-title">Network Isolation Status</div>
      <div class="card-value" style="color:{{ISOLATION_COLOR}}; font-size:1.4rem;">
        {{ISOLATION_MODE_NAME}}
      </div>
      <div style="color:#9399b2; font-size:0.85rem; margin-top:4px;">
        {{ISOLATION_DESC}}
      </div>
    </div>
    <button class="btn" style="margin-top:0;" onclick="window.chrome.webview.postMessage('toggle_isolation')">
      &#x1F504; Toggle Mode (Ctrl+Shift+A)
    </button>
  </div>
  <div class="card">
    <div class="card-title">Session ID</div>
    <div class="card-value session">{{SESSION_ID}}</div>
  </div>
  <div class="card">
    <div class="card-title">Requests Blocked</div>
    <div class="card-value blocked">{{BLOCKED}}</div>
  </div>
  <div class="card">
    <div class="card-title">Requests Allowed</div>
    <div class="card-value allowed">{{ALLOWED}}</div>
  </div>
  <div class="card">
    <div class="card-title">Session Uptime</div>
    <div class="card-value">{{UPTIME}}</div>
  </div>
</div>
<div class="section-title">Active Privacy Flags</div>
<div class="flag-list">
  <div class="flag">--disable-third-party-cookies</div>
  <div class="flag">--metrics-recording-only</div>
  <div class="flag">--disable-breakpad</div>
  <div class="flag">--disable-field-trial-config</div>
  <div class="flag">--force-webrtc-ip-handling-policy</div>
  <div class="flag">--disable-features=BatteryStatus</div>
  <div class="flag">--disable-features=SensorExtraClasses</div>
  <div class="flag">--disable-features=CanvasColorCache</div>
  <div class="flag">--no-referrers</div>
  <div class="flag">--no-pings</div>
  <div class="flag">--dns-prefetch-disable</div>
  <div class="flag">--disable-features=NetworkPrediction</div>
  <div class="flag">--disable-features=SharedArrayBuffer</div>
  <div class="flag">--disable-features=WebBluetooth,WebUsb,WebHid</div>
  <div class="flag">--disable-features=IdleDetection</div>
  <div class="flag">--disable-features=FileSystemAccessAPI</div>
  <div class="flag">--deny-permission-prompts</div>
  <div class="flag">--disable-background-networking</div>
  <div class="flag">--disable-component-update</div>
  <div class="flag">--disable-safe-browsing</div>
  <div class="flag">IsInPrivateModeEnabled=True</div>
  <div class="flag">AreBrowserAcceleratorKeysEnabled=False</div>
  <div class="flag">IsSwipeNavigationEnabled=False</div>
  <div class="flag">UserAgent=Pawer/1.0 (Local)</div>
</div>
<button class="btn" onclick="window.chrome.webview.postMessage('rescan_ports')">&#x1F3E0; Back to Home</button>
</body></html>"""


def get_security_html(stats: dict) -> str:
    """Renders the pawer://security dashboard with live session stats and isolation toggle."""
    css = get_base_css()
    uptime = stats.get("uptime_secs", 0)
    minutes, secs = divmod(uptime, 60)
    uptime_str = f"{minutes}m {secs}s" if minutes else f"{secs}s"

    isolation = str(stats.get("isolation_mode", "local")).lower()
    if isolation == "airgap":
        mode_name = "🔒 Strict Airgap (Loopback Only)"
        mode_color = "#89b4fa"
        mode_desc = "Complete machine airgap: All LAN (192.168.x.x) and external internet traffic blocked. Zero packets leave this PC."
    elif isolation == "open":
        mode_name = "⚠️ Unrestricted (Internet Allowed)"
        mode_color = "#f38ba8"
        mode_desc = "External internet browsing is unlocked. Use with caution for external documentation lookup."
    else:
        mode_name = "🟢 Local Isolation (Default)"
        mode_color = "#a6e3a1"
        mode_desc = "Local apps and private LAN permitted (e.g. 192.168.x.x). External internet strictly blocked."

    return (
        SECURITY_TEMPLATE.replace("{{BASE_CSS}}", css)
        .replace("{{SESSION_ID}}", str(stats.get("session_id", "unknown")))
        .replace("{{BLOCKED}}", str(stats.get("blocked", 0)))
        .replace("{{ALLOWED}}", str(stats.get("allowed", 0)))
        .replace("{{UPTIME}}", uptime_str)
        .replace("{{ISOLATION_MODE_NAME}}", mode_name)
        .replace("{{ISOLATION_COLOR}}", mode_color)
        .replace("{{ISOLATION_DESC}}", mode_desc)
    )
