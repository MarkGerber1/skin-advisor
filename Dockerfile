FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY bot/ ./bot/
COPY engine/ ./engine/
COPY assets/ ./assets/
COPY tests/ ./tests/
COPY *.py ./
COPY *.toml ./
COPY *.txt ./

# Debug: List files to verify structure
RUN ls -la && ls -la bot/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV CATALOG_PATH=assets/fixed_catalog.yaml

# Run the bot
CMD ["python", "start.py"]








