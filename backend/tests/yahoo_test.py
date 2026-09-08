import asyncio
import httpx

URL = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=TSLA&region=US&lang=en-US"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def main():
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            URL,
            headers={"User-Agent": UA},
        )

        print("STATUS:", response.status_code)
        print("LENGTH:", len(response.content))
        print(response.text[:200])


asyncio.run(main())