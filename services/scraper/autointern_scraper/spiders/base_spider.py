from scrapy import Spider, Request

class BaseJobSpider(Spider):
    custom_settings = {
        # Configure playright, proxies, middlewares in real implementation
    }

    def start_requests(self):
        # Placeholder: load site config and generate start requests
        yield Request(url=self.start_urls[0])

    def parse(self, response):
        # Placeholder parsing logic
        self.logger.info("Base spider response received")
        yield {
            "title": "stub",
            "company": "stub",
            "location": "remote",
            "raw": response.text[:500]
        }
