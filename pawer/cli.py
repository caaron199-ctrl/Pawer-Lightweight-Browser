"""
Pawer Command-Line Interface.
Usage:
  pawer                     # Open Pawer Hub
  pawer 8501                # Open localhost:8501
  pawer app.py              # Launch Streamlit app and open in Pawer
  pawer run app.py          # Launch Streamlit app explicitly
  pawer serve ./dist        # Serve directory statically and open in Pawer
"""

import argparse
import os
import sys
import threading
import time
from typing import List

from System.Threading import ApartmentState, Thread, ThreadStart

from .app import start_pawer
from .security.guardian import normalize_url
from .services.app_launcher import launcher
from .services.port_scanner import check_port


def run_app_on_sta_thread(urls: List[str]):
    """Windows Forms + WebView2 requires an STA (Single Threaded Apartment) thread."""
    def target():
        start_pawer(urls)

    thread = Thread(ThreadStart(target))
    thread.SetApartmentState(ApartmentState.STA)
    thread.Start()
    thread.Join()


def main():
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        prog="pawer",
        description="Pawer - Super lightweight browser designed for Streamlit apps and local apps.",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="Pawer 1.0.0",
        help="Show Pawer version",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Port number (e.g. 8501), local URL (e.g. localhost:8000), or Python Streamlit script (e.g. app.py)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Custom port for launching Streamlit or static server",
    )
    parser.add_argument(
        "--serve",
        metavar="DIR",
        type=str,
        default=None,
        help="Serve a local directory statically via HTTP and open in Pawer",
    )

    args = parser.parse_args()

    # Mode 1: Serve a directory statically
    if args.serve:
        folder = os.path.abspath(args.serve)
        if not os.path.isdir(folder):
            print(f"[Error] Directory not found: {folder}")
            sys.exit(1)

        print(f"[Pawer] Serving {folder}...")
        assigned_port = launcher.launch_static_folder(folder, desired_port=args.port)
        time.sleep(0.3)
        run_app_on_sta_thread([f"http://localhost:{assigned_port}"])
        return

    # Mode 2: No argument -> Open Pawer Hub
    if not args.target:
        run_app_on_sta_thread(["pawer://home"])
        return

    target = args.target.strip()

    # Mode 3: Target is a Python script -> launch Streamlit and open
    if target.endswith(".py") and os.path.isfile(target):
        script_path = os.path.abspath(target)
        print(f"[Pawer] Launching Streamlit on {script_path}...")

        ready_url = []
        ready_event = threading.Event()

        def on_ready(url: str):
            ready_url.append(url)
            ready_event.set()

        def on_error(err: str):
            print(f"[Pawer Error] {err}")
            ready_event.set()

        assigned_port = launcher.launch_streamlit(
            script_path, desired_port=args.port, on_ready=on_ready, on_error=on_error
        )
        ready_event.wait(timeout=15.0)

        url = ready_url[0] if ready_url else f"http://localhost:{assigned_port}"
        print(f"[Pawer] Opening {url}...")
        run_app_on_sta_thread([url])
        return

    # Mode 4: Target is a port, URL, or internal page
    normalized = normalize_url(target)
    print(f"[Pawer] Opening {normalized}...")
    run_app_on_sta_thread([normalized])


if __name__ == "__main__":
    main()
