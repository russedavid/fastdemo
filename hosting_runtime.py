"""Small, persistent limits and storage configuration for the public demo."""

import hashlib
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from starlette.responses import PlainTextResponse


class LimitReached(Exception):
    def __init__(self, message, retry_after=0):
        super().__init__(message)
        self.retry_after = retry_after


class DemoSettings:
    def __init__(self):
        self.demo = os.getenv("FRONTLINE_DEMO", "0") == "1"
        self.data_root = Path(os.getenv("FRONTLINE_DATA_DIR", ".")).resolve()
        self.data_dir = self.data_root / "data"
        self.upload_dir = self.data_root / "uploads"
        for directory in (self.data_dir, *(self.upload_dir / x for x in ("audio", "images", "text"))):
            directory.mkdir(parents=True, exist_ok=True)
        self.max_file_bytes = 4 * 1024 * 1024
        self.max_request_bytes = 9 * 1024 * 1024
        self.max_user_bytes = 12 * 1024 * 1024
        self.max_upload_bytes = 300 * 1024 * 1024
        self.max_text_chars = 12000
        self.max_source_chars = 9000
        key_file = self.data_dir / ".session-key"
        if not key_file.exists():
            try:
                fd = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                pass
            else:
                with os.fdopen(fd, "w") as stream:
                    stream.write(secrets.token_hex(32))
        self.session_key = os.getenv("FRONTLINE_SESSION_KEY") or key_file.read_text().strip()


class Budget:
    """Atomic reservations survive restarts; no model calls occur in this class."""

    def __init__(self, path):
        self.path = str(path)
        with self.connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS usage (id TEXT PRIMARY KEY, at REAL, actor TEXT, kind TEXT, units INTEGER)")
            conn.execute("CREATE INDEX IF NOT EXISTS usage_window ON usage(kind, at)")
            conn.execute("CREATE TABLE IF NOT EXISTS cooldown (name TEXT PRIMARY KEY, until REAL)")

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=10)
        try:
            with conn:
                conn.execute("PRAGMA busy_timeout=10000")
                yield conn
        finally:
            conn.close()

    def reserve(self, actor, kind, units=1, *, now=None):
        now = time.time() if now is None else now
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM usage WHERE at < ?", (now - 172800,))
            cooldown = conn.execute("SELECT until FROM cooldown WHERE name=?", (kind,)).fetchone()
            if cooldown and cooldown[0] > now:
                raise LimitReached("AI is temporarily at capacity. Please try again shortly.", int(cooldown[0] - now) + 1)
            rules = {
                "text": [(60, 7000, False, True), (86400, 120000, False, True), (86400, 12, True, False)],
                "output": [(60, 900, False, True), (86400, 24000, False, True)],
                "audio": [(3600, 12, False, False), (86400, 40, False, False), (86400, 6, True, False)],
                "report": [(86400, 3, True, False), (86400, 35, False, False)],
                "session": [(3600, 10, True, False), (86400, 100, False, False)],
            }[kind]
            for window, limit, per_actor, count_units in rules:
                sql = "SELECT COALESCE(SUM(units),0), COUNT(*), MIN(at) FROM usage WHERE kind=? AND at>?"
                args = [kind, now - window]
                if per_actor:
                    sql += " AND actor=?"
                    args.append(str(actor))
                total, count, earliest = conn.execute(sql, args).fetchone()
                if (total + units if count_units else count + 1) > limit:
                    wait = max(1, int((earliest or now) + window - now) + 1)
                    message = ("This demo's daily AI allowance has been reached. Saved examples are still available."
                               if window == 86400 else "AI is temporarily at capacity. Please try again shortly.")
                    raise LimitReached(message, wait)
            token = secrets.token_hex(16)
            conn.execute("INSERT INTO usage VALUES (?,?,?,?,?)", (token, now, str(actor), kind, units))
            return token

    def settle(self, token, units):
        with self.connection() as conn:
            conn.execute("UPDATE usage SET units=? WHERE id=?", (max(1, int(units)), token))

    def release(self, token):
        with self.connection() as conn:
            conn.execute("DELETE FROM usage WHERE id=?", (token,))

    def cool_down(self, kind, seconds):
        with self.connection() as conn:
            conn.execute("INSERT INTO cooldown VALUES (?,?) ON CONFLICT(name) DO UPDATE SET until=MAX(until,excluded.until)",
                         (kind, time.time() + max(1, seconds)))

    def actor_for_ip(self, ip, secret):
        return hashlib.sha256((secret + ip).encode()).hexdigest()


class RequestLimits:
    """Bound bodies before Starlette's multipart parser can spool large uploads."""

    def __init__(self, app, max_bytes):
        self.app, self.max_bytes = app, max_bytes
        self.inflight = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in ("POST", "PUT", "PATCH", "DELETE"):
            return await self.app(scope, receive, send)
        if self.inflight >= 2:
            return await PlainTextResponse("The demo is busy. Please try again shortly.", status_code=429)(scope, receive, send)
        self.inflight += 1
        try:
            return await self.bounded_request(scope, receive, send)
        finally:
            self.inflight -= 1

    async def bounded_request(self, scope, receive, send):
        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin")
        host = headers.get(b"host", b"")
        if origin and origin.split(b"://", 1)[-1].rstrip(b"/") != host:
            return await PlainTextResponse("This request must come from Frontline.", status_code=403)(scope, receive, send)
        messages, total = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            total += len(message.get("body", b""))
            if total > self.max_bytes:
                return await PlainTextResponse("Upload too large. Use files up to 4 MB, at most two at a time.", status_code=413)(scope, receive, send)
            messages.append(message)
            if not message.get("more_body", False):
                break
        iterator = iter(messages)

        async def bounded_receive():
            try:
                return next(iterator)
            except StopIteration:
                return await receive()

        await self.app(scope, bounded_receive, send)
