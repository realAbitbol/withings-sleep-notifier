import os
import json
import requests
from urllib.parse import urlencode
from flask import Flask, request

app = Flask(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
APP_URL = os.getenv("APP_URL")
CALLBACK_URL = f"{APP_URL}/withings_notify"
TOKEN_FILE = os.getenv("TOKEN_FILE", "/tokens.json")

@app.before_first_request
def announce_if_needed():
    if not os.path.exists(TOKEN_FILE):
        print(f"🔑 Visit {APP_URL}/auth/start to authorize the Withings app")

@app.route("/auth/start")
def start_auth():
    query = urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": CALLBACK_URL,
        "scope": "user.sleep",
        "state": "secure123"
    })
    url = f"https://account.withings.com/oauth2_user/authorize?{query}"
    return f"Please visit this URL to authorize the app:<br><a href='{url}'>{url}</a>"

@app.route("/withings_notify")
def receive_code():
    code = request.args.get("code")
    if not code:
        return "Missing code parameter", 400

    resp = requests.post("https://wbsapi.withings.net/v2/oauth2", data={
        "action": "requesttoken",
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": CALLBACK_URL
    })
    resp.raise_for_status()
    tokens = resp.json()["body"]
    json.dump(tokens, open(TOKEN_FILE, "w"))
    return "✅ Authorized! Tokens saved. You can now close this page."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
