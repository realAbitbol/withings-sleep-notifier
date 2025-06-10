# app/withings_client.py
import os, time, requests
from urllib.parse import urlencode
from .utils import load_tokens, save_tokens, token_is_expired

AUTH_BASE = "https://account.withings.com/oauth2_user/authorize2"
TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
NOTIFY_URL = "https://wbsapi.withings.net/notify"
SCOPE = "user.sleepevents"

CLIENT_ID = os.environ["WITHINGS_CLIENT_ID"]
CLIENT_SECRET = os.environ["WITHINGS_CLIENT_SECRET"]
BASE_URL = os.environ["BASE_URL"].rstrip("/")

def get_authorize_url(state=None):
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/webhook",
        "scope": SCOPE,
        "state": state or "secret1234",
    }
    return f"{AUTH_BASE}?{urlencode(params)}"

def _make_token_data(data):
    return {
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "expires_at": time.time() + data.get("expires_in", 0),
        "userid": data.get("userid")
    }

def exchange_code_for_tokens(code):
    params = {
        "action": "requesttoken",
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": f"{BASE_URL}/webhook"
    }
    resp = requests.get(TOKEN_URL, params=params)
    resp.raise_for_status()
    token_data = _make_token_data(resp.json().get("body", {}))
    save_tokens(token_data)
    return token_data

def refresh_access_token(token_data):
    params = {
        "action": "requesttoken",
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": token_data.get("refresh_token")
    }
    resp = requests.get(TOKEN_URL, params=params)
    resp.raise_for_status()
    token_data = _make_token_data(resp.json().get("body", {}))
    save_tokens(token_data)
    return token_data

def get_valid_access_token():
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No tokens found. Authorize first.")
    if token_is_expired(tokens):
        tokens = refresh_access_token(tokens)
    return tokens["access_token"]

def subscribe_notifications():
    """
    Subscribe the user to bed-in (appli=50) and bed-out (appli=51) notifications.
    Uses action=subscribe on the Notify API.
    """
    access_token = get_valid_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    callback_url = f"{BASE_URL}/webhook"
    for appli in ("50", "51"):
        params = {
            "action": "subscribe",
            "callbackurl": callback_url,
            "appli": appli
        }
        resp = requests.post(NOTIFY_URL, data=params, headers=headers)
        resp.raise_for_status()
