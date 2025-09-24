#!/usr/bin/env python
"""
Render.com deployment entry point
Flask web server with background bot process
"""

import os
import sys
import asyncio
import threading
import signal
import os
from flask import Flask, jsonify

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

print("🌐 Render Flask app initialized (polling mode)")


async def _run_bot_polling():
    """Run aiogram polling loop."""
    try:
        from bot.main import main as bot_main

        await bot_main()
    except Exception as e:
        print(f"❌ Bot polling crashed: {e}")


def _start_bot_background():
    """Start the bot polling in a background thread with its own event loop."""
    # Singleton lock to avoid double polling instances (Render multi-start protection)
    lock_path = "/tmp/bot_polling.lock"
    try:
        if os.path.exists(lock_path):
            print("⚠️ Polling lock exists - skipping bot start to avoid conflicts")
            return
        with open(lock_path, "w", encoding="utf-8") as f:
            f.write("locked")
    except Exception as e:
        print(f"⚠️ Could not create polling lock: {e}")

    def _runner():
        try:
            asyncio.run(_run_bot_polling())
        except Exception as e:
            print(f"❌ Background bot runner error: {e}")
        finally:
            try:
                if os.path.exists(lock_path):
                    os.remove(lock_path)
                    print("🧹 Polling lock removed")
            except Exception as ce:
                print(f"⚠️ Could not remove polling lock: {ce}")

    t = threading.Thread(target=_runner, name="BotPollingThread", daemon=True)
    t.start()
    print("✅ Bot polling thread started")


@app.route("/health")
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "OK", "mode": "polling"})


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"📡 Received signal {signum}")
    print("🛑 Shutting down gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print("🚀 Starting Render Flask application (polling mode)...")

    # Start bot polling in background
    _start_bot_background()

    # Get port from environment (Render provides PORT)
    port = int(os.getenv("PORT", "8080"))
    print(f"🌐 Port: {port}")

    # Start Flask server
    print(f"🌐 Starting Flask server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
