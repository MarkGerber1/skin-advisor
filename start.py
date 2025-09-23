#!/usr/bin/env python
"""Entry point that starts both Flask health server and bot."""

import sys
import os
import asyncio
from flask import Flask, request, jsonify

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create Flask app for health checks and webhooks
app = Flask(__name__)
print("🌐 Flask app created")

# Global bot and dispatcher for webhook handling
bot_instance = None
dp_instance = None
print("🌐 Global variables initialized")


@app.route("/health")
def health():
    return "OK_UPDATED"


@app.route("/webhook", methods=["GET", "POST"])
def telegram_webhook():
    """Handle Telegram webhook requests"""
    print("🌐 Webhook endpoint called!")

    if request.method == "GET":
        return jsonify({"status": "Webhook endpoint active", "method": "GET"})

    # For POST requests - just acknowledge for now
    print("📨 Webhook POST received")
    return jsonify({"status": "OK", "method": "POST"})


print("🌐 Webhook route registered")


def run_flask():
    """Run Flask server"""
    port = int(os.getenv("PORT", "8080"))
    print(f"🌐 Starting Flask health server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)


def run_bot():
    """Run the bot"""
    print("🤖 Starting bot...")
    from bot.main import main, get_bot_and_dispatcher

    # Get bot and dispatcher instances for webhook handling
    global bot_instance, dp_instance
    bot_instance, dp_instance = get_bot_and_dispatcher()

    asyncio.run(main())


if __name__ == "__main__":
    print("🚀 Starting combined Flask + Bot server...")

    # Start Flask in background thread
    import threading

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start bot in main thread
    run_bot()
