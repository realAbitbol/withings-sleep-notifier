# Dockerfile
FROM python:3-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk add --no-cache gcc  libffi-dev musl-dev openssl-dev
# Copy application code
COPY app/ ./app/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Expose port and run
EXPOSE 8000
VOLUME ["/app/tokens"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
