FROM python:3.11-slim

# Use the path Railway expects
WORKDIR /usr/src/app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Debug: List files to verify structure
RUN ls -la && ls -la bot/ || echo "bot/ directory not found"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/usr/src/app
ENV CATALOG_PATH=assets/fixed_catalog.yaml

# Run the bot
CMD ["python", "start.py"]








