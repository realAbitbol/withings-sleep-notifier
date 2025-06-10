# Withings Sleep Notifier

A simple Python app that send GET notifications to a remote server whenever you get into bed or leave your bed.

## Env variables

- `CLIENT_ID`: Your Withings client ID.
- `CLIENT_SECRET`: Your Withings client secret.
- `APP_URL`: The URL of the application. This is used for authorization and notification URLs.
- `BEDIN_URL`: The URL to send GET notifications when you enter your bed.
- `BEDOUT_URL`: The URL to send GET notifications when you leave your bed.

## Usage

1. Create a Withings account and create an app with the following permissions:
   - `user.sleep`
2. Set the env variables in your application's environment or use them directly in your code.
3. Run the Python script using Docker Compose to start the server and listen for bed events.

