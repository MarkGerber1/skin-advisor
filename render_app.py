#!/usr/bin/env python
"""
Render.com deployment entry point
Flask web server with background bot process
"""

import os
import sys
import asyncio
import signal
from flask import Flask, request, jsonify

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

print("🌐 Render Flask app initialized")


async def _set_webhook():
    """Configure Telegram webhook based on environment variables."""
    try:
        from bot.main import get_bot_and_dispatcher

        bot, dp = get_bot_and_dispatcher()
        base = os.getenv("WEBHOOK_URL")
        path = os.getenv("WEBHOOK_PATH", "/webhook")
        if not base:
            print("⚠️ WEBHOOK_URL is not set - skipping webhook setup")
            return
        webhook_full_url = f"{base.rstrip('/')}{path}"
        await bot.set_webhook(
            url=webhook_full_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "inline_query"],
        )
        print(f"✅ Webhook set to {webhook_full_url}")
    except Exception as e:
        print(f"❌ Failed to set webhook: {e}")


@app.route("/health")
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "OK", "timestamp": "2025"})


@app.route("/webhook", methods=["GET", "POST"])
def telegram_webhook():
    """Handle Telegram webhook requests: forward updates to aiogram dispatcher."""
    if request.method == "GET":
        return jsonify({"status": "Webhook endpoint active"})

    data = request.get_json(silent=True) or {}
    try:
        from aiogram.types import Update
        from bot.main import get_bot_and_dispatcher

        async def _process_update():
            bot, dp = get_bot_and_dispatcher()
            update = Update.model_validate(data)
            await dp.feed_update(bot, update)

        asyncio.run(_process_update())
        return jsonify({"status": "OK"})
    except Exception as e:
        print(f"❌ Webhook processing error: {e}")
        return jsonify({"status": "ERROR", "detail": str(e)}), 500


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"📡 Received signal {signum}")
    print("🛑 Shutting down gracefully...")
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

    # Configure webhook on startup
    try:
        asyncio.run(_set_webhook())
    except Exception as e:
        print(f"⚠️ Webhook setup skipped: {e}")

    # Start Flask server
    print(f"🌐 Starting Flask server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
