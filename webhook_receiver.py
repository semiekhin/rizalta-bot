#!/usr/bin/env python3
"""GitHub Webhook Receiver for RIZALTA WebApp DEV auto-deploy."""

import hashlib
import hmac
import json
import logging
import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 9001
SECRET = os.environ.get("WEBHOOK_SECRET", "")
REPO_DIR = "/opt/webapp-dev"
BRANCH = "webapp"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("webhook")


def verify_signature(payload: bytes, signature: str) -> bool:
    if not SECRET:
        log.warning("No WEBHOOK_SECRET set — skipping signature check")
        return True
    expected = "sha256=" + hmac.new(
        SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def deploy():
    """git pull → npm build → restart service."""
    steps = [
        ("git pull", ["git", "-C", REPO_DIR, "pull", "origin", BRANCH]),
        ("npm build", ["npm", "run", "build", "--prefix", f"{REPO_DIR}/frontend"]),
        ("restart", ["systemctl", "restart", "webapp-dev"]),
    ]
    for name, cmd in steps:
        log.info(f"→ {name}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            log.error(f"✗ {name} failed:\n{result.stderr}")
            return False, name
        log.info(f"✓ {name} ok")
    return True, None


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length)

        # Verify signature
        sig = self.headers.get("X-Hub-Signature-256", "")
        if SECRET and not verify_signature(payload, sig):
            log.warning("Invalid signature — rejected")
            self.send_response(403)
            self.end_headers()
            return

        # Parse event
        event = self.headers.get("X-GitHub-Event", "")
        if event == "ping":
            log.info("Ping received ✓")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":"pong"}')
            return

        if event != "push":
            self.send_response(200)
            self.end_headers()
            return

        # Check branch
        try:
            data = json.loads(payload)
            ref = data.get("ref", "")
        except json.JSONDecodeError:
            ref = ""

        if ref != f"refs/heads/{BRANCH}":
            log.info(f"Push to {ref} — ignoring (want {BRANCH})")
            self.send_response(200)
            self.end_headers()
            return

        # Deploy
        log.info(f"Push to {BRANCH} — deploying...")
        success, failed_step = deploy()
        status = 200 if success else 500
        body = json.dumps({"ok": success, "failed": failed_step})
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        pass  # suppress default access log


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), WebhookHandler)
    log.info(f"Webhook receiver listening on 127.0.0.1:{PORT}")
    server.serve_forever()
