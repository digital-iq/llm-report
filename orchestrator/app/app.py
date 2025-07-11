import os
import json
import time
import uuid
import subprocess
import logging
from flask import Flask, request, render_template, redirect, session, jsonify, send_from_directory
import httpx

# ----------------------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")

MANAGER1_URL = os.getenv("MANAGER1_URL", "http://manager1-service:8080")
MANAGER2_URL = os.getenv("MANAGER2_URL", "http://manager2-service:8080")
REPORTS_PATH = os.getenv("REPORTS_PATH", "/reports")
USER_HISTORY_PATH = os.getenv("USER_HISTORY_PATH", "/user_histories")
ASCIIDOCTOR_CMD = os.getenv("ASCIIDOCTOR_CMD", "asciidoctor-pdf")

os.makedirs(REPORTS_PATH, exist_ok=True)
os.makedirs(USER_HISTORY_PATH, exist_ok=True)

TIMEOUT = httpx.Timeout(connect=30.0, read=300.0, write=300.0, pool=60.0)

# ----------------------------------------------------------------------------
# USER HISTORY HELPERS
# ----------------------------------------------------------------------------

def get_user_id():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    return session["user_id"]

def get_history_file(user_id):
    return os.path.join(USER_HISTORY_PATH, f"{user_id}.json")

def load_history(user_id):
    filepath = get_history_file(user_id)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history for {user_id}: {e}")
    return []

def save_history(user_id, history):
    filepath = get_history_file(user_id)
    try:
        with open(filepath, "w") as f:
            json.dump(history, f)
    except Exception as e:
        logger.error(f"Failed to save history for {user_id}: {e}")

# ----------------------------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------------------------

def is_engineer1_task(subtask):
    fmt = subtask.get("expected_format", "").lower()
    prompt_text = subtask.get("manager2_prompt", "").lower()
    return (
        "command" in fmt or "plain text" in fmt
        or "provide commands" in prompt_text
        or "command outputs" in prompt_text
    )

def emulate_engineer1_output(subtask):
    title = subtask.get('subtask', 'Unknown Task')
    logger.info(f"Emulating Engineer1 output for subtask: {title}")
    return {
        "final_output": f"""[EMULATED ENGINEER1 OUTPUT]

This is simulated command output for subtask:

{title}

Example results:

oc get nodes
----------------
NAME       STATUS   ROLES    AGE   VERSION
master-0   Ready    master   60d   v4.12.3
worker-0   Ready    worker   60d   v4.12.3

oc get pods --all-namespaces
------------------------------
NAMESPACE       NAME                           READY   STATUS
openshift-api   api-server-xyz                 1/1     Running
...
"""
    }

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
    user_id = get_user_id()
    history = load_history(user_id)
    return render_template("index.html", history=history)

@app.route("/generate", methods=["POST"])
def generate():
    user_id = get_user_id()
    history = load_history(user_id)

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
            logger.info("Calling Manager1 for task decomposition.")
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

            # Step 2: Process subtasks
            assembled_sections = []
            prior_context = ""
            for idx, subtask in enumerate(subtasks, start=1):
                subtask_title = subtask.get("subtask", f"Subtask {idx}")
                logger.info(f"Processing subtask {idx}: {subtask_title}")

                if is_engineer1_task(subtask):
                    engineer1_result = emulate_engineer1_output(subtask)
                    full_conversation.append({
                        "role": f"engineer1 (subtask {idx})",
                        "content": json.dumps(engineer1_result, indent=2)
                    })
                    prior_context += f"\n\nENGINEER1 OUTPUT:\n{engineer1_result['final_output']}"
                    assembled_sections.append(engineer1_result["final_output"])

                else:
                    manager2_payload = {
                        "subtask": subtask,
                        "prior_context": prior_context
                    }
                    logger.info(f"Calling Manager2 for subtask {idx}")
                    res2 = client.post(f"{MANAGER2_URL}/process", json=manager2_payload)
                    res2.raise_for_status()
                    manager2_result = res2.json()

                    full_conversation.append({
                        "role": f"manager2 (subtask {idx})",
                        "content": json.dumps(manager2_result, indent=2)
                    })

                    section = manager2_result.get("final_output", "")
                    assembled_sections.append(section)
                    prior_context += f"\n\nMANAGER2 OUTPUT:\n{section}"

            # Step 3: Write AsciiDoctor document
            assembled_doc = "\n\n".join(assembled_sections)
            with open(adoc_path, "w") as f:
                f.write(assembled_doc)
            logger.info(f"AsciiDoctor source written to {adoc_path}")

            # Step 4: Convert to PDF
            logger.info(f"Converting {adoc_file} to PDF using {ASCIIDOCTOR_CMD}")
            result = subprocess.run(
                [ASCIIDOCTOR_CMD, adoc_path, "-o", pdf_path],
                capture_output=True
            )
            if result.returncode != 0:
                logger.error(result.stderr.decode())
                raise RuntimeError(f"asciidoctor-pdf error: {result.stderr.decode()}")
            logger.info(f"PDF generated at {pdf_path}")

            # Step 5: Save result in history
            duration = round(time.time() - start_time, 2)
            history.append({
                "user_request": prompt,
                "messages": full_conversation,
                "adoc_file": f"/files/{adoc_file}",
                "pdf_file": f"/files/{pdf_file}",
                "response_time": duration
            })
            save_history(user_id, history)

    except Exception as e:
        logger.error(f"Error during generation: {e}")
        duration = round(time.time() - start_time, 2)
        history.append({
            "user_request": prompt,
            "messages": full_conversation + [{
                "role": "error",
                "content": str(e)
            }],
            "response_time": duration
        })
        save_history(user_id, history)

    return redirect("/")

@app.route("/clear", methods=["POST"])
def clear():
    user_id = get_user_id()
    save_history(user_id, [])
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

