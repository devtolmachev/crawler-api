import asyncio
from datetime import datetime
from fastapi import FastAPI
import httpx
import uvloop
import uvicorn

from crawler.parser.scraper import scrap_links
from crawler.parser.utils import error_handler

app = FastAPI()


@error_handler
async def set_post_request(url: str, data: str | dict):
    async with httpx.AsyncClient() as client:
        await client.post(url, data=data)


@app.get("/get_links")
async def get_links(url: str, slice: int = None):
    start = datetime.now()
    result = await scrap_links(url=url, max_links_count=slice)
    ms = (datetime.now() - start).microseconds
    return {"took_ms": ms, "resilt": result}

@app.get("/working")
async def get_links():
    return {"working": True}


@app.post("/put_links")
async def long_task(url: str, webhook_url: str):
    
    @error_handler
    async def get_links(queue: asyncio.Queue):
        while True:
            start = datetime.now()
            data = await queue.get()
            
            if data == "finish":
                break
            
            ms = (datetime.now() - start).microseconds
            response = {"took_ms": ms, "resilt": [data]}
            await set_post_request(webhook_url, response)
    
    q = asyncio.Queue()
    await asyncio.gather(get_links(q), scrap_links(url, queue=q))


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    uvicorn.run(app=app, host="0.0.0.0", port=5500)
