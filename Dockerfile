FROM python:3-alpine

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/tokens.json"]

EXPOSE 5000 8000
CMD ["sh", "-c", "python3 auth_helper.py & gunicorn --bind 0.0.0.0:5000 app:app"]
