# app/utils.py
import json, os, time

TOKEN_FILE = os.environ.get("TOKEN_FILE", "/app/tokens/withings_tokens.json")

def load_tokens():
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def save_tokens(token_data):
    dirpath = os.path.dirname(TOKEN_FILE)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

def token_is_expired(token_data):
    return time.time() >= token_data.get("expires_at", 0) - 120
