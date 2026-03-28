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

# Expose Dash port
EXPOSE 8070

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8070/ || exit 1

# Run with gunicorn
CMD ["gunicorn", "app:server", \
     "--bind", "0.0.0.0:8070", \
     "--workers", "4", \
     "--timeout", "120"]
