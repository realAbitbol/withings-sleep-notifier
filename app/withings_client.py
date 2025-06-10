# app/withings_client.py
import os, time, requests
from urllib.parse import urlencode
from .utils import load_tokens, save_tokens, token_is_expired

# Withings OAuth2 endpoints
AUTH_BASE = "https://account.withings.com/oauth2_user/authorize2"
TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
NOTIFY_URL = "https://wbsapi.withings.net/notify"

# Scopes: only user.sleepevents needed for bed notifications:contentReference[oaicite:10]{index=10}.
SCOPE = "user.sleepevents"

CLIENT_ID = os.environ["WITHINGS_CLIENT_ID"]
CLIENT_SECRET = os.environ["WITHINGS_CLIENT_SECRET"]
BASE_URL = os.environ["BASE_URL"].rstrip("/")

def get_authorize_url(state=None):
    """Build the Withings OAuth2 authorization URL."""
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/webhook",
        "scope": SCOPE,
        "state": state or "secret1234",  # In production, use a secure random state
    }
    url = f"{AUTH_BASE}?{urlencode(params)}"
    return url

def exchange_code_for_tokens(code):
    """
    Exchange the OAuth authorization code for access and refresh tokens.
    This calls the Withings /v2/oauth2 endpoint with action=requesttoken.
    """
    params = {
        "action": "requesttoken",
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": f"{BASE_URL}/webhook"
    }
    # Using GET with data as query (per Withings example):contentReference[oaicite:11]{index=11}.
    resp = requests.get(TOKEN_URL, params=params)
    resp.raise_for_status()
    data = resp.json().get("body", {})
    # Compute expiry timestamp
    expires_at = time.time() + data.get("expires_in", 0)
    token_data = {
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "expires_at": expires_at,
        "userid": data.get("userid")
    }
    save_tokens(token_data)
    return token_data

def refresh_access_token(token_data):
    """
    Refresh the access token using the stored refresh token.
    Saves updated tokens to file.
    """
    params = {
        "action": "requesttoken",
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": token_data.get("refresh_token")
    }
    resp = requests.get(TOKEN_URL, params=params)
    resp.raise_for_status()
    data = resp.json().get("body", {})
    expires_at = time.time() + data.get("expires_in", 0)
    token_data = {
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "expires_at": expires_at,
        "userid": data.get("userid")
    }
    save_tokens(token_data)
    return token_data

def get_valid_access_token():
    """
    Ensure we have a valid access token. Refreshes if expired.
    """
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No tokens found. Authorize first.")
    if token_is_expired(tokens):
        tokens = refresh_access_token(tokens)
    return tokens["access_token"]

def subscribe_notifications():
    """
    Subscribe the user to bed-in (appli=50) and bed-out (appli=51) notifications.
    Uses action=subscribe on the Notify API as documented:contentReference[oaicite:12]{index=12}.
    """
    access_token = get_valid_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    callback_url = f"{BASE_URL}/webhook"
    for appli in (50, 51):  # 50=bed in, 51=bed out:contentReference[oaicite:13]{index=13}
        params = {
            "action": "subscribe",
            "callbackurl": callback_url,
            "appli": str(appli)
        }
        resp = requests.post(NOTIFY_URL, data=params, headers=headers)
        resp.raise_for_status()
