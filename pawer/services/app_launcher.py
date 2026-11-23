"""
Pawer App Launcher — Spawns and manages local background servers (Streamlit, Flask, static)
with automatic port assignment, silent process flags, live log streaming, and zero-orphan cleanup.
"""

import atexit
import collections
import os
import subprocess
import sys
import threading
import time
from typing import Callable, Dict, List, Optional

from .port_scanner import check_port, find_free_port

# Windows CREATE_NO_WINDOW flag to prevent console popups
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


class ManagedProcess:
    def __init__(
        self,
        proc: subprocess.Popen,
        app_path: str,
        port: int,
        app_type: str,
        on_log: Optional[Callable[[int, str], None]] = None,
    ):
        self.proc = proc
        self.app_path = app_path
        self.port = port
        self.app_type = app_type
        self.started_at = time.time()
        self.logs: collections.deque = collections.deque(maxlen=1000)
        self._on_log = on_log

        # Start live background log reader thread
        if self.proc.stdout:
            t = threading.Thread(target=self._read_output, daemon=True)
            t.start()

    def _read_output(self):
        try:
            for line in iter(self.proc.stdout.readline, ""):
                if not line:
                    break
                clean = line.rstrip()
                self.logs.append(clean)
                if self._on_log:
                    try:
                        self._on_log(self.port, clean)
                    except Exception:
                        pass
        except Exception:
            pass

    def is_alive(self) -> bool:
        return self.proc.poll() is None

    def terminate(self):
        try:
            if self.is_alive():
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
        except Exception:
            pass


class PawerAppLauncher:
    """Manages lifecycle of local Streamlit and HTTP servers launched from Pawer."""

    def __init__(self):
        self._processes: Dict[int, ManagedProcess] = {}
        self._log_listeners: List[Callable[[int, str], None]] = []
        atexit.register(self.stop_all)

    def add_log_listener(self, listener: Callable[[int, str], None]):
        """Registers a callback to receive live log lines (port, text)."""
        if listener not in self._log_listeners:
            self._log_listeners.append(listener)

    def remove_log_listener(self, listener: Callable[[int, str], None]):
        if listener in self._log_listeners:
            self._log_listeners.remove(listener)

    def _broadcast_log(self, port: int, line: str):
        for listener in list(self._log_listeners):
            try:
                listener(port, line)
            except Exception:
                pass

    def get_logs(self, port: Optional[int] = None) -> List[str]:
        """Returns captured log lines for a specific port or all running processes."""
        if port is not None:
            proc = self._processes.get(port)
            return list(proc.logs) if proc else []
        all_logs = []
        for p, proc in self._processes.items():
            all_logs.extend([f"[{p}] {line}" for line in proc.logs])
        return all_logs

    def launch_streamlit(
        self,
        script_path: str,
        desired_port: Optional[int] = None,
        on_ready: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> Optional[int]:
        """
        Launches a Streamlit app in the background without a console window.
        Polls the port until ready and calls on_ready(url). Streams logs to drawer.
        """
        if not os.path.isfile(script_path):
            if on_error:
                on_error(f"File not found: {script_path}")
            return None

        port = desired_port if desired_port and not check_port(desired_port) else find_free_port(8501)
        abs_script = os.path.abspath(script_path)

        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            abs_script,
            f"--server.port={port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.runOnSave=true",
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=CREATE_NO_WINDOW,
            )
            managed = ManagedProcess(proc, abs_script, port, "streamlit", on_log=self._broadcast_log)
            self._processes[port] = managed

            # Initial log message
            self._broadcast_log(port, f"[Pawer] Spawning Streamlit on port {port}: {abs_script}")

            # Asynchronously poll until the port is open and accepting HTTP traffic
            def wait_for_server():
                deadline = time.time() + 20.0
                while time.time() < deadline:
                    if not proc.poll() is None:
                        # Process terminated prematurely
                        if on_error:
                            on_error(f"Streamlit process exited unexpectedly on port {port}.")
                        return
                    if check_port(port, timeout=0.1):
                        url = f"http://localhost:{port}"
                        self._broadcast_log(port, f"[Pawer] Server online at {url}")
                        if on_ready:
                            on_ready(url)
                        return
                    time.sleep(0.3)

                if on_error:
                    on_error(f"Streamlit server timed out starting on port {port}.")

            threading.Thread(target=wait_for_server, daemon=True).start()
            return port

        except Exception as ex:
            if on_error:
                on_error(f"Failed to launch Streamlit: {ex}")
            return None

    def launch_static_folder(
        self,
        folder_path: str,
        desired_port: Optional[int] = None,
        on_ready: Optional[Callable[[str], None]] = None,
    ) -> Optional[int]:
        """Serves a local directory using Python's built-in HTTP server."""
        if not os.path.isdir(folder_path):
            return None

        port = desired_port if desired_port and not check_port(desired_port) else find_free_port(8080)
        abs_dir = os.path.abspath(folder_path)

        cmd = [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--directory",
            abs_dir,
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=CREATE_NO_WINDOW,
            )
            managed = ManagedProcess(proc, abs_dir, port, "static", on_log=self._broadcast_log)
            self._processes[port] = managed

            self._broadcast_log(port, f"[Pawer] Serving static directory on port {port}: {abs_dir}")

            def wait_for_server():
                deadline = time.time() + 5.0
                while time.time() < deadline:
                    if check_port(port, timeout=0.1):
                        url = f"http://localhost:{port}"
                        if on_ready:
                            on_ready(url)
                        return
                    time.sleep(0.1)

            threading.Thread(target=wait_for_server, daemon=True).start()
            return port

        except Exception as ex:
            print(f"[PawerAppLauncher] Failed to start HTTP server: {ex}")
            return None

    def stop_process(self, port: int):
        """Stops the server running on the specified port."""
        proc = self._processes.pop(port, None)
        if proc:
            self._broadcast_log(port, f"[Pawer] Terminated server on port {port}")
            proc.terminate()

    def stop_all(self):
        """Stops all managed processes. Called automatically on application exit."""
        for port, proc in list(self._processes.items()):
            try:
                proc.terminate()
            except Exception:
                pass
        self._processes.clear()

    @property
    def active_ports(self) -> List[int]:
        """Returns list of ports with active processes."""
        alive = []
        for port, proc in list(self._processes.items()):
            if proc.is_alive():
                alive.append(port)
            else:
                self._processes.pop(port, None)
        return alive


# Singleton instance shared across the application
launcher = PawerAppLauncher()
