#!/usr/bin/env python
"""Entry point that starts both Flask health server and bot."""

import sys
import os
import asyncio
import threading
from flask import Flask

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create Flask app for health checks
app = Flask(__name__)

@app.route("/health")
def health():
    return "OK"

def run_flask():
    """Run Flask server in a separate thread"""
    port = int(os.getenv("PORT", "8080"))
    print(f"🌐 Starting Flask health server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def run_bot():
    """Run the bot"""
    print("🤖 Starting bot...")
    from bot.main import main
    asyncio.run(main())

if __name__ == "__main__":
    print("🚀 Starting combined Flask + Bot server...")

    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start bot in main thread
    run_bot()
