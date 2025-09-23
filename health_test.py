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
    port = int(os.getenv("PORT", "8080"))  # Render uses 8080
    print(f"Starting test server on port {port}")
    print(f"PORT env var: {os.getenv('PORT')}")
    app.run(host="0.0.0.0", port=port)
