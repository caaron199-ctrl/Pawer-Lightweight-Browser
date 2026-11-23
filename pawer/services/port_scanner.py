"""
Pawer Port Scanner — Ultra-fast local port scanner for discovering active local apps,
inspecting process IDs (PIDs), and 1-click port conflict termination.
"""

import os
import re
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, NamedTuple, Optional

try:
    import clr
    from System.Diagnostics import Process as DotNetProcess
except Exception:
    DotNetProcess = None


class ServiceInfo(NamedTuple):
    port: int
    name: str
    category: str
    icon: str
    description: str


STANDARD_SERVICES: List[ServiceInfo] = [
    ServiceInfo(8501, "Streamlit App", "streamlit", "🎈", "Default Streamlit dashboard port"),
    ServiceInfo(8502, "Streamlit (Alt)", "streamlit", "🎈", "Secondary Streamlit instance"),
    ServiceInfo(8000, "FastAPI / Django", "api", "⚡", "High-performance Python backend / Swagger UI"),
    ServiceInfo(3000, "React / Next.js", "frontend", "⚛️", "Modern JavaScript / TypeScript frontend"),
    ServiceInfo(5173, "Vite Dev Server", "frontend", "⚡", "Next-gen frontend tooling"),
    ServiceInfo(5000, "Flask / Microservice", "python", "🧪", "Flask web service or API"),
    ServiceInfo(8080, "Local Web Server", "general", "🌐", "General HTTP development server"),
    ServiceInfo(7860, "Gradio AI App", "ai", "🤖", "Machine Learning & Gradio interface"),
    ServiceInfo(11434, "Ollama Local LLM", "ai", "🦙", "Local AI models (Llama, Mistral, Gemma)"),
    ServiceInfo(8888, "Jupyter Server", "datascience", "🪐", "Jupyter Notebook or JupyterLab"),
]


def check_port(port: int, host: str = "127.0.0.1", timeout: float = 0.05) -> bool:
    """Checks whether a TCP port is open and accepting connections on localhost."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((host, port)) == 0
    except Exception:
        return False


def get_port_pid_map() -> Dict[int, Dict[str, any]]:
    """
    Inspects which Windows processes (PIDs) are actively listening on local TCP ports.
    Returns a mapping of port -> {'pid': int, 'process': str}.
    """
    mapping: Dict[int, Dict[str, any]] = {}
    if sys.platform != "win32":
        return mapping

    try:
        # Run netstat quietly with CREATE_NO_WINDOW
        flags = 0x08000000
        res = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True,
            text=True,
            creationflags=flags,
            timeout=1.5,
        )
        if res.returncode != 0:
            return mapping

        # Match lines like: TCP    127.0.0.1:8501    0.0.0.0:0    LISTENING    14208
        pattern = re.compile(r":(\d+)\s+.*LISTENING\s+(\d+)", re.IGNORECASE)
        for match in pattern.finditer(res.stdout):
            port = int(match.group(1))
            pid = int(match.group(2))
            proc_name = "Unknown"

            if DotNetProcess:
                try:
                    p = DotNetProcess.GetProcessById(pid)
                    proc_name = p.ProcessName
                except Exception:
                    pass

            mapping[port] = {"pid": pid, "process": proc_name}

    except Exception:
        pass

    return mapping


def kill_process_on_port(port: int) -> bool:
    """
    Kills the process listening on the specified port to immediately free it.
    Returns True if killed successfully.
    """
    pid_map = get_port_pid_map()
    info = pid_map.get(port)
    if not info or not info.get("pid"):
        return False

    pid = info["pid"]
    # Don't kill system or idle process
    if pid <= 4:
        return False

    try:
        if DotNetProcess:
            try:
                p = DotNetProcess.GetProcessById(pid)
                p.Kill()
                return True
            except Exception:
                pass

        # Fallback to taskkill
        flags = 0x08000000 if sys.platform == "win32" else 0
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True,
            creationflags=flags,
            timeout=2.0,
        )
        return True
    except Exception:
        return False


def scan_known_ports() -> List[Dict]:
    """
    Scans all registered standard local developer ports concurrently.
    Returns a list of dicts with service details, online status, PID, and process name.
    """
    pid_map = get_port_pid_map()

    def probe(service: ServiceInfo) -> Dict:
        is_online = check_port(service.port)
        p_info = pid_map.get(service.port) if is_online else None

        return {
            "port": service.port,
            "name": service.name,
            "category": service.category,
            "icon": service.icon,
            "description": service.description,
            "url": f"http://localhost:{service.port}",
            "online": is_online,
            "pid": p_info["pid"] if p_info else None,
            "process": p_info["process"] if p_info else None,
        }

    with ThreadPoolExecutor(max_workers=len(STANDARD_SERVICES)) as executor:
        results = list(executor.map(probe, STANDARD_SERVICES))

    return results


def find_free_port(start_port: int = 8501, max_port: int = 8600) -> int:
    """Finds the first available free port on localhost starting from start_port."""
    for port in range(start_port, max_port + 1):
        if not check_port(port):
            return port
    return start_port
