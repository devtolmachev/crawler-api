import re
import bs4

from crawler.parser.utils import error_handler


@error_handler
def scrap_links_from_html(html: str, base_domain: str) -> list[str]:
    soup = bs4.BeautifulSoup(html, "lxml")
    protos = ["http", "https"]
    links = []
    
    domain = f"{base_domain.split("://")[0]}://{base_domain.split("://")[1].split("/")[0]}"
    for tag in soup.find_all("a", href=True):
        if not isinstance(tag, bs4.Tag):
            continue
        
        link = tag.get("href")
        if not isinstance(link, str) or link == "/":
            continue
        
        if link.startswith("/"):
            link = f"{domain}{link}"
        
        proto = link.split("://")[0]
        if proto not in protos:
            continue
        
        updated_domain_url = re.sub(r"/{2,}", "/", link.split(f"{proto}://")[1])
        full_url = f"{proto}://{updated_domain_url}"
        
        if link not in links:
            links.append(full_url)
    
    return list(set(links))

