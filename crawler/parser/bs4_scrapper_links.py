import bs4

from crawler.parser.utils import error_handler


@error_handler
def scrap_links_from_html(html: str, base_domain: str) -> list[str]:
    soup = bs4.BeautifulSoup(html, "lxml")
    protos = ["http", "https"]
    links = []
    for tag in soup.find_all("a", href=True):
        if not isinstance(tag, bs4.Tag):
            continue
        
        link = tag.get("href")
        if not isinstance(link, str):
            continue
        
        if link.startswith("/"):
            link = f"{base_domain}{link}"
        
        proto = link.split("://")[0]
        if proto not in protos:
            continue
        
        if link not in links:
            links.append(link)
    
    return list(set(links))

