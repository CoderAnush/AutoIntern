Scraper service (Scrapy + Playwright)

- Config-driven spiders (YAML site definitions)
- BaseSpider with proxy, rate limiting, ban detection
- Pipelines push normalized results to Redis queue

Usage:
- `cd services/scraper` and run spiders via `scrapy crawl <name>`
