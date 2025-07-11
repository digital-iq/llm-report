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

def extract_all_json_objects(text: str):
    """
    Extract all JSON objects or arrays found in the text.
    Returns a list of dicts.
    """
    json_objects = []
    try:
        # Greedy matching of braces/brackets
        pattern = r'(\{.*?\}|\[.*?\])'
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                obj = json.loads(match)
                if isinstance(obj, dict):
                    json_objects.append(obj)
                elif isinstance(obj, list):
                    json_objects.extend(obj)
            except Exception as e:
                logger.warning(f"Failed to parse match as JSON: {e}")
        return json_objects
    except Exception as e:
        logger.error(f"Regex extraction error: {e}")
    return []

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

Return ONLY a valid JSON array of subtasks with no extra text before or after.
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

        # Attempt 1: Direct parse as JSON list
        try:
            parsed = json.loads(raw_response)
            if isinstance(parsed, dict):
                logger.warning("Ollama returned single JSON object instead of list. Wrapping it.")
                parsed = [parsed]
            elif not isinstance(parsed, list):
                raise ValueError("Ollama output is not a list or object.")
            logger.info("Direct JSON parse successful.")
            return {"subtasks": parsed}
        except json.JSONDecodeError as e:
            logger.warning(f"Direct JSON parse failed: {e}")

        # Attempt 2: Fallback extraction from text
        logger.info("Attempting fallback regex-based JSON extraction...")
        parsed_list = extract_all_json_objects(raw_response)
        if parsed_list:
            logger.info(f"Successfully extracted {len(parsed_list)} JSON object(s) from text fallback.")
            return {"subtasks": parsed_list}

        logger.error("Failed to extract any JSON from Ollama response.")
        raise HTTPException(status_code=500, detail="Ollama returned no usable JSON subtasks. Please refine your system prompt.")

    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama error: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

