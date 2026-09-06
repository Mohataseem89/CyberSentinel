"""Small in-memory abuse controls suitable for one process; use Redis in production."""
from collections import defaultdict, deque
from time import monotonic
from flask import jsonify, request

class FixedWindowLimiter:
    def __init__(self, app, limit=None, window=60):
        limit = limit or app.config.get("API_RATE_LIMIT_PER_MINUTE", 30)
        self.limit, self.window, self.hits = limit, window, defaultdict(deque)
        app.before_request(self.check)
    def check(self):
        if request.path not in {"/analyze", "/api/auth/login", "/api/auth/register"}: return None
        key = f"{request.path}:{request.remote_addr or 'unknown'}"; now = monotonic(); bucket = self.hits[key]
        while bucket and bucket[0] <= now-self.window: bucket.popleft()
        if len(bucket) >= self.limit:
            return jsonify({"error": "Too many requests. Please try again shortly.", "code": "rate_limited"}), 429
        bucket.append(now)
