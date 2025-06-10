FROM python:3-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk add --no-cache gcc libffi-dev musl-dev openssl-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

COPY app/ ./app/

EXPOSE 8000
VOLUME ["/app/tokens"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
