from flask import Flask
import os

app = Flask(__name__)

@app.route("/health")
def health():
    return f"OK - PID: {os.getpid()}"

@app.route("/")
def index():
    return "Bot health check server is running"

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    print(f"Starting test server on port {port}")
    app.run(host="0.0.0.0", port=port)
