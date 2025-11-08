FROM python:3.11-slim

RUN apt-get update      && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates      && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PORT=8080

HEALTHCHECK --interval=30s --timeout=5s --retries=5       CMD curl -fsS http://localhost:8080/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
