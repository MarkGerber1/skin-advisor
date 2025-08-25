FROM python:3.11-slim
# Force rebuild: v2

WORKDIR /usr/src/app

# First, copy only requirements to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy specific directories and files
COPY bot/ ./bot/
COPY engine/ ./engine/
COPY assets/ ./assets/
COPY start.py ./start.py
COPY *.toml ./
COPY *.json ./

# Verify files were copied
RUN echo "=== Listing /usr/src/app ===" && \
    ls -la /usr/src/app/ && \
    echo "=== Checking start.py ===" && \
    test -f /usr/src/app/start.py && echo "start.py EXISTS" || echo "start.py NOT FOUND" && \
    echo "=== Checking bot/ ===" && \
    ls -la /usr/src/app/bot/ || echo "bot/ NOT FOUND"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/usr/src/app
ENV CATALOG_PATH=assets/fixed_catalog.yaml

# Copy entrypoint script
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Use entrypoint for flexible startup
ENTRYPOINT ["/bin/sh", "/usr/src/app/entrypoint.sh"]








