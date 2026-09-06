"""Central application construction and HTTP safety controls."""
import logging
import os
import time
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.update(MAX_CONTENT_LENGTH=int(os.getenv("MAX_REQUEST_BYTES", "32768")))
    CORS(app, resources={r"/*": {"origins": [os.environ.get("FRONTEND_URL", "http://localhost:5173")]}}, supports_credentials=True)
    app.jwt = JWTManager(app)

    @app.before_request
    def request_start():
        g.request_started = time.monotonic()

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store" if request.path.startswith("/api/") or request.path == "/analyze" else response.headers.get("Cache-Control", "no-store")
        response.headers["X-Request-ID"] = os.urandom(8).hex()
        logging.getLogger("access").info("request method=%s path=%s status=%s duration_ms=%s", request.method, request.path, response.status_code, int((time.monotonic()-g.request_started)*1000))
        return response

    @app.errorhandler(413)
    def too_large(_): return jsonify({"error": "Request body is too large."}), 413
    return app
