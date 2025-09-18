from flask import Flask
import subprocess
import signal
import sys
import os

app = Flask(__name__)
bot_process = None

@app.route("/health")
def health():
    return "OK"

def start_bot():
    global bot_process
    if bot_process is None or bot_process.poll() is not None:
        print("🚀 Starting bot process...")
        bot_process = subprocess.Popen([sys.executable, "-m", "bot.main"])
        print(f"✅ Bot started with PID: {bot_process.pid}")
    return bot_process

def stop_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        print(f"🛑 Stopping bot process (PID: {bot_process.pid})...")
        bot_process.terminate()
        try:
            bot_process.wait(timeout=10)
            print("✅ Bot stopped gracefully")
        except subprocess.TimeoutExpired:
            bot_process.kill()
            print("⚠️ Bot force killed")

@app.route("/start")
def start():
    start_bot()
    return "Bot started"

@app.route("/stop")
def stop():
    stop_bot()
    return "Bot stopped"

if __name__ == "__main__":
    # Start bot on startup
    start_bot()

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print(f"📡 Received signal {signum}, shutting down...")
        stop_bot()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Start Flask server
    app.run(host="0.0.0.0", port=10000)
