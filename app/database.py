"""Database operations for grid credentials."""
import json
from app.config import CREDENTIALS_FILE


def load_credentials():
    """Load grid credentials from JSON file."""
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('users', [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_credentials(users):
    """Save grid credentials to JSON file."""
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump({"users": users}, f, indent=2)
