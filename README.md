# Withings Sleep Notifier

A simple Python app that send GET notifications to a remote server whenever you get into bed or leave your bed.

## Env variables

- `CLIENT_ID`: Your Withings client ID.
- `CLIENT_SECRET`: Your Withings client secret.
- `BASE_URL`: The public URL of the application. This is used for authorization and notification URLs.
- `BEDIN_URL`: The URL to send GET notifications when you enter your bed.
- `BEDOUT_URL`: The URL to send GET notifications when you leave your bed.

## Usage

1. Create a Withings account and register your app (see below)
2. Set the env variables either in docker-compose.yml or in .env
3. Run the app using Docker Compose or directly with `uvicorn app.main:app --host 0.0.0.0 --port 8000` after having run `pip install -r requirements.txt`

## Registering with Withings Developer Portal

1. Create an app: Go to <developer.withings.com> and open your Dashboard. Add a new application. You’ll get a `Client ID` and `Client Secret`.
2. Set redirect URI: In your app settings, set the Callback URL (Redirect URI) to your base URL plus /webhook (e.g. `https://yourdomain.com/webhook`).
3. Enable notifications: In the app settings, ensure that your callback URL (`BASE_URL`/webhook) is registered/allowed for data notifications. The Withings docs note that subscriptions use your registered callback URL
4. Scopes: Request the `user.sleepevents` scope (which allows receiving bed-in/out notifications). No other scopes are needed since we only handle sleep events.
