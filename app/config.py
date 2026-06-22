"""Application configuration."""
import os
from secrets import token_hex

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = token_hex(32)
CREDENTIALS_FILE = "database/grid_credentials.json"
ROOT_PATH = os.getenv("FASTAPI_ROOT_PATH", "")

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
