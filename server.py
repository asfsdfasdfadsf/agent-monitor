"""
Agent Monitor - Live UI for watching Claude Code agent activity.
Zero external dependencies — pure Python stdlib.

Usage:
    python server.py
    Then open http://localhost:7778
"""

import json
import socket
import time
import random
import string
import os
import threading
import queue
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT = int(os.environ.get("PORT", 7778))
PUBLIC_DIR = Path(__file__).parent / "public"

MAX_EVENTS = 1000  # Increased for longer sessions
lock = threading.Lock()
events = []
tool_counts = {}
files_read = set()
files_written = set()

# SSE: each connected client gets a queue
sse_clients = []  # list of queue.Queue
sse_lock = threading.Lock()


def make_id():
    ts = int(time.time() * 1000)
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"evt_{ts}_{suffix}"


def track_event(event):
    with lock:
        events.append(event)
        if len(events) > MAX_EVENTS:
            events.pop(0)

        tool = event.get("tool_name", "unknown")
        tool_counts[tool] = tool_counts.get(tool, 0) + 1

        inp = event.get("tool_input") or {}
        if tool == "Read" and inp.get("file_path"):
            files_read.add(inp["file_path"])
        if tool in ("Edit", "Write") and inp.get("file_path"):
            files_written.add(inp["file_path"])

    # Push to all SSE client queues
    with sse_lock:
        for q in sse_clients:
            try:
                q.put_nowait(event)
            except queue.Full:
                pass  # Drop if client is too slow


class Handler(SimpleHTTPRequestHandler):
    """Handles static files, the /event POST endpoint, and /api/* endpoints."""

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            pass

    def log_message(self, fmt, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path == "/event":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.send_json({"error": "bad json"}, 400)
                return
            event = {**data, "timestamp": int(time.time() * 1000), "id": make_id()}
            track_event(event)
            self.send_json({"ok": True})
        else:
            self.send_json({"error": "not found"}, 404)

    def do_GET(self):
        if self.path.startswith("/api/stream"):
            self._handle_sse()
            return
        if self.path == "/api/events":
            with lock:
                snapshot = list(events[-200:])
            self.send_json({"events": snapshot})
            return
        if self.path == "/api/stats":
            with lock:
                self.send_json({
                    "tool_counts": dict(tool_counts),
                    "files_read": sorted(files_read),
                    "files_written": sorted(files_written),
                })
            return
        super().do_GET()

    def _handle_sse(self):
        """Server-Sent Events with per-client queue."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        # Create a queue for this client
        client_queue = queue.Queue(maxsize=200)
        with sse_lock:
            sse_clients.append(client_queue)

        try:
            while True:
                # Drain all available events from queue
                sent = False
                try:
                    while True:
                        evt = client_queue.get_nowait()
                        data = json.dumps(evt)
                        self.wfile.write(f"data: {data}\n\n".encode())
                        sent = True
                except queue.Empty:
                    pass

                if sent:
                    self.wfile.flush()

                # Heartbeat
                self.wfile.write(b": hb\n\n")
                self.wfile.flush()

                time.sleep(0.3)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            with sse_lock:
                try:
                    sse_clients.remove(client_queue)
                except ValueError:
                    pass


def main():
    print(f"\n  Agent Monitor")
    print(f"  Dashboard:  http://localhost:{PORT}")
    print(f"  POST hook:  http://localhost:{PORT}/event\n")

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
