import os
import json
import time
import uuid
import subprocess
from flask import Flask, request, render_template, redirect, session, jsonify, send_from_directory
import httpx

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")

MANAGER1_URL = os.getenv("MANAGER1_URL", "http://manager1-service:8080")
MANAGER2_URL = os.getenv("MANAGER2_URL", "http://manager2-service:8080")
REPORTS_PATH = os.getenv("REPORTS_PATH", "/reports")
ASCIIDOCTOR_CMD = os.getenv("ASCIIDOCTOR_CMD", "asciidoctor-pdf")

os.makedirs(REPORTS_PATH, exist_ok=True)

TIMEOUT = httpx.Timeout(connect=30.0, read=300.0, write=300.0, pool=60.0)

# ----------------------------------------------------------------------------
# ROUTES
# ----------------------------------------------------------------------------

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/files/<path:filename>")
def download_file(filename):
    return send_from_directory(REPORTS_PATH, filename, as_attachment=True)

@app.route("/", methods=["GET"])
def index():
    history = session.get("history", [])
    return render_template("index.html", history=history)

@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("request_text", "").strip()
    if not prompt:
        return redirect("/")

    request_id = str(uuid.uuid4())
    adoc_file = f"{request_id}.adoc"
    pdf_file = f"{request_id}.pdf"
    adoc_path = os.path.join(REPORTS_PATH, adoc_file)
    pdf_path = os.path.join(REPORTS_PATH, pdf_file)

    full_conversation = []
    start_time = time.time()

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Step 1: Call Manager1
            manager1_payload = {"user_request": prompt}
            res1 = client.post(f"{MANAGER1_URL}/process", json=manager1_payload)
            res1.raise_for_status()
            manager1_result = res1.json()

            full_conversation.append({
                "role": "manager1",
                "content": json.dumps(manager1_result, indent=2)
            })

            subtasks = manager1_result.get("subtasks", [])
            if not subtasks:
                raise ValueError("Manager1 did not return any subtasks.")

            # Step 2: For each subtask → call Manager2
            assembled_sections = []
            for idx, subtask in enumerate(subtasks, start=1):
                manager2_payload = {"subtask": subtask}
                res2 = client.post(f"{MANAGER2_URL}/process", json=manager2_payload)
                res2.raise_for_status()
                manager2_result = res2.json()

                full_conversation.append({
                    "role": f"manager2 (subtask {idx})",
                    "content": json.dumps(manager2_result, indent=2)
                })

                section = manager2_result.get("final_output", "")
                assembled_sections.append(section)

            # Step 3: Assemble AsciiDoctor document
            assembled_doc = "\n\n".join(assembled_sections)
            with open(adoc_path, "w") as f:
                f.write(assembled_doc)

            # Step 4: Convert to PDF
            result = subprocess.run(
                [ASCIIDOCTOR_CMD, adoc_path, "-o", pdf_path],
                capture_output=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"asciidoctor-pdf error: {result.stderr.decode()}")

            # Step 5: Save result in history
            duration = round(time.time() - start_time, 2)
            history = session.get("history", [])
            history.append({
                "user_request": prompt,
                "messages": full_conversation,
                "adoc_file": f"/files/{adoc_file}",
                "pdf_file": f"/files/{pdf_file}",
                "response_time": duration
            })
            session["history"] = history

    except Exception as e:
        # Handle failure in one place
        duration = round(time.time() - start_time, 2)
        history = session.get("history", [])
        history.append({
            "user_request": prompt,
            "messages": full_conversation + [{
                "role": "error",
                "content": str(e)
            }],
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

