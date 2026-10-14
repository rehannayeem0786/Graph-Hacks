FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY .env.example .env

EXPOSE 8000

CMD ["python", "-m", "src.cli", "serve"]
