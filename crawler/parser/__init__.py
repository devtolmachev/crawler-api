from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class LinkSpider(CrawlSpider):
    name = "link_spider"
    start_urls = ["https://programarecetatenie.eu"]

    def parse_item(self, response):
        for link in LinkExtractor().extract_links(response):
            self.links.append(link.url)
            
    def parse(self, response):
        for href in response.css("a::attr(href)").extract():
            yield response.follow(href, self.parse)

    def __init__(self):
        super().__init__()
        self.links = []


async def main():
    start = datetime.now()
    print(start)

    process = LinkSpider()

    print(process.links)
    print(datetime.now() - start)
    ...


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
