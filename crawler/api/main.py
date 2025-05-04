import asyncio
from datetime import datetime
from fastapi import FastAPI, Request
import httpx
import uvloop
import uvicorn

from pydantic import BaseModel

from crawler.parser.scraper import scrap_links, scrap_links_and_send_to
from crawler.parser.utils import error_handler, get_proxy_iproyal

app = FastAPI()


@error_handler
async def set_post_request(url: str, data: str | dict):
    async with httpx.AsyncClient() as client:
        await client.post(url, data=data)


class TaskBody(BaseModel):
    website_id: str
    website_url: str
    endpoint_url: str
    slice: int | None = None
    proxy: str | None = None


@app.post("/get_links")
async def get_links(task: TaskBody):
    loop = asyncio.get_running_loop()
    proxy = task.proxy
    if not proxy:
        proxy = get_proxy_iproyal(session_seconds=200)
        
    asyncio.eager_task_factory(
        loop=loop,
        coro=scrap_links_and_send_to(
            endpoint_url=task.endpoint_url,
            website_id=task.website_id,
            slice=task.slice,
            website_url=task.website_url,
            try_proxy=proxy
        ),
    )
    return {
        "ok": True,
        "message": f"task has been created and result will send on {task.endpoint_url}",
    }


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
