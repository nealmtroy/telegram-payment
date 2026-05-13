from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in {"/", "/health"}:
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps({"ok": True, "service": "telegram-vip-payment-bot"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def start_health_server() -> None:
    host = os.getenv("HEALTH_HOST", "127.0.0.1")
    port = int(os.getenv("HEALTH_PORT", "8080"))
    server = ThreadingHTTPServer((host, port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
