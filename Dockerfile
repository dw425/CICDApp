FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose Dash port (matches app.yaml / Databricks Apps)
EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8050/ || exit 1

# Default env for Databricks deployment
ENV AUTH_MODE=databricks
ENV CICD_APP_USE_MOCK=false
ENV APP_DEBUG=false

# Run with gunicorn
CMD ["gunicorn", "app:server", \
     "--bind", "0.0.0.0:8050", \
     "--workers", "2", \
     "--timeout", "120"]
