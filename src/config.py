"""
Environment configuration
Load API keys and settings from .env file
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _parse_bool(value: str | None, default: bool = False) -> bool:
    """Consistently parse environment boolean strings."""
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"  # Vision-enabled model

# eBay
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_SANDBOX = _parse_bool(os.getenv("EBAY_SANDBOX"), default=True)
EBAY_OAUTH_ENDPOINT = (
    "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
    if EBAY_SANDBOX
    else "https://api.ebay.com/identity/v1/oauth2/token"
)
EBAY_API_ENDPOINT = (
    "https://api.sandbox.ebay.com"
    if EBAY_SANDBOX
    else "https://api.ebay.com"
)

# App settings
DEBUG = _parse_bool(os.getenv("DEBUG"), default=False)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Mock APIs — default to mock so the app works out-of-the-box without credentials.
# Set USE_OPENAI_MOCK=False and USE_EBAY_MOCK=False in .env to use real APIs.
USE_OPENAI_MOCK = _parse_bool(os.getenv("USE_OPENAI_MOCK"), default=True)
USE_EBAY_MOCK = _parse_bool(os.getenv("USE_EBAY_MOCK"), default=True)

# Business logic thresholds
HIGH_VALUE_THRESHOLD = float(os.getenv("HIGH_VALUE_THRESHOLD", "20.0"))

# Upload configuration
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "16"))
MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Web UI Config
from src.paths import get_upload_dir
UPLOAD_FOLDER = get_upload_dir()
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}


def validate_config() -> None:
    """Validate critical configuration on startup; raise ValueError if misconfigured."""
    if not USE_OPENAI_MOCK and not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required when USE_OPENAI_MOCK=False")
    if not USE_EBAY_MOCK and not (EBAY_CLIENT_ID and EBAY_CLIENT_SECRET):
        raise ValueError("EBAY_CLIENT_ID and EBAY_CLIENT_SECRET are required when USE_EBAY_MOCK=False")