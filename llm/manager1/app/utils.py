import httpx

async def call_ollama_generate(payload):
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post("http://localhost:11434/api/generate", json=payload)
        response.raise_for_status()
        return response.json()
