# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=core.settings \
    PORT=8000

# Only the runtime system lib needed for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Create a non-root user for security
RUN groupadd --system django && useradd --system --gid django django

COPY --chown=django:django . .

RUN mkdir -p logs staticfiles media \
    && chown -R django:django logs staticfiles media

USER django

EXPOSE $PORT

ENTRYPOINT ["./entrypoint.sh"]
# Development default — override in docker-compose for production
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
