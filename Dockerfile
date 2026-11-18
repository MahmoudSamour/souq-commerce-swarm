# ==============================================================================
# SOUQ // Autonomous Commerce Edge Server on Koyeb Free Tier (<512MB RAM)
# ==============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PYTHONPATH=/app

WORKDIR /app

# Install lean runtime dependency (curl for healthcheck); binary wheels suffice without gcc
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and writable data directories
RUN groupadd --gid 10001 souq \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin souq \
    && mkdir -p /app/data/receipts /app/data/exports /app/data/cache \
    && chown -R souq:souq /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY --chown=souq:souq . /app/
RUN mkdir -p /app/data/receipts /app/data/exports /app/data/cache \
    && chown -R souq:souq /app/data

USER souq

# Expose Koyeb port
EXPOSE 8000

# Health check probe with 30s start period
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Launch production server
CMD ["python3", "scripts/koyeb_server.py"]

