#!/usr/bin/env python
"""Entry point that starts both Flask health server and bot."""

import sys
import os
import asyncio
import subprocess
import signal
import time
from flask import Flask

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create Flask app for health checks
app = Flask(__name__)

@app.route("/health")
def health():
    return "OK"

def run_flask():
    """Run Flask server"""
    port = int(os.getenv("PORT", "8080"))
    print(f"🌐 Starting Flask health server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)

def run_bot():
    """Run the bot in subprocess to avoid conflicts"""
    print("🤖 Starting bot in subprocess...")

    # Kill any existing bot processes
    try:
        subprocess.run(['pkill', '-f', 'python.*main'], timeout=5, capture_output=True)
        time.sleep(2)  # Wait for processes to die
    except:
        pass

    # Start bot in subprocess
    try:
        bot_process = subprocess.Popen(
            [sys.executable, '-m', 'bot.main'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        print(f"✅ Bot process started with PID: {bot_process.pid}")

        # Wait a bit for bot to initialize
        time.sleep(5)

        # Check if process is still running
        if bot_process.poll() is None:
            print("✅ Bot process is running")
            return bot_process
        else:
            stdout, stderr = bot_process.communicate()
            print(f"❌ Bot process failed to start")
            if stderr:
                print(f"Bot stderr: {stderr.decode()}")
            return None

    except Exception as e:
        print(f"❌ Failed to start bot process: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Starting combined Flask + Bot server...")

    # Start bot first
    bot_process = run_bot()

    if bot_process is None:
        print("❌ CRITICAL: Bot failed to start, exiting...")
        sys.exit(1)

    # Start Flask in main thread
    try:
        run_flask()
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
        if bot_process and bot_process.poll() is None:
            print("🛑 Terminating bot process...")
            bot_process.terminate()
            try:
                bot_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                bot_process.kill()
        sys.exit(0)
