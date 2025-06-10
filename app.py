import os
import json
import time
import logging
import threading
import requests
from flask import Flask, request, abort

app = Flask(__name__)

TOKEN_FILE = os.getenv("TOKEN_FILE", "/tokens.json")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
BEDIN_URL = os.getenv("BEDIN_URL")
BEDOUT_URL = os.getenv("BEDOUT_URL")

logging.basicConfig(level=logging.INFO)

tokens = {}
last_sleep_status = None
lock = threading.Lock()

def load_tokens():
    global tokens
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            tokens = json.load(f)
            logging.info("Tokens loaded")
    else:
        logging.warning("Token file not found, authorize first.")

def save_tokens():
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f)
    logging.info("Tokens saved")

def refresh_token():
    global tokens
    logging.info("Refreshing Withings access token...")
    resp = requests.post("https://wbsapi.withings.net/v2/oauth2", data={
        "action": "requesttoken",
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": tokens["refresh_token"]
    })
    resp.raise_for_status()
    body = resp.json()["body"]
    tokens.update(body)
    save_tokens()
    logging.info("Token refreshed")

def get_sleep_data():
    global tokens
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = requests.get("https://wbsapi.withings.net/v2/sleep?action=get", headers=headers)
    if resp.status_code == 401:
        refresh_token()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = requests.get("https://wbsapi.withings.net/v2/sleep?action=get", headers=headers)
    resp.raise_for_status()
    return resp.json()

def handle_bed_event(in_bed):
    url = BEDIN_URL if in_bed else BEDOUT_URL
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        logging.info(f"Sent {'bed in' if in_bed else 'bed out'} request to {url}")
    except Exception as e:
        logging.error(f"Failed to send {'bed in' if in_bed else 'bed out'} request to {url}: {e}")

@app.route("/withings_notify", methods=["POST", "GET"])
def withings_notify():
    global last_sleep_status

    # You can verify signatures here if you want, but skipping for simplicity

    # Fetch current sleep data
    try:
        data = get_sleep_data()
    except Exception as e:
        logging.error(f"Error fetching sleep data: {e}")
        abort(500)

    # Find the latest sleep summary to get in_bed status
    series = data.get("body", {}).get("series", [])
    if not series:
        logging.warning("No sleep series data found.")
        return "No sleep data", 200

    latest = series[-1]
    in_bed = latest.get("in_bed") == 1

    with lock:
        if last_sleep_status is None:
            last_sleep_status = in_bed
            logging.info(f"Initial bed status: {'in bed' if in_bed else 'out of bed'}")
        elif in_bed != last_sleep_status:
            logging.info(f"Bed status changed to: {'in bed' if in_bed else 'out of bed'}")
            handle_bed_event(in_bed)
            last_sleep_status = in_bed
        else:
            logging.debug("No change in bed status.")

    return "OK", 200

if __name__ == "__main__":
    load_tokens()
    if not tokens:
        print("🔑 No tokens found! Please authorize via /auth/start endpoint on port 8000.")
    app.run(host="0.0.0.0", port=5000)
