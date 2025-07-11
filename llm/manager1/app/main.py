from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import logging
import re
from app.utils import call_ollama_generate

# ----------------------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------

PROMPT_FILE_PATH = "/home/ollama/prompts/prompt.txt"
MODEL_FILE_PATH = "/home/ollama/model/model.txt"

def load_system_prompt():
    with open(PROMPT_FILE_PATH, "r") as f:
        return f.read()

def load_model_name():
    try:
        with open(MODEL_FILE_PATH, "r") as f:
            return f.read().strip()
    except Exception:
        # fallback if not mounted
        return "mixtral:8x7b"

SYSTEM_PROMPT = load_system_prompt()
MODEL_NAME = load_model_name()

# ----------------------------------------------------------------------------
# UTILS
# ----------------------------------------------------------------------------

def extract_json_from_text(text: str):
    """
    Try to extract the first JSON object or array found in the text.
    """
    try:
        match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        logger.error(f"Regex JSON extraction failed: {e}")
    return None

# ----------------------------------------------------------------------------
# FastAPI App
# ----------------------------------------------------------------------------

app = FastAPI(title="Manager1 Service", version="1.0")

class ProcessRequest(BaseModel):
    user_request: str

class ProcessResponse(BaseModel):
    subtasks: list

@app.post("/process", response_model=ProcessResponse)
async def process_task(request: ProcessRequest):
    """
    Decompose user request into subtasks using system prompt and local Ollama.
    """
    final_prompt = f"""{SYSTEM_PROMPT}

USER REQUEST:
{request.user_request}

Return the list of subtasks in JSON format:
"""

    ollama_payload = {
        "model": MODEL_NAME,
        "prompt": final_prompt,
        "stream": False
    }

    try:
        logger.info(f"Sending prompt to Ollama: {final_prompt[:200]}...")
        result = await call_ollama_generate(ollama_payload)
        raw_response = result.get("response", "")
        logger.info(f"Ollama raw response: {raw_response}")

        # First attempt: direct JSON
        try:
            parsed = json.loads(raw_response)
            return {"subtasks": parsed}
        except json.JSONDecodeError as e:
            logger.warning(f"Direct JSON parse failed: {e}")

        # Second attempt: extract JSON from text
        parsed = extract_json_from_text(raw_response)
        if parsed:
            logger.info("Successfully extracted JSON from text fallback.")
            return {"subtasks": parsed}

        logger.error("Failed to extract JSON from Ollama response.")
        raise HTTPException(status_code=500, detail="Ollama returned non-JSON output. Please refine your system prompt.")

    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama error: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

