FROM python:3.11-slim

# -----------------------------------------------------------------------------------------
#   Dockerfile: Celery Crawler Worker
# -----------------------------------------------------------------------------------------
#   This Dockerfile builds a Celery worker for the tax-lien crawler.
#   
#   Includes:
#   - System dependencies for SeleniumBase browser automation
#   - Xvfb for headless browser operation
#   - Celery worker with Flower event emission support
#
#   Usage:
#   - Build: docker build -t celery-crawler .
#   - Run: docker-compose up -d
# -----------------------------------------------------------------------------------------

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Browser dependencies (SeleniumBase)
    xvfb \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    # Utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data and platforms
RUN mkdir -p /data /app/platforms

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DISPLAY=:99

# Default command (override in docker-compose)
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--send-events"]
