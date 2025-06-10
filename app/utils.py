# app/utils.py
import json, os, time

TOKEN_FILE = os.environ.get("TOKEN_FILE", "/app/tokens/withings_tokens.json")

def load_tokens():
    """Load stored tokens from file, or None if not found."""
    try:
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return None

def save_tokens(token_data):
    """Save tokens (including refresh_token) to file."""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)

def token_is_expired(token_data):
    """Check if the current access token has expired."""
    expires_at = token_data.get("expires_at", 0)
    return time.time() >= expires_at - 120  # Refresh 2 minutes before expiry
