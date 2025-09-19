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

    # MULTI-LAYER cleanup: Try multiple methods to kill existing bot processes
    print("🧹 Performing MULTI-LAYER bot process cleanup...")
    total_killed = 0

    # Method 1: psutil (if available)
    try:
        import psutil
        current_pid = os.getpid()
        psutil_killed = 0

        print("🔍 Checking processes with psutil...")
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] in ['python', 'python3']:
                    cmdline = proc.info['cmdline'] or []
                    pid = proc.info['pid']

                    # Skip current Flask process
                    if pid == current_pid:
                        continue

                    # Check if it's our bot process
                    if any('bot.main' in arg or 'start.py' in arg or 'health.py' in arg for arg in cmdline):
                        print(f"🛑 Found bot-related process (PID: {pid}), terminating...")
                        try:
                            proc.terminate()
                            proc.wait(timeout=3)
                            print(f"✅ Process {pid} terminated gracefully")
                            psutil_killed += 1
                        except psutil.TimeoutExpired:
                            proc.kill()
                            print(f"⚠️ Process {pid} force killed")
                            psutil_killed += 1
                        except Exception as e:
                            print(f"⚠️ Could not kill process {pid}: {e}")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        print(f"🧹 psutil cleanup: {psutil_killed} processes terminated")
        total_killed += psutil_killed

    except ImportError:
        print("⚠️ psutil not available")
    except Exception as e:
        print(f"⚠️ psutil cleanup failed: {e}")

    # Method 2: pgrep/killall (system commands)
    try:
        print("🔍 Checking for python processes with system commands...")

        # Try pgrep first
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'bot.main'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                pids = [pid for pid in pids if pid.strip() and pid != str(current_pid)]
                if pids:
                    print(f"🛑 Found bot processes via pgrep: {pids}")
                    for pid in pids:
                        try:
                            subprocess.run(['kill', '-TERM', pid], timeout=3)
                            print(f"✅ Sent TERM to process {pid}")
                            total_killed += 1
                        except subprocess.TimeoutExpired:
                            subprocess.run(['kill', '-KILL', pid])
                            print(f"⚠️ Force killed process {pid}")
                        except Exception as e:
                            print(f"⚠️ Could not kill process {pid}: {e}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️ pgrep not available or failed")

        # Try killall as fallback
        try:
            result = subprocess.run(['killall', '-TERM', 'python'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                print("✅ Sent TERM to all python processes")
            else:
                print(f"⚠️ killall failed: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️ killall not available")

    except Exception as e:
        print(f"⚠️ System command cleanup failed: {e}")

    # Method 3: Lock file cleanup
    lock_file = "/tmp/skin-advisor.lock"
    if os.path.exists(lock_file):
        try:
            print(f"🧹 Removing old lock file: {lock_file}")
            os.remove(lock_file)
            print("✅ Lock file removed")
        except Exception as e:
            print(f"⚠️ Could not remove lock file: {e}")

    # Method 4: Terminate existing subprocess (fallback)
    if bot_process and bot_process.poll() is None:
        print(f"🛑 Terminating existing bot subprocess (PID: {bot_process.pid})...")
        bot_process.terminate()
        try:
            bot_process.wait(timeout=5)
            print("✅ Old bot subprocess terminated")
            total_killed += 1
        except subprocess.TimeoutExpired:
            bot_process.kill()
            print("⚠️ Old bot subprocess force killed")

    if total_killed > 0:
        print(f"🧹 Total cleanup: {total_killed} processes terminated")
        # Give Telegram time to detect terminations
        import time
        time.sleep(5)
    else:
        print("✅ No existing bot processes found")

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
