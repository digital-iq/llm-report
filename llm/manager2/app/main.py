from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import logging
from app.utils import call_ollama_generate

# ----------------------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------

MODEL_FILE_PATH = "/home/ollama/model/model.txt"
PROMPT_FILE_PATH = "/home/ollama/prompts/prompt.txt"

def load_system_prompt():
    try:
        with open(PROMPT_FILE_PATH, "r") as f:
            return f.read()
    except Exception:
        return ""

def load_model_name():
    try:
        with open(MODEL_FILE_PATH, "r") as f:
            return f.read().strip()
    except Exception:
        return "mixtral:8x7b"

SYSTEM_PROMPT = load_system_prompt()
MODEL_NAME = load_model_name()

# ----------------------------------------------------------------------------
# FastAPI App
# ----------------------------------------------------------------------------

app = FastAPI(title="Manager2 Service", version="1.0")

# ----------------------------------------------------------------------------
# Pydantic models
# ----------------------------------------------------------------------------

class Subtask(BaseModel):
    subtask: str
    purpose: str
    expected_format: str
    manager2_prompt: str

class SubtaskRequest(BaseModel):
    subtask: Subtask

class SubtaskResponse(BaseModel):
    final_output: str

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------

@app.post("/process", response_model=SubtaskResponse)
async def process_subtask(request: SubtaskRequest):
    """
    Handles a single subtask coming from Orchestrator.
    Decides whether to answer directly or instruct Engineer1.
    """

    sub = request.subtask
    logger.info(f"Received subtask: {sub.dict()}")

    # Decide whether it needs Engineer1
    if "command" in sub.expected_format.lower() or "plain text command" in sub.expected_format.lower():
        # Needs Engineer1 (future implementation)
        logger.warning("This subtask needs Engineer1 integration, which is not yet implemented.")
        raise HTTPException(status_code=501, detail="Engineer1 integration not implemented yet.")
    else:
        # Manager2 can handle this subtask directly
        final_prompt = f"""{SYSTEM_PROMPT}

You are Manager #2. Answer the following subtask in detail.

SUBTASK:
{sub.subtask}

PURPOSE:
{sub.purpose}

EXPECTED FORMAT:
{sub.expected_format}

INSTRUCTION FOR YOU:
{sub.manager2_prompt}
"""

        ollama_payload = {
            "model": MODEL_NAME,
            "prompt": final_prompt,
            "stream": False
        }

        logger.info("Sending prompt to Ollama...")
        try:
            result = await call_ollama_generate(ollama_payload)
            answer = result.get("response", "").strip()
            logger.info("Received answer from Ollama.")
            return {"final_output": answer}
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise HTTPException(status_code=500, detail=f"Ollama error: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

