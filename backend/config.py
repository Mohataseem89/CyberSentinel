import os
from urllib.parse import urlsplit, urlunsplit
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def _database_url():
    raw = os.getenv("DATABASE_URL", "").strip()
    if raw:
        if raw.startswith("postgres://"):
            raw = "postgresql://" + raw[len("postgres://"):]
        return raw
    required=("DB_USER","DB_PASSWORD","DB_HOST","DB_PORT","DB_NAME")
    missing=[k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError("Missing DATABASE_URL or database variables: " + ", ".join(missing))
    return f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"

def _origins():
    raw=os.getenv("FRONTEND_URLS") or os.getenv("FRONTEND_URL", "http://localhost:5173")
    values=[]
    for item in raw.split(','):
        value=item.strip().rstrip('/')
        if value and value not in values: values.append(value)
    return values

class Config:
    APP_ENV=os.getenv("APP_ENV","development").lower()
    IS_PRODUCTION=APP_ENV=="production"
    DATABASE_URL=_database_url()
    SQLALCHEMY_DATABASE_URI=DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    DB_POOL_SIZE=int(os.getenv("DB_POOL_SIZE","3"))
    DB_MAX_OVERFLOW=int(os.getenv("DB_MAX_OVERFLOW","2"))
    DB_POOL_TIMEOUT=int(os.getenv("DB_POOL_TIMEOUT","10"))
    DB_POOL_RECYCLE=int(os.getenv("DB_POOL_RECYCLE","300"))
    SECRET_KEY=os.getenv("SECRET_KEY","")
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY","")
    if not SECRET_KEY or not JWT_SECRET_KEY:
        raise RuntimeError("SECRET_KEY and JWT_SECRET_KEY are required.")
    if IS_PRODUCTION and (len(SECRET_KEY)<32 or len(JWT_SECRET_KEY)<32):
        raise RuntimeError("Production signing secrets must each be at least 32 characters.")
    JWT_ACCESS_TOKEN_EXPIRES=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_SECONDS","3600"))
    FRONTEND_ORIGINS=_origins()
    if IS_PRODUCTION:
        if not FRONTEND_ORIGINS or any(not x.startswith("https://") for x in FRONTEND_ORIGINS):
            raise RuntimeError("Production FRONTEND_URLS must contain only explicit HTTPS origins.")
    MAX_REQUEST_BYTES=int(os.getenv("MAX_REQUEST_BYTES","32768"))
    API_RATE_LIMIT_PER_MINUTE=int(os.getenv("API_RATE_LIMIT_PER_MINUTE","30"))
    BULK_MAX_CSV_BYTES=int(os.getenv("BULK_MAX_CSV_BYTES","1048576"))
    BULK_MAX_URLS_PER_JOB=int(os.getenv("BULK_MAX_URLS_PER_JOB","1000"))
    BULK_MAX_ACTIVE_JOBS_PER_USER=int(os.getenv("BULK_MAX_ACTIVE_JOBS_PER_USER","2"))
    BULK_MAX_JOBS_PER_DAY=int(os.getenv("BULK_MAX_JOBS_PER_DAY","10"))
    BULK_RETENTION_HOURS=int(os.getenv("BULK_RETENTION_HOURS","24"))
    FILE_SCAN_ENABLED=os.getenv("FILE_SCAN_ENABLED","false").lower()=="true"
    FILE_SCAN_MAX_BYTES=int(os.getenv("FILE_SCAN_MAX_BYTES","10485760"))
    FILE_SCAN_MAX_ACTIVE_PER_USER=int(os.getenv("FILE_SCAN_MAX_ACTIVE_PER_USER","2"))
    FILE_SCAN_MAX_DAILY_PER_USER=int(os.getenv("FILE_SCAN_MAX_DAILY_PER_USER","20"))
    FILE_SCAN_RESULT_RETENTION_HOURS=int(os.getenv("FILE_SCAN_RESULT_RETENTION_HOURS","24"))
