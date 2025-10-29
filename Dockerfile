# -------- Stage 1: Build dependencies --------
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

COPY . /app

# -------- Stage 2: Final lightweight image --------
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && apt-get clean

# Create non-root user
RUN useradd -m den4ik

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /app /app

RUN chown -R den4ik:den4ik /app

USER den4ik

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:5000/health || exit 1

# Run app with Gunicorn
CMD ["gunicorn", "application:app", "--workers=3", "--bind=0.0.0.0:5000"]

