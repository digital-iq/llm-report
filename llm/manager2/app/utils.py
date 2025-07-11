import httpx

TIMEOUT = httpx.Timeout(
    connect=300.0,
    read=300.0,    # 5 min read timeout for big CPU generations
    write=300.0,
    pool=300.0
)

async def call_ollama_generate(payload):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post("http://localhost:11434/api/generate", json=payload)
        response.raise_for_status()
        return response.json()

