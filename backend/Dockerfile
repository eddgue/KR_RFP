# Kroger Produce RFP / Sourcing — backend API/worker image.
# Runs `alembic upgrade head` then serves the FastAPI app via uvicorn.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

# Application source.
COPY . .

EXPOSE 8000

# Apply migrations, then serve. The store must be migrated before the API accepts traffic.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
