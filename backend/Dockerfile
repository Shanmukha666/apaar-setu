# Persistent-host container for the synthetic APAAR-Setu staging API.
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# `seed.load_all` is idempotent, so every restart has the required demo dataset
# without overwriting a persistent database.
CMD ["sh", "-c", "python -m seed.load_all && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
