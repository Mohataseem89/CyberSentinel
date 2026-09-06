import unittest
try:
    from flask import Flask
    from middleware import FixedWindowLimiter
except ImportError:
    Flask = None

class ApiControlTests(unittest.TestCase):
    @unittest.skipIf(Flask is None, "Flask is installed from backend/requirements.txt in the application environment")
    def test_rate_limit_returns_429(self):
        app = Flask(__name__); app.config["API_RATE_LIMIT_PER_MINUTE"] = 1
        FixedWindowLimiter(app)
        @app.post("/analyze")
        def analyze(): return {"ok": True}
        client = app.test_client()
        self.assertEqual(client.post("/analyze").status_code, 200)
        self.assertEqual(client.post("/analyze").status_code, 429)
