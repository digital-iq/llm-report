import os
import json
import time
from flask import Flask, request, render_template, redirect, session, jsonify
import httpx

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")

MANAGER1_URL = os.getenv("MANAGER1_URL", "http://manager1-service:8080")
TIMEOUT = httpx.Timeout(connect=30.0, read=300.0, write=300.0, pool=60.0)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def index():
    history = session.get("history", [])
    return render_template("index.html", history=history)

@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("request_text", "").strip()
    if not prompt:
        return redirect("/")

    start_time = time.time()
    try:
        payload = {"user_request": prompt}
        with httpx.Client(timeout=TIMEOUT) as client:
            res = client.post(f"{MANAGER1_URL}/process", json=payload)
            res.raise_for_status()
            result = res.json()
    except Exception as e:
        result = {"error": f"Failed to contact Manager1: {str(e)}"}
    end_time = time.time()
    duration = round(end_time - start_time, 2)

    history = session.get("history", [])

    # NEW: store whole thread
    history.append({
        "user_request": prompt,
        "messages": [
            {
                "role": "manager1",
                "content": json.dumps(result, indent=2)
            }
        ],
        "response_time": duration
    })

    session["history"] = history

    return redirect("/")

@app.route("/clear", methods=["POST"])
def clear():
    session["history"] = []
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

