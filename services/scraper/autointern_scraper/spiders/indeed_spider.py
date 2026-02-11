"""Indeed Job Spider

This spider scrapes job listings from Indeed.com.
Configuration is loaded from sites_config.yaml

Usage:
    scrapy crawl indeed

Environment:
    REDIS_URL: Redis connection URL (default: redis://localhost:6379)
"""

from autointern_scraper.spiders.base_spider import BaseJobSpider


class IndeedSpider(BaseJobSpider):
    """
    Spider for scraping jobs from Indeed.com

    Indeed provides:
    - 500+ million jobs globally
    - US, Canada, Europe, Asia coverage
    - Job descriptions, salary ranges, company info
    - Full-time, part-time, contract positions

    Selectors are defined in sites_config.yaml under 'indeed' section.
    """

    name = 'indeed'
    site_name = 'indeed'
    allowed_domains = ['indeed.com']

    # These are populated by BaseJobSpider from sites_config.yaml
    start_urls = []  # Generated dynamically in start_requests()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.info(f"Initializing {self.name} spider")
        self.logger.info(f"  Base URL: {self.site_config['base_url']}")
        self.logger.info(f"  Search queries: {len(self.site_config.get('search_queries', []))}")
        self.logger.info(f"  Locations: {len(self.site_config.get('search_locations', []))}")
        self.logger.info(f"  Max pages: {self.site_config['pagination'].get('max_pages', 10)}")
