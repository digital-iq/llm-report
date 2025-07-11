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
        logger.warning("Prompt file not found or unreadable. Using empty prompt.")
        return ""

def load_model_name():
    try:
        with open(MODEL_FILE_PATH, "r") as f:
            return f.read().strip()
    except Exception:
        logger.warning("Model file not found. Defaulting to 'mixtral:8x7b'")
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
    prior_context: str = ""  # New: Orchestrator will pass accumulated prior context here

class SubtaskResponse(BaseModel):
    final_output: str

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------

@app.post("/process", response_model=SubtaskResponse)
async def process_subtask(request: SubtaskRequest):
    """
    Handles a single subtask from Orchestrator.
    Incorporates prior_context so Manager2 can "see" Engineer1 outputs and earlier sections.
    """

    sub = request.subtask
    logger.info(f"Processing subtask: {sub.subtask}")

    # Decide whether it's intended for Engineer1
    if "command" in sub.expected_format.lower() or "plain text" in sub.expected_format.lower():
        logger.warning("Engineer1 task detected. This should be emulated by Orchestrator. Rejecting at Manager2 level.")
        raise HTTPException(
            status_code=501,
            detail="This subtask requires Engineer1 output. Manager2 cannot handle it directly."
        )

    # Build the prompt including prior context
    final_prompt = f"""{SYSTEM_PROMPT}

You are Manager #2. Your task is to answer the following subtask in detail.

SUBTASK TITLE:
{sub.subtask}

PURPOSE:
{sub.purpose}

EXPECTED OUTPUT FORMAT:
{sub.expected_format}

INSTRUCTION:
{sub.manager2_prompt}

----------------------------
CONTEXT FROM EARLIER TASKS:
{request.prior_context}
----------------------------

Your answer should consider all prior context and produce the requested section of the report.
"""

    logger.debug(f"Final prompt for Ollama (truncated): {final_prompt[:300]}...")

    ollama_payload = {
        "model": MODEL_NAME,
        "prompt": final_prompt,
        "stream": False
    }

    try:
        logger.info("Sending prompt to Ollama for generation...")
        result = await call_ollama_generate(ollama_payload)
        answer = result.get("response", "").strip()
        if not answer:
            logger.warning("Ollama returned an empty response.")
            raise ValueError("Empty response from Ollama.")
        logger.info("Successfully received answer from Ollama.")
        return {"final_output": answer}
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama error: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

