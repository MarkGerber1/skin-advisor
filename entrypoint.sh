#!/bin/sh
set -e

echo "=== Docker Entrypoint ==="
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

if [ -f "start.py" ]; then
    echo "Found start.py, starting bot..."
    exec python start.py
elif [ -f "/usr/src/app/start.py" ]; then
    echo "Found /usr/src/app/start.py, starting bot..."
    exec python /usr/src/app/start.py
elif [ -d "bot" ]; then
    echo "Found bot/ directory, trying python -m bot.main..."
    exec python -m bot.main
else
    echo "ERROR: Cannot find start.py or bot module!"
    echo "Directory contents:"
    ls -la
    exit 1
fi


