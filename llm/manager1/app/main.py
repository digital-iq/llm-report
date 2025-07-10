from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
from app.utils import call_ollama_generate

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
        result = await call_ollama_generate(ollama_payload)
        parsed = json.loads(result["response"])
        return {"subtasks": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {e}")

