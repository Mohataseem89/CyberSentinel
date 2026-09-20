"""Central application construction and production HTTP safety controls."""
import logging, os, sys, time
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

def _configure_logging():
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL","INFO").upper(), logging.INFO),
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

def _configure_sentry():
    dsn=os.getenv("SENTRY_DSN","").strip()
    if not dsn: return
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    def before_send(event, hint):
        req=event.get("request") or {}
        req.pop("data",None); req.pop("query_string",None)
        if "url" in req: req["url"]=req["url"].split("?",1)[0]
        headers=req.get("headers") or {}
        for key in list(headers):
            if key.lower() in {"authorization","cookie","x-api-key"}: headers[key]="[Filtered]"
        event.pop("user",None)
        return event
    sentry_sdk.init(dsn=dsn, integrations=[FlaskIntegration()], environment=Config.APP_ENV, send_default_pii=False, traces_sample_rate=0.0, before_send=before_send)

def create_app():
    _configure_logging(); _configure_sentry()
    app=Flask(__name__)
    app.config.from_object(Config)
    app.config.update(
        DEBUG=False if Config.IS_PRODUCTION else os.getenv("FLASK_DEBUG","false").lower()=="true",
        TESTING=False,
        MAX_CONTENT_LENGTH=max(Config.MAX_REQUEST_BYTES,Config.BULK_MAX_CSV_BYTES+65536,Config.FILE_SCAN_MAX_BYTES+65536),
        SESSION_COOKIE_SECURE=Config.IS_PRODUCTION, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
    )
    if Config.IS_PRODUCTION:
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1,x_host=1,x_port=1)
    CORS(app, resources={r"/*":{"origins":Config.FRONTEND_ORIGINS}}, supports_credentials=False, allow_headers=["Content-Type","Authorization","X-Retain-Scan"])
    app.jwt=JWTManager(app)

    @app.before_request
    def request_start():
        g.request_started=time.monotonic()
        content_length=request.content_length or 0
        if request.path.startswith('/api/file-scans'): limit=Config.FILE_SCAN_MAX_BYTES+65536
        elif request.path.startswith('/api/bulk/jobs'): limit=Config.BULK_MAX_CSV_BYTES+65536
        else: limit=Config.MAX_REQUEST_BYTES
        if content_length>limit: return jsonify({"error":"Request body is too large."}),413

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["X-Frame-Options"]="DENY"
        response.headers["Referrer-Policy"]="no-referrer"
        response.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"]="default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        if Config.IS_PRODUCTION: response.headers["Strict-Transport-Security"]="max-age=31536000; includeSubDomains"
        if request.path.startswith('/api/') or request.path in {'/analyze','/health','/ready'}: response.headers["Cache-Control"]="no-store"
        response.headers["X-Request-ID"]=os.urandom(8).hex()
        duration=int((time.monotonic()-getattr(g,'request_started',time.monotonic()))*1000)
        logging.getLogger("access").info("request method=%s path=%s status=%s duration_ms=%s",request.method,request.path,response.status_code,duration)
        return response

    @app.errorhandler(413)
    def too_large(_): return jsonify({"error":"Request body is too large."}),413
    @app.errorhandler(500)
    def internal_error(_):
        logging.getLogger("app").exception("Unhandled request failure")
        return jsonify({"error":"Internal server error."}),500
    return app
