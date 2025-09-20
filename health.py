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

    # SIMPLE cleanup: Just terminate existing subprocess
    print("Ì∑π Performing simple bot process cleanup...")

    if bot_process and bot_process.poll() is None:
        print(f"Ìªë Terminating existing bot subprocess (PID: {bot_process.pid})...")
        try:
            bot_process.terminate()
            bot_process.wait(timeout=3)
            print("‚úÖ Old bot subprocess terminated")
        except subprocess.TimeoutExpired:
            bot_process.kill()
            print("‚ö†Ô∏è Old bot subprocess force killed")
        except Exception as e:
            print(f"‚ö†Ô∏è Could not terminate subprocess: {e}")

    # Clean up lock file if exists
    lock_file = "/tmp/skin-advisor.lock"
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print("‚úÖ Lock file cleaned up")
        except Exception as e:
            print(f"‚ö†Ô∏è Could not remove lock file: {e}")

    print("‚úÖ Process cleanup completed")

    if bot_process is None or bot_process.poll() is not None:
        print("Ì∫Ä Starting bot process...")
        print(f"Ì∞ç Python executable: {sys.executable}")
        print("Ì≥¶ Command: python -m bot.main")
        try:
            # Don't capture stdout/stderr - let bot log directly
            bot_process = subprocess.Popen([sys.executable, "-m", "bot.main"])
            print(f"‚úÖ Bot process created with PID: {bot_process.pid}")

            # Check if process is still running after 3 seconds
            import time
            time.sleep(3)
            if bot_process.poll() is None:
                print("‚úÖ Bot process is running after 3 seconds - logs should appear above")
            else:
                print(f"‚ùå Bot process exited immediately with code: {bot_process.returncode}")
                # Try to get any remaining output
                try:
                    stdout, stderr = bot_process.communicate(timeout=5)
                    if stdout:
                        print(f"Ì∫® Bot stdout: {stdout}")
                    if stderr:
                        print(f"Ì∫® Bot stderr: {stderr}")
                except:
                    print("‚ö†Ô∏è Could not read bot output")

        except Exception as e:
            print(f"‚ùå Failed to start bot process: {e}")
            return None

    return bot_process

def stop_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        print(f"Ìªë Stopping bot process (PID: {bot_process.pid})...")
        bot_process.terminate()
        try:
            bot_process.wait(timeout=10)
            print("‚úÖ Bot stopped gracefully")
        except subprocess.TimeoutExpired:
            bot_process.kill()
            print("‚ö†Ô∏è Bot force killed")

@app.route("/start")
def start():
    start_bot()
    return "Bot started"

@app.route("/stop")
def stop():
    stop_bot()
    return "Bot stopped"

if __name__ == "__main__":
    print("ÌøÅ Starting application...")
    print(f"Ì≥¶ Python path: {sys.path[:3]}...")  # Show first 3 paths
    print(f"Ì≥Å Current directory: {os.getcwd()}")

    # Start bot on startup
    print("Ì¥ñ Attempting to start bot...")
    bot_started = start_bot()

    if bot_started is None:
        print("‚ùå CRITICAL: Bot failed to start!")
        print("Ì¥ç Check BOT_TOKEN and other environment variables")
        # Continue with Flask anyway for health checks
    else:
        print("‚úÖ Bot start initiated")

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print(f"Ì≥° Received signal {signum}, shutting down...")
        stop_bot()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Start Flask server (use PORT env var for Render)
    port = int(os.getenv("PORT", "10000"))
    print(f"Ìºê Starting Flask server on port {port}")
    print("Ì¥ç Environment variables:")
    for key in ['BOT_TOKEN', 'PORT', 'USE_WEBHOOK']:
        value = os.getenv(key, 'NOT_SET')
        if key == 'BOT_TOKEN' and value != 'NOT_SET':
            value = value[:10] + '...'  # Hide token
        print(f"  {key}: {value}")

    try:
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        print(f"‚ùå Flask server failed to start: {e}")
        sys.exit(1)
