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

# Global bot and dispatcher for webhook handling
bot_instance = None
dp_instance = None


@app.route("/health")
def health():
    return "OK"


@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    """Handle Telegram webhook requests"""
    global bot_instance, dp_instance

    # For debugging - temporarily accept requests even if bot not initialized
    print(f"🌐 Webhook request received. Bot initialized: {bot_instance is not None}")

    if not bot_instance or not dp_instance:
        print("⚠️ Bot not initialized yet, returning OK to acknowledge")
        return jsonify({"status": "Bot not ready"}), 200

    try:
        from aiogram import types

        update_data = request.get_json()
        if not update_data:
            return jsonify({"error": "No JSON data"}), 400

        print(
            f"📨 Processing webhook update: {update_data.get('message', {}).get('text', 'N/A')[:50]}..."
        )

        update = types.Update(**update_data)

        # Process update asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(dp_instance.feed_update(bot_instance, update))
        loop.close()

        print("✅ Webhook update processed successfully")
        return jsonify({"status": "OK"})
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500


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
