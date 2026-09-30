"""Relata Live Showcase Launcher.

Allows developers and regulatory teams to launch the local interactive showcase
in their web browser or print an executive summary of the deterministic engine.
"""

from __future__ import annotations

import argparse
import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path


def launch_web_showcase(port: int = 8080) -> None:
    # Try finding the showcase in playgriff-hub
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "playgriff-hub" / "relata",
        Path.home() / "playgriff-hub" / "relata",
    ]

    showcase_dir: Path | None = None
    for c in candidates:
        if c.exists() and (c / "index.html").exists():
            showcase_dir = c
            break

    if not showcase_dir:
        print("[!] Local showcase directory not found. Please visit https://www.playgriff.me/relata/")
        sys.exit(1)

    os.chdir(showcase_dir)
    handler = http.server.SimpleHTTPRequestHandler

    print("=" * 80)
    print("RELATA // INTERACTIVE CVM REGULATORY & CPC 10 SHOWCASE")
    print("=" * 80)
    print(f"Serving local regulatory workbench at: http://localhost:{port}/")
    print("Live Cloud Sandbox: https://www.playgriff.me/relata/")
    print("Press Ctrl+C to terminate.")
    print("=" * 80)

    try:
        webbrowser.open(f"http://localhost:{port}/")
    except Exception:
        pass

    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down showcase server.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch Relata Interactive Regulatory Showcase")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind the HTTP server to (default: 8080)")
    args = parser.parse_args()
    launch_web_showcase(args.port)


if __name__ == "__main__":
    main()
