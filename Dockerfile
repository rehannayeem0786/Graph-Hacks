FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY static/ static/
COPY .env.example .env

EXPOSE 8000

CMD ["sh", "-c", "python -m src.cli ingest ./src 2>/dev/null || true && python -m uvicorn src.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
