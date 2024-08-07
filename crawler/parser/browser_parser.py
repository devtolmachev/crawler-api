import asyncio
from datetime import datetime
from loguru import logger
from playwright.async_api import async_playwright, Playwright, Browser, Page
import bs4

from crawler.parser.utils import error_handler


links = []


@error_handler
async def get_html(page: Page, url: str):
    await page.goto(url)
    return await page.content()


async def scrap_child_links(browser: Browser, url: str):
    global links
    if "https://" not in url:
        return

    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded")
    except Exception as e:
        print(f"{e.__class__.__name__}: {e}")
        return
    
    domain = url.split("https://")[1].split("/")[0]
    html = await page.content()
    await page.close()

    soup = bs4.BeautifulSoup(html, "lxml")
    proto = url.split("://")[0]

    for i, tag in enumerate(soup.find_all("a", href=True)):
        if not isinstance(tag, bs4.Tag):
            continue

        link = tag["href"]
        try:
            if not link.startswith("http"):
                proto = url.split("://")[0]
                link = f"{proto}://{domain}{link}"
        except (KeyError, IndexError):
            continue

        if link in list(set(links)):
            continue

        # print(f"{i} {url}: {link}")
        links.append(link)
        yield link


async def scrap_links(browser: Browser, url: str):
    global links
    async for link in scrap_child_links(browser=browser, url=url):
        if link not in links:
            links.append(link)
            yield link
        else:
            ...

    domain = url.split("https://")[1].split("/")[0]
    proto = url.split("://")[0]
    for link in list(set(links)):
        if link != f"{proto}://{domain}" and link != f"{proto}://{domain}/":
            async for next_link in scrap_child_links(browser=browser, url=link):
                if next_link not in list(set(links)):
                    links.append(next_link)
                yield next_link


async def playwright_work(playwright: Playwright, url: str):
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    links = []

    async for link in scrap_links(browser=browser, url=url):
        with open("links.txt", "a") as f:
            f.write(f"{link}\n")
        links.append(link)

    return links


async def main():
    async with async_playwright() as plw:
        start = datetime.now()
        links = await playwright_work(
            playwright=plw, url="https://lookilife.nl/"
        )
        print(datetime.now() - start)
        print(len(links))
    ...


if __name__ == "__main__":
    asyncio.run(main())
