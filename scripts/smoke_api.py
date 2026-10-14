import asyncio

import httpx

from learning_plane.api.app import app


async def main() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        print(response.status_code, response.json())


if __name__ == "__main__":
    asyncio.run(main())
