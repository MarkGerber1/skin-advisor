#!/usr/bin/env python
"""
Render.com deployment entry point
Flask web server with background bot process
"""

import os
import sys
import asyncio
import signal
import threading
from flask import Flask, request, jsonify

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
bot_thread = None
bot_started = False

print("🌐 Render Flask app initialized")


@app.route("/health")
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "OK", "bot_started": bot_started, "timestamp": "2024"})


@app.route("/webhook", methods=["GET", "POST"])
def telegram_webhook():
    """Handle Telegram webhook requests"""
    if request.method == "GET":
        return jsonify({"status": "Webhook endpoint active"})

    # For POST requests - acknowledge
    data = request.get_json(silent=True) or {}
    print(f"📨 Webhook received: {data.get('update_id', 'unknown')}")

    # TODO: Process webhook updates if needed
    return jsonify({"status": "OK"})


def run_bot_in_background():
    """Run bot in background thread"""
    global bot_started

    def bot_worker():
        global bot_started
        try:
            print("🤖 Starting bot in background thread...")

            # Import and run bot
            from bot.main import main

            bot_started = True
            print("✅ Bot thread started successfully")

            # Run the bot (this will block)
            asyncio.run(main())

        except Exception as e:
            print(f"❌ Bot thread error: {e}")
            bot_started = False

    # Start bot in daemon thread
    bot_thread = threading.Thread(target=bot_worker, daemon=True, name="BotThread")
    bot_thread.start()
    print("🚀 Bot thread launched")


@app.route("/start-bot")
def start_bot_endpoint():
    """Manually start bot (for debugging)"""
    global bot_thread

    if bot_thread and bot_thread.is_alive():
        return jsonify({"status": "Bot already running"})

    run_bot_in_background()
    return jsonify({"status": "Bot start initiated"})


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"📡 Received signal {signum}")
    print("🛑 Shutting down gracefully...")
    # Flask will handle the shutdown
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print("🚀 Starting Render Flask application...")

    # Get port from environment (Render provides PORT)
    port = int(os.getenv("PORT", "8080"))
    print(f"🌐 Port: {port}")
    print(f"🌐 Environment: {os.getenv('RENDER', 'NOT_SET')}")

    # Auto-start bot in background on startup
    print("🤖 Auto-starting bot...")
    run_bot_in_background()

    # Start Flask server
    print(f"🌐 Starting Flask server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
