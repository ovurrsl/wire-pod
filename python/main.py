#!/usr/bin/env python3
"""
Wire-Pod Vector Server Supervisor for Arduino App Lab (Arduino UNO Q).
Manages the chipper binary, sets up library paths, routes the Arduino Web UI,
and pipes execution logs to the Arduino App CLI daemon.
"""

import os
import sys
import time
import signal
import threading
import subprocess
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [WirePod-UNOQ] %(message)s")
logger = logging.getLogger("wirepod.unoq")

def locate_chipper_bin():
    candidates = [
        "/app/chipper/chipper",
        "/app/wire-pod/chipper/chipper",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chipper", "chipper"),
        os.path.join(os.getcwd(), "chipper", "chipper"),
    ]
    for path in candidates:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return os.path.abspath(path)
    return None

class WebUIRedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        host = self.headers.get("Host", "127.0.0.1").split(":")[0]
        target_url = f"http://{host}:8080/"
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url={target_url}">
    <title>Wire-Pod Vector Server</title>
</head>
<body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
    <h2>🤖 Wire-Pod Vector Server</h2>
    <p>Redirecting to Wire-Pod setup dashboard...</p>
    <p><a href="{target_url}">Click here if not redirected automatically ({target_url})</a></p>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass

def start_redirect_server(port=7000):
    try:
        server = HTTPServer(("0.0.0.0", port), WebUIRedirectHandler)
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Port {port} redirect server warning: {e}")

def main():
    logger.info("Initializing Wire-Pod Vector Server on Arduino UNO Q...")
    
    chipper_bin = locate_chipper_bin()
    if not chipper_bin:
        logger.error("Chipper binary not found or not executable. Ensure chipper is compiled.")
        sys.exit(1)
        
    chipper_dir = os.path.dirname(chipper_bin)
    logger.info(f"Chipper executable: {chipper_bin} (Working Dir: {chipper_dir})")

    env = os.environ.copy()
    if "STT_SERVICE" not in env:
        env["STT_SERVICE"] = "vosk"
    if "DEBUG_LOGGING" not in env:
        env["DEBUG_LOGGING"] = "true"

    # Ensure libvosk and system libraries are discoverable
    lib_dirs = [
        "/app/lib",
        "/app/wire-pod/lib",
        "/home/arduino/.vosk/libvosk",
        "/usr/local/lib",
        os.path.join(os.path.dirname(chipper_dir), "lib"),
    ]
    existing_ld = env.get("LD_LIBRARY_PATH", "")
    new_ld = ":".join([p for p in lib_dirs if os.path.isdir(p)] + ([existing_ld] if existing_ld else []))
    env["LD_LIBRARY_PATH"] = new_ld

    # Start Arduino App Lab Web UI redirect daemon on port 7000
    redirect_thread = threading.Thread(target=start_redirect_server, args=(7000,), daemon=True)
    redirect_thread.start()
    logger.info("Arduino Web UI router active on port 7000 -> routes to port 8080")

    # Launch chipper process
    proc = subprocess.Popen(
        [chipper_bin],
        cwd=chipper_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    def shutdown_handler(sig, frame):
        logger.info(f"Signal {sig} received, stopping Wire-Pod...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    logger.info("Wire-Pod running! Listening on ports 8080 (Web), 443 (gRPC), 8084 (jdocs), 80 (connCheck)")
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

    proc.wait()
    logger.info(f"Chipper process exited with code {proc.returncode}")
    sys.exit(proc.returncode)

if __name__ == "__main__":
    main()
