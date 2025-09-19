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

    # AGGRESSIVE cleanup: Find and kill ALL bot processes
    print("🧹 Performing aggressive bot process cleanup...")
    try:
        import psutil
        current_pid = os.getpid()

        # Find all python processes
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python' or proc.info['name'] == 'python3':
                    cmdline = proc.info['cmdline'] or []
                    pid = proc.info['pid']

                    # Skip current Flask process
                    if pid == current_pid:
                        continue

                    # Check if it's our bot process
                    if any('bot.main' in arg or 'start.py' in arg for arg in cmdline):
                        print(f"🛑 Found existing bot process (PID: {pid}), terminating...")
                        try:
                            proc.terminate()
                            # Wait up to 5 seconds for graceful shutdown
                            proc.wait(timeout=5)
                            print(f"✅ Bot process {pid} terminated gracefully")
                        except psutil.TimeoutExpired:
                            proc.kill()
                            print(f"⚠️ Bot process {pid} force killed")
                        killed_count += 1

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed_count > 0:
            print(f"🧹 Cleaned up {killed_count} existing bot processes")
            # Give Telegram some time to detect the termination
            import time
            time.sleep(3)
        else:
            print("✅ No existing bot processes found")

    except ImportError:
        print("⚠️ psutil not available, using basic cleanup...")
    except Exception as e:
        print(f"⚠️ Error during aggressive cleanup: {e}")

    # Terminate any existing bot process (fallback)
    if bot_process and bot_process.poll() is None:
        print(f"🛑 Terminating existing bot process (PID: {bot_process.pid})...")
        bot_process.terminate()
        try:
            bot_process.wait(timeout=5)
            print("✅ Old bot process terminated")
        except subprocess.TimeoutExpired:
            bot_process.kill()
            print("⚠️ Old bot process force killed")

    if bot_process is None or bot_process.poll() is not None:
        print("🚀 Starting bot process...")
        print(f"🐍 Python executable: {sys.executable}")
        print("📦 Command: python -m bot.main")
        try:
            # Don't capture stdout/stderr - let bot log directly
            bot_process = subprocess.Popen([sys.executable, "-m", "bot.main"])
            print(f"✅ Bot process created with PID: {bot_process.pid}")

            # Check if process is still running after 3 seconds
            import time
            time.sleep(3)
            if bot_process.poll() is None:
                print("✅ Bot process is running after 3 seconds - logs should appear above")
            else:
                print(f"❌ Bot process exited immediately with code: {bot_process.returncode}")
                # Try to get any remaining output
                try:
                    stdout, stderr = bot_process.communicate(timeout=5)
                    if stdout:
                        print(f"🚨 Bot stdout: {stdout}")
                    if stderr:
                        print(f"🚨 Bot stderr: {stderr}")
                except:
                    print("⚠️ Could not read bot output")

        except Exception as e:
            print(f"❌ Failed to start bot process: {e}")
            return None

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
    print("🏁 Starting application...")
    print(f"📦 Python path: {sys.path[:3]}...")  # Show first 3 paths
    print(f"📁 Current directory: {os.getcwd()}")

    # Start bot on startup
    print("🤖 Attempting to start bot...")
    bot_started = start_bot()

    if bot_started is None:
        print("❌ CRITICAL: Bot failed to start!")
        print("🔍 Check BOT_TOKEN and other environment variables")
        # Continue with Flask anyway for health checks
    else:
        print("✅ Bot start initiated")

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print(f"📡 Received signal {signum}, shutting down...")
        stop_bot()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Start Flask server (use PORT env var for Render)
    port = int(os.getenv("PORT", "10000"))
    print(f"🌐 Starting Flask server on port {port}")
    print("🔍 Environment variables:")
    for key in ['BOT_TOKEN', 'PORT', 'USE_WEBHOOK']:
        value = os.getenv(key, 'NOT_SET')
        if key == 'BOT_TOKEN' and value != 'NOT_SET':
            value = value[:10] + '...'  # Hide token
        print(f"  {key}: {value}")

    try:
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        print(f"❌ Flask server failed to start: {e}")
        sys.exit(1)
