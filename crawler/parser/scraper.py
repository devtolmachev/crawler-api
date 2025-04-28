import asyncio
from datetime import datetime
import os
import random
import re
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

import httpx
from loguru import logger
import uvloop
from playwright.async_api import Browser, async_playwright

from crawler.parser import request_parser, browser_parser
from crawler.parser.bs4_scrapper_links import scrap_links_from_html
from crawler.parser.utils import append_ua_to_headers


GLOBAL_THREAD_POOL = ThreadPoolExecutor()
GLOBAL_ASYNC_SEMAPHORE = asyncio.Semaphore(max(30, os.cpu_count() or 1 + 6))

async def iter_links(html: str, base_domain: str):
    global GLOBAL_THREAD_POOL
    loop = asyncio.get_running_loop()
    links = await loop.run_in_executor(
        GLOBAL_THREAD_POOL,
        partial(
            scrap_links_from_html, html=html, base_domain=base_domain
        )
    )
    if not links:
        logger.error(f"Not found links on url: {base_domain}")
        return

    for link in links:
        yield link


async def get_html(url: str, browser: Browser, timeout: int = 5):
    global GLOBAL_ASYNC_SEMAPHORE
    headers = append_ua_to_headers()
    httpx_client = httpx.AsyncClient(headers=headers, timeout=httpx.Timeout(timeout))
    html = await request_parser.get_html(client=httpx_client, url=url)

    if not isinstance(html, str):
        extra_http_headers = headers.copy()
        async with GLOBAL_ASYNC_SEMAPHORE:
            page = await browser.new_page(
                user_agent=headers["user-agent"],
                extra_http_headers=extra_http_headers,
            )
            page.set_default_timeout(timeout * 1000 * 2.5)
            html = await browser_parser.get_html(page=page, url=url)

        if not isinstance(html, str):
            logger.error(f"Error when trying to get full html on: {url}")
            await asyncio.sleep(random.uniform(1, 3))
            return

    return html


async def get_links(url: str, browser: Browser, __cache=[], timeout: int = 5):
    links = __cache or []
    proto, base_domain = url.split("://")
    base_domain = base_domain.split("/")[0]
    html = await get_html(url, browser, timeout=timeout)
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
        and all(not l.count(symbol) for symbol in ["#", "?"])
    ]

    if url:
        linkss = links.copy()
        links = []
        for link in linkss:
            try:
                if link.startswith(url) and all(
                    l not in links for l in [link, link + "/", link.rstrip("/")]
                ):
                    links.append(link.rstrip("/"))
            except (IndexError, KeyError):
                continue

    return list(sorted(list(set(links))))


async def scrap_links(url: str, queue: asyncio.Queue = None, max_links_count: int = None):
    url = url + "/" if not url.endswith("/") else url
    links = []
    async with async_playwright() as plw:
        browser = await plw.firefox.launch(headless=True)
        async for link in get_links(url, browser):
            if queue:
                await queue.put(link)
            links.append(link)

        async def crawl_all_links(link, cache=[]):
            nonlocal links, browser
            ...
            if max_links_count and len(links) >= max_links_count:
                return
            async for link in get_links(link, browser, __cache=links.copy()):
                
                if link not in links:
                    if queue:
                        await queue.put(link)
                    links.append(link)

        tasks = [crawl_all_links(link, links.copy()) for link in links]
        await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )
    
    return filter_links(links if not max_links_count else links[:max_links_count], url=url)


async def main():
    # links = open("results.txt").read().split()
    
    
    urls = ["https://neostyle-nn.ru/sofas/"]
    urls = ["https://lookilife.nl"]

    for url in urls:
        start = datetime.now()
        links = await scrap_links(url)

        with open("results2.txt", "w") as f:
            f.write(f"{"\n".join(links)}")

        print(f"Crawle {len(links)} from url: {url}, at {datetime.now()-start}")
    ...


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(main())
