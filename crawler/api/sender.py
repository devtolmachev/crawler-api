import aiohttp
import orjson


async def send_links_to(
    url: str, 
    links: list[str], 
    took_ms: float,
    message: str,
    website_id: str,
    ok: bool = True
):
    request_body = {
        "success": ok,
        "website_id": website_id,
        "links_array": links,
        "took_ms": took_ms,
        "message": message,
    }
    async with aiohttp.ClientSession(json_serialize=lambda val: orjson.dumps(val).decode()) as session:
        async with session.post(url, json=request_body) as resp:
            ...
    ...
