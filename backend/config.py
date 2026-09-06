import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Config:
    """Configuration loaded exclusively from the environment.

    The backend must not start with placeholder credentials or a deterministic
    signing key. Keep optional integrations (such as VirusTotal) outside this
    required list so the scanner can report them as unavailable instead.
    """

    REQUIRED_ENV = (
        "DB_USER",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "SECRET_KEY",
        "JWT_SECRET_KEY",
    )
    missing = tuple(name for name in REQUIRED_ENV if not os.getenv(name))
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variables: {names}. "
            "Copy backend/.env.example to backend/.env and set unique values."
        )

    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DB_HOST = os.environ["DB_HOST"]
    DB_PORT = os.environ["DB_PORT"]
    DB_NAME = os.environ["DB_NAME"]

    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24 hours
    SECRET_KEY = os.environ["SECRET_KEY"]
    MAX_REQUEST_BYTES = int(os.getenv("MAX_REQUEST_BYTES", "32768"))
    API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "30"))
