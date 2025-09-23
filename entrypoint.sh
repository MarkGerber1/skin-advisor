#!/bin/sh
set -e

echo "🚀 === Railway Docker Entrypoint ==="
echo "📁 Current directory: $(pwd)"
echo "📋 Environment variables:"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   CATALOG_PATH: $CATALOG_PATH"
echo "   BOT_TOKEN: ${BOT_TOKEN:0:10}..."

echo "📂 Files in /usr/src/app:"
ls -la /usr/src/app/

echo "🔍 Looking for entry points..."

# Check if we're running on Render
if [ -n "$RENDER" ] || [ -n "$RENDER_SERVICE_ID" ]; then
    echo "🎨 Detected Render environment"
    if [ -f "/usr/src/app/render_app.py" ]; then
        echo "✅ Found render_app.py - starting Render web server..."
        cd /usr/src/app
        exec python render_app.py
    else
        echo "❌ ERROR: render_app.py not found for Render deployment!"
        exit 1
    fi
elif [ -f "/usr/src/app/start.py" ]; then
    echo "✅ Found /usr/src/app/start.py - starting bot..."
    cd /usr/src/app
    exec python start.py
elif [ -f "start.py" ]; then
    echo "✅ Found start.py in current dir - starting bot..."
    exec python start.py
elif [ -d "/usr/src/app/bot" ] && [ -f "/usr/src/app/bot/main.py" ]; then
    echo "✅ Found bot module - starting via python -m bot.main..."
    cd /usr/src/app
    exec python -m bot.main
else
    echo "❌ ERROR: Cannot find any entry point!"
    echo "📂 Current directory contents:"
    ls -la
    echo "📂 /usr/src/app contents:"
    ls -la /usr/src/app/ || echo "Cannot access /usr/src/app"
    exit 1
fi


