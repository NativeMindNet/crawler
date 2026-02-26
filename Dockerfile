FROM python:3.11-slim

# Install system dependencies for SeleniumBase
RUN apt-get update && apt-get install -y \
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
    libgtk-3-0 \
    libxss1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY crawler/ ./crawler/
COPY config/ ./config/

# Create volume mount points
RUN mkdir -p /data/results /data/raw /data/state

# Set environment variables
ENV PYTHONPATH=/app
ENV CONFIG_DIR=/config
ENV DATA_DIR=/data
ENV DB_PATH=/data/state/crawler.db

# Expose API port
EXPOSE 8000

# Default command: run worker
ENTRYPOINT ["python", "-m", "crawler"]
CMD ["worker", "run"]
