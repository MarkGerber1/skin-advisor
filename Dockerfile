# Use Render mirror image to bypass Docker Hub 401/limits
FROM us-west1-docker.pkg.dev/render-images/public/python:3.11-slim
# Force rebuild: v2

WORKDIR /usr/src/app

# Install system dependencies for fonts and PDF generation
RUN apt-get update && apt-get install -y \
    fonts-dejavu \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    && rm -rf /var/lib/apt/lists/*

# First, copy only requirements to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy specific directories and files
COPY bot/ ./bot/
COPY engine/ ./engine/
COPY assets/ ./assets/
COPY services/ ./services/
COPY i18n/ ./i18n/
COPY report/ ./report/
COPY start.py ./start.py
COPY render_app.py ./render_app.py
COPY *.toml ./
COPY *.json ./

# Verify critical files were copied
RUN echo "=== Build verification ===" && \
    ls -la /usr/src/app/ && \
    echo "=== Checking render_app.py ===" && \
    test -f /usr/src/app/render_app.py && echo "✓ render_app.py EXISTS" || echo "✗ render_app.py NOT FOUND" && \
    echo "=== Checking bot/main.py ===" && \
    test -f /usr/src/app/bot/main.py && echo "✓ bot/main.py EXISTS" || echo "✗ bot/main.py NOT FOUND" && \
    echo "=== Checking assets/ ===" && \
    test -d /usr/src/app/assets && echo "✓ assets/ EXISTS" || echo "✗ assets/ NOT FOUND" && \
    echo "=== Checking services/ ===" && \
    test -d /usr/src/app/services && echo "✓ services/ EXISTS" || echo "✗ services/ NOT FOUND" && \
    echo "=== Checking i18n/ ===" && \
    test -d /usr/src/app/i18n && echo "✓ i18n/ EXISTS" || echo "✗ i18n/ NOT FOUND" && \
    echo "=== Checking report/ ===" && \
    test -d /usr/src/app/report && echo "✓ report/ EXISTS" || echo "✗ report/ NOT FOUND"

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

# Alternative CMD for Railway compatibility
CMD ["python", "start.py"]

# Debug: Test imports before starting
RUN python -c "import sys; print('Python version:', sys.version)" && \
    python -c "from bot.main import main; print('✅ Main function imported successfully')" && \
    python -c "import render_app; print('✅ Render app imported successfully')" && \
    echo "✅ All imports work correctly" && \
    echo "🚀 Docker build completed successfully"








