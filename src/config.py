"""
Environment configuration
Load API keys and settings from .env file
"""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"  # Vision-enabled model

# eBay
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_SANDBOX = os.getenv("EBAY_SANDBOX", "True").lower() == "true"
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
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Mock APIs (for development without credentials)
USE_OPENAI_MOCK = os.getenv("USE_OPENAI_MOCK", "False").lower() == "true"
USE_EBAY_MOCK = os.getenv("USE_EBAY_MOCK", "True").lower() == "true"  # Default to mock until eBay API ready
# Web UI Config
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}