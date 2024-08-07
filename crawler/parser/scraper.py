import asyncio
from datetime import datetime
import random
import re

import httpx
from loguru import logger
import uvloop
from playwright.async_api import async_playwright

from crawler.parser import request_parser, browser_parser
from crawler.parser.bs4_scrapper_links import scrap_links_from_html
from crawler.parser.utils import append_ua_to_headers


async def iter_links(html: str, base_domain: str):
    links = scrap_links_from_html(html=html, base_domain=base_domain)
    if not links:
        logger.error(f"Not found links on url: {base_domain}")
        return

    for link in links:
        yield link


async def get_html(url: str, timeout: int = 5):
    headers = append_ua_to_headers()
    httpx_client = httpx.AsyncClient(
        headers=headers, timeout=httpx.Timeout(timeout)
    )
    html = await request_parser.get_html(client=httpx_client, url=url)

    if not isinstance(html, str):
        async with async_playwright() as plw:
            browser = await plw.chromium.launch(headless=True)

            extra_http_headers = headers.copy()
            extra_http_headers.pop("user-agent")
            page = await browser.new_page(
                user_agent=headers["user-agent"],
                extra_http_headers=extra_http_headers,
            )
            page.set_default_timeout(timeout)
            html = await browser_parser.get_html(page=page, url=url)

        if not isinstance(html, str):
            logger.error(f"Error when trying to get full html on: {url}")
            await asyncio.sleep(random.uniform(1, 3))
            return

    return html


async def get_links(url: str, __cache=[], timeout: int = 5):
    links = __cache or []
    proto, base_domain = url.split("://")
    base_domain = base_domain.split("/")[0]

    html = await get_html(url, timeout=timeout)
    if not isinstance(html, str):
        for link in links:
            yield link
        return

    async for link in iter_links(html, base_domain=url):
        if link not in links and link.count(base_domain):
            yield link
            links.append(link)


def filter_links(links: list[str], url: str = None) -> list[str]:
    if not links:
        raise ValueError(f"Not links: {links}")
    
    links = [
        f"{l.split("://")[0]}://{l.split("://")[1].replace("//", "/")}"
        for l in links
        if not re.findall(r"(.+)\..{2,4}$", l)
    ]
    
    if url:
        linkss = links.copy()
        links = []
        for link in linkss:
            try:
                if link.startswith(url):
                    links.append(link)
            except (IndexError, KeyError):
                continue
    
    return list(sorted(links))
    
    
async def scrap_links(url: str, queue: asyncio.Queue = None):
    url = url + "/" if not url.endswith("/") else url
    links = []
    async for link in get_links(url):
        if queue:
            await queue.put(link)
        links.append(link)

    async def crawl_all_links(link, cache=[]):
        nonlocal links
        async for link in get_links(link, __cache=links.copy()):
            if link not in links:
                if queue:
                    await queue.put(link)
                links.append(link)

    tasks = [crawl_all_links(link, links.copy()) for link in links]
    await asyncio.gather(
        *tasks,
        return_exceptions=True,
    )
    
    return filter_links(links, url=url)


async def main():
    
    links = open("results.txt").read().split()
    
    urls = ["https://lookilife.nl"]
    urls = ["https://neostyle-nn.ru/sofas/"]

    for url in urls:
        start = datetime.now()
        links = await scrap_links(url)

        with open("results.txt", "w") as f:
            f.write(f"{"\n".join(links)}")

        print(f"Crawle {len(links)} from url: {url}, at {datetime.now()-start}")
    ...


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
