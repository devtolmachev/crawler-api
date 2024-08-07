import httpx

from crawler.parser.utils import error_handler


@error_handler
async def get_html(client: httpx.AsyncClient, url: str, headers: dict = None):
    resp = await client.get(url, headers=headers)
    
    if resp.is_error:
        return

    return resp.text
    