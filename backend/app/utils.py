import httpx

TIMEOUT = httpx.Timeout(
    connect=30.0,
    read=300.0,
    write=300.0,
    pool=60.0
)

async def call_service(url, payload):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
