# app/main.py
import os, logging, requests, asyncio
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from .withings_client import get_authorize_url, exchange_code_for_tokens, subscribe_notifications
from .utils import load_tokens, token_is_expired, refresh_access_token

logger = logging.getLogger("uvicorn")
load_dotenv()  # Loads .env file into os.environ if present

BASE_URL = os.getenv("BASE_URL").rstrip("/")
BEDIN_URL = os.getenv("BEDIN_URL")
BEDOUT_URL = os.getenv("BEDOUT_URL")
REFRESH_INTERVAL = 60  # seconds; check every minute

async def token_refresher_loop():
    while True:
        tokens = load_tokens()
        if tokens and token_is_expired(tokens):
            try:
                refresh_access_token(tokens)
                logger.info("🔄 Withings access token refreshed")
            except Exception as e:
                logger.error(f"❌ Error refreshing token: {e}")
        await asyncio.sleep(REFRESH_INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    tokens = load_tokens()
    if not tokens or token_is_expired(tokens):
        logger.info(f"\n🚀 Please visit {BASE_URL}/authorize to link your Withings account.\n")
    # Start background token refresher
    asyncio.create_task(token_refresher_loop())
    yield
    # Cleanup if needed (e.g., close connections, etc.)
    # No cleanup needed for this simple app
    logger.info("\n👋 Shutting down the app. No cleanup needed.\n")

app = FastAPI(lifespan=lifespan)

@app.get("/authorize")
def authorize():
    """
    Redirect the user to Withings OAuth2 authorization.
    """
    url = get_authorize_url()
    return RedirectResponse(url)

@app.get("/webhook")
def callback(code: str = None, state: str = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code in callback")
    try:
        exchange_code_for_tokens(code)
        subscribe_notifications()
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "subscribed for bed events"}

@app.post("/webhook")
async def webhook(request: Request):
    """
    Endpoint for Withings to POST data notifications (Content-Type: application/x-www-form-urlencoded).
    We must respond 200 OK. Check the 'appli' field for 50 or 51 to determine the event.
    """
    form = await request.form()
    appli = form.get("appli")
    # debug log (in production, use proper logging)
    logger.info(f"Notification received: {form}")
    # Identify bed-in/out events by appli code:contentReference[oaicite:14]{index=14}
    if appli == "50":
        target_url = BEDIN_URL
    elif appli == "51":
        target_url = BEDOUT_URL
    else:
        return "OK"  # ignore other notifications

    try:
        # Trigger the local GET request
        resp = requests.get(target_url)
        resp.raise_for_status()
        logger.info(f"Triggered GET {target_url}: {resp.status_code}")
    except Exception as e:
        logger.error(f"Error triggering {target_url}: {e}")
    return "OK"

@app.head("/webhook")
def webhook_head():
    """
    Respond OK to HEAD requests (Withings may send HEAD to test the endpoint).
    """
    return "OK"
