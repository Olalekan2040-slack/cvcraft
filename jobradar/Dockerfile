FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2 and lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc libxml2-dev libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium + all its system dependencies in one step
RUN playwright install --with-deps chromium

COPY . .

EXPOSE 8000

# Run DB migrations then start the server.
# Render injects PORT; fall back to 8000 for local docker-compose.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
