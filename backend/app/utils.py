import httpx

async def call_service(url, payload):
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
