"""
CoralTwin-DT: Cyber-Physical Command Center Local Web Server
============================================================
Serves the modern high-end frontend portal on http://localhost:8000.

Author: CoralTwin-DT Engineering Consortium
License: MIT
"""

import os
import sys
import webbrowser
import http.server
import socketserver

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class CustomHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Clean custom logging
        sys.stderr.write(f"[CoralTwin-DT Portal] {self.address_string()} - {format%args}\n")


def run_server():
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHTTPHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 75)
        print("  🪸  CORALTWIN-DT: CYBER-PHYSICAL DIGITAL TWIN COMMAND CENTER")
        print("=" * 75)
        print(f"  [>] Server running at: {url}")
        print(f"  [>] Serving directory: {DIRECTORY}")
        print("  [>] Press Ctrl+C to stop server.")
        print("=" * 75)
        
        # Open default browser automatically
        try:
            webbrowser.open(url)
        except Exception:
            pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Shutting down CoralTwin-DT Command Center Server.")


if __name__ == "__main__":
    run_server()
